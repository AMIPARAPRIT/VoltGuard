"""
System status endpoint — reports the health of every VoltGuard subsystem.
"""

from fastapi import APIRouter

from backend.database.database import check_db_health
from backend.websocket.manager import ws_manager

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status")
def system_status() -> dict:
    """
    Returns the status of each subsystem.

    - backend: always OPERATIONAL if this endpoint responds.
    - database: checks actual connectivity.
    - physics_engine: NOT_INITIALIZED (Phase 2).
    - decision_engine: NOT_INITIALIZED (Phase 3).
    - websocket: OPERATIONAL if manager is available.
    """
    db_ok = check_db_health()

    return {
        "backend": "OPERATIONAL",
        "database": "OPERATIONAL" if db_ok else "ERROR",
        "physics_engine": "NOT_INITIALIZED",
        "decision_engine": "NOT_INITIALIZED",
        "websocket": "OPERATIONAL",
        "websocket_clients": ws_manager.active_count,
    }
