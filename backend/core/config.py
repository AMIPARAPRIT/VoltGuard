"""
VoltGuard — Centralized Configuration

Loads settings from config/config.yaml and exposes them as typed Pydantic models.
All safety limits, database URLs, and server params live here — never scattered.
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
    """Physical safety thresholds for the industrial process."""
    max_pressure: float = 150.0       # bar
    max_rpm: int = 3600               # RPM
    max_temperature: float = 350.0    # °C
    max_flow: float = 500.0           # L/min
    max_stress: float = 250.0         # MPa


class DatabaseConfig(BaseModel):
    """Database connection settings."""
    url: str = "sqlite:///data/voltguard.db"


class ServerConfig(BaseModel):
    """Uvicorn server settings."""
    host: str = "0.0.0.0"
    port: int = 8000


class VoltGuardInfo(BaseModel):
    """Top-level application metadata."""
    version: str = "0.1.0"
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
