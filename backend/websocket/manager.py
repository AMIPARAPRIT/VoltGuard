"""
VoltGuard — WebSocket Connection Manager

Manages WebSocket client connections for real-time telemetry broadcast.

Endpoint: /ws/telemetry

Usage (in future phases):
    await ws_manager.broadcast({"pump_rpm": 2500, "pressure": 85.3})
"""

import json
from typing import Any

from fastapi import WebSocket

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    """
    Tracks active WebSocket connections and supports broadcasting
    JSON payloads to all connected clients.
    """

    def __init__(self) -> None:
        self._active_connections: list[WebSocket] = []

    @property
    def active_count(self) -> int:
        """Number of currently connected clients."""
        return len(self._active_connections)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket client."""
        await websocket.accept()
        self._active_connections.append(websocket)
        logger.info(f"WebSocket client connected ({self.active_count} total)")

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a disconnected client from the active list."""
        if websocket in self._active_connections:
            self._active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected ({self.active_count} total)")

    async def broadcast(self, data: dict[str, Any]) -> None:
        """
        Send a JSON payload to every connected client.

        Clients that fail to receive the message are silently disconnected.
        """
        stale: list[WebSocket] = []
        for connection in self._active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except Exception:
                stale.append(connection)

        for connection in stale:
            self.disconnect(connection)


# Singleton manager instance used by the application
ws_manager = ConnectionManager()
