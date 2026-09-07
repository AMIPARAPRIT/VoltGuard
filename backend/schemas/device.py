"""
Device — Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class DeviceResponse(BaseModel):
    """Schema for returning a Device from the API."""
    id: int
    device_id: str
    name: Optional[str] = None
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    protocol: Optional[str] = None
    connection_status: str = "ONLINE"
    last_seen: Optional[datetime] = None

    # Latest telemetry snapshot
    last_pump_rpm: Optional[float] = None
    last_valve_position: Optional[float] = None
    last_pressure: Optional[float] = None
    last_flow_rate: Optional[float] = None
    last_temperature: Optional[float] = None
    last_stress: Optional[float] = None
    last_risk_score: Optional[float] = None
    last_safety_state: Optional[str] = None
    last_decision: Optional[str] = None

    model_config = {"from_attributes": True}


class DeviceList(BaseModel):
    """List of devices with count."""
    items: List[DeviceResponse]
    total: int
