import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "operational"

def test_api_system_status():
    response = client.get("/api/system/status")
    assert response.status_code in (200, 404, 501)
    if response.status_code == 200:
        assert "backend" in response.json()

def test_api_events():
    response = client.get("/api/events/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data

def test_api_alerts():
    response = client.get("/api/alerts/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data

def test_api_devices():
    response = client.get("/api/devices/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list) or "items" in data
