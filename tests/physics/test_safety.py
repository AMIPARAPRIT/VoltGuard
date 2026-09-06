import pytest
from physics.models import SafetyState, ViolationDetail
from physics.safety import compute_violations, compute_risk_score, build_explanation

# Default limits for testing
LIMITS = {
    "rpm_limit": 2000.0,
    "flow_limit": 100.0,
    "pressure_limit": 500.0,
    "temperature_limit": 150.0,
    "stress_limit": 1000.0
}

def test_safety_safe():
    # Below 70%
    violations, state = compute_violations(
        pump_rpm=1000.0,
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert state == SafetyState.SAFE
    assert len(violations) == 0

def test_safety_warning():
    # > 70% < 90%
    violations, state = compute_violations(
        pump_rpm=1500.0, # 75%
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert state == SafetyState.WARNING
    assert len(violations) == 1

def test_safety_critical():
    # > 90% < 100%
    violations, state = compute_violations(
        pump_rpm=1900.0, # 95%
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert state == SafetyState.CRITICAL
    assert len(violations) == 1

def test_safety_catastrophic():
    # >= 100%
    violations, state = compute_violations(
        pump_rpm=50000.0, # Huge attack value
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert state == SafetyState.CATASTROPHIC
    assert len(violations) == 1
    assert violations[0].ratio > 1.0

def test_risk_score():
    score = compute_risk_score(
        pump_rpm=1000.0, # 0.5 ratio -> ~11
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert score > 0
    assert score < 20

    score_attack = compute_risk_score(
        pump_rpm=50000.0,
        predicted_flow=50.0,
        predicted_pressure=200.0,
        predicted_temperature=80.0,
        system_stress=400.0,
        **LIMITS
    )
    assert score_attack == 100.0
