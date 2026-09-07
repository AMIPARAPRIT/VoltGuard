"""
pytest conftest for physics tests.

Clears the get_settings() lru_cache before each test so that any
config changes (e.g., via environment variable or file edits) are picked up
without restarting the process.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from backend.core.config import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear the cached Settings before every test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
