"""
VoltGuard Phase 2 — Physics Engine Demo Script

Demonstrates the four key operating scenarios and runs a performance benchmark.

Usage (from project root):
    python scripts/test_physics_demo.py

No server needs to be running. The physics engine is called directly as a module.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Ensure project root is on sys.path regardless of where the script is called from
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from physics.simulator import simulate, simulate_timeseries
from physics.models import PhysicsCommand, SafetyState


# ---------------------------------------------------------------------------
# Colour helpers (simple ANSI — degrades gracefully on Windows without colour)
# ---------------------------------------------------------------------------

def _colour(text: str, code: str) -> str:
    """Wrap text in ANSI colour code if stdout supports it."""
    if sys.stdout.isatty():
        return f"\033[{code}m{text}\033[0m"
    return text

def green(t: str)  -> str: return _colour(t, "92")
def yellow(t: str) -> str: return _colour(t, "93")
def red(t: str)    -> str: return _colour(t, "91")
def bold(t: str)   -> str: return _colour(t, "1")
def cyan(t: str)   -> str: return _colour(t, "96")


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

STATE_COLOUR = {
    SafetyState.SAFE:         green,
    SafetyState.WARNING:      yellow,
    SafetyState.CRITICAL:     red,
    SafetyState.CATASTROPHIC: red,
    # str variants (model_config use_enum_values=True)
    "SAFE":         green,
    "WARNING":      yellow,
    "CRITICAL":     red,
    "CATASTROPHIC": red,
}


def _state_str(state) -> str:
    colourise = STATE_COLOUR.get(state, lambda x: x)
    return bold(colourise(str(state)))


def print_result(scenario_name: str, result) -> None:
    """Pretty-print a PhysicsResult."""
    divider = "─" * 55
    print(f"\n{divider}")
    print(bold(f"  Scenario: {scenario_name}"))
    print(divider)
    print(f"  Pump RPM          : {result.pump_rpm:>10.0f} RPM")
    print(f"  Valve Position    : {result.valve_position:>10.1f} %")
    print(f"  Predicted Flow    : {result.predicted_flow:>10.2f} L/min  (limit: {result.flow_limit:.1f})")
    print(f"  Predicted Pressure: {result.predicted_pressure:>10.2f} bar   (limit: {result.pressure_limit:.1f})")
    print(f"  Predicted Temp    : {result.predicted_temperature:>10.2f} °C    (limit: {result.temperature_limit:.1f})")
    print(f"  System Stress     : {result.system_stress:>10.2f} MPa   (limit: {result.stress_limit:.1f})")
    print(f"  Risk Score        : {result.risk_score:>10.2f} / 100")
    print(f"  Safety State      : {_state_str(result.safety_state)}")
    print(f"  Explanation       : {result.explanation}")
    print(f"  Sim Time          : {result.simulation_time_ms:.4f} ms")

    state_val = result.safety_state.value if isinstance(result.safety_state, SafetyState) else result.safety_state
    if state_val in ("CRITICAL", "CATASTROPHIC"):
        print()
        print(bold(red("  ██████████████████████████████████████████████████")))
        print(bold(red("  ██  ACTION REQUIRED: PHYSICAL SAFETY VIOLATION!  ██")))
        if state_val == "CATASTROPHIC":
            print(bold(red("  ██  COMMAND WOULD CAUSE CATASTROPHIC FAILURE!    ██")))
        print(bold(red("  ██████████████████████████████████████████████████")))


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "name": "NORMAL OPERATION",
        "cmd": {"pump_rpm": 1500, "valve_position": 70,
                "current_pressure": 10.0, "current_temperature": 40.0},
    },
    {
        "name": "WARNING — ELEVATED LOAD",
        "cmd": {"pump_rpm": 2400, "valve_position": 90,
                "current_pressure": 10.0, "current_temperature": 40.0},
    },
    {
        "name": "CRITICAL — NEAR LIMIT",
        "cmd": {"pump_rpm": 2900, "valve_position": 100,
                "current_pressure": 10.0, "current_temperature": 40.0},
    },
    {
        "name": "ATTACK — 50000 RPM INJECTION",
        "cmd": {"pump_rpm": 50000, "valve_position": 100,
                "current_pressure": 10.0, "current_temperature": 40.0},
    },
]


def run_scenarios() -> None:
    print()
    print(bold(cyan("═" * 55)))
    print(bold(cyan("       VOLTGUARD — PHYSICS ENGINE DEMO (Phase 2)      ")))
    print(bold(cyan("       Physics-Aware ICS Safety Analysis               ")))
    print(bold(cyan("═" * 55)))

    for scenario in SCENARIOS:
        cmd = PhysicsCommand(**scenario["cmd"])
        result = simulate(cmd)
        print_result(scenario["name"], result)

    print(f"\n{'─' * 55}")


# ---------------------------------------------------------------------------
# Time-step demo
# ---------------------------------------------------------------------------

def run_timeseries_demo() -> None:
    print()
    print(bold(cyan("─" * 55)))
    print(bold(cyan("  TIME-SERIES DEMO — Pressure build-up at RPM=2400    ")))
    print(bold(cyan("─" * 55)))

    cmd = PhysicsCommand(pump_rpm=2400, valve_position=90,
                         current_pressure=10.0, current_temperature=40.0)
    steps = simulate_timeseries(cmd, steps=5, dt=0.5)

    print(f"  {'Step':<6} {'Pressure (bar)':<18} {'Flow (L/min)':<16} {'State'}")
    print(f"  {'─'*6} {'─'*18} {'─'*16} {'─'*14}")
    for i, r in enumerate(steps):
        state_display = STATE_COLOUR.get(r.safety_state, lambda x: x)(str(r.safety_state))
        print(f"  {i:>4}   {r.predicted_pressure:>14.2f}   {r.predicted_flow:>13.2f}   {state_display}")


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def run_benchmark(iterations: int = 1000) -> None:
    print()
    print(bold(cyan("─" * 55)))
    print(bold(cyan(f"  BENCHMARK — {iterations} iterations (prototype machine)    ")))
    print(bold(cyan("─" * 55)))

    cmd = PhysicsCommand(pump_rpm=2400, valve_position=90,
                         current_pressure=10.0, current_temperature=40.0)

    timings: list[float] = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        simulate(cmd)
        timings.append((time.perf_counter() - t0) * 1000.0)

    avg_ms = sum(timings) / len(timings)
    min_ms = min(timings)
    max_ms = max(timings)

    print(f"  Iterations : {iterations}")
    print(f"  Average    : {avg_ms:.4f} ms")
    print(f"  Minimum    : {min_ms:.4f} ms")
    print(f"  Maximum    : {max_ms:.4f} ms")
    print(f"\n  NOTE: Prototype benchmark on development machine.")
    print(f"        Not representative of industrial real-time performance.")
    print()

    return avg_ms, min_ms, max_ms


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_scenarios()
    run_timeseries_demo()
    run_benchmark(iterations=1000)
    run_benchmark(iterations=100)
