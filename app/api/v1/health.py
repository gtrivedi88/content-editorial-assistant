"""Health check route — reports service status.

Handles GET /api/v1/health which returns the overall health of the
application including SpaCy model status, LLM availability, loaded
rules count, and uptime.
"""

import logging
import time
from typing import Tuple

from flask import Response, jsonify

from app.api.v1 import bp

logger = logging.getLogger(__name__)

_start_time: float = time.monotonic()


@bp.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """Return the health status of the application.

    Checks SpaCy model loading, LLM availability, and rules
    registry, and returns a summary JSON response.

    Returns:
        Tuple of (JSON response with health data, HTTP 200).
    """
    spacy_loaded = _check_spacy()
    llm_available = _check_llm()
    rules_count = _get_rules_count()
    uptime = round(time.monotonic() - _start_time, 2)

    return jsonify({
        "status": "ok",
        "spacy_loaded": spacy_loaded,
        "llm_available": llm_available,
        "rules_count": rules_count,
        "uptime_seconds": uptime,
    }), 200


def _check_spacy() -> bool:
    """Check whether the SpaCy model is loaded and functional.

    Returns:
        True if the SpaCy model is available, False otherwise.
    """
    try:
        from app.extensions import get_nlp
        nlp = get_nlp()
        return nlp is not None
    except (ImportError, OSError):
        return False


def _check_llm() -> bool:
    """Check whether the LLM integration is available.

    Returns:
        True if the LLM client reports availability.
    """
    try:
        from app.llm.client import LLMClient
        client = LLMClient()
        return client.is_available()
    except (ImportError, RuntimeError, OSError):
        return False


def _get_rules_count() -> int:
    """Get the total number of registered rules.

    Returns:
        Count of discovered rules, or 0 if the registry is unavailable.
    """
    try:
        from rules import get_registry
        registry = get_registry()
        return len(registry.rules)
    except (ImportError, ValueError, OSError):
        return 0
