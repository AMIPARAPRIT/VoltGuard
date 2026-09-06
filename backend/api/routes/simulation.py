"""
VoltGuard API — Simulation Control Routes

Provides REST endpoints to send simulation commands through the central pipeline
and control automated synthetic OT traffic streaming.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services.pipeline_service import pipeline_service
from backend.services.simulation_service import simulation_service
from backend.models.simulation import SimulationHistory
import json

router = APIRouter(prefix="/simulation", tags=["Simulation Control"])


class CommandSimulationRequest(BaseModel):
    hex_payload: Optional[str] = Field(None, description="Optional raw hexadecimal packet payload", json_schema_extra={"example": "00010000000601069C41C350"})
    protocol: str = Field("modbus", description="Protocol type: 'modbus' or 'dnp3'", json_schema_extra={"example": "modbus"})
    source_ip: str = Field("192.168.1.20", description="Source IP address", json_schema_extra={"example": "192.168.1.20"})
    destination_ip: str = Field("192.168.1.50", description="Destination IP address", json_schema_extra={"example": "192.168.1.50"})
    
    # Command parameter shortcuts
    command: Optional[str] = Field(None, description="Normalized command (e.g. 'SET_RPM', 'SET_VALVE')", json_schema_extra={"example": "SET_RPM"})
    value: Optional[float] = Field(None, description="Target command value (e.g. 1500.0, 50000.0)", json_schema_extra={"example": 50000.0})
    device_id: Optional[str] = Field(None, description="Target OT device ID", json_schema_extra={"example": "Pump-01"})
    scenario: Optional[str] = Field(None, description="Scenario type e.g., NORMAL, WARNING, CRITICAL, ATTACK, CUSTOM")
    
    current_state: Optional[Dict[str, float]] = Field(None, description="Optional current state overrides", json_schema_extra={"example": {"current_pressure": 2.0}})


class StartStreamRequest(BaseModel):
    mode: str = Field("mixed", description="Simulation mode: 'normal', 'suspicious', 'attack', 'mixed'", json_schema_extra={"example": "mixed"})
    rate_fps: float = Field(1.0, description="Traffic streaming rate in FPS (0.1 - 10.0)", ge=0.1, le=10.0, json_schema_extra={"example": 1.0})


@router.post("/command", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def process_simulation_command(
    request: CommandSimulationRequest,
    db: Session = Depends(get_db)
):
    """
    Process a single simulation command or hex payload through the central VoltGuard pipeline:
    Parser -> Physics Engine -> Rust Decision Engine -> DB Persistence -> WS Broadcast.
    """
    try:
        if request.hex_payload:
            cmd_input = request.hex_payload
        elif request.command and request.value is not None:
            cmd_input = {
                "timestamp": None,
                "source_ip": request.source_ip,
                "destination_ip": request.destination_ip,
                "device_id": request.device_id or ("Pump-01" if request.command == "SET_RPM" else "PLC-01"),
                "protocol": request.protocol,
                "function_code": 6,
                "register": 40001 if request.command == "SET_RPM" else 40002,
                "command": request.command,
                "value": request.value,
                "unit": "RPM" if request.command == "SET_RPM" else "%",
                "success": True
            }
        else:
            # Fallback default normal command
            cmd_input = "00010000000601069C4105DC"  # FC 06 -> SET_RPM = 1500

        result = pipeline_service.process_pipeline(
            command_input=cmd_input,
            protocol=request.protocol,
            src_ip=request.source_ip,
            dest_ip=request.destination_ip,
            current_state=request.current_state,
            db_session=db
        )
        
        # Save to history
        sim_history = SimulationHistory(
            scenario=request.scenario or "CUSTOM",
            device_id=request.device_id or "Pump-01",
            protocol=request.protocol,
            command=request.command or "RAW",
            command_value=request.value or 0.0,
            risk_score=result.get("decision_result", {}).get("risk_score"),
            safety_state=result.get("decision_result", {}).get("safety_state"),
            decision=result.get("decision_result", {}).get("decision"),
            event_id=result.get("event_id"),
            alert_id=result.get("alert_id"),
            raw_result=json.dumps(result)
        )
        db.add(sim_history)
        db.commit()
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process simulation command: {str(e)}"
        )


@router.post("/start", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def start_simulation_stream(request: StartStreamRequest):
    """
    Start automated background traffic stream through the central pipeline.
    """
    try:
        res = await simulation_service.start_stream(mode=request.mode, rate_fps=request.rate_fps)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start simulation stream: {str(e)}"
        )


@router.post("/stop", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def stop_simulation_stream():
    """
    Stop active background simulation traffic stream.
    """
    try:
        res = await simulation_service.stop_stream()
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop simulation stream: {str(e)}"
        )


@router.get("/status", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_simulation_status():
    """
    Get current background simulation status.
    """
    return simulation_service.get_status()

@router.get("/history", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_simulation_history(db: Session = Depends(get_db)):
    from sqlalchemy import desc
    hist = db.query(SimulationHistory).order_by(desc(SimulationHistory.timestamp)).limit(50).all()
    return {
        "items": [
            {
                "id": h.id,
                "timestamp": h.timestamp.isoformat(),
                "scenario": h.scenario,
                "device_id": h.device_id,
                "protocol": h.protocol,
                "command": h.command,
                "command_value": h.command_value,
                "risk_score": h.risk_score,
                "safety_state": h.safety_state,
                "decision": h.decision,
                "event_id": h.event_id,
                "alert_id": h.alert_id
            } for h in hist
        ]
    }

@router.get("/history/{sim_id}", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_simulation_detail(sim_id: int, db: Session = Depends(get_db)):
    h = db.query(SimulationHistory).filter(SimulationHistory.id == sim_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return {
        "id": h.id,
        "timestamp": h.timestamp.isoformat(),
        "scenario": h.scenario,
        "device_id": h.device_id,
        "protocol": h.protocol,
        "command": h.command,
        "command_value": h.command_value,
        "risk_score": h.risk_score,
        "safety_state": h.safety_state,
        "decision": h.decision,
        "event_id": h.event_id,
        "alert_id": h.alert_id,
        "raw_result": json.loads(h.raw_result) if h.raw_result else None
    }
