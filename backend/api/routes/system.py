"""
System status endpoint — reports the health of every VoltGuard subsystem.
"""

from fastapi import APIRouter

from backend.database.database import check_db_health
from backend.websocket.manager import ws_manager
from decision_engine.wrapper import decision_engine_wrapper

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status")
def system_status() -> dict:
    """
    Returns the status of each subsystem.

    - backend: always OPERATIONAL if this endpoint responds.
    - database: checks actual connectivity.
    - physics_engine: OPERATIONAL (Phase 2).
    - decision_engine: OPERATIONAL if Rust engine binary is present; else UNAVAILABLE.
    - websocket: OPERATIONAL if manager is available.
    """
    db_ok = check_db_health()
    rust_ok = decision_engine_wrapper.is_available()

    return {
        "backend": "OPERATIONAL",
        "database": "OPERATIONAL" if db_ok else "ERROR",
        "physics_engine": "OPERATIONAL",
        "decision_engine": "OPERATIONAL" if rust_ok else "UNAVAILABLE",
        "websocket": "OPERATIONAL",
        "websocket_clients": ws_manager.active_count,
    }
