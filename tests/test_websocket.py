"""
Tests for WebSocket connectivity.
"""

from fastapi.testclient import TestClient
import pytest

from backend.main import app
from backend.websocket.manager import ws_manager

client = TestClient(app)


def test_websocket_connection():
    """Verify a client can connect to the telemetry WebSocket."""
    initial_count = ws_manager.active_count
    
    with client.websocket_connect("/ws/telemetry") as websocket:
        # Connected
        assert ws_manager.active_count == initial_count + 1
        
        # Test basic receive/send loop if needed in future
        # For now, just ensuring connection works
    
    # Disconnected
    assert ws_manager.active_count == initial_count
