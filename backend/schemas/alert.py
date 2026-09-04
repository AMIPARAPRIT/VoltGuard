"""
Alert — Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertBase(BaseModel):
    """Shared fields for Alert creation and display."""
    severity: str = "INFO"
    title: str
    message: Optional[str] = None
    device: Optional[str] = None
    acknowledged: bool = False


class AlertCreate(AlertBase):
    """Schema for creating a new Alert via POST."""
    pass


class AlertResponse(AlertBase):
    """Schema for returning an Alert from the API."""
    id: int
    timestamp: datetime

    model_config = {"from_attributes": True}
