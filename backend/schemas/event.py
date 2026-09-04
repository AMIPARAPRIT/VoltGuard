"""
SecurityEvent — Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SecurityEventBase(BaseModel):
    """Shared fields for SecurityEvent creation and display."""
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    device: Optional[str] = None
    protocol: str = "modbus_tcp"
    command: Optional[str] = None
    command_value: Optional[float] = None
    predicted_pressure: Optional[float] = None
    predicted_flow: Optional[float] = None
    predicted_temperature: Optional[float] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    safety_state: Optional[str] = None
    decision: Optional[str] = None
    latency_ms: Optional[float] = None


class SecurityEventCreate(SecurityEventBase):
    """Schema for creating a new SecurityEvent via POST."""
    pass


class SecurityEventResponse(SecurityEventBase):
    """Schema for returning a SecurityEvent from the API."""
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}
