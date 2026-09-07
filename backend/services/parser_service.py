"""
VoltGuard Backend Parser Service

Service layer connecting network traffic parser wrapper to backend business logic & physics engine.
"""

from typing import Dict, Any, Optional, Tuple
from parser.wrapper import ProtocolParserWrapper, parse_and_simulate


class ParserService:
    """
    Parser service orchestrating industrial network traffic decoding and physics evaluation.
    """

    def __init__(self):
        self.wrapper = ProtocolParserWrapper()

    def parse_payload(
        self,
        hex_payload: str,
        protocol: str = "modbus",
        src_ip: str = "192.168.1.20",
        dest_ip: str = "192.168.1.50"
    ) -> Dict[str, Any]:
        """Parse raw hex string payload into normalized command format."""
        return self.wrapper.parse_hex(hex_payload, protocol=protocol, src_ip=src_ip, dest_ip=dest_ip)

    def process_and_evaluate(
        self,
        hex_payload: str,
        protocol: str = "modbus",
        src_ip: str = "192.168.1.20",
        dest_ip: str = "192.168.1.50",
        current_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Processes hex packet through Parser -> Physics Engine pipeline,
        returning structured dict containing normalized command and physics evaluation result.
        """
        norm_cmd, physics_res = parse_and_simulate(
            hex_payload=hex_payload,
            protocol=protocol,
            src_ip=src_ip,
            dest_ip=dest_ip,
            current_state=current_state
        )

        return {
            "normalized_command": norm_cmd,
            "physics_result": physics_res.model_dump(),
        }


# Singleton service instance
parser_service = ParserService()
