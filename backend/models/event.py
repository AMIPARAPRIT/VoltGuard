"""
SecurityEvent — SQLAlchemy model for recording parsed industrial commands
and their safety analysis results.

Phase 8 extensions:
  - reason: human-readable explanation from Rust decision engine
  - violations: JSON-encoded list of physics violations
  - explanation: physics engine explanation text
  - function_code / register: raw protocol fields
  - alert_id: FK back-reference to associated Alert
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Text

from backend.database.database import Base


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_ip = Column(String, nullable=True)
    destination_ip = Column(String, nullable=True)
    device = Column(String, nullable=True)
    protocol = Column(String, nullable=False, default="modbus_tcp")
    function_code = Column(Integer, nullable=True)
    register = Column(Integer, nullable=True)
    command = Column(String, nullable=True)
    command_value = Column(Float, nullable=True)
    predicted_pressure = Column(Float, nullable=True)
    predicted_flow = Column(Float, nullable=True)
    predicted_temperature = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=True)
    safety_state = Column(String, nullable=True)       # SAFE, WARNING, CRITICAL, CATASTROPHIC
    decision = Column(String, nullable=True)            # ALLOW, MONITOR, BLOCK, BLOCK_CRITICAL
    reason = Column(Text, nullable=True)                # Decision reason from Rust engine
    violations = Column(Text, nullable=True)            # JSON: list of physics violations
    explanation = Column(Text, nullable=True)           # Physics engine explanation
    latency_ms = Column(Float, nullable=True)
    alert_id = Column(Integer, nullable=True)           # FK back-reference to Alert.id

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} decision={self.decision} risk={self.risk_score}>"
