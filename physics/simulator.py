"""
VoltGuard Physics Engine — Simulator

Orchestrates the full simulation pipeline:
    1. Load safety limits & physics parameters from centralized config
    2. Validate the incoming PhysicsCommand (Pydantic handles this)
    3. Run the physics equations (equations.py — pure functions)
    4. Run safety analysis (safety.py — classification + risk scoring)
    5. Return a structured PhysicsResult

Public API:
    simulate(command)                         → PhysicsResult
    simulate_timeseries(command, steps, dt)   → list[PhysicsResult]

The engine has zero dependency on FastAPI, database, or WebSocket layers.
It can be imported and called as a plain Python module from any context.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so this can be run standalone
# (e.g., python scripts/test_physics_demo.py from the project root)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.core.config import get_settings, SafetyLimits, PhysicsParameters
from backend.core.logging import get_logger
from physics.equations import (
    compute_flow,
    compute_pressure,
    compute_temperature,
    compute_stress,
)
from physics.models import PhysicsCommand, PhysicsResult, SafetyState
from physics.safety import compute_violations, compute_risk_score, build_explanation

logger = get_logger("physics.simulator")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_limits() -> SafetyLimits:
    """Return the configured safety limits (cached via lru_cache)."""
    return get_settings().safety_limits


def _get_params() -> PhysicsParameters:
    """Return the configured physics parameters (cached via lru_cache)."""
    return get_settings().physics


def _run_physics(cmd: PhysicsCommand, params: PhysicsParameters) -> tuple[float, float, float, float]:
    """
    Execute the physics equations for one time step.

    Returns:
        (flow, pressure, temperature, stress) — all in their configured units.
    """
    flow = compute_flow(
        pump_rpm=cmd.pump_rpm,
        valve_position=cmd.valve_position,
        reference_rpm=params.reference_rpm,
        base_flow=params.base_flow,
        pump_efficiency=cmd.pump_efficiency,
    )
    pressure = compute_pressure(
        current_pressure=cmd.current_pressure,
        flow=flow,
        pipeline_resistance=cmd.pipeline_resistance,
        pressure_gain_coefficient=params.pressure_gain_coefficient,
        pressure_loss_coefficient=params.pressure_loss_coefficient,
    )
    temperature = compute_temperature(
        current_temperature=cmd.current_temperature,
        flow=flow,
        thermal_gain_coefficient=params.thermal_gain_coefficient,
    )
    stress = compute_stress(
        predicted_pressure=pressure,
        stress_per_bar=params.stress_per_bar,
    )
    return flow, pressure, temperature, stress


def _build_result(
    cmd: PhysicsCommand,
    flow: float,
    pressure: float,
    temperature: float,
    stress: float,
    limits: SafetyLimits,
    elapsed_ms: float,
) -> PhysicsResult:
    """Assemble the PhysicsResult from raw computed values."""
    violations, safety_state = compute_violations(
        pump_rpm=cmd.pump_rpm,
        predicted_flow=flow,
        predicted_pressure=pressure,
        predicted_temperature=temperature,
        system_stress=stress,
        rpm_limit=float(limits.max_rpm),
        flow_limit=limits.max_flow,
        pressure_limit=limits.max_pressure,
        temperature_limit=limits.max_temperature,
        stress_limit=limits.max_stress,
    )
    risk_score = compute_risk_score(
        pump_rpm=cmd.pump_rpm,
        predicted_flow=flow,
        predicted_pressure=pressure,
        predicted_temperature=temperature,
        system_stress=stress,
        rpm_limit=float(limits.max_rpm),
        flow_limit=limits.max_flow,
        pressure_limit=limits.max_pressure,
        temperature_limit=limits.max_temperature,
        stress_limit=limits.max_stress,
    )
    explanation = build_explanation(violations, safety_state)

    return PhysicsResult(
        # Input echo
        pump_rpm=cmd.pump_rpm,
        valve_position=cmd.valve_position,
        current_pressure=cmd.current_pressure,
        current_temperature=cmd.current_temperature,
        # Predicted outputs
        predicted_flow=round(flow, 4),
        predicted_pressure=round(pressure, 4),
        predicted_temperature=round(temperature, 4),
        system_stress=round(stress, 4),
        # Limits (for auditability)
        pressure_limit=limits.max_pressure,
        rpm_limit=float(limits.max_rpm),
        temperature_limit=limits.max_temperature,
        flow_limit=limits.max_flow,
        stress_limit=limits.max_stress,
        # Risk assessment
        risk_score=risk_score,
        safety_state=safety_state,
        violations=violations,
        explanation=explanation,
        # Timing
        simulation_time_ms=round(elapsed_ms, 4),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate(command: PhysicsCommand | dict) -> PhysicsResult:
    """
    Run a single physics simulation step.

    Args:
        command: A PhysicsCommand instance OR a dict that can be coerced
                 into one (for convenience from the Modbus parser in Phase 3).

    Returns:
        PhysicsResult with predicted physical state and safety classification.

    Raises:
        PhysicsValidationError: If command contains invalid values.
                                (Pydantic raises ValidationError on dict input.)
        PhysicsSimulationError: If the simulation itself fails unexpectedly.
    """
    # Accept raw dicts for Phase 3 interop
    if isinstance(command, dict):
        command = PhysicsCommand(**command)

    limits = _get_limits()
    params = _get_params()

    logger.debug("[PHYSICS] Simulation started")
    logger.debug(f"[PHYSICS] RPM={command.pump_rpm}  Valve={command.valve_position}%")

    t_start = time.perf_counter()
    flow, pressure, temperature, stress = _run_physics(command, params)
    elapsed_ms = (time.perf_counter() - t_start) * 1000.0

    result = _build_result(command, flow, pressure, temperature, stress, limits, elapsed_ms)

    logger.debug(f"[PHYSICS] Predicted pressure={pressure:.2f} bar  flow={flow:.2f} L/min")
    logger.debug(f"[PHYSICS] Temperature={temperature:.2f}°C  stress={stress:.2f} MPa")
    logger.debug(f"[PHYSICS] RiskScore={result.risk_score}  State={result.safety_state}")

    if result.safety_state in (SafetyState.CRITICAL, SafetyState.CATASTROPHIC):
        logger.warning(
            f"[PHYSICS] RPM={command.pump_rpm}  "
            f"Pressure={pressure:.2f}  "
            f"Limit={limits.max_pressure}  "
            f"State={result.safety_state}"
        )

    return result


def simulate_timeseries(
    command: PhysicsCommand | dict,
    steps: int = 10,
    dt: float = 0.1,
) -> List[PhysicsResult]:
    """
    Run a lightweight time-step simulation.

    Each step uses the previous step's predicted pressure as the new
    current_pressure, modelling pressure build-up over time. All other
    inputs remain constant. This generates a trajectory suitable for
    dashboard visualization.

    Args:
        command: Initial PhysicsCommand.
        steps:   Number of time steps (default 10).
        dt:      Time step duration in seconds (informational only — the
                 simplified model is quasi-steady-state per step).

    Returns:
        List of PhysicsResult, one per time step.
    """
    if isinstance(command, dict):
        command = PhysicsCommand(**command)

    results: List[PhysicsResult] = []
    current_cmd = command.model_copy()

    logger.debug(f"[PHYSICS] Timeseries simulation: {steps} steps, dt={dt}s")

    for step in range(steps):
        result = simulate(current_cmd)
        results.append(result)
        # Feed predicted pressure back as input for next step
        current_cmd = current_cmd.model_copy(
            update={"current_pressure": result.predicted_pressure}
        )
        logger.debug(f"[PHYSICS] Step {step + 1}/{steps} — pressure={result.predicted_pressure:.2f} bar")

    return results
