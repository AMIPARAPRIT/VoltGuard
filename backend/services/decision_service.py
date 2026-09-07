"""
VoltGuard Backend Decision Service

Service layer coordinating raw packet parsing, physics simulation,
and Rust decision engine policy evaluation.
"""

from typing import Dict, Any, Optional
from parser.wrapper import parse_and_simulate
from decision_engine.wrapper import decision_engine_wrapper, build_fail_closed_decision


class DecisionService:
    """
    Coordinates end-to-end processing pipeline:
    Parser -> Physics Simulation -> Rust Decision Engine.
    """

    def __init__(self):
        self.decision_wrapper = decision_engine_wrapper

    def process_packet_and_decide(
        self,
        hex_payload: str,
        protocol: str = "modbus",
        src_ip: str = "192.168.1.20",
        dest_ip: str = "192.168.1.50",
        current_state: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Executes full security pipeline:
          1. Protocol Parser decodes raw hex into NormalizedCommand.
          2. Physics Engine calculates physical outputs and safety state.
          3. Rust Decision Engine evaluates policy and returns DecisionResult.
        """
        try:
            norm_cmd, physics_res = parse_and_simulate(
                hex_payload=hex_payload,
                protocol=protocol,
                src_ip=src_ip,
                dest_ip=dest_ip,
                current_state=current_state
            )

            # Evaluate through Rust Decision Engine
            decision_res = self.decision_wrapper.evaluate(physics_res)

            return {
                "normalized_command": norm_cmd,
                "physics_result": physics_res.model_dump(),
                "decision_result": decision_res,
            }
        except Exception as e:
            # Enforce fail-closed policy on pipeline failure
            fail_closed = build_fail_closed_decision(f"Pipeline processing failure: {str(e)}", 0)
            return {
                "normalized_command": None,
                "physics_result": None,
                "decision_result": fail_closed,
            }


# Singleton instance
decision_service = DecisionService()
