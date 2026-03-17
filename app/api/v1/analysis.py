"""Analysis route — accepts text for editorial review.

Handles POST /api/v1/analyze which validates the incoming text,
delegates to the analysis orchestrator, and returns a JSON response
containing issues, score, and report.
"""

import logging
from typing import Tuple

from flask import Response, jsonify, request

from app.api.v1 import bp
from app.api.middleware.request_validator import sanitize_input, validate_text_length
from app.config import Config
from app.models.enums import ContentType

logger = logging.getLogger(__name__)


@bp.route("/analyze", methods=["POST"])
def analyze() -> Tuple[Response, int]:
    """Analyze submitted text for editorial issues.

    Expects a JSON body with ``text`` (required), ``content_type``
    (optional, defaults to ``"concept"``), and ``format_hint`` (optional).

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    text = data.get("text")
    if not text or not isinstance(text, str):
        return jsonify({"error": "Field 'text' is required and must be a non-empty string"}), 400

    text = sanitize_input(text)
    if not text:
        return jsonify({"error": "Text is empty after sanitization"}), 400

    try:
        validate_text_length(text, Config.MAX_TEXT_LENGTH)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    content_type = _resolve_content_type(data.get("content_type", "concept"))
    if content_type is None:
        valid_values = [ct.value for ct in ContentType]
        return jsonify({"error": f"Invalid content_type. Must be one of: {valid_values}"}), 400

    session_id = data.get("session_id") or None
    html_content = data.get("html_content") or None
    user_selected = bool(data.get("user_selected", False))
    logger.debug(
        "/analyze received session_id=%r from frontend (raw=%r), html_content=%s, user_selected=%s",
        session_id, data.get("session_id"),
        f"{len(html_content)} chars" if html_content else "None",
        user_selected,
    )
    return _run_analysis(
        text, content_type.value,
        session_id=session_id,
        html_content=html_content,
        user_selected=user_selected,
    )


def _resolve_content_type(raw_value: str) -> ContentType | None:
    """Convert a raw string to a ContentType enum member.

    Args:
        raw_value: The string value from the request payload.

    Returns:
        The matching ContentType, or None if invalid.
    """
    try:
        return ContentType(raw_value)
    except ValueError:
        return None


def _run_analysis(
    text: str,
    content_type: str,
    session_id: str | None = None,
    html_content: str | None = None,
    user_selected: bool = False,
) -> Tuple[Response, int]:
    """Execute the analysis pipeline and return the result.

    Detects format from pasted text and parses into blocks so the
    orchestrator can build lite_markers for LLM analysis.  When
    *html_content* is provided (from a browser paste), the HTML parser
    is used directly for structure-aware block detection.

    Args:
        text: Sanitized and validated input text.
        content_type: Validated content type string value.
        session_id: Optional session ID from the client for session continuity.
        html_content: Optional sanitized HTML from the browser's contenteditable.
        user_selected: Whether the user explicitly selected the content type.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    from app.services.analysis.orchestrator import analyze as run_analysis
    from app.services.parsing import detect_and_parse
    from app.services.parsing.format_detector import detect_format
    from app.models.enums import FileType

    try:
        if html_content:
            # Browser paste — use HTML parser for structure-aware parsing
            from app.services.parsing.html_parser import HtmlParser
            file_type = FileType.HTML
            html_parser = HtmlParser()
            parse_result = html_parser.parse(html_content)
            blocks = parse_result.blocks if parse_result.blocks else []
            logger.debug(
                "HTML-aware paste: parsed %d blocks from %d chars of HTML",
                len(blocks), len(html_content),
            )
        else:
            # Standard flow — format detection + auto-parsing
            file_type = detect_format(text, None)
            parse_result = detect_and_parse(text, None)
            blocks = parse_result.blocks if parse_result.blocks else []

        response = run_analysis(
            text, content_type,
            file_type=file_type.value,
            session_id=session_id,
            blocks=blocks,
            user_selected=user_selected,
        )
        logger.debug(
            "/analyze responding with session_id=%s, %d issues, partial=%s",
            response.session_id, len(response.issues), response.partial,
        )
        return jsonify(response.to_dict()), 200
    except (RuntimeError, OSError) as exc:
        logger.error("Analysis failed: %s", exc, exc_info=True)
        return jsonify({"error": "Analysis failed due to an internal error"}), 500
