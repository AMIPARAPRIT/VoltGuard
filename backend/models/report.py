from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from backend.database.database import Base

class ReportMetadata(Base):
    __tablename__ = "report_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String, index=True) # SECURITY_EVENT, PHYSICAL_SAFETY, SIMULATION, INCIDENT_SUMMARY, SYSTEM_ACTIVITY
    report_id = Column(String, unique=True, index=True) # e.g. RPT-20260906-0001
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata for filtering/history
    primary_device = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    status = Column(String, default="READY")
    
    # Store applied filters for reference
    filters = Column(Text, nullable=True) # JSON string
    
    # If it is generated from a specific event/alert/simulation
    event_id = Column(Integer, nullable=True)
    alert_id = Column(Integer, nullable=True)
    simulation_id = Column(Integer, nullable=True)
