"""
Device registry endpoints — Phase 8.

Provides device inventory derived from event traffic.
Devices are auto-registered by the pipeline service on first event.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.device import Device
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.telemetry import Telemetry
from backend.schemas.device import DeviceResponse, DeviceList
from backend.schemas.event import SecurityEventResponse, PaginatedEvents
from backend.schemas.alert import AlertResponse, PaginatedAlerts

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("/", response_model=DeviceList)
def list_devices(db: Session = Depends(get_db)) -> DeviceList:
    """Return all registered OT/ICS assets."""
    items = db.query(Device).order_by(Device.last_seen.desc().nullslast()).all()
    return DeviceList(items=items, total=len(items))


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(device_id: str, db: Session = Depends(get_db)) -> Device:
    """Return a single device by its device_id string."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device '{device_id}' not found")
    return device


@router.get("/{device_id}/events", response_model=PaginatedEvents)
def get_device_events(
    device_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedEvents:
    """Return paginated security events for a specific device."""
    q = db.query(SecurityEvent).filter(SecurityEvent.device == device_id)
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


@router.get("/{device_id}/alerts", response_model=PaginatedAlerts)
def get_device_alerts(
    device_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedAlerts:
    """Return paginated alerts for a specific device."""
    q = db.query(Alert).filter(Alert.device == device_id)
    total = q.count()
    offset = (page - 1) * page_size
    items = q.order_by(Alert.timestamp.desc()).offset(offset).limit(page_size).all()
    return PaginatedAlerts(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(offset + page_size) < total,
    )


@router.get("/{device_id}/telemetry")
def get_device_telemetry(
    device_id: str,
    limit: int = Query(60, ge=1, le=300),
    db: Session = Depends(get_db),
):
    """Return recent telemetry readings for a specific device."""
    items = (
        db.query(Telemetry)
        .filter(Telemetry.device == device_id)
        .order_by(Telemetry.timestamp.desc())
        .limit(limit)
        .all()
    )
    return {"items": items, "total": len(items)}
