import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.models.report import ReportMetadata
from backend.models.event import SecurityEvent
from backend.reports.generators.pdf_generator import generate_report_pdf
from backend.core.config import PROJECT_ROOT

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
            report_type=request_data.get('report_type'),
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
                "status": metadata.status
            },
            "data": data
        }

    def _gather_report_data(self, metadata: ReportMetadata, db: Session) -> Dict[str, Any]:
        result = {}
        # If it's linked to a specific event
        if metadata.event_id:
            event = db.query(SecurityEvent).filter(SecurityEvent.id == metadata.event_id).first()
            if event:
                result['event'] = {
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "device": event.device,
                    "protocol": event.protocol,
                    "command": event.command,
                    "command_value": event.command_value,
                    "predicted_pressure": event.predicted_pressure,
                    "predicted_flow": event.predicted_flow,
                    "predicted_temperature": event.predicted_temperature,
                    "risk_score": event.risk_score,
                    "safety_state": event.safety_state,
                    "decision": event.decision,
                    "reason": event.reason,
                    "violations": event.violations,
                    "explanation": event.explanation
                }
        else:
            # Gather list of events based on filters
            query = db.query(SecurityEvent)
            if metadata.primary_device:
                query = query.filter(SecurityEvent.device == metadata.primary_device)
            if metadata.severity:
                if metadata.severity == 'CRITICAL':
                    query = query.filter(SecurityEvent.safety_state.in_(['CRITICAL', 'CATASTROPHIC']))
                else:
                    query = query.filter(SecurityEvent.safety_state == metadata.severity)
            
            events = query.order_by(desc(SecurityEvent.timestamp)).limit(50).all()
            result['events'] = []
            for event in events:
                result['events'].append({
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "device": event.device,
                    "command": event.command,
                    "command_value": event.command_value,
                    "safety_state": event.safety_state,
                    "decision": event.decision
                })
                
        return result

    def get_report_pdf(self, report_db_id: int, db: Session) -> str:
        """
        Generates the PDF file on demand and returns the file path.
        """
        metadata = db.query(ReportMetadata).filter(ReportMetadata.id == report_db_id).first()
        if not metadata:
            return None
            
        pdf_path = str(REPORTS_DIR / f"{metadata.report_id}.pdf")
        
        # If already exists, just return it (optional caching)
        if os.path.exists(pdf_path):
            return pdf_path
            
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
