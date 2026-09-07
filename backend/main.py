"""
VoltGuard Backend — Main Application Entry Point

Initializes FastAPI, mounts all API routes, sets up the database,
configures static dashboard serving, and configures global exception handling.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from backend.core.config import get_settings, PROJECT_ROOT
from backend.core.logging import get_logger
from backend.database.database import init_db
from backend.websocket.manager import ws_manager

from backend.api.routes import health, system, events, telemetry, alerts, traffic, simulation, devices, reports

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Executes startup and shutdown logic.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.voltguard.service_name} v{settings.voltguard.version}")
    logger.info(f"Mode: {settings.voltguard.mode}")
    
    # Initialize database tables
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    logger.info("Shutting down VoltGuard Backend")


# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.voltguard.service_name,
    version=settings.voltguard.version,
    description="Physics-Aware ICS/SCADA Intrusion Detection & Prevention System",
    lifespan=lifespan,
)


# --- Error Handling ---------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean JSON response for validation errors."""
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation error", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all for 500 errors to prevent leaking stack traces."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# --- API Routes -------------------------------------------------------------

app.include_router(health.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(telemetry.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(traffic.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# --- WebSocket Endpoints ----------------------------------------------------

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming.
    Clients connect here to receive continuous JSON updates.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client disconnect
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# --- Static Dashboard Mounting -----------------------------------------------

dist_path = PROJECT_ROOT / "dashboard" / "dist"
if dist_path.exists():
    app.mount("/assets", StaticFiles(directory=dist_path / "assets"), name="static_assets")

    @app.get("/{full_path:path}")
    async def serve_dashboard(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        file_path = dist_path / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(dist_path / "index.html")
