"""
VoltGuard API — Traffic Parsing, Physics & Decision Processing Routes

Provides REST endpoints to process raw industrial network payloads (Modbus/TCP, DNP3)
through the C++ Protocol Parser, Physics Engine, and Rust Decision Engine.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.services.parser_service import parser_service
from backend.services.decision_service import decision_service
from parser.traffic_generator.generator import IndustrialTrafficGenerator

router = APIRouter(prefix="/traffic", tags=["Traffic Processing"])


class ParseTrafficRequest(BaseModel):
    hex_payload: str = Field(..., description="Raw hexadecimal packet payload (e.g. '00010000000601069C41C350')", json_schema_extra={"example": "00010000000601069C41C350"})
    protocol: str = Field("modbus", description="Protocol type: 'modbus' or 'dnp3'", json_schema_extra={"example": "modbus"})
    source_ip: str = Field("192.168.1.20", description="Source IP address", json_schema_extra={"example": "192.168.1.20"})
    destination_ip: str = Field("192.168.1.50", description="Destination IP address", json_schema_extra={"example": "192.168.1.50"})


class ProcessTrafficRequest(ParseTrafficRequest):
    current_state: Optional[Dict[str, float]] = Field(
        None,
        description="Optional current physical state overrides (pump_rpm, valve_position, current_pressure, current_temperature)",
        json_schema_extra={"example": {"pump_rpm": 1200.0, "valve_position": 50.0, "current_pressure": 2.0, "current_temperature": 45.0}}
    )


class GenerateTrafficRequest(BaseModel):
    mode: str = Field("normal", description="Mode: 'normal', 'suspicious', 'attack', 'mixed'", json_schema_extra={"example": "attack"})
    count: int = Field(5, description="Number of packets to generate", ge=1, le=100, json_schema_extra={"example": 5})


@router.post("/parse", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def parse_traffic(request: ParseTrafficRequest):
    """
    Parse a raw hexadecimal network packet payload into a NormalizedCommand.
    """
    try:
        norm_cmd = parser_service.parse_payload(
            hex_payload=request.hex_payload,
            protocol=request.protocol,
            src_ip=request.source_ip,
            dest_ip=request.destination_ip
        )
        return norm_cmd
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse payload: {str(e)}"
        )


@router.post("/process", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def process_traffic(request: ProcessTrafficRequest):
    """
    Parse raw packet hex AND run Physics Engine + Rust Decision Engine safety evaluation.
    """
    try:
        result = decision_service.process_packet_and_decide(
            hex_payload=request.hex_payload,
            protocol=request.protocol,
            src_ip=request.source_ip,
            dest_ip=request.destination_ip,
            current_state=request.current_state
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating packet decision: {str(e)}"
        )


@router.post("/generate", response_model=List[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def generate_traffic(request: GenerateTrafficRequest):
    """
    Generate synthetic industrial OT traffic payloads (Normal, Suspicious, Attack, Mixed).
    """
    try:
        items = IndustrialTrafficGenerator.generate(mode=request.mode, count=request.count)
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate traffic: {str(e)}"
        )
