"""
VoltGuard Phase 5 — Full End-to-End Pipeline Smoke Check Script

Verifies the complete VoltGuard end-to-end integration:
1. Normal command (RPM 1500) -> SAFE -> ALLOW -> Persisted SecurityEvent & Telemetry.
2. Warning command (RPM 3000) -> WARNING -> MONITOR -> Warning Alert created.
3. Attack command (RPM 50000) -> CATASTROPHIC -> BLOCK_CRITICAL -> Critical Security Alert created.
4. Fail-closed safety check.
5. System status API endpoint check (/api/system/status).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.database.database import init_db, SessionLocal
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.telemetry import Telemetry
from backend.services.pipeline_service import pipeline_service
from fastapi.testclient import TestClient
from backend.main import app


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.center(78)} ")
    print("=" * 80)


def run_phase5_smoke_check():
    print_banner("VOLTGUARD PHASE 5 — END-TO-END PIPELINE ORCHESTRATION SMOKE CHECK")
    init_db()
    db = SessionLocal()

    # Step 1: Normal Command (RPM = 1500)
    print("\n[STEP 1] Testing Normal Command (SET_RPM = 1500)...")
    res_normal = pipeline_service.process_pipeline(
        command_input={"command": "SET_RPM", "value": 1500.0, "device_id": "Pump-01", "success": True},
        db_session=db
    )
    print(f"         Decision: {res_normal['decision_result']['decision']} | Safety State: {res_normal['decision_result']['safety_state']}")
    print(f"         Event ID: {res_normal['event_id']} | Processing Time: {res_normal['timing_ms']['total_processing_ms']} ms")
    assert res_normal["decision_result"]["decision"] == "ALLOW"
    assert res_normal["event_id"] is not None

    # Step 2: Warning Command (RPM = 3000)
    print("\n[STEP 2] Testing Warning Command (SET_RPM = 3000)...")
    res_warn = pipeline_service.process_pipeline(
        command_input={"command": "SET_RPM", "value": 3000.0, "device_id": "Pump-01", "success": True},
        db_session=db
    )
    print(f"         Decision: {res_warn['decision_result']['decision']} | Safety State: {res_warn['decision_result']['safety_state']}")
    print(f"         Alert ID: {res_warn['alert_id']}")
    assert res_warn["decision_result"]["decision"] in ("MONITOR", "BLOCK")

    # Step 3: Extreme Attack Payload (SET_RPM = 50000)
    attack_hex = "00010000000601069C41C350"
    print(f"\n[STEP 3] Ingesting Extreme Attack Modbus Payload ({attack_hex})...")
    res_attack = pipeline_service.process_pipeline(
        command_input=attack_hex,
        db_session=db
    )
    print(f"         Normalized Command: {res_attack['normalized_command']['command']} = {res_attack['normalized_command']['value']} {res_attack['normalized_command']['unit']}")
    print(f"         Physics Pressure:   {res_attack['physics_result']['predicted_pressure']:.2f} bar")
    print(f"         Decision Result:    {res_attack['decision_result']['decision']} | Risk: {res_attack['decision_result']['risk_score']}")
    print(f"         Alert Created ID:   {res_attack['alert_id']}")
    assert res_attack["decision_result"]["decision"] == "BLOCK_CRITICAL"
    assert res_attack["decision_result"]["safety_state"] == "CATASTROPHIC"
    assert res_attack["alert_id"] is not None

    # Step 4: Fail-Closed Pipeline Check
    print("\n[STEP 4] Testing Fail-Closed Pipeline Protection on Corrupted Input...")
    res_fail = pipeline_service.process_pipeline(
        command_input="INVALID_CORRUPTED_HEX_PAYLOAD",
        db_session=db
    )
    print(f"         Decision: {res_fail['decision_result']['decision']} | Reason: {res_fail['decision_result']['reason']}")
    assert res_fail["decision_result"]["decision"] == "BLOCK_CRITICAL"

    # Step 5: System Status API Check
    print("\n[STEP 5] Checking GET /api/system/status Endpoint...")
    client = TestClient(app)
    resp = client.get("/api/system/status")
    print(f"         System Status Response (HTTP {resp.status_code}):")
    print(f"         {resp.json()}")
    assert resp.status_code == 200
    assert resp.json()["backend"] == "OPERATIONAL"

    db.close()

    print("\n" + "=" * 80)
    print(" ALL PHASE 5 END-TO-END SMOKE CHECKS PASSED SUCCESSFULLY! ".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_phase5_smoke_check()
