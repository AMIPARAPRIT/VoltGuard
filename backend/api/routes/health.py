"""
Health endpoint — lightweight liveness probe for the VoltGuard backend.
"""

from fastapi import APIRouter

from backend.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check() -> dict:
    """
    Liveness probe.

    Returns the operational status, service name, and version.
    """
    settings = get_settings()
    return {
        "status": "operational",
        "service": settings.voltguard.service_name,
        "version": settings.voltguard.version,
    }
