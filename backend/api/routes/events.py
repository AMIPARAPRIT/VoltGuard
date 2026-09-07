"""
SecurityEvent CRUD endpoints — Phase 8.

Provides: list (with filters + pagination) and detail operations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.event import SecurityEvent
from backend.schemas.event import SecurityEventCreate, SecurityEventResponse, PaginatedEvents

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("/", response_model=PaginatedEvents)
def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    decision: Optional[str] = Query(None),
    safety_state: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    protocol: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PaginatedEvents:
    """Return a paginated, filtered list of security events, newest first."""
    q = db.query(SecurityEvent)

    if decision:
        q = q.filter(SecurityEvent.decision == decision.upper())
    if safety_state:
        q = q.filter(SecurityEvent.safety_state == safety_state.upper())
    if device:
        q = q.filter(SecurityEvent.device.ilike(f"%{device}%"))
    if protocol:
        q = q.filter(SecurityEvent.protocol.ilike(f"%{protocol}%"))
    if search:
        s = f"%{search.lower()}%"
        q = q.filter(
            SecurityEvent.device.ilike(s)
            | SecurityEvent.command.ilike(s)
            | SecurityEvent.protocol.ilike(s)
            | SecurityEvent.reason.ilike(s)
        )

    total = q.count()
    offset = (page - 1) * page_size
    items = q.order_by(SecurityEvent.timestamp.desc()).offset(offset).limit(page_size).all()

    return PaginatedEvents(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
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
