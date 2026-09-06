"""
VoltGuard Phase 3 — End-to-End Integration & Attack Demonstration Script

Demonstrates the industrial protocol parsing layer and its direct coupling to the Phase 2 Physics Engine.

Steps demonstrated:
1. Parsing raw hexadecimal Modbus/TCP packet (00 01 00 00 00 06 01 06 9C 41 C3 50).
2. Decoding MBAP header, PDU, Function Code 06, Register 40001 (SET_RPM), Value 50000.
3. Normalizing into protocol-agnostic NormalizedCommand format.
4. Feeding normalized command into Physics Engine (physics.simulator.simulate()).
5. Evaluating physical state, verifying CATASTROPHIC classification and 100.0 risk score.
6. Displaying traffic generator scenarios across Normal, Suspicious, Attack, and Mixed modes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from parser.wrapper import ProtocolParserWrapper, parse_and_simulate
from parser.traffic_generator.generator import IndustrialTrafficGenerator
from physics.models import SafetyState


def print_banner(title: str):
    print("\n" + "=" * 80)
    print(f" {title.center(78)} ")
    print("=" * 80)


def run_attack_demo():
    print_banner("VOLTGUARD PHASE 3 — INDUSTRIAL PROTOCOL PARSER & ATTACK DEMO")

    # Step 1: Raw payload
    attack_hex = "00010000000601069C41C350"
    print(f"[STEP 1] Ingesting Raw Hex Modbus/TCP Payload:")
    print(f"         Payload: {attack_hex}")
    print(f"         Formatted: 00 01 00 00 00 06 01 06 9C 41 C3 50")
    print(f"         Source IP: 192.168.1.20 | Destination IP: 192.168.1.50 (Pump-01 Controller)")

    # Step 2 & 3: C++ / Wrapper Parser Execution
    print("\n[STEP 2] Executing C++ Protocol Parser...")
    wrapper = ProtocolParserWrapper()
    norm_cmd = wrapper.parse_hex(attack_hex, protocol="modbus", src_ip="192.168.1.20", dest_ip="192.168.1.50")

    print("\n[STEP 3] Normalized Command Object:")
    print(json.dumps(norm_cmd, indent=2))

    # Step 4: Physics Engine Evaluation
    print("\n[STEP 4] Passing Normalized Command to Physics Engine (physics.simulator.simulate)...")
    _, physics_res = parse_and_simulate(attack_hex, protocol="modbus", src_ip="192.168.1.20", dest_ip="192.168.1.50")

    safety_state_str = str(physics_res.safety_state).upper()

    print("\n[STEP 5] Physics Engine Impact & Risk Assessment:")
    print(f"         Command Parameter:  {norm_cmd['command']} = {norm_cmd['value']} {norm_cmd['unit']}")
    print(f"         Predicted Pressure: {physics_res.predicted_pressure:.2f} bar (Limit: {physics_res.pressure_limit} bar)")
    print(f"         Predicted Flow:     {physics_res.predicted_flow:.2f} L/min (Limit: {physics_res.flow_limit} L/min)")
    print(f"         Predicted Temp:     {physics_res.predicted_temperature:.2f} °C (Limit: {physics_res.temperature_limit} °C)")
    print(f"         System Stress:      {physics_res.system_stress:.2f} MPa (Limit: {physics_res.stress_limit} MPa)")
    print(f"         --------------------------------------------------")
    print(f"         SAFETY STATE:       [{safety_state_str}]")
    print(f"         RISK SCORE:         {physics_res.risk_score:.1f} / 100.0")

    if physics_res.violations:
        print(f"         VIOLATIONS DETECTED:")
        for v in physics_res.violations:
            print(f"           - {v.parameter.upper()}: actual={v.value:.2f}, limit={v.limit:.2f} ({v.description})")

    print(f"\n         EXPLANATION:\n         {physics_res.explanation}")

    # Assertion check for demo validity
    assert safety_state_str == "CATASTROPHIC", f"Expected CATASTROPHIC state, got {safety_state_str}"
    assert physics_res.risk_score == 100.0, f"Expected Risk Score 100.0, got {physics_res.risk_score}"

    print("\n[VERIFICATION SUCCESS] Attack payload correctly parsed and flagged as CATASTROPHIC with Risk Score 100.0!")


def run_generator_demo():
    print_banner("INDUSTRIAL TRAFFIC GENERATOR DEMONSTRATION")

    modes = ["normal", "suspicious", "attack", "mixed"]
    for m in modes:
        print(f"\n--- Scenario Mode: {m.upper()} (Showing 2 sample items) ---")
        items = IndustrialTrafficGenerator.generate(mode=m, count=2)
        for item in items:
            print(f"[{item['category']}] ID #{item['id']} | {item['protocol']} | Src: {item['source_ip']} -> Dest: {item['destination_ip']}")
            print(f"  HEX: {item['hex_payload']}")
            print(f"  Desc: {item['description']}")


def main():
    run_attack_demo()
    run_generator_demo()
    print("\n" + "=" * 80)
    print(" PHASE 3 DEMONSTRATION COMPLETED SUCCESSFULLY ".center(80))
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
