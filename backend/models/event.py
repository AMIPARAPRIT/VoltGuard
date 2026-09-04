"""
SecurityEvent — SQLAlchemy model for recording parsed industrial commands
and their safety analysis results.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime

from backend.database.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_ip = Column(String, nullable=True)
    destination_ip = Column(String, nullable=True)
    device = Column(String, nullable=True)
    protocol = Column(String, nullable=False, default="modbus_tcp")
    command = Column(String, nullable=True)
    command_value = Column(Float, nullable=True)
    predicted_pressure = Column(Float, nullable=True)
    predicted_flow = Column(Float, nullable=True)
    predicted_temperature = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    safety_state = Column(String, nullable=True)       # SAFE, WARNING, CRITICAL
    decision = Column(String, nullable=True)            # ALLOW, BLOCK
    latency_ms = Column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} decision={self.decision} risk={self.risk_score}>"
