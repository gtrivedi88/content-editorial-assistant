"""Singleton service instances shared across the application.

Provides lazily-initialized extensions so that importing this module
does not trigger heavy setup (e.g., loading a SpaCy model) at import
time.  Call the init functions after the Flask app is created.
"""

import logging
from typing import Any, Optional

from flask_socketio import SocketIO

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Socket.IO instance — initialized with the app in create_app()
# ---------------------------------------------------------------------------
socketio: SocketIO = SocketIO()

# ---------------------------------------------------------------------------
# SpaCy NLP — lazily loaded to avoid startup cost during testing
# ---------------------------------------------------------------------------
_nlp_instance: Optional[Any] = None


def get_nlp() -> Any:
    """Return the shared SpaCy Language model, loading it on first call.

    Returns:
        The loaded SpaCy Language pipeline.

    Raises:
        OSError: If the configured SpaCy model is not installed.
    """
    global _nlp_instance  # noqa: PLW0603
    if _nlp_instance is None:
        import spacy  # noqa: F811 — deferred import to keep startup fast

        from app.config import Config

        model_name = Config.SPACY_MODEL
        logger.info("Loading SpaCy model: %s", model_name)
        _nlp_instance = spacy.load(model_name)
        logger.info("SpaCy model loaded successfully")
    return _nlp_instance


def set_nlp(nlp_override: Any) -> None:
    """Replace the SpaCy NLP instance (used in testing).

    Args:
        nlp_override: A mock or alternative SpaCy Language object.
    """
    global _nlp_instance  # noqa: PLW0603
    _nlp_instance = nlp_override
    logger.debug("SpaCy NLP instance overridden")
