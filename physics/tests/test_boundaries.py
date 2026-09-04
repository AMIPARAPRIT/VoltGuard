"""
VoltGuard Phase 2 — Physics Test Suite: Input Boundary Validation

Tests that invalid physical inputs are rejected before simulation starts.
All tests here expect Pydantic ValidationError to be raised.

Spec references: §15 (Impossible Inputs) and Tests 8 & 9.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from pydantic import ValidationError

from physics.models import PhysicsCommand


# ---------------------------------------------------------------------------
# Test 8 — Negative RPM (spec §15, Test 8)
# ---------------------------------------------------------------------------

def test_negative_rpm_raises_validation_error():
    """pump_rpm < 0 must raise a ValidationError."""
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        PhysicsCommand(pump_rpm=-1, valve_position=50)


def test_large_negative_rpm_raises_validation_error():
    """Very large negative RPM must also raise ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=-99999, valve_position=50)


# ---------------------------------------------------------------------------
# Test 9 — Valve position > 100% (spec §15, Test 9)
# ---------------------------------------------------------------------------

def test_valve_above_100_raises_validation_error():
    """valve_position > 100 must raise a ValidationError."""
    with pytest.raises(ValidationError, match="less than or equal to 100"):
        PhysicsCommand(pump_rpm=1500, valve_position=101)


def test_valve_at_200_raises_validation_error():
    """valve_position=200 must raise ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=200)


# ---------------------------------------------------------------------------
# Negative valve position
# ---------------------------------------------------------------------------

def test_negative_valve_raises_validation_error():
    """valve_position < 0 must raise a ValidationError."""
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        PhysicsCommand(pump_rpm=1500, valve_position=-10)


# ---------------------------------------------------------------------------
# NaN inputs
# ---------------------------------------------------------------------------

def test_nan_rpm_raises_validation_error():
    """NaN pump_rpm must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=float("nan"), valve_position=50)


def test_nan_valve_raises_validation_error():
    """NaN valve_position must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=float("nan"))


def test_nan_pressure_raises_validation_error():
    """NaN current_pressure must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, current_pressure=float("nan"))


def test_nan_temperature_raises_validation_error():
    """NaN current_temperature must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, current_temperature=float("nan"))


# ---------------------------------------------------------------------------
# Infinite inputs
# ---------------------------------------------------------------------------

def test_infinite_rpm_raises_validation_error():
    """Infinite pump_rpm must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=math.inf, valve_position=50)


def test_negative_infinite_rpm_raises_validation_error():
    """Negative infinite pump_rpm must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=-math.inf, valve_position=50)


def test_infinite_valve_raises_validation_error():
    """Infinite valve_position must raise a ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=math.inf)


# ---------------------------------------------------------------------------
# Missing required fields
# ---------------------------------------------------------------------------

def test_missing_pump_rpm_raises_validation_error():
    """pump_rpm is required — omitting it must raise ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(valve_position=50)  # type: ignore[call-arg]


def test_missing_valve_position_raises_validation_error():
    """valve_position is required — omitting it must raise ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Sub-zero temperature (below absolute zero)
# ---------------------------------------------------------------------------

def test_below_absolute_zero_raises_validation_error():
    """current_temperature < -273.15°C (absolute zero) must raise ValidationError."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, current_temperature=-300.0)


# ---------------------------------------------------------------------------
# Boundary values that SHOULD be accepted
# ---------------------------------------------------------------------------

def test_zero_rpm_is_valid():
    """pump_rpm=0 (pump stopped) is physically valid and must be accepted."""
    cmd = PhysicsCommand(pump_rpm=0, valve_position=50)
    assert cmd.pump_rpm == 0.0


def test_zero_valve_is_valid():
    """valve_position=0 (fully closed) is physically valid."""
    cmd = PhysicsCommand(pump_rpm=1500, valve_position=0)
    assert cmd.valve_position == 0.0


def test_valve_100_is_valid():
    """valve_position=100 (fully open) is physically valid."""
    cmd = PhysicsCommand(pump_rpm=1500, valve_position=100)
    assert cmd.valve_position == 100.0


def test_extreme_but_valid_rpm_is_accepted():
    """Very high RPM (e.g. 50000) is physically questionable but passes validation.
    The physics model and safety classifier will flag it as CATASTROPHIC."""
    cmd = PhysicsCommand(pump_rpm=50000, valve_position=100)
    assert cmd.pump_rpm == 50000.0


def test_negative_pressure_raises_validation_error():
    """Negative inlet pressure is not physically valid for this model."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, current_pressure=-5.0)


def test_efficiency_above_1_raises_validation_error():
    """pump_efficiency > 1.0 violates thermodynamics."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, pump_efficiency=1.5)


def test_zero_resistance_raises_validation_error():
    """pipeline_resistance = 0 would cause division issues — must be rejected."""
    with pytest.raises(ValidationError):
        PhysicsCommand(pump_rpm=1500, valve_position=50, pipeline_resistance=0.0)
