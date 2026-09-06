"""
VoltGuard — Database Engine & Session Management

Uses SQLAlchemy with SQLite. The database file is created under
the project's data/ directory.

Usage:
    from backend.database.database import get_db, init_db
"""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator

from backend.core.config import get_settings, PROJECT_ROOT
from backend.core.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

# --- Engine setup -----------------------------------------------------------

_engine = None
_SessionLocal = None


def _get_db_path() -> str:
    """Resolve the SQLite file path from config, relative to project root."""
    raw_url = get_settings().database.url
    # sqlite:///data/voltguard.db  →  data/voltguard.db
    if raw_url.startswith("sqlite:///"):
        relative = raw_url.replace("sqlite:///", "")
        db_path = PROJECT_ROOT / relative
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"
    return raw_url


def get_engine():
    """Return the singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_url = _get_db_path()
        _engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},  # Required for SQLite
            echo=False,
        )
    return _engine


def get_session_factory():
    """Return the singleton session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def SessionLocal() -> Session:
    """Return a new database session instance."""
    factory = get_session_factory()
    return factory()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session.

    Automatically closes the session when the request ends.
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Create all tables defined by SQLAlchemy models.

    Must be called after all model modules have been imported so that
    Base.metadata is fully populated.
    """
    # Import models to register them with Base.metadata
    import backend.models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized — all tables created")


def check_db_health() -> bool:
    """Return True if the database is reachable."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
