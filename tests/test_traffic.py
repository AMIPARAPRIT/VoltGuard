"""
VoltGuard — Phase 3 Traffic Parsing & API Endpoint Unit Tests
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from parser.wrapper import ProtocolParserWrapper, parse_and_simulate
from parser.traffic_generator.generator import IndustrialTrafficGenerator

client = TestClient(app)


def test_wrapper_modbus_parsing():
    wrapper = ProtocolParserWrapper()
    # Modbus FC 06 -> Register 40001 -> Value 50000
    hex_payload = "00010000000601069C41C350"
    res = wrapper.parse_hex(hex_payload, protocol="modbus")
    assert res["success"] is True
    assert res["command"] == "SET_RPM"
    assert res["value"] == 50000.0
    assert res["register"] == 40001


def test_wrapper_dnp3_parsing():
    wrapper = ProtocolParserWrapper()
    # DNP3 Read header
    hex_payload = "05640A0001003200123401"
    res = wrapper.parse_hex(hex_payload, protocol="dnp3")
    assert res["protocol"] == "DNP3"
    assert res["success"] is True


def test_parse_and_simulate_catastrophic():
    attack_hex = "00010000000601069C41C350"
    norm_cmd, phys_res = parse_and_simulate(attack_hex)
    assert norm_cmd["command"] == "SET_RPM"
    assert norm_cmd["value"] == 50000.0
    assert str(phys_res.safety_state).upper() == "CATASTROPHIC"
    assert phys_res.risk_score == 100.0


def test_traffic_generator_modes():
    for mode in ["normal", "suspicious", "attack", "mixed"]:
        items = IndustrialTrafficGenerator.generate(mode=mode, count=5)
        assert len(items) == 5
        assert all("hex_payload" in item for item in items)


def test_api_parse_endpoint():
    response = client.post(
        "/api/traffic/parse",
        json={
            "hex_payload": "00010000000601069C41C350",
            "protocol": "modbus",
            "source_ip": "192.168.1.20",
            "destination_ip": "192.168.1.50"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["command"] == "SET_RPM"
    assert data["value"] == 50000.0


def test_api_process_endpoint():
    response = client.post(
        "/api/traffic/process",
        json={
            "hex_payload": "00010000000601069C41C350",
            "protocol": "modbus"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "normalized_command" in data
    assert "physics_result" in data
    assert data["physics_result"]["risk_score"] == 100.0


def test_api_generate_endpoint():
    response = client.post(
        "/api/traffic/generate",
        json={"mode": "attack", "count": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["category"] == "ATTACK"
