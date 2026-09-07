"""
Telemetry — Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TelemetryBase(BaseModel):
    """Shared fields for Telemetry creation and display."""
    device: Optional[str] = None
    pump_rpm: Optional[float] = None
    valve_position: Optional[float] = None
    pressure: Optional[float] = None
    flow_rate: Optional[float] = None
    temperature: Optional[float] = None
    stress: Optional[float] = None


class TelemetryCreate(TelemetryBase):
    """Schema for creating a new Telemetry reading via POST."""
    pass


class TelemetryResponse(TelemetryBase):
    """Schema for returning a Telemetry reading from the API."""
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}
