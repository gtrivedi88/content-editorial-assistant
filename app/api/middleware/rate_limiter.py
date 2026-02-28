"""Rate limiting middleware for API endpoints.

Disabled by default for local development. Enable via
RATE_LIMIT_ENABLED=true environment variable.
"""

import logging
from typing import Optional

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import Config

logger = logging.getLogger(__name__)

_limiter: Optional[Limiter] = None


def init_rate_limiter(app: Flask) -> None:
    """Initialize rate limiter if enabled via config.

    Args:
        app: The Flask application instance.
    """
    global _limiter  # noqa: PLW0603
    if not Config.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting disabled (RATE_LIMIT_ENABLED=False)")
        return

    _limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[Config.RATE_LIMIT_DEFAULT],
        storage_uri="memory://",
    )
    logger.info(
        "Rate limiting enabled: default=%s, analyze=%s",
        Config.RATE_LIMIT_DEFAULT, Config.RATE_LIMIT_ANALYZE,
    )


def get_limiter() -> Optional[Limiter]:
    """Return the limiter instance, or None if disabled."""
    return _limiter
