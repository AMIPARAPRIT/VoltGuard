"""
Tests for the /api/system/status endpoint.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_system_status():
    """Verify system status reports correct subsystem states."""
    response = client.get("/api/system/status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["backend"] == "OPERATIONAL"
    assert data["database"] in ["OPERATIONAL", "ERROR"]
    assert data["physics_engine"] in ["OPERATIONAL", "NOT_INITIALIZED"]
    assert data["decision_engine"] in ["OPERATIONAL", "FALLBACK_FAILSAFE", "UNAVAILABLE", "NOT_INITIALIZED"]
    assert data["websocket"] == "OPERATIONAL"
    assert "websocket_clients" in data
