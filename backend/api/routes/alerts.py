"""
Alert CRUD endpoints — Phase 8.

Provides: list (with filters + pagination), detail, create,
acknowledge, resolve, and summary (counters) operations.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.alert import Alert
from backend.schemas.alert import AlertCreate, AlertResponse, AlertSummary, PaginatedAlerts

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/summary", response_model=AlertSummary)
def get_alert_summary(db: Session = Depends(get_db)) -> AlertSummary:
    """Return aggregate counts for the Alerts Center header bar."""
    rows = db.query(Alert).all()
    total = len(rows)
    active = sum(1 for a in rows if getattr(a, "status", "ACTIVE") == "ACTIVE")
    acknowledged = sum(1 for a in rows if getattr(a, "status", "ACTIVE") == "ACKNOWLEDGED")
    resolved = sum(1 for a in rows if getattr(a, "status", "ACTIVE") == "RESOLVED")
    critical = sum(1 for a in rows if a.severity == "CRITICAL" and getattr(a, "status", "ACTIVE") != "RESOLVED")
    catastrophic = sum(1 for a in rows if a.severity == "CATASTROPHIC" and getattr(a, "status", "ACTIVE") != "RESOLVED")
    warning = sum(1 for a in rows if a.severity == "WARNING" and getattr(a, "status", "ACTIVE") != "RESOLVED")
    return AlertSummary(
        total=total,
        active=active,
        acknowledged=acknowledged,
        resolved=resolved,
        critical=critical,
        catastrophic=catastrophic,
        warning=warning,
    )


@router.get("/", response_model=PaginatedAlerts)
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PaginatedAlerts:
    """Return a paginated, filtered list of alerts, newest first."""
    q = db.query(Alert)

    if severity:
        q = q.filter(Alert.severity == severity.upper())
    if status:
        q = q.filter(Alert.status == status.upper())
    if device:
        q = q.filter(Alert.device.ilike(f"%{device}%"))
    if search:
        search_lower = f"%{search.lower()}%"
        q = q.filter(
            Alert.title.ilike(search_lower)
            | Alert.message.ilike(search_lower)
            | Alert.device.ilike(search_lower)
        )

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


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    """Return a single alert by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/", response_model=AlertResponse, status_code=201)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
) -> Alert:
    """Create and persist a new alert."""
    alert = Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    """Transition an ACTIVE alert to ACKNOWLEDGED."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    current_status = getattr(alert, "status", "ACTIVE")
    if current_status == "RESOLVED":
        raise HTTPException(status_code=400, detail="Cannot acknowledge a resolved alert")
    alert.acknowledged = True
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


@router.patch("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)) -> Alert:
    """Transition an ACKNOWLEDGED alert to RESOLVED."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    current_status = getattr(alert, "status", "ACTIVE")
    if current_status == "RESOLVED":
        raise HTTPException(status_code=400, detail="Alert is already resolved")
    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_at = alert.acknowledged_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert
