"""
VoltGuard Simulation Service

Manages controlled background simulation stream execution for testing & demonstration.
"""

from __future__ import annotations

import asyncio
import random
import sys
from pathlib import Path
from typing import Dict, Any, Optional

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.core.logging import get_logger
from backend.services.pipeline_service import pipeline_service
from parser.traffic_generator.generator import IndustrialTrafficGenerator

logger = get_logger("simulation.service")


class SimulationService:
    """
    Manages background simulation streams.
    """

    def __init__(self):
        self._is_running: bool = False
        self._task: Optional[asyncio.Task] = None
        self._mode: str = "mixed"
        self._rate_fps: float = 1.0
        self._processed_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._is_running,
            "mode": self._mode,
            "rate_fps": self._rate_fps,
            "processed_count": self._processed_count,
        }

    async def start_stream(self, mode: str = "mixed", rate_fps: float = 1.0) -> Dict[str, Any]:
        if self._is_running:
            return {"status": "ALREADY_RUNNING", **self.get_status()}

        self._is_running = True
        self._mode = mode
        self._rate_fps = max(0.1, min(10.0, rate_fps))
        self._processed_count = 0

        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._simulation_loop())

        logger.info(f"[SIMULATION] Stream started mode={mode} rate_fps={rate_fps}")
        return {"status": "STARTED", **self.get_status()}

    async def stop_stream(self) -> Dict[str, Any]:
        if not self._is_running:
            return {"status": "NOT_RUNNING", **self.get_status()}

        self._is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info(f"[SIMULATION] Stream stopped after {self._processed_count} packets")
        return {"status": "STOPPED", **self.get_status()}

    async def _simulation_loop(self):
        delay_sec = 1.0 / self._rate_fps
        while self._is_running:
            try:
                packets = IndustrialTrafficGenerator.generate(mode=self._mode, count=1)
                if packets:
                    pkt = packets[0]
                    # Run through central pipeline
                    pipeline_service.process_pipeline(
                        command_input=pkt["hex_payload"],
                        protocol=pkt.get("protocol", "modbus"),
                        src_ip=pkt.get("source_ip", "192.168.1.20"),
                        dest_ip=pkt.get("destination_ip", "192.168.1.50")
                    )
                    self._processed_count += 1
                await asyncio.sleep(delay_sec)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[SIMULATION] Error in simulation stream loop: {e}")
                await asyncio.sleep(1.0)


# Singleton instance
simulation_service = SimulationService()
