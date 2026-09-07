from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime
from backend.database.database import Base

class SimulationHistory(Base):
    __tablename__ = "simulation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    scenario = Column(String, index=True)  # NORMAL, WARNING, CRITICAL, ATTACK, CUSTOM
    device_id = Column(String, index=True)
    protocol = Column(String)
    command = Column(String)
    command_value = Column(Float)
    
    # Results (can be joined or stored denormalized for speed)
    risk_score = Column(Float)
    safety_state = Column(String)
    decision = Column(String)
    
    event_id = Column(Integer, nullable=True)
    alert_id = Column(Integer, nullable=True)
    
    # Store complete response dump as JSON string
    raw_result = Column(Text, nullable=True)
