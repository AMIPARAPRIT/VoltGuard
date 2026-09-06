"""
SecurityEvent — Pydantic schemas for API request/response validation.

Phase 8 extensions:
  - reason, violations, explanation: physics/decision detail
  - function_code, register: raw protocol fields
  - alert_id: FK to associated alert
  - PaginatedEvents: paginated list response
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class SecurityEventBase(BaseModel):
    """Shared fields for SecurityEvent creation and display."""
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    device: Optional[str] = None
    protocol: str = "modbus_tcp"
    function_code: Optional[int] = None
    register: Optional[int] = None
    command: Optional[str] = None
    command_value: Optional[float] = None
    predicted_pressure: Optional[float] = None
    predicted_flow: Optional[float] = None
    predicted_temperature: Optional[float] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    safety_state: Optional[str] = None
    decision: Optional[str] = None
    reason: Optional[str] = None
    violations: Optional[str] = None       # JSON string: list of violation objects
    explanation: Optional[str] = None      # Physics engine explanation
    latency_ms: Optional[float] = None
    alert_id: Optional[int] = None


class SecurityEventCreate(SecurityEventBase):
    """Schema for creating a new SecurityEvent via POST."""
    pass


class SecurityEventResponse(SecurityEventBase):
    """Schema for returning a SecurityEvent from the API."""
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class PaginatedEvents(BaseModel):
    """Paginated event list response."""
    items: List[SecurityEventResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
