"""Issue lifecycle routes — accept, dismiss, and provide feedback.

Handles POST endpoints for updating issue status (accept/dismiss)
and recording user feedback (thumbs up/down with optional comment).
"""

import logging
from typing import Tuple

from flask import Response, jsonify, request

from app.api.v1 import bp
from app.models.enums import IssueStatus

logger = logging.getLogger(__name__)


@bp.route("/issues/<issue_id>/accept", methods=["POST"])
def accept_issue(issue_id: str) -> Tuple[Response, int]:
    """Mark an issue as accepted by the user.

    Expects JSON body with ``session_id``. Updates the issue status
    to ACCEPTED and returns the recalculated score.

    Args:
        issue_id: Unique identifier of the issue to accept.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    return _update_issue_status(issue_id, IssueStatus.ACCEPTED)


@bp.route("/issues/<issue_id>/dismiss", methods=["POST"])
def dismiss_issue(issue_id: str) -> Tuple[Response, int]:
    """Mark an issue as dismissed by the user.

    Expects JSON body with ``session_id``. Updates the issue status
    to DISMISSED and returns the recalculated score.

    Args:
        issue_id: Unique identifier of the issue to dismiss.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    return _update_issue_status(issue_id, IssueStatus.DISMISSED)


@bp.route("/issues/<issue_id>/feedback", methods=["POST"])
def submit_feedback(issue_id: str) -> Tuple[Response, int]:
    """Record user feedback (thumbs up/down) for an issue.

    Expects JSON body with ``session_id``, ``rule_type``,
    ``thumbs_up`` (bool), and optional ``comment``.

    Args:
        issue_id: Unique identifier of the issue.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Field 'session_id' is required"}), 400

    rule_type = data.get("rule_type")
    if not rule_type:
        return jsonify({"error": "Field 'rule_type' is required"}), 400

    thumbs_up = data.get("thumbs_up")
    if not isinstance(thumbs_up, bool):
        return jsonify({"error": "Field 'thumbs_up' must be a boolean"}), 400

    comment = data.get("comment", "")

    return _store_feedback(session_id, issue_id, rule_type, thumbs_up, comment)


def _update_issue_status(
    issue_id: str, status: IssueStatus
) -> Tuple[Response, int]:
    """Update an issue's lifecycle status in the session store.

    Args:
        issue_id: Unique identifier of the issue.
        status: The new IssueStatus to apply.

    Returns:
        Tuple of (JSON response with updated score, HTTP status code).
    """
    from app.services.session.store import get_session_store

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Field 'session_id' is required"}), 400

    store = get_session_store()
    updated_score = store.update_issue_status(session_id, issue_id, status)

    if updated_score is None:
        return jsonify({"error": "Session or issue not found"}), 404

    return jsonify(updated_score.to_dict()), 200


def _store_feedback(
    session_id: str,
    issue_id: str,
    rule_type: str,
    thumbs_up: bool,
    comment: str,
) -> Tuple[Response, int]:
    """Persist user feedback for an issue.

    Args:
        session_id: The analysis session identifier.
        issue_id: Unique identifier of the issue.
        rule_type: Rule type identifier for the feedback.
        thumbs_up: True for positive feedback, False for negative.
        comment: Optional user comment.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    from app.services.feedback.store import get_feedback_store

    try:
        store = get_feedback_store()
        store.store_feedback(session_id, issue_id, rule_type, thumbs_up, comment)
        return jsonify({"status": "ok"}), 200
    except (RuntimeError, OSError) as exc:
        logger.error("Failed to store feedback: %s", exc, exc_info=True)
        return jsonify({"error": "Failed to store feedback"}), 500
