"""Socket.IO event handlers for the Content Editorial Assistant.

Registers connect, disconnect, and start_analysis event handlers
with the shared Socket.IO instance.  The ``start_analysis`` handler
launches the analysis pipeline in a background task to avoid
blocking the WebSocket connection.

Event constants are defined here for reference by other modules:
    - ``EVENT_ANALYSIS_PROGRESS`` — emitted during each pipeline phase
    - ``EVENT_DETERMINISTIC_COMPLETE`` — emitted after Phase 1
    - ``EVENT_LLM_GRANULAR_COMPLETE`` — emitted after Phase 2
    - ``EVENT_LLM_GLOBAL_COMPLETE`` — emitted after Phase 3
    - ``EVENT_ANALYSIS_COMPLETE`` — emitted when all phases finish
    - ``EVENT_LLM_SKIPPED`` — emitted when an LLM phase is skipped
"""

import logging
from typing import Any

from app.extensions import socketio
from app.models.enums import ContentType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event name constants
# ---------------------------------------------------------------------------
EVENT_ANALYSIS_PROGRESS = "analysis_progress"
EVENT_DETERMINISTIC_COMPLETE = "deterministic_complete"
EVENT_LLM_GRANULAR_COMPLETE = "llm_granular_complete"
EVENT_LLM_GLOBAL_COMPLETE = "llm_global_complete"
EVENT_ANALYSIS_COMPLETE = "analysis_complete"
EVENT_LLM_SKIPPED = "llm_skipped"


def register_events() -> None:
    """Register all Socket.IO event handlers.

    This function exists so that ``app/__init__.py`` can call it
    during application setup.  The actual handlers are registered
    via decorators on the shared ``socketio`` instance.
    """
    logger.info("Socket.IO event handlers registered")


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------


@socketio.on("connect")
def handle_connect(auth: dict[str, Any] | None = None) -> None:
    """Handle a new WebSocket client connection.

    Args:
        auth: Optional authentication data sent by the client.

    Logs the connection with the assigned session ID (``request.sid``).
    """
    from flask import request

    sid = getattr(request, "sid", "unknown")
    logger.info("WebSocket client connected: sid=%s", sid)


@socketio.on("join_session")
def handle_join_session(data: dict[str, Any]) -> None:
    """Join the client to a session room for targeted event delivery.

    The frontend calls this after receiving a session_id from the HTTP
    analysis response. All subsequent analysis events (progress,
    analysis_complete, etc.) are emitted to this room.

    Args:
        data: Dictionary with ``session_id`` (required).
    """
    from flask import request

    from flask_socketio import join_room

    sid = getattr(request, "sid", "unknown")
    session_id = data.get("session_id") if isinstance(data, dict) else None

    if not session_id:
        logger.warning("join_session called without session_id from sid=%s", sid)
        return

    join_room(session_id)
    logger.info("Client %s joined session room %s", sid, session_id)


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Handle a WebSocket client disconnection.

    Logs the disconnection and performs any necessary cleanup
    of the session association.
    """
    from flask import request

    sid = getattr(request, "sid", "unknown")
    logger.info("WebSocket client disconnected: sid=%s", sid)
    _cleanup_session(sid)


@socketio.on("start_analysis")
def handle_start_analysis(data: dict[str, Any]) -> None:
    """Handle a client request to start content analysis.

    Validates the incoming data, resolves the content type, and
    launches the analysis pipeline in a background task.

    Args:
        data: Dictionary with ``text`` (required) and
            ``content_type`` (optional, defaults to ``"concept"``).
    """
    from flask import request

    sid = getattr(request, "sid", "unknown")

    if not isinstance(data, dict):
        socketio.emit("error", {"error": "Invalid data format"}, to=sid)
        return

    text = data.get("text", "")
    if not text or not isinstance(text, str):
        socketio.emit("error", {"error": "Field 'text' is required"}, to=sid)
        return

    content_type = _resolve_content_type(data.get("content_type", "concept"))

    logger.info(
        "Starting analysis via WebSocket: sid=%s, content_type=%s, text_length=%d",
        sid, content_type, len(text),
    )

    socketio.start_background_task(
        _run_analysis_background, text, content_type, sid,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_content_type(raw_value: str) -> str:
    """Convert a raw string to a validated content type value.

    Args:
        raw_value: The string value from the WebSocket payload.

    Returns:
        The validated content type string, defaulting to ``"concept"``.
    """
    try:
        return ContentType(raw_value).value
    except ValueError:
        return ContentType.CONCEPT.value


def _run_analysis_background(
    text: str, content_type: str, socket_sid: str
) -> None:
    """Execute the analysis pipeline in a background task.

    This function runs outside the request context in a separate
    thread managed by Socket.IO.

    Args:
        text: The text to analyze.
        content_type: Validated content type string.
        socket_sid: Socket.IO session ID for progress emission.
    """
    try:
        from app.services.analysis.orchestrator import analyze
        analyze(text, content_type, socket_sid=socket_sid)
    except (RuntimeError, OSError, ValueError) as exc:
        logger.error("Background analysis failed: %s", exc, exc_info=True)
        socketio.emit("error", {
            "error": "Analysis failed",
            "detail": str(exc),
        }, to=socket_sid)


def _cleanup_session(sid: str) -> None:
    """Clean up session data when a WebSocket client disconnects.

    Args:
        sid: The Socket.IO session ID of the disconnected client.
    """
    try:
        from app.services.session.store import get_session_store
        store = get_session_store()
        if hasattr(store, "remove_active_analysis"):
            store.remove_active_analysis(sid)
    except (ImportError, AttributeError, RuntimeError):
        pass
