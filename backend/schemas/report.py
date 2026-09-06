from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class ReportMetadataBase(BaseModel):
    report_type: str
    primary_device: Optional[str] = None
    severity: Optional[str] = None
    filters: Optional[str] = None
    event_id: Optional[int] = None
    alert_id: Optional[int] = None
    simulation_id: Optional[int] = None

class ReportMetadataCreate(ReportMetadataBase):
    pass

class ReportMetadataResponse(ReportMetadataBase):
    id: int
    report_id: str
    generated_at: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class ReportGenerationRequest(BaseModel):
    report_type: str = Field(..., description="SECURITY_EVENT, PHYSICAL_SAFETY, SIMULATION, INCIDENT_SUMMARY, SYSTEM_ACTIVITY")
    primary_device: Optional[str] = None
    severity: Optional[str] = None
    event_id: Optional[int] = None
    alert_id: Optional[int] = None
    simulation_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
