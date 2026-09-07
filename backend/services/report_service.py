import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.report import ReportMetadata
from backend.models.event import SecurityEvent
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.simulation import SimulationHistory
from backend.reports.generators.pdf_generator import generate_report_pdf
from backend.core.config import PROJECT_ROOT, get_settings

REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

class ReportService:
    
    def generate_report(self, request_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """
        Creates a new report metadata entry in the database and prepares the data.
        """
        report_id = f"RPT-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Prepare metadata
        metadata = ReportMetadata(
            report_type=request_data.get('report_type', 'SECURITY_EVENT'),
            report_id=report_id,
            primary_device=request_data.get('primary_device'),
            severity=request_data.get('severity'),
            event_id=request_data.get('event_id'),
            alert_id=request_data.get('alert_id'),
            simulation_id=request_data.get('simulation_id'),
            filters=json.dumps(request_data)
        )
        
        db.add(metadata)
        db.commit()
        db.refresh(metadata)
        
        # Gather data for preview
        data = self._gather_report_data(metadata, db)
        
        return {
            "metadata": {
                "id": metadata.id,
                "report_id": metadata.report_id,
                "report_type": metadata.report_type,
                "generated_at": metadata.generated_at.isoformat(),
                "status": metadata.status,
                "primary_device": metadata.primary_device,
                "severity": metadata.severity
            },
            "data": data
        }

    def _gather_report_data(self, metadata: ReportMetadata, db: Session) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        limits = get_settings().safety_limits

        # 1. System Summary Metrics
        device_count = db.query(Device).count()
        event_count = db.query(SecurityEvent).count()
        alert_count = db.query(Alert).count()
        blocked_count = db.query(SecurityEvent).filter(SecurityEvent.decision.in_(['BLOCK', 'BLOCK_CRITICAL'])).count()
        critical_count = db.query(SecurityEvent).filter(SecurityEvent.safety_state.in_(['CRITICAL', 'CATASTROPHIC'])).count()

        result['system_summary'] = {
            "device_count": device_count,
            "event_count": event_count,
            "alert_count": alert_count,
            "blocked_count": blocked_count,
            "critical_count": critical_count,
            "safety_limits": limits.model_dump()
        }

        # 2. Targeted Event / Alert / Incident Identification
        target_event = None
        if metadata.event_id:
            target_event = db.query(SecurityEvent).filter(SecurityEvent.id == metadata.event_id).first()
        elif metadata.alert_id:
            alert = db.query(Alert).filter(Alert.id == metadata.alert_id).first()
            if alert and alert.event_id:
                target_event = db.query(SecurityEvent).filter(SecurityEvent.id == alert.event_id).first()
        elif metadata.report_type == 'INCIDENT_SUMMARY':
            # Default to latest critical/catastrophic event if no event_id specified
            target_event = db.query(SecurityEvent).filter(
                SecurityEvent.safety_state.in_(['CRITICAL', 'CATASTROPHIC'])
            ).order_by(desc(SecurityEvent.timestamp)).first()
            if not target_event:
                target_event = db.query(SecurityEvent).order_by(desc(SecurityEvent.timestamp)).first()

        if target_event:
            related_alert = None
            if target_event.alert_id:
                related_alert = db.query(Alert).filter(Alert.id == target_event.alert_id).first()

            result['event'] = {
                "id": target_event.id,
                "timestamp": target_event.timestamp.isoformat(),
                "device": target_event.device,
                "protocol": target_event.protocol,
                "source_ip": target_event.source_ip,
                "destination_ip": target_event.destination_ip,
                "command": target_event.command,
                "command_value": target_event.command_value,
                "predicted_pressure": target_event.predicted_pressure,
                "predicted_flow": target_event.predicted_flow,
                "predicted_temperature": target_event.predicted_temperature,
                "risk_score": target_event.risk_score,
                "safety_state": target_event.safety_state,
                "decision": target_event.decision,
                "reason": target_event.reason,
                "violations": target_event.violations,
                "explanation": target_event.explanation,
                "latency_ms": target_event.latency_ms,
                "alert_id": target_event.alert_id
            }

            if related_alert:
                result['alert'] = {
                    "id": related_alert.id,
                    "title": related_alert.title,
                    "severity": related_alert.severity,
                    "status": related_alert.status,
                    "message": related_alert.message,
                    "timestamp": related_alert.timestamp.isoformat()
                }

            # Chronological Incident Timeline
            t_iso = target_event.timestamp.isoformat()
            timeline = [
                {"timestamp": t_iso, "stage": "Command Received", "details": f"{target_event.protocol.upper()} command {target_event.command} = {target_event.command_value} sent to {target_event.device} from {target_event.source_ip}"},
                {"timestamp": t_iso, "stage": "Physics Simulation", "details": f"Physics engine evaluated: Pressure={target_event.predicted_pressure or 0:.1f} bar, Flow={target_event.predicted_flow or 0:.1f} L/min, Temp={target_event.predicted_temperature or 0:.1f} °C"},
            ]
            if target_event.safety_state != 'SAFE':
                timeline.append({"timestamp": t_iso, "stage": "Safety Violation Detected", "details": f"Safety State: {target_event.safety_state} | Violations: {target_event.violations or 'Parameter limit exceeded'}"})
            
            timeline.append({"timestamp": t_iso, "stage": "Rust Security Decision", "details": f"Rust Decision Engine evaluated policy: {target_event.decision} (Reason: {target_event.reason or 'Policy check'})"})
            
            if related_alert:
                timeline.append({"timestamp": related_alert.timestamp.isoformat(), "stage": "Alert Generated", "details": f"Active Alert #{related_alert.id} generated: {related_alert.title} [{related_alert.severity}]"})
            
            result['timeline'] = timeline

        # 3. Report-Specific Querying
        if metadata.report_type == 'SIMULATION':
            sim_query = db.query(SimulationHistory)
            if metadata.primary_device:
                sim_query = sim_query.filter(SimulationHistory.device_id == metadata.primary_device)
            sims = sim_query.order_by(desc(SimulationHistory.timestamp)).limit(50).all()
            result['simulations'] = [
                {
                    "id": s.id,
                    "timestamp": s.timestamp.isoformat(),
                    "scenario": s.scenario,
                    "device_id": s.device_id,
                    "protocol": s.protocol,
                    "command": s.command,
                    "command_value": s.command_value,
                    "risk_score": s.risk_score,
                    "safety_state": s.safety_state,
                    "decision": s.decision,
                    "event_id": s.event_id,
                    "alert_id": s.alert_id
                } for s in sims
            ]
        
        # 4. Multi-Event Summaries
        query = db.query(SecurityEvent)
        if metadata.primary_device:
            query = query.filter(SecurityEvent.device == metadata.primary_device)
        if metadata.severity:
            if metadata.severity == 'CRITICAL':
                query = query.filter(SecurityEvent.safety_state.in_(['CRITICAL', 'CATASTROPHIC']))
            else:
                query = query.filter(SecurityEvent.safety_state == metadata.severity)

        events = query.order_by(desc(SecurityEvent.timestamp)).limit(50).all()
        result['events'] = [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "device": e.device,
                "protocol": e.protocol,
                "command": e.command,
                "command_value": e.command_value,
                "predicted_pressure": e.predicted_pressure,
                "predicted_flow": e.predicted_flow,
                "predicted_temperature": e.predicted_temperature,
                "risk_score": e.risk_score,
                "safety_state": e.safety_state,
                "decision": e.decision,
                "reason": e.reason
            } for e in events
        ]

        return result

    def get_report_pdf(self, report_db_id: int, db: Session) -> str:
        """
        Generates the PDF file on demand and returns the file path.
        """
        metadata = db.query(ReportMetadata).filter(ReportMetadata.id == report_db_id).first()
        if not metadata:
            return None
            
        pdf_path = str(REPORTS_DIR / f"{metadata.report_id}.pdf")
        
        # Regenerate to ensure fresh snapshot
        data = self._gather_report_data(metadata, db)
        
        meta_dict = {
            "report_id": metadata.report_id,
            "report_type": metadata.report_type,
            "primary_device": metadata.primary_device,
            "severity": metadata.severity
        }
        
        generate_report_pdf(meta_dict, data, pdf_path)
        return pdf_path

    def get_history(self, db: Session) -> List[Dict[str, Any]]:
        reports = db.query(ReportMetadata).order_by(desc(ReportMetadata.generated_at)).limit(50).all()
        return [
            {
                "id": r.id,
                "report_id": r.report_id,
                "report_type": r.report_type,
                "generated_at": r.generated_at.isoformat(),
                "status": r.status,
                "primary_device": r.primary_device,
                "severity": r.severity
            } for r in reports
        ]

report_service = ReportService()

