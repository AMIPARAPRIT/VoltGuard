"""
VoltGuard Physics Engine — Input/Output Models

Pydantic v2 models for the physics simulation interface.

Units used throughout:
    pressure    → bar
    rpm         → RPM
    temperature → °C
    flow        → L/min
    stress      → MPa
    risk_score  → 0–100 (dimensionless)

NOTE: This is a simplified prototype model for controlled demonstration.
      It is NOT intended to control real industrial equipment.
"""

from __future__ import annotations

import math
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, field_validator, model_validator


class SafetyState(str, Enum):
    """
    Discrete safety classification for the predicted physical state.

    SAFE        — All parameters comfortably within limits.
    WARNING     — One or more parameters approaching a safety limit (≥70 % of max).
    CRITICAL    — One or more parameters very close to a safety limit (≥90 % of max).
    CATASTROPHIC— One or more safety limits exceeded.
    """
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    CATASTROPHIC = "CATASTROPHIC"


class PhysicsCommand(BaseModel):
    """
    Input command to the physics simulation engine.

    All fields are validated for physical plausibility before the simulation runs.
    Missing optional fields fall back to the configured defaults.
    """

    pump_rpm: float = Field(
        ...,
        ge=0.0,
        description="Pump speed in RPM. Must be ≥ 0.",
    )
    valve_position: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Valve opening percentage [0–100]. 0 = fully closed.",
    )
    current_pressure: float = Field(
        default=0.0,
        ge=0.0,
        description="Inlet pressure in bar. Must be ≥ 0.",
    )
    current_temperature: float = Field(
        default=20.0,
        ge=-273.15,
        description="Fluid temperature in °C. Must be above absolute zero.",
    )
    pipeline_resistance: float = Field(
        default=1.0,
        gt=0.0,
        description="Dimensionless resistance coefficient of the pipeline. Must be > 0.",
    )
    pump_efficiency: float = Field(
        default=0.85,
        gt=0.0,
        le=1.0,
        description="Pump mechanical efficiency [0–1].",
    )

    @field_validator("pump_rpm", "current_pressure", "current_temperature",
                     "pipeline_resistance", "pump_efficiency", "valve_position",
                     mode="before")
    @classmethod
    def reject_nan_and_inf(cls, v: object) -> object:
        """Reject NaN and infinite values regardless of which field they appear in."""
        if isinstance(v, float):
            if math.isnan(v):
                raise ValueError("NaN is not a valid physical value.")
            if math.isinf(v):
                raise ValueError("Infinite values are not physically meaningful.")
        return v

    model_config = {"str_strip_whitespace": True}


class ViolationDetail(BaseModel):
    """A single physical constraint that was violated or approached."""
    parameter: str
    value: float
    limit: float
    ratio: float          # value / limit — >1.0 means exceeded
    description: str


class PhysicsResult(BaseModel):
    """
    Output of the physics simulation engine.

    Contains:
      - Echo of the command inputs
      - Predicted physical state after applying the command
      - Safety limits used in evaluation (for transparency)
      - Risk assessment: score, state, violations, explanation
      - Simulation timing

    This model is JSON-serializable and can be stored directly in the
    SecurityEvent table or streamed via WebSocket.
    """

    # --- Input echo ---
    pump_rpm: float
    valve_position: float
    current_pressure: float
    current_temperature: float

    # --- Predicted physical outputs ---
    predicted_flow: float         # L/min
    predicted_pressure: float     # bar
    predicted_temperature: float  # °C
    system_stress: float          # MPa

    # --- Safety limits used (for auditability) ---
    pressure_limit: float
    rpm_limit: float
    temperature_limit: float
    flow_limit: float
    stress_limit: float

    # --- Risk assessment ---
    risk_score: float             # 0–100
    safety_state: SafetyState

    # --- Human-readable output ---
    violations: List[ViolationDetail]
    explanation: str

    # --- Performance ---
    simulation_time_ms: float

    model_config = {"use_enum_values": True}
