"""
SecurityEvent CRUD endpoints.

Provides list, detail, and create operations backed by SQLite.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.event import SecurityEvent
from backend.schemas.event import SecurityEventCreate, SecurityEventResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=list[SecurityEventResponse])
def list_events(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[SecurityEvent]:
    """Return a paginated list of security events, newest first."""
    return (
        db.query(SecurityEvent)
        .order_by(SecurityEvent.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{event_id}", response_model=SecurityEventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)) -> SecurityEvent:
    """Return a single security event by ID."""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Security event not found")
    return event


@router.post("/", response_model=SecurityEventResponse, status_code=201)
def create_event(
    payload: SecurityEventCreate,
    db: Session = Depends(get_db),
) -> SecurityEvent:
    """Create and persist a new security event."""
    event = SecurityEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
