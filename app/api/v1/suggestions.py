"""Suggestion route — requests LLM rewrite suggestions for flagged issues.

Handles POST /api/v1/suggestions which retrieves a rewrite suggestion
from the suggestion engine for a specific issue within a session.
"""

import logging
from typing import Tuple

from flask import Response, jsonify, request

from app.api.v1 import bp

logger = logging.getLogger(__name__)


@bp.route("/suggestions", methods=["POST"])
def get_suggestion() -> Tuple[Response, int]:
    """Request a rewrite suggestion for a specific issue.

    Expects a JSON body with ``session_id`` and ``issue_id``.
    Delegates to the suggestion engine and returns the result.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Field 'session_id' is required"}), 400

    issue_id = data.get("issue_id")
    if not issue_id:
        return jsonify({"error": "Field 'issue_id' is required"}), 400

    return _fetch_suggestion(session_id, issue_id)


def _fetch_suggestion(session_id: str, issue_id: str) -> Tuple[Response, int]:
    """Fetch a suggestion from the engine and return it.

    Args:
        session_id: The analysis session identifier.
        issue_id: The issue to generate a suggestion for.

    Returns:
        Tuple of (JSON response with suggestion data, HTTP status code).
    """
    from app.services.suggestions.engine import get_suggestion as engine_get_suggestion

    try:
        result = engine_get_suggestion(session_id, issue_id)

        if result is None:
            return jsonify({"error": "Session or issue not found"}), 404

        if isinstance(result, dict) and "error" in result:
            return jsonify(result), 200

        return jsonify(result), 200
    except (KeyError, ValueError) as exc:
        logger.warning("Suggestion lookup failed: %s", exc)
        return jsonify({"error": "Session or issue not found"}), 404
    except (RuntimeError, OSError) as exc:
        logger.error("Suggestion generation failed: %s", exc, exc_info=True)
        return jsonify({"error": "Failed to generate suggestion"}), 500
