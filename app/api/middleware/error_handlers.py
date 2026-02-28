"""Global HTTP error handlers returning consistent JSON responses.

Registered on the Flask app during factory initialization so that every
error — whether raised explicitly or by Flask/Werkzeug — produces a
machine-readable JSON body.
"""

import logging
from typing import TYPE_CHECKING, Tuple

from flask import jsonify
from werkzeug.exceptions import HTTPException

if TYPE_CHECKING:
    from flask import Flask, Response

logger = logging.getLogger(__name__)


def _error_response(message: str, code: int) -> Tuple["Response", int]:
    """Build a standard JSON error response.

    Args:
        message: Human-readable error description.
        code: HTTP status code.

    Returns:
        A tuple of (JSON response, status code).
    """
    return jsonify({"error": message, "code": code}), code


def handle_400(error: HTTPException) -> Tuple["Response", int]:
    """Handle 400 Bad Request errors.

    Args:
        error: The Werkzeug HTTPException.

    Returns:
        JSON error response with status 400.
    """
    logger.warning("Bad request: %s", error.description)
    return _error_response(str(error.description), 400)


# Browser asset paths that should not pollute logs
_BROWSER_ASSET_PATHS = frozenset([
    '/favicon.ico', '/manifest.json', '/robots.txt',
    '/apple-touch-icon.png', '/apple-touch-icon-precomposed.png',
    '/browserconfig.xml', '/site.webmanifest',
])


def handle_404(error: HTTPException) -> Tuple["Response", int]:
    """Handle 404 Not Found errors.

    Args:
        error: The Werkzeug HTTPException.

    Returns:
        JSON error response with status 404.
    """
    from flask import request
    if request.path not in _BROWSER_ASSET_PATHS:
        logger.info("Resource not found: %s", request.path)
    return _error_response("Resource not found", 404)


def handle_413(error: HTTPException) -> Tuple["Response", int]:
    """Handle 413 Content Too Large errors.

    Args:
        error: The Werkzeug HTTPException.

    Returns:
        JSON error response with status 413.
    """
    logger.warning("Request entity too large: %s", error.description)
    return _error_response("Request entity too large", 413)


def handle_422(error: HTTPException) -> Tuple["Response", int]:
    """Handle 422 Unprocessable Entity errors.

    Args:
        error: The Werkzeug HTTPException.

    Returns:
        JSON error response with status 422.
    """
    logger.warning("Unprocessable entity: %s", error.description)
    return _error_response(str(error.description), 422)


def handle_500(error: HTTPException) -> Tuple["Response", int]:
    """Handle 500 Internal Server Error.

    Args:
        error: The Werkzeug HTTPException or underlying exception.

    Returns:
        JSON error response with status 500.
    """
    logger.error("Internal server error: %s", error, exc_info=True)
    return _error_response("Internal server error", 500)


def register_error_handlers(app: "Flask") -> None:
    """Attach all error handlers to the Flask application.

    Args:
        app: The Flask application instance.
    """
    app.register_error_handler(400, handle_400)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(413, handle_413)
    app.register_error_handler(422, handle_422)
    app.register_error_handler(500, handle_500)
    logger.info("Registered global error handlers")
