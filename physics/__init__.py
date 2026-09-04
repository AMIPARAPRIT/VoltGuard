"""
VoltGuard — Physics Engine (Phase 2)

Public interface:

    from physics import simulate, simulate_timeseries
    from physics.models import PhysicsCommand, PhysicsResult, SafetyState

The engine is fully independent of FastAPI.
It can be called as a plain Python module from any context.

Pipeline model (simplified):
    Pump → Valve → Pipeline → Pressure Sensor
"""

from physics.simulator import simulate, simulate_timeseries
from physics.models import PhysicsCommand, PhysicsResult, SafetyState

__all__ = [
    "simulate",
    "simulate_timeseries",
    "PhysicsCommand",
    "PhysicsResult",
    "SafetyState",
]
