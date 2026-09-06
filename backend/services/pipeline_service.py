"""
VoltGuard Pipeline Service — Central Orchestrator

Single source of truth pipeline entry point:
Raw Industrial Payload / Command
       ↓
Protocol Parser (parser/wrapper.py)
       ↓
NormalizedCommand
       ↓
Physics Engine (physics/simulator.py)
       ↓
PhysicsResult
       ↓
Rust Decision Engine (decision_engine/wrapper.py)
       ↓
DecisionResult
       ↓
Database Persistence (SecurityEvent, Alert, Telemetry)
       ↓
WebSocket Live Event Broadcast (ws_manager)
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

# Project root setup
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.core.logging import get_logger
from backend.database.database import SessionLocal
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.telemetry import Telemetry
from backend.websocket.manager import ws_manager

from parser.wrapper import ProtocolParserWrapper, command_to_physics_input
from physics.simulator import simulate
from physics.models import PhysicsResult
from decision_engine.wrapper import decision_engine_wrapper, build_fail_closed_decision

logger = get_logger("pipeline.service")


def get_current_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class PipelineService:
    """
    Central Pipeline Orchestrator for VoltGuard.
    """

    def __init__(self):
        self.parser_wrapper = ProtocolParserWrapper()
        self.decision_wrapper = decision_engine_wrapper

    def process_pipeline(
        self,
        command_input: Union[str, Dict[str, Any]],
        protocol: str = "modbus",
        src_ip: str = "192.168.1.20",
        dest_ip: str = "192.168.1.50",
        current_state: Optional[Dict[str, float]] = None,
        db_session: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute full VoltGuard pipeline synchronously.
        """
        start_time = time.perf_counter()

        # Step 1: Parse / Normalize Command
        norm_cmd: Optional[Dict[str, Any]] = None
        parse_error: Optional[str] = None

        try:
            if isinstance(command_input, str):
                if command_input.startswith("{"): # JSON string
                    norm_cmd = json.loads(command_input)
                else: # Raw hex packet payload
                    norm_cmd = self.parser_wrapper.parse_hex(
                        command_input, protocol=protocol, src_ip=src_ip, dest_ip=dest_ip
                    )
            elif isinstance(command_input, dict):
                if "command" in command_input or "register" in command_input:
                    norm_cmd = command_input
                elif "hex_payload" in command_input:
                    norm_cmd = self.parser_wrapper.parse_hex(
                        command_input["hex_payload"],
                        protocol=command_input.get("protocol", protocol),
                        src_ip=command_input.get("source_ip", src_ip),
                        dest_ip=command_input.get("destination_ip", dest_ip)
                    )
                else:
                    norm_cmd = command_input
        except Exception as e:
            parse_error = f"Parser exception: {str(e)}"
            logger.error(f"[PARSER] {parse_error}")

        if not norm_cmd or norm_cmd.get("success") is False:
            err_msg = parse_error or norm_cmd.get("error") if norm_cmd else "Invalid input format"
            logger.warning(f"[PIPELINE] Protocol parsing failed: {err_msg}")

        # Step 2: Physics Simulation
        physics_result: Optional[PhysicsResult] = None
        physics_error: Optional[str] = None
        t_phys_start = time.perf_counter()

        if norm_cmd and norm_cmd.get("success", True):
            try:
                phys_inputs = command_to_physics_input(norm_cmd, current_state=current_state)
                logger.info(f"[PACKET] Ingested: {norm_cmd.get('protocol')} from {norm_cmd.get('source_ip')} -> {norm_cmd.get('destination_ip')}")
                logger.info(f"[PARSED] Command={norm_cmd.get('command')} Value={norm_cmd.get('value')} Device={norm_cmd.get('device_id')}")

                physics_result = simulate(phys_inputs)
                logger.info(f"[PHYSICS] Device={norm_cmd.get('device_id')} RPM={physics_result.pump_rpm} Pressure={physics_result.predicted_pressure:.2f} bar State={physics_result.safety_state}")
            except Exception as e:
                physics_error = f"Physics Engine exception: {str(e)}"
                logger.error(f"[PHYSICS] {physics_error}")

        physics_latency_ms = (time.perf_counter() - t_phys_start) * 1000.0

        # Step 3: Rust Decision Engine Policy Evaluation
        decision_result: Dict[str, Any]
        t_dec_start = time.perf_counter()

        if physics_result:
            try:
                decision_result = self.decision_wrapper.evaluate(physics_result)
                logger.info(f"[DECISION] Device={norm_cmd.get('device_id', 'PLC-01')} Decision={decision_result.get('decision')} RiskScore={decision_result.get('risk_score')}")
            except Exception as e:
                logger.error(f"[DECISION] Rust Decision Engine exception: {e}")
                decision_result = build_fail_closed_decision(f"Decision engine failure: {str(e)}", 0)
        else:
            reason = physics_error or parse_error or "Physical safety validation unavailable."
            decision_result = build_fail_closed_decision(reason, 0)
            logger.warning(f"[DECISION] Fail-Closed triggered: Decision=BLOCK_CRITICAL Reason={reason}")

        total_processing_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 4: Database Persistence (SecurityEvent, Alert, Telemetry)
        db_created = False
        db = db_session or SessionLocal()

        event_record = None
        alert_record = None
        telemetry_record = None

        try:
            device_id = norm_cmd.get("device_id", "PLC-01") if norm_cmd else "PLC-01"
            cmd_name = norm_cmd.get("command", "UNKNOWN") if norm_cmd else "UNKNOWN"
            cmd_val = norm_cmd.get("value", 0.0) if norm_cmd else 0.0
            proto = norm_cmd.get("protocol", protocol) if norm_cmd else protocol

            # SecurityEvent
            event_record = SecurityEvent(
                source_ip=norm_cmd.get("source_ip", src_ip) if norm_cmd else src_ip,
                destination_ip=norm_cmd.get("destination_ip", dest_ip) if norm_cmd else dest_ip,
                device=device_id,
                protocol=proto,
                command=cmd_name,
                command_value=float(cmd_val),
                predicted_pressure=physics_result.predicted_pressure if physics_result else None,
                predicted_flow=physics_result.predicted_flow if physics_result else None,
                predicted_temperature=physics_result.predicted_temperature if physics_result else None,
                risk_score=decision_result.get("risk_score"),
                safety_state=str(decision_result.get("safety_state")),
                decision=str(decision_result.get("decision")),
                latency_ms=total_processing_ms,
            )
            db.add(event_record)

            # Alert Creation (if BLOCK, BLOCK_CRITICAL, or MONITOR)
            dec_str = str(decision_result.get("decision")).upper()
            if dec_str in ("BLOCK", "BLOCK_CRITICAL", "MONITOR"):
                severity = "CRITICAL" if dec_str == "BLOCK_CRITICAL" else ("WARNING" if dec_str in ("BLOCK", "MONITOR") else "INFO")
                title = f"SECURITY ALERT: [{dec_str}] on {device_id}"
                message = decision_result.get("reason", "Physical safety threshold exceeded.")

                alert_record = Alert(
                    severity=severity,
                    title=title,
                    message=message,
                    device=device_id,
                    acknowledged=False,
                )
                db.add(alert_record)
                logger.info(f"[ALERT] Created Alert id={title} severity={severity}")

            # Telemetry Persistence
            if physics_result:
                telemetry_record = Telemetry(
                    device=device_id,
                    pump_rpm=physics_result.pump_rpm,
                    valve_position=physics_result.valve_position,
                    pressure=physics_result.predicted_pressure,
                    flow_rate=physics_result.predicted_flow,
                    temperature=physics_result.predicted_temperature,
                    stress=physics_result.system_stress,
                )
                db.add(telemetry_record)

            db.commit()
            if event_record:
                db.refresh(event_record)
            if alert_record:
                db.refresh(alert_record)
            if telemetry_record:
                db.refresh(telemetry_record)

            logger.info(f"[PERSISTED] SecurityEvent ID={event_record.id if event_record else 'N/A'}")

        except Exception as e:
            logger.error(f"[ERROR] Database persistence failed: {e}")
            db.rollback()
        finally:
            if not db_session:
                db.close()

        # Step 5: Prepare WS Payload & Schedule Async Broadcast
        ws_payload = {
            "type": "security_event",
            "timestamp": get_current_iso(),
            "device_id": norm_cmd.get("device_id", "PLC-01") if norm_cmd else "PLC-01",
            "protocol": norm_cmd.get("protocol", protocol) if norm_cmd else protocol,
            "command": norm_cmd.get("command") if norm_cmd else None,
            "value": norm_cmd.get("value") if norm_cmd else None,
            "predicted_pressure": physics_result.predicted_pressure if physics_result else None,
            "predicted_flow": physics_result.predicted_flow if physics_result else None,
            "predicted_temperature": physics_result.predicted_temperature if physics_result else None,
            "system_stress": physics_result.system_stress if physics_result else None,
            "risk_score": decision_result.get("risk_score"),
            "safety_state": decision_result.get("safety_state"),
            "decision": decision_result.get("decision"),
            "reason": decision_result.get("reason"),
            "event_id": event_record.id if event_record else None,
            "alert_id": alert_record.id if alert_record else None,
            "total_latency_ms": round(total_processing_ms, 3)
        }

        # Try async broadcast if event loop is running
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(ws_payload))
                logger.info(f"[WEBSOCKET] Live event broadcast scheduled")
        except RuntimeError:
            pass

        return {
            "normalized_command": norm_cmd,
            "physics_result": physics_result.model_dump() if physics_result else None,
            "decision_result": decision_result,
            "event_id": event_record.id if event_record else None,
            "alert_id": alert_record.id if alert_record else None,
            "telemetry_id": telemetry_record.id if telemetry_record else None,
            "timing_ms": {
                "physics_latency_ms": round(physics_latency_ms, 3),
                "total_processing_ms": round(total_processing_ms, 3)
            }
        }


# Singleton pipeline service instance
pipeline_service = PipelineService()
