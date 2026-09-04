"""
Telemetry — SQLAlchemy model for storing real-time sensor readings
from industrial devices.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime

from backend.database.database import Base


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    device = Column(String, nullable=True)
    pump_rpm = Column(Float, nullable=True)
    valve_position = Column(Float, nullable=True)       # 0.0 – 100.0 %
    pressure = Column(Float, nullable=True)             # bar
    flow_rate = Column(Float, nullable=True)            # L/min
    temperature = Column(Float, nullable=True)          # °C
    stress = Column(Float, nullable=True)               # MPa

    def __repr__(self) -> str:
        return f"<Telemetry id={self.id} device={self.device} rpm={self.pump_rpm}>"
