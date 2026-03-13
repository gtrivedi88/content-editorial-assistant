"""Report routes — retrieves reports and generates PDF exports.

Handles GET /api/v1/report/<session_id> for JSON report data and
POST /api/v1/report/pdf for downloadable PDF generation.
"""

import logging
from typing import Tuple

from flask import Response, jsonify, request

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


@bp.route("/report/pdf", methods=["POST"])
def generate_pdf() -> Tuple[Response, int]:
    """Generate a PDF report for an analysis session.

    Expects JSON body with ``session_id``.

    Returns:
        Tuple of (PDF bytes response, HTTP status code).
    """
    from app.services.reporting.pdf_generator import generate_pdf_report
    from app.services.session.store import get_session_store

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    store = get_session_store()
    session = store.get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found"}), 404

    pdf_bytes = generate_pdf_report(
        report_data=session.report.to_dict(),
        score_data=session.score.to_dict(),
        issues_data=[issue.to_dict() for issue in session.issues],
    )

    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=cea_report.pdf",
        },
    ), 200
