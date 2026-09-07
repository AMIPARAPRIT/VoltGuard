"""
VoltGuard Protocol Parser Python Wrapper & Bridge

Provides Python interface to the compiled C++ voltguard_parser binary,
with a native Python fallback implementation for environments without C++ toolchains.
Connects raw industrial network payloads to the Physics Engine.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Project root setup
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from physics.models import PhysicsCommand, PhysicsResult
from physics.simulator import simulate


class RegisterMapPython:
    """Python mirror of C++ RegisterMap for fallback parsing."""

    DEFAULT_MAP = {
        40001: {"command": "SET_RPM", "description": "Pump RPM", "unit": "RPM", "device_id": "Pump-01"},
        40002: {"command": "SET_VALVE", "description": "Valve Position", "unit": "%", "device_id": "Valve-01"},
        40003: {"command": "SET_PRESSURE", "description": "Pressure Setpoint", "unit": "bar", "device_id": "Pressure-Sensor-01"},
        40004: {"command": "SET_TEMPERATURE", "description": "Temperature Setpoint", "unit": "°C", "device_id": "Temp-Sensor-01"},
    }

    @classmethod
    def get_mapping(cls, reg: int) -> dict:
        return cls.DEFAULT_MAP.get(reg, {
            "command": "UNKNOWN_COMMAND",
            "description": "Unknown Register",
            "unit": "RAW",
            "device_id": "PLC-01"
        })


class NativePythonParser:
    """Pure-Python fallback parser for Modbus/TCP and DNP3."""

    @staticmethod
    def current_iso_timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def hex_to_bytes(hex_str: str) -> bytes:
        clean = "".join(c for c in hex_str if c.isalnum())
        if len(clean) % 2 != 0:
            return b""
        try:
            return bytes.fromhex(clean)
        except ValueError:
            return b""

    @classmethod
    def parse_modbus(cls, hex_str: str, src_ip: str = "192.168.1.20", dest_ip: str = "192.168.1.50") -> dict:
        raw_bytes = cls.hex_to_bytes(hex_str)
        timestamp = cls.current_iso_timestamp()

        if len(raw_bytes) < 8:
            return {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dest_ip,
                "device_id": "PLC-01",
                "protocol": "Modbus/TCP",
                "function_code": 0,
                "register": 0,
                "command": "INVALID",
                "value": 0.0,
                "unit": "NONE",
                "success": False,
                "error": "Invalid Modbus/TCP packet length (minimum 8 bytes required)."
            }

        transaction_id = (raw_bytes[0] << 8) | raw_bytes[1]
        protocol_id = (raw_bytes[2] << 8) | raw_bytes[3]
        length = (raw_bytes[4] << 8) | raw_bytes[5]
        unit_id = raw_bytes[6]
        function_code = raw_bytes[7]

        if function_code == 3:  # Read Holding Registers
            if len(raw_bytes) < 12:
                reg_addr = 40001
                reg_qty = 1
            else:
                reg_addr = (raw_bytes[8] << 8) | raw_bytes[9]
                reg_qty = (raw_bytes[10] << 8) | raw_bytes[11]

            reg_def = RegisterMapPython.get_mapping(reg_addr)
            return {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dest_ip,
                "device_id": reg_def["device_id"],
                "protocol": "Modbus/TCP",
                "function_code": function_code,
                "register": reg_addr,
                "command": "READ_REGISTERS",
                "value": float(reg_qty),
                "unit": "COUNT",
                "success": True
            }

        elif function_code == 6:  # Write Single Register
            if len(raw_bytes) < 12:
                return {
                    "timestamp": timestamp,
                    "source_ip": src_ip,
                    "destination_ip": dest_ip,
                    "device_id": "PLC-01",
                    "protocol": "Modbus/TCP",
                    "function_code": function_code,
                    "register": 0,
                    "command": "INVALID",
                    "value": 0.0,
                    "unit": "NONE",
                    "success": False,
                    "error": "Invalid payload length for FC 06 (Write Single Register)."
                }

            reg_addr = (raw_bytes[8] << 8) | raw_bytes[9]
            reg_val = (raw_bytes[10] << 8) | raw_bytes[11]
            reg_def = RegisterMapPython.get_mapping(reg_addr)

            return {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dest_ip,
                "device_id": reg_def["device_id"],
                "protocol": "Modbus/TCP",
                "function_code": function_code,
                "register": reg_addr,
                "command": reg_def["command"],
                "value": float(reg_val),
                "unit": reg_def["unit"],
                "success": True
            }

        elif function_code == 16:  # Write Multiple Registers (0x10)
            if len(raw_bytes) < 13:
                return {
                    "timestamp": timestamp,
                    "source_ip": src_ip,
                    "destination_ip": dest_ip,
                    "device_id": "PLC-01",
                    "protocol": "Modbus/TCP",
                    "function_code": function_code,
                    "register": 0,
                    "command": "INVALID",
                    "value": 0.0,
                    "unit": "NONE",
                    "success": False,
                    "error": "Invalid payload length for FC 16."
                }

            reg_addr = (raw_bytes[8] << 8) | raw_bytes[9]
            first_val = (raw_bytes[13] << 8) | raw_bytes[14] if len(raw_bytes) >= 15 else 0
            reg_def = RegisterMapPython.get_mapping(reg_addr)

            return {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dest_ip,
                "device_id": reg_def["device_id"],
                "protocol": "Modbus/TCP",
                "function_code": function_code,
                "register": reg_addr,
                "command": reg_def["command"],
                "value": float(first_val),
                "unit": reg_def["unit"],
                "success": True
            }

        return {
            "timestamp": timestamp,
            "source_ip": src_ip,
            "destination_ip": dest_ip,
            "device_id": "PLC-01",
            "protocol": "Modbus/TCP",
            "function_code": function_code,
            "register": 0,
            "command": "UNSUPPORTED",
            "value": 0.0,
            "unit": "NONE",
            "success": False,
            "error": f"Unsupported function code: {function_code}"
        }

    @classmethod
    def parse_dnp3(cls, hex_str: str, src_ip: str = "192.168.1.50", dest_ip: str = "192.168.1.10") -> dict:
        raw_bytes = cls.hex_to_bytes(hex_str)
        timestamp = cls.current_iso_timestamp()

        if len(raw_bytes) < 10 or raw_bytes[0] != 0x05 or raw_bytes[1] != 0x64:
            return {
                "timestamp": timestamp,
                "source_ip": src_ip,
                "destination_ip": dest_ip,
                "device_id": "RTU-01",
                "protocol": "DNP3",
                "function_code": 0,
                "register": 0,
                "command": "INVALID",
                "value": 0.0,
                "unit": "NONE",
                "success": False,
                "error": "Invalid DNP3 frame header or sync bytes."
            }

        dest_addr = raw_bytes[4] | (raw_bytes[5] << 8)
        device_id = f"RTU-{dest_addr:02d}"
        func_code = raw_bytes[12] if len(raw_bytes) >= 13 else 0

        cmd_name = "DNP3_COMMAND"
        unit = "RAW"
        val = 0.0
        point_index = 0

        if len(raw_bytes) >= 18:
            point_index = raw_bytes[15]
            raw_val = int.from_bytes(raw_bytes[16:18], byteorder="little", signed=True)
            val = float(raw_val)
            if point_index in (0, 1):
                cmd_name = "SET_RPM"
                unit = "RPM"
                device_id = "Pump-01"
            elif point_index == 2:
                cmd_name = "SET_VALVE"
                unit = "%"
                device_id = "Valve-01"

        return {
            "timestamp": timestamp,
            "source_ip": src_ip,
            "destination_ip": dest_ip,
            "device_id": device_id,
            "protocol": "DNP3",
            "function_code": func_code,
            "register": point_index,
            "command": cmd_name,
            "value": val,
            "unit": unit,
            "success": True
        }


class ProtocolParserWrapper:
    """
    Main Python wrapper interface for VoltGuard Protocol Parser.
    Tries the compiled C++ executable first; falls back to NativePythonParser.
    """

    def __init__(self, binary_path: Optional[str] = None):
        if binary_path:
            self.binary_path = Path(binary_path)
        else:
            # Check standard build directory paths
            exe_name = "voltguard_parser.exe" if sys.platform == "win32" else "voltguard_parser"
            possible_paths = [
                _PROJECT_ROOT / "build" / exe_name,
                _PROJECT_ROOT / "parser" / "build" / exe_name,
                _PROJECT_ROOT / exe_name,
            ]
            self.binary_path = next((p for p in possible_paths if p.is_file()), None)

    def parse_hex(
        self,
        hex_string: str,
        protocol: str = "modbus",
        src_ip: str = "192.168.1.20",
        dest_ip: str = "192.168.1.50"
    ) -> dict:
        """
        Parse a hexadecimal packet payload into a NormalizedCommand dictionary.
        """
        # Try C++ binary executable if available
        if self.binary_path and self.binary_path.exists():
            try:
                cmd = [
                    str(self.binary_path),
                    "--hex", hex_string,
                    "--protocol", protocol,
                    "--src", src_ip,
                    "--dest", dest_ip
                ]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                stdout = result.stdout.strip()
                if stdout and "{" in stdout:
                    json_str = stdout[stdout.find("{"):stdout.rfind("}") + 1]
                    return json.loads(json_str)
            except Exception as e:
                # Log error and fall back to python parser
                pass

        # Fallback to pure Python parser
        if protocol.lower() in ("dnp3",):
            return NativePythonParser.parse_dnp3(hex_string, src_ip, dest_ip)
        else:
            return NativePythonParser.parse_modbus(hex_string, src_ip, dest_ip)


def command_to_physics_input(
    normalized_cmd: dict,
    current_state: Optional[dict] = None
) -> dict:
    """
    Translates a NormalizedCommand dict into inputs suitable for PhysicsCommand.

    Default baseline physical state:
      pump_rpm: 1200.0
      valve_position: 50.0
      current_pressure: 2.0 bar
      current_temperature: 45.0 °C
    """
    state = {
        "pump_rpm": 1200.0,
        "valve_position": 50.0,
        "current_pressure": 2.0,
        "current_temperature": 45.0,
    }
    if current_state:
        state.update(current_state)

    command_name = normalized_cmd.get("command", "")
    val = float(normalized_cmd.get("value", 0.0))

    if command_name == "SET_RPM":
        state["pump_rpm"] = val
    elif command_name == "SET_VALVE":
        state["valve_position"] = val
    elif command_name == "SET_PRESSURE":
        state["current_pressure"] = val
    elif command_name == "SET_TEMPERATURE":
        state["current_temperature"] = val

    return state


def parse_and_simulate(
    hex_payload: str,
    protocol: str = "modbus",
    src_ip: str = "192.168.1.20",
    dest_ip: str = "192.168.1.50",
    current_state: Optional[dict] = None
) -> Tuple[dict, PhysicsResult]:
    """
    Complete end-to-end processing pipeline:
    Raw Hex Payload -> C++/Python Parser -> NormalizedCommand -> Physics Engine -> PhysicsResult.
    """
    wrapper = ProtocolParserWrapper()
    norm_cmd = wrapper.parse_hex(hex_payload, protocol=protocol, src_ip=src_ip, dest_ip=dest_ip)
    physics_inputs = command_to_physics_input(norm_cmd, current_state=current_state)
    physics_res = simulate(physics_inputs)
    return norm_cmd, physics_res


if __name__ == "__main__":
    # Quick sanity check
    test_hex = "00010000000601069C41C350"
    print("Testing ProtocolParserWrapper on sample hex:", test_hex)
    cmd, res = parse_and_simulate(test_hex)
    print("\n[Normalized Command]")
    print(json.dumps(cmd, indent=2))
    print("\n[Physics Result]")
    print(f"Safety State: {res.safety_state}")
    print(f"Risk Score:   {res.risk_score}")
    print(f"Predicted Pressure: {res.predicted_pressure} bar")
