"""
VoltGuard Phase 4 — Rust Decision Engine Smoke Check Script

Basic smoke check verifying:
1. SAFE -> ALLOW
2. WARNING -> MONITOR
3. CRITICAL -> BLOCK
4. CATASTROPHIC -> BLOCK_CRITICAL (including 50000 RPM attack flow)
5. Failure / Invalid / Missing Input -> BLOCK_CRITICAL (Fail-Closed Logic)
6. Phase 3 Parser -> Phase 2 Physics -> Rust Decision Engine -> Backend pipeline
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from decision_engine.wrapper import decision_engine_wrapper, build_fail_closed_decision
from backend.services.decision_service import decision_service
from physics.models import PhysicsResult, SafetyState


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.center(78)} ")
    print("=" * 80)


def run_smoke_checks():
    print_banner("VOLTGUARD PHASE 4 — RUST DECISION ENGINE SMOKE CHECK")

    # Check 1: SAFE -> ALLOW
    safe_input = {
        "pump_rpm": 1200.0,
        "valve_position": 50.0,
        "predicted_pressure": 2.0,
        "predicted_flow": 120.0,
        "predicted_temperature": 45.0,
        "system_stress": 15.0,
        "risk_score": 10.0,
        "safety_state": "SAFE",
        "violations": []
    }
    res_safe = decision_engine_wrapper.evaluate(safe_input)
    print(f"[CHECK 1] SAFE Input -> Decision: {res_safe['decision']} | State: {res_safe['safety_state']}")
    assert res_safe["decision"] == "ALLOW", f"Expected ALLOW, got {res_safe['decision']}"

    # Check 2: WARNING -> MONITOR
    warning_input = {
        "pump_rpm": 2800.0,
        "valve_position": 85.0,
        "predicted_pressure": 60.0,
        "predicted_flow": 380.0,
        "predicted_temperature": 95.0,
        "system_stress": 90.0,
        "risk_score": 75.0,
        "safety_state": "WARNING",
        "violations": [{"parameter": "predicted_pressure", "value": 60.0, "limit": 80.0, "description": "High pressure"}]
    }
    res_warning = decision_engine_wrapper.evaluate(warning_input)
    print(f"[CHECK 2] WARNING Input -> Decision: {res_warning['decision']} | State: {res_warning['safety_state']}")
    assert res_warning["decision"] == "MONITOR", f"Expected MONITOR, got {res_warning['decision']}"

    # Check 3: CRITICAL -> BLOCK
    critical_input = {
        "pump_rpm": 3500.0,
        "valve_position": 95.0,
        "predicted_pressure": 76.0,
        "predicted_flow": 470.0,
        "predicted_temperature": 115.0,
        "system_stress": 125.0,
        "risk_score": 92.0,
        "safety_state": "CRITICAL",
        "violations": [{"parameter": "predicted_pressure", "value": 76.0, "limit": 80.0, "description": "Critical pressure threshold"}]
    }
    res_critical = decision_engine_wrapper.evaluate(critical_input)
    print(f"[CHECK 3] CRITICAL Input -> Decision: {res_critical['decision']} | State: {res_critical['safety_state']}")
    assert res_critical["decision"] == "BLOCK", f"Expected BLOCK, got {res_critical['decision']}"

    # Check 4: CATASTROPHIC -> BLOCK_CRITICAL (50000 RPM Attack Payload)
    attack_hex = "00010000000601069C41C350"
    res_attack = decision_service.process_packet_and_decide(attack_hex)
    dec_res = res_attack["decision_result"]
    print(f"[CHECK 4] 50000 RPM Attack Payload -> Decision: {dec_res['decision']} | State: {dec_res['safety_state']}")
    print(f"         Reason: {dec_res['reason']}")
    assert dec_res["decision"] == "BLOCK_CRITICAL", f"Expected BLOCK_CRITICAL, got {dec_res['decision']}"
    assert dec_res["safety_state"] == "CATASTROPHIC"

    # Check 5: FAIL-CLOSED Logic on missing / invalid input
    res_missing = decision_engine_wrapper.evaluate(None)
    print(f"[CHECK 5] None Input -> Decision: {res_missing['decision']} | Reason: {res_missing['reason']}")
    assert res_missing["decision"] == "BLOCK_CRITICAL"

    res_invalid_json = decision_engine_wrapper.evaluate("invalid json string {}")
    print(f"[CHECK 5b] Invalid JSON -> Decision: {res_invalid_json['decision']} | Reason: {res_invalid_json['reason']}")
    assert res_invalid_json["decision"] == "BLOCK_CRITICAL"

    print("\n" + "=" * 80)
    print(" ALL PHASE 4 SMOKE CHECKS PASSED SUCCESSFULLY! ".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_smoke_checks()
