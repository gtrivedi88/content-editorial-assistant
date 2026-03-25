"""Health check route — reports service status.

Handles GET /api/v1/health which returns the overall health of the
application including SpaCy model status, LLM availability, loaded
rules count, and uptime.

LLM availability is cached with a TTL to avoid expensive TLS
round-trips to LlamaStack on every Kubernetes probe cycle.
"""

import logging
import threading
import time
from typing import Tuple

from flask import Response, jsonify

from app.api.v1 import bp

logger = logging.getLogger(__name__)

_start_time: float = time.monotonic()

# Cached LLM availability — prevents TLS + models.list() on every probe
_LLM_CACHE_TTL: float = 30.0
_llm_cache_lock = threading.Lock()
_llm_cached_result: bool = False
_llm_cache_timestamp: float = 0.0


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

    Returns a cached result when the cache is fresh (within
    ``_LLM_CACHE_TTL`` seconds).  This prevents each Kubernetes
    liveness/readiness probe from triggering a full TLS handshake
    and ``models.list()`` call to LlamaStack.

    Returns:
        True if the LLM client reports availability.
    """
    global _llm_cached_result, _llm_cache_timestamp  # noqa: PLW0603

    now = time.monotonic()
    with _llm_cache_lock:
        if now - _llm_cache_timestamp < _LLM_CACHE_TTL:
            return _llm_cached_result

    # Cache miss — perform the real check outside the lock
    try:
        from app.llm.client import LLMClient
        client = LLMClient()
        result = client.is_available()
    except (ImportError, RuntimeError, OSError):
        result = False

    with _llm_cache_lock:
        _llm_cached_result = result
        _llm_cache_timestamp = time.monotonic()

    return result


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
