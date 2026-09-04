"""
VoltGuard — Centralized Configuration

Loads settings from config/config.yaml and exposes them as typed Pydantic models.
All safety limits, database URLs, server params, and physics constants live here.
"""

import os
from pathlib import Path
from functools import lru_cache

import yaml
from pydantic import BaseModel


# Resolve project root (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class SafetyLimits(BaseModel):
    """Physical safety thresholds for the industrial process.

    Units: pressure=bar, rpm=RPM, temperature=°C, flow=L/min, stress=MPa
    """
    max_pressure: float = 80.0        # bar  (prototype scale)
    max_rpm: int = 3600               # RPM
    max_temperature: float = 120.0    # °C
    max_flow: float = 500.0           # L/min
    max_stress: float = 130.0         # MPa


class PhysicsParameters(BaseModel):
    """
    Physics engine model constants.

    These govern the simulation equations — NOT safety limits.
    Loaded from the [physics] block in config.yaml.
    All values have engineering-sensible defaults so tests run without a file.

    Assumptions (prototype):
    - Centrifugal pump: flow is linear with RPM and valve position.
    - Pressure rise quadratic in flow (simplified Bernoulli / head-loss model).
    - Temperature rises linearly with flow above an ambient baseline.
    - Pipeline hoop stress proportional to internal pressure.
    """
    reference_rpm: float = 3000.0           # RPM defining base_flow
    base_flow: float = 300.0                # L/min at ref RPM, full valve, 100% eff.
    default_pump_efficiency: float = 0.85   # fraction 0-1
    default_pipeline_resistance: float = 1.0
    pressure_gain_coefficient: float = 0.0016    # bar / (L/min)^2 (tuned for prototype zones)
    pressure_loss_coefficient: float = 0.0002    # bar / (L/min) / resistance
    thermal_gain_coefficient: float = 0.04       # °C / (L/min)
    stress_per_bar: float = 1.55                 # MPa / bar


class DatabaseConfig(BaseModel):
    """Database connection settings."""
    url: str = "sqlite:///data/voltguard.db"


class ServerConfig(BaseModel):
    """Uvicorn server settings."""
    host: str = "0.0.0.0"
    port: int = 8000


class VoltGuardInfo(BaseModel):
    """Top-level application metadata."""
    version: str = "0.2.0"
    service_name: str = "VoltGuard Backend"
    mode: str = "offline"


class Settings(BaseModel):
    """
    Root configuration container.

    All settings are loaded from config/config.yaml at startup.
    Defaults are provided so the app can start even without the YAML file.
    """
    voltguard: VoltGuardInfo = VoltGuardInfo()
    safety_limits: SafetyLimits = SafetyLimits()
    physics: PhysicsParameters = PhysicsParameters()
    database: DatabaseConfig = DatabaseConfig()
    server: ServerConfig = ServerConfig()


def _load_yaml() -> dict:
    """Load and return the raw YAML config dict."""
    config_path = os.environ.get("VOLTGUARD_CONFIG", str(CONFIG_PATH))
    path = Path(config_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


@lru_cache()
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.

    Cached after first call — restart the process to pick up config changes.
    """
    raw = _load_yaml()
    return Settings(**raw)

