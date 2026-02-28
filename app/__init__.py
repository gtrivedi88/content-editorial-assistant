"""Content Editorial Assistant — Flask application factory.

Usage::

    from app import create_app
    app = create_app()

The factory pattern keeps the module importable without side-effects,
which is required for testing, WSGI servers (gunicorn), and the Flask
CLI.
"""

import logging
import os
from typing import Optional

from flask import Flask
from flask_cors import CORS

from app.api import register_blueprints
from app.api.middleware.error_handlers import register_error_handlers
from app.config import Config
from app.extensions import socketio

logger = logging.getLogger(__name__)


def create_app(config_override: Optional[dict] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_override: Optional dictionary of config values that
            override ``Config`` class attributes.  Useful in tests.

    Returns:
        A fully configured Flask application instance.
    """
    _configure_logging()

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    )

    _apply_config(app, config_override)

    _init_cors(app)
    _init_rate_limiter(app)

    from app.api.middleware.correlation import init_correlation
    init_correlation(app)

    register_error_handlers(app)
    register_blueprints(app)
    _init_socketio(app)
    _register_events()

    Config.log_summary()
    logger.info("Application factory complete")

    return app


def _configure_logging() -> None:
    """Set up the root logger with a consistent format.

    When the ``LOG_FORMAT`` environment variable is set to ``json``,
    log output uses structured JSON via *python-json-logger*.  Otherwise
    the default human-readable text format is used.
    """
    log_format = os.environ.get("LOG_FORMAT", "text")

    if log_format == "json":
        from pythonjsonlogger.json import JsonFormatter

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
        ))
        logging.root.handlers.clear()
        logging.root.addHandler(handler)
        logging.root.setLevel(logging.INFO)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def _apply_config(app: Flask, overrides: Optional[dict]) -> None:
    """Load Config class attributes into the Flask app config.

    Args:
        app: The Flask application.
        overrides: Optional dict of values to layer on top.
    """
    app.config.from_object(Config)

    if overrides:
        app.config.update(overrides)
        logger.info("Applied %d config overrides", len(overrides))


def _init_cors(app: Flask) -> None:
    """Initialize CORS with the configured origins.

    Args:
        app: The Flask application.
    """
    origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, origins=origins)
    logger.info("CORS initialized with origins=%s", origins)


def _init_rate_limiter(app: Flask) -> None:
    """Initialize rate limiting middleware if enabled.

    Args:
        app: The Flask application.
    """
    from app.api.middleware.rate_limiter import init_rate_limiter
    init_rate_limiter(app)


def _init_socketio(app: Flask) -> None:
    """Attach Socket.IO to the Flask application.

    Args:
        app: The Flask application.
    """
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    socketio.init_app(app, cors_allowed_origins=cors_origins)
    logger.info("Socket.IO initialized")


def _register_events() -> None:
    """Import and register Socket.IO event handlers.

    The ``app.events`` module registers handlers via decorators
    on the shared ``socketio`` instance at import time. The
    ``register_events()`` call logs confirmation.
    """
    from app.events import register_events
    register_events()
