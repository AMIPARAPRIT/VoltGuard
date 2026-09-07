"""
Telemetry CRUD endpoints.

Provides list, detail, and create operations backed by SQLite.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.models.telemetry import Telemetry
from backend.schemas.telemetry import TelemetryCreate, TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.get("/", response_model=list[TelemetryResponse])
def list_telemetry(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> list[Telemetry]:
    """Return a paginated list of telemetry readings, newest first."""
    return (
        db.query(Telemetry)
        .order_by(Telemetry.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{telemetry_id}", response_model=TelemetryResponse)
def get_telemetry(telemetry_id: int, db: Session = Depends(get_db)) -> Telemetry:
    """Return a single telemetry reading by ID."""
    reading = db.query(Telemetry).filter(Telemetry.id == telemetry_id).first()
    if reading is None:
        raise HTTPException(status_code=404, detail="Telemetry reading not found")
    return reading


@router.post("/", response_model=TelemetryResponse, status_code=201)
def create_telemetry(
    payload: TelemetryCreate,
    db: Session = Depends(get_db),
) -> Telemetry:
    """Create and persist a new telemetry reading."""
    reading = Telemetry(**payload.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
