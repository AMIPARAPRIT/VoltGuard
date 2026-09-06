"""
Device — SQLAlchemy model for OT/ICS asset registry.

Auto-populated by the pipeline service whenever a new device_id
is seen in an incoming event. Tracks connection state and last
known telemetry snapshot.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime

from backend.database.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    device_type = Column(String, nullable=True, default="PLC")  # PLC, PUMP, VALVE, SENSOR, RTU
    ip_address = Column(String, nullable=True)
    protocol = Column(String, nullable=True)
    connection_status = Column(String, nullable=False, default="ONLINE")  # ONLINE, OFFLINE, STALE
    last_seen = Column(DateTime, nullable=True)

    # Latest telemetry snapshot (denormalised for fast read)
    last_pump_rpm = Column(Float, nullable=True)
    last_valve_position = Column(Float, nullable=True)
    last_pressure = Column(Float, nullable=True)
    last_flow_rate = Column(Float, nullable=True)
    last_temperature = Column(Float, nullable=True)
    last_stress = Column(Float, nullable=True)
    last_risk_score = Column(Float, nullable=True)
    last_safety_state = Column(String, nullable=True)
    last_decision = Column(String, nullable=True)

    def __repr__(self) -> str:
        return f"<Device device_id={self.device_id} status={self.connection_status}>"
