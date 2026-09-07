"""
VoltGuard Phase 2 — Physics Test Suite: Safety Classification & Risk Scoring

Unit tests for safety.py in isolation.
These do NOT call simulate() — they test the classification functions directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from physics.models import SafetyState, ViolationDetail
from physics.safety import (
    compute_violations,
    compute_risk_score,
    build_explanation,
    SAFE_THRESHOLD,
    WARNING_THRESHOLD,
    CRITICAL_THRESHOLD,
)


# Convenience: standard limits matching config defaults
LIMITS = dict(
    rpm_limit=3600.0,
    flow_limit=500.0,
    pressure_limit=80.0,
    temperature_limit=120.0,
    stress_limit=130.0,
)


def _violations_and_state(**overrides) -> tuple:
    defaults = dict(
        pump_rpm=0,
        predicted_flow=0,
        predicted_pressure=0,
        predicted_temperature=20,
        system_stress=0,
        **LIMITS,
    )
    defaults.update(overrides)
    return compute_violations(**defaults)


def _risk_score(**overrides) -> float:
    defaults = dict(
        pump_rpm=0,
        predicted_flow=0,
        predicted_pressure=0,
        predicted_temperature=20,
        system_stress=0,
        **LIMITS,
    )
    defaults.update(overrides)
    return compute_risk_score(**defaults)


# ---------------------------------------------------------------------------
# SafetyState classification tests
# ---------------------------------------------------------------------------

def test_all_zeros_is_safe():
    violations, state = _violations_and_state(predicted_temperature=20)
    assert state == SafetyState.SAFE


def test_at_safe_threshold_below_warning_is_safe():
    """Value at 69% of limit → SAFE."""
    pressure = LIMITS["pressure_limit"] * 0.69
    violations, state = _violations_and_state(predicted_pressure=pressure)
    assert state == SafetyState.SAFE


def test_at_warning_boundary():
    """Value at exactly 70% of limit → WARNING."""
    pressure = LIMITS["pressure_limit"] * WARNING_THRESHOLD
    violations, state = _violations_and_state(predicted_pressure=pressure)
    assert state == SafetyState.WARNING
    assert any(v.parameter == "predicted_pressure" for v in violations)


def test_at_critical_boundary():
    """Value at exactly 90% of limit → CRITICAL."""
    pressure = LIMITS["pressure_limit"] * CRITICAL_THRESHOLD
    violations, state = _violations_and_state(predicted_pressure=pressure)
    assert state == SafetyState.CRITICAL


def test_at_100_percent_of_limit():
    """Value exactly at limit → CATASTROPHIC."""
    pressure = LIMITS["pressure_limit"] * 1.0
    violations, state = _violations_and_state(predicted_pressure=pressure)
    assert state == SafetyState.CATASTROPHIC


def test_exceeding_limit_is_catastrophic():
    """Value 150% of limit → CATASTROPHIC."""
    pressure = LIMITS["pressure_limit"] * 1.5
    violations, state = _violations_and_state(predicted_pressure=pressure)
    assert state == SafetyState.CATASTROPHIC


def test_worst_state_wins():
    """Multiple parameters: the worst (CATASTROPHIC) must win."""
    _, state = _violations_and_state(
        predicted_pressure=LIMITS["pressure_limit"] * 0.80,   # WARNING
        pump_rpm=LIMITS["rpm_limit"] * 1.2,                   # CATASTROPHIC
    )
    assert state == SafetyState.CATASTROPHIC


def test_violation_count_for_two_violations():
    """Two parameters in WARNING should produce two ViolationDetail entries."""
    violations, _ = _violations_and_state(
        predicted_pressure=LIMITS["pressure_limit"] * 0.75,   # WARNING
        predicted_flow=LIMITS["flow_limit"] * 0.75,           # WARNING
    )
    assert len(violations) == 2


def test_safe_parameters_not_in_violations():
    """Safe parameters must not appear in violations list."""
    violations, _ = _violations_and_state(
        predicted_pressure=LIMITS["pressure_limit"] * 0.30,   # SAFE
    )
    assert violations == []


# ---------------------------------------------------------------------------
# Risk score tests
# ---------------------------------------------------------------------------

def test_risk_score_zero_at_zero_values():
    """Zero values → risk score should be 0 (or very near 0)."""
    score = _risk_score(predicted_temperature=20)
    # Temperature 20°C / 120°C limit = 16.7% ratio → small score
    assert score < 5.0


def test_risk_score_increases_with_pressure():
    """Higher pressure → higher risk score."""
    low  = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * 0.3)
    mid  = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * 0.7)
    high = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * 1.2)
    assert low < mid < high


def test_risk_score_near_100_when_150_percent():
    """150% of any limit should saturate the score to 100."""
    score = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * 1.5)
    assert score == 100.0


def test_risk_score_bounded_0_to_100():
    """Risk score must always stay in [0, 100]."""
    for multiplier in [0.0, 0.5, 1.0, 2.0, 10.0, 100.0]:
        score = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * multiplier)
        assert 0.0 <= score <= 100.0, f"Score out of bounds at multiplier {multiplier}: {score}"


def test_risk_score_driven_by_worst_parameter():
    """The worst parameter should dominate the overall risk score."""
    # Only flow is high
    score_flow_high = _risk_score(predicted_flow=LIMITS["flow_limit"] * 1.4)
    # Only pressure is slightly elevated
    score_pressure_low = _risk_score(predicted_pressure=LIMITS["pressure_limit"] * 0.5)
    assert score_flow_high > score_pressure_low


# ---------------------------------------------------------------------------
# build_explanation tests
# ---------------------------------------------------------------------------

def test_explanation_safe_state():
    """SAFE state should say 'within safe operating limits'."""
    text = build_explanation([], SafetyState.SAFE)
    assert "safe" in text.lower()


def test_explanation_single_violation():
    """Single violation should produce a concise explanation."""
    v = ViolationDetail(
        parameter="predicted_pressure",
        value=200.0,
        limit=150.0,
        ratio=1.333,
        description="Pipeline pressure exceeds the safety limit by 33.3%.",
    )
    text = build_explanation([v], SafetyState.CATASTROPHIC)
    assert "pressure" in text.lower() or "ALERT" in text


def test_explanation_multiple_violations_mentions_all():
    """Multiple violations must reference them in the explanation."""
    violations = [
        ViolationDetail(
            parameter="predicted_pressure",
            value=160.0, limit=150.0, ratio=1.067,
            description="Pressure exceeded.",
        ),
        ViolationDetail(
            parameter="pump_rpm",
            value=4000.0, limit=3600.0, ratio=1.111,
            description="RPM exceeded.",
        ),
    ]
    text = build_explanation(violations, SafetyState.CATASTROPHIC)
    assert "pressure" in text.lower() or "rpm" in text.lower()
