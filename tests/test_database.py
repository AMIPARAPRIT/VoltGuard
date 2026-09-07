"""
Tests for database initialization and connectivity.
"""

import os
from pathlib import Path

from backend.database.database import init_db, check_db_health, get_engine
from backend.core.config import PROJECT_ROOT

def test_database_initialization():
    """Verify that tables are created successfully."""
    # This will use the default SQLite DB or the one defined in config.yaml
    # In a real environment, we'd use a separate test DB, but for Phase 1 
    # verification, this is sufficient.
    init_db()
    
    # Ensure health check passes
    assert check_db_health() is True
    
    # Verify file was created if using SQLite
    engine = get_engine()
    if engine.url.drivername == "sqlite":
        db_path = str(engine.url).replace("sqlite:///", "")
        if db_path != ":memory:":
            path = Path(db_path)
            # If path is relative in config, it resolves relative to cwd
            # If it's absolute, it resolves absolutely
            assert path.exists() or (PROJECT_ROOT / path).exists()
