"""
Suspicious Industrial Traffic Generator

Generates anomalous or boundary-testing network traffic: rapid setpoint shifts,
high-rpm operations near threshold limits, or bursts from unusual network locations.
"""

import random
from typing import List, Dict, Any
from .normal_traffic import DEVICES, build_modbus_fc06_hex, build_modbus_fc03_hex


def generate_suspicious_traffic(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate suspicious operational traffic items.
    """
    traffic = []
    suspicious_ips = ["192.168.1.199", "192.168.1.250", "10.0.4.15"]

    for i in range(1, count + 1):
        traffic_type = random.choice(["high_rpm", "valve_max", "rapid_write", "unauthorized_ip"])
        trans_id = 5000 + i

        if traffic_type == "high_rpm":
            rpm = random.randint(2500, 3800)
            hex_payload = build_modbus_fc06_hex(trans_id, 40001, rpm)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Pump-01"],
                "hex_payload": hex_payload,
                "description": f"Suspicious boundary setpoint: High Pump RPM = {rpm} RPM",
                "category": "SUSPICIOUS"
            }
        elif traffic_type == "valve_max":
            valve_pct = random.randint(90, 100)
            hex_payload = build_modbus_fc06_hex(trans_id, 40002, valve_pct)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Valve-01"],
                "hex_payload": hex_payload,
                "description": f"Suspicious valve state: Valve forced to {valve_pct}% position",
                "category": "SUSPICIOUS"
            }
        elif traffic_type == "unauthorized_ip":
            src = random.choice(suspicious_ips)
            rpm = random.randint(2200, 3500)
            hex_payload = build_modbus_fc06_hex(trans_id, 40001, rpm)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": src,
                "destination_ip": DEVICES["Pump-01"],
                "hex_payload": hex_payload,
                "description": f"Unrecognized IP command source ({src}) sending Pump RPM = {rpm}",
                "category": "SUSPICIOUS"
            }
        else:
            # Rapid read burst
            hex_payload = build_modbus_fc03_hex(trans_id, 40001, 100)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Pressure-Sensor-01"],
                "hex_payload": hex_payload,
                "description": "High-frequency reconnaissance scan: Requesting 100 registers",
                "category": "SUSPICIOUS"
            }

        traffic.append(item)

    return traffic
