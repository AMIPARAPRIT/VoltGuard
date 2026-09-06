"""
Normal Industrial Traffic Generator

Generates legitimate Modbus/TCP and DNP3 payloads representing standard
operational telemetry and control commands within safe operating boundaries.
"""

import random
from typing import List, Dict, Any


DEVICES = {
    "PLC-01": "192.168.1.10",
    "Pump-01": "192.168.1.20",
    "Pump-02": "192.168.1.21",
    "Valve-01": "192.168.1.30",
    "Pressure-Sensor-01": "192.168.1.40",
    "Flow-Sensor-01": "192.168.1.41",
    "RTU-01": "192.168.1.50",
}


def build_modbus_fc06_hex(trans_id: int, register: int, value: int) -> str:
    """Construct Modbus/TCP FC 06 hex string."""
    return f"{trans_id:04X}000000060106{register:04X}{value:04X}"


def build_modbus_fc03_hex(trans_id: int, register: int, qty: int) -> str:
    """Construct Modbus/TCP FC 03 hex string."""
    return f"{trans_id:04X}000000060103{register:04X}{qty:04X}"


def generate_normal_traffic(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate normal operational traffic items.
    """
    traffic = []
    for i in range(1, count + 1):
        traffic_type = random.choice(["modbus_rpm", "modbus_valve", "modbus_read", "dnp3_read"])
        trans_id = i

        if traffic_type == "modbus_rpm":
            rpm = random.randint(1000, 2000)
            hex_payload = build_modbus_fc06_hex(trans_id, 40001, rpm)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Pump-01"],
                "hex_payload": hex_payload,
                "description": f"Standard operational setpoint: Pump RPM = {rpm} RPM",
                "category": "NORMAL"
            }
        elif traffic_type == "modbus_valve":
            valve_pct = random.randint(40, 80)
            hex_payload = build_modbus_fc06_hex(trans_id, 40002, valve_pct)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Valve-01"],
                "hex_payload": hex_payload,
                "description": f"Standard operational command: Valve Position = {valve_pct}%",
                "category": "NORMAL"
            }
        elif traffic_type == "modbus_read":
            hex_payload = build_modbus_fc03_hex(trans_id, 40001, 4)
            item = {
                "id": i,
                "protocol": "Modbus/TCP",
                "source_ip": DEVICES["PLC-01"],
                "destination_ip": DEVICES["Pressure-Sensor-01"],
                "hex_payload": hex_payload,
                "description": "Routine telemetry polling: Read Holding Registers 40001–40004",
                "category": "NORMAL"
            }
        else:
            # DNP3 Read frame sync 05 64 length 0A ctrl C4 dest 00 01 src 00 32 crc ... app read 01
            hex_payload = "05640A0001003200123401"
            item = {
                "id": i,
                "protocol": "DNP3",
                "source_ip": DEVICES["RTU-01"],
                "destination_ip": DEVICES["PLC-01"],
                "hex_payload": hex_payload,
                "description": "DNP3 Class 1 data read poll",
                "category": "NORMAL"
            }

        traffic.append(item)

    return traffic
