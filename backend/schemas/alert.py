"""
Alert — Pydantic schemas for API request/response validation.

Phase 8 extensions:
  - AlertResponse: status, event_id, acknowledged_at, resolved_at
  - AlertSummary: counters by status/severity
  - PaginatedAlerts: paginated list response
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class AlertBase(BaseModel):
    """Shared fields for Alert creation and display."""
    severity: str = "INFO"          # INFO, WARNING, CRITICAL, CATASTROPHIC
    status: str = "ACTIVE"          # ACTIVE, ACKNOWLEDGED, RESOLVED
    title: str
    message: Optional[str] = None
    device: Optional[str] = None
    event_id: Optional[int] = None
    acknowledged: bool = False


class AlertCreate(AlertBase):
    """Schema for creating a new Alert via POST."""
    pass


class AlertResponse(AlertBase):
    """Schema for returning an Alert from the API."""
    id: int
    timestamp: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertSummary(BaseModel):
    """Aggregate counters for the Alerts Center header."""
    total: int = 0
    active: int = 0
    acknowledged: int = 0
    resolved: int = 0
    critical: int = 0
    catastrophic: int = 0
    warning: int = 0


class PaginatedAlerts(BaseModel):
    """Paginated alert list response."""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
