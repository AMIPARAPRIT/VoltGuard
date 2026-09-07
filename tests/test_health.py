"""
Tests for the /api/health endpoint.
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_health_check():
    """Verify the health endpoint returns 200 OK and expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "operational"
    assert "service" in data
    assert "version" in data
