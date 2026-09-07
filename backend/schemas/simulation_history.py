from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SimulationHistoryBase(BaseModel):
    scenario: str
    device_id: str
    protocol: str
    command: str
    command_value: float
    risk_score: Optional[float] = None
    safety_state: Optional[str] = None
    decision: Optional[str] = None
    event_id: Optional[int] = None
    alert_id: Optional[int] = None
    raw_result: Optional[str] = None

class SimulationHistoryCreate(SimulationHistoryBase):
    pass

class SimulationHistoryResponse(SimulationHistoryBase):
    id: int
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
