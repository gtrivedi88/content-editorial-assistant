"""Report route — retrieves the statistical report for a session.

Handles GET /api/v1/report/<session_id> which looks up the
analysis session and returns the report data including word counts,
readability metrics, and compliance percentages.
"""

import logging
from typing import Tuple

from flask import Response, jsonify

from app.api.v1 import bp

logger = logging.getLogger(__name__)


@bp.route("/report/<session_id>", methods=["GET"])
def get_report(session_id: str) -> Tuple[Response, int]:
    """Retrieve the statistical report for an analysis session.

    Args:
        session_id: Unique identifier of the analysis session.

    Returns:
        Tuple of (JSON response with report data, HTTP status code).
    """
    from app.services.session.store import get_session_store

    store = get_session_store()
    session = store.get_session(session_id)

    if session is None:
        return jsonify({"error": "Session not found"}), 404

    return jsonify(session.report.to_dict()), 200
