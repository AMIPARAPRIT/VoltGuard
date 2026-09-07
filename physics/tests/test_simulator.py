"""
VoltGuard Phase 2 — Physics Test Suite: Simulator Scenarios

Tests the full simulate() pipeline end-to-end against the
four named operating scenarios from the specification.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is resolvable when running pytest from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from physics.models import PhysicsCommand, SafetyState
from physics.simulator import simulate


# ---------------------------------------------------------------------------
# Fixtures — representative PhysicsCommands
# ---------------------------------------------------------------------------

@pytest.fixture
def normal_cmd() -> PhysicsCommand:
    """Normal operating condition — RPM=1500, Valve=70%."""
    return PhysicsCommand(
        pump_rpm=1500,
        valve_position=70,
        current_pressure=10.0,
        current_temperature=40.0,
    )


@pytest.fixture
def warning_cmd() -> PhysicsCommand:
    """Elevated operating condition — RPM=2400, Valve=90%."""
    return PhysicsCommand(
        pump_rpm=2400,
        valve_position=90,
        current_pressure=10.0,
        current_temperature=40.0,
    )


@pytest.fixture
def critical_cmd() -> PhysicsCommand:
    """Near-limit condition — RPM=2900, Valve=100%."""
    return PhysicsCommand(
        pump_rpm=2900,
        valve_position=100,
        current_pressure=10.0,
        current_temperature=40.0,
    )


@pytest.fixture
def attack_cmd() -> PhysicsCommand:
    """Cyber-attack simulation — RPM=50000, Valve=100%."""
    return PhysicsCommand(
        pump_rpm=50000,
        valve_position=100,
        current_pressure=10.0,
        current_temperature=40.0,
    )


# ---------------------------------------------------------------------------
# Test 1 — Normal RPM: expect SAFE or WARNING
# ---------------------------------------------------------------------------

def test_normal_scenario_safe_or_warning(normal_cmd):
    """Normal operating conditions should classify as SAFE or WARNING."""
    result = simulate(normal_cmd)
    assert result.safety_state in (SafetyState.SAFE, SafetyState.WARNING), (
        f"Expected SAFE or WARNING at RPM=1500, got {result.safety_state}"
    )


def test_normal_scenario_produces_positive_flow(normal_cmd):
    """Positive RPM + open valve must produce positive flow."""
    result = simulate(normal_cmd)
    assert result.predicted_flow > 0.0, "Flow must be > 0 for a running pump with open valve."


def test_normal_scenario_produces_positive_pressure(normal_cmd):
    """Pressure must be above the inlet pressure."""
    result = simulate(normal_cmd)
    assert result.predicted_pressure >= normal_cmd.current_pressure


# ---------------------------------------------------------------------------
# Test 2 — High RPM: expect WARNING or CRITICAL
# ---------------------------------------------------------------------------

def test_warning_scenario_elevated_state(warning_cmd):
    """RPM=2400, Valve=90% should produce WARNING or CRITICAL."""
    result = simulate(warning_cmd)
    assert result.safety_state in (SafetyState.WARNING, SafetyState.CRITICAL), (
        f"Expected WARNING or CRITICAL at RPM=2400, got {result.safety_state}"
    )


def test_warning_scenario_higher_flow_than_normal(normal_cmd, warning_cmd):
    """Higher RPM + wider valve must produce higher flow than normal."""
    normal_result = simulate(normal_cmd)
    warning_result = simulate(warning_cmd)
    assert warning_result.predicted_flow > normal_result.predicted_flow


def test_warning_scenario_risk_score_elevated(warning_cmd):
    """Risk score at warning conditions should be meaningfully non-zero."""
    result = simulate(warning_cmd)
    assert result.risk_score > 10.0, (
        f"Risk score should be elevated at RPM=2400, got {result.risk_score}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Pressure near limit: expect CRITICAL
# ---------------------------------------------------------------------------

def test_critical_scenario(critical_cmd):
    """RPM=2900, Valve=100% should produce CRITICAL or CATASTROPHIC."""
    result = simulate(critical_cmd)
    assert result.safety_state in (SafetyState.CRITICAL, SafetyState.CATASTROPHIC), (
        f"Expected CRITICAL or CATASTROPHIC at RPM=2900 full valve, got {result.safety_state}"
    )


def test_critical_scenario_risk_score_high(critical_cmd):
    """Risk score at critical conditions should be high (>50)."""
    result = simulate(critical_cmd)
    assert result.risk_score > 50.0, (
        f"Risk score should be high at critical RPM, got {result.risk_score}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Pressure above limit: expect CATASTROPHIC
# ---------------------------------------------------------------------------

def test_attack_scenario_catastrophic(attack_cmd):
    """RPM=50000, Valve=100% must classify as CATASTROPHIC."""
    result = simulate(attack_cmd)
    assert result.safety_state == SafetyState.CATASTROPHIC, (
        f"50000 RPM attack must be CATASTROPHIC, got {result.safety_state}"
    )


def test_attack_scenario_pressure_exceeds_limit(attack_cmd):
    """Predicted pressure must exceed the configured safety limit."""
    result = simulate(attack_cmd)
    assert result.predicted_pressure > result.pressure_limit, (
        f"Predicted pressure {result.predicted_pressure:.2f} must exceed "
        f"limit {result.pressure_limit:.2f}"
    )


def test_attack_scenario_risk_score_very_high(attack_cmd):
    """Risk score for 50000 RPM attack must be ≥ 90."""
    result = simulate(attack_cmd)
    assert result.risk_score >= 90.0, (
        f"Attack scenario risk score should be ≥ 90, got {result.risk_score}"
    )


# ---------------------------------------------------------------------------
# Test 5 — 50000 RPM: explicit attack test (spec requirement §14)
# ---------------------------------------------------------------------------

def test_50000_rpm_classified_catastrophic():
    """Explicit spec test: pump_rpm=50000 must always return CATASTROPHIC."""
    cmd = PhysicsCommand(pump_rpm=50000, valve_position=100)
    result = simulate(cmd)
    assert result.safety_state == SafetyState.CATASTROPHIC
    assert result.predicted_pressure > result.pressure_limit
    assert result.risk_score >= 90.0


# ---------------------------------------------------------------------------
# Test 6 — Valve = 0%: flow should be approximately zero
# ---------------------------------------------------------------------------

def test_valve_closed_produces_minimal_flow():
    """With valve fully closed, flow should be zero or near-zero."""
    cmd = PhysicsCommand(pump_rpm=2000, valve_position=0)
    result = simulate(cmd)
    assert result.predicted_flow < 1.0, (
        f"Closed valve should produce ~0 flow, got {result.predicted_flow:.4f}"
    )


# ---------------------------------------------------------------------------
# Test 7 — Valve = 100% > Valve = 50%: higher valve = higher flow
# ---------------------------------------------------------------------------

def test_open_valve_produces_more_flow_than_half_open():
    """Full valve must produce strictly more flow than half-open at same RPM."""
    rpm = 2000
    half_open = simulate(PhysicsCommand(pump_rpm=rpm, valve_position=50))
    full_open  = simulate(PhysicsCommand(pump_rpm=rpm, valve_position=100))
    assert full_open.predicted_flow > half_open.predicted_flow


# ---------------------------------------------------------------------------
# Test 10 — Determinism: same input → identical output
# ---------------------------------------------------------------------------

def test_simulation_is_deterministic(normal_cmd):
    """Same PhysicsCommand must always produce the same PhysicsResult."""
    result_a = simulate(normal_cmd)
    result_b = simulate(normal_cmd)
    assert result_a.predicted_pressure   == result_b.predicted_pressure
    assert result_a.predicted_flow       == result_b.predicted_flow
    assert result_a.predicted_temperature == result_b.predicted_temperature
    assert result_a.system_stress        == result_b.system_stress
    assert result_a.risk_score           == result_b.risk_score
    assert result_a.safety_state         == result_b.safety_state


def test_dict_input_accepted():
    """simulate() must accept a raw dict and coerce it to PhysicsCommand."""
    result = simulate({"pump_rpm": 1500, "valve_position": 70})
    assert result.safety_state in (SafetyState.SAFE, SafetyState.WARNING, SafetyState.CRITICAL)


def test_result_is_json_serializable(normal_cmd):
    """PhysicsResult must be JSON-serializable without error."""
    import json
    result = simulate(normal_cmd)
    json_str = result.model_dump_json()
    parsed = json.loads(json_str)
    assert "safety_state" in parsed
    assert "risk_score" in parsed
