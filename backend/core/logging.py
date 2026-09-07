"""
VoltGuard — Structured Logging

Provides a consistent logging setup across the entire application.
All log output follows the format:

    [LEVEL] YYYY-MM-DD HH:MM:SS — message

Usage:
    from backend.core.logging import get_logger
    logger = get_logger(__name__)
    logger.info("Database initialized")
"""

import logging
import sys


LOG_FORMAT = "[%(levelname)s] %(asctime)s — %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root_logger() -> None:
    """Configure the root logger once. Idempotent."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("voltguard")
    root.setLevel(logging.DEBUG)

    # Console handler — INFO and above go to stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    # Debug handler — DEBUG goes to stderr (keeps demo output clean)
    debug_handler = logging.StreamHandler(sys.stderr)
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(lambda r: r.levelno < logging.INFO)
    debug_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root.addHandler(console)
    root.addHandler(debug_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger under the 'voltguard' namespace.

    Args:
        name: Module name, typically __name__.

    Returns:
        A configured logging.Logger instance.
    """
    _configure_root_logger()
    return logging.getLogger(f"voltguard.{name}")
