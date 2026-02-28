"""Content Editorial Assistant -- Application entry point.

Supports two modes:
  - Direct execution: ``python main.py`` (development with Socket.IO)
  - WSGI import: ``gunicorn main:application`` (production via LightRail)

Gevent monkey-patching MUST happen before any other imports.
"""

from gevent import monkey
monkey.patch_all(signal=False)

import logging
import os
import signal
import sys
from types import FrameType
from typing import Optional

from app import create_app 
from app.extensions import socketio 

logger = logging.getLogger(__name__)

# Module-level application instance for WSGI servers (gunicorn)
application = None


def _configure_logging() -> None:
    """Set up root logging from the LOG_LEVEL environment variable."""
    level_name = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _signal_handler(signum: int, frame: Optional[FrameType]) -> None:
    """Handle termination signals for graceful shutdown.

    Args:
        signum: Signal number received.
        frame: Current stack frame (unused).
    """
    sig_name = signal.Signals(signum).name
    logger.info("Received %s -- shutting down", sig_name)
    sys.exit(0)


def initialize_application():
    """Create and configure the Flask application.

    Eagerly loads SpaCy model and rule registry so the server is
    fully ready before accepting requests (matching legacy behavior).

    Returns:
        The configured Flask application instance.
    """
    global application  # noqa: PLW0603
    _configure_logging()
    application = create_app()
    _warmup()

    logger.info("Application initialized successfully")
    return application


def _warmup() -> None:
    """Pre-load SpaCy model and rules registry at startup."""
    from app.extensions import get_nlp
    from rules import get_registry

    logger.info("Warming up: loading SpaCy model...")
    get_nlp()
    logger.info("Warming up: discovering rules...")
    registry = get_registry()
    logger.info(
        "Warmup complete: %d rules loaded", len(registry.rules),
    )


def main() -> None:
    """Run the development server with Socket.IO support."""
    signal.signal(signal.SIGTERM, _signal_handler)
    # Do NOT register a custom SIGINT handler — gevent's monkey-patched
    # signal module conflicts with socketio.run()'s own event loop,
    # causing spurious SIGINT on startup.  Let gevent handle Ctrl+C
    # naturally via KeyboardInterrupt.

    app = initialize_application()

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")

    logger.info("Starting CEA server on %s:%d (debug=%s)", host, port, debug)
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True,
        )
    except KeyboardInterrupt:
        logger.info("Received SIGINT -- shutting down")


if __name__ == "__main__":
    main()
else:
    # WSGI mode -- gunicorn imports this module and uses `application`
    initialize_application()
