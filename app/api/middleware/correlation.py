"""Request correlation ID middleware.

Reads or generates a unique ``X-Request-ID`` for every HTTP request
and makes it available via ``flask.g.request_id``.  The ID is echoed
back in the response headers for client-side tracing.
"""

import logging
import uuid

from flask import Flask, g, has_request_context, request


class RequestIdFilter(logging.Filter):
    """Inject request_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add *request_id* attribute to the log record.

        Args:
            record: The log record to augment.

        Returns:
            Always ``True`` so the record is never suppressed.
        """
        if has_request_context():
            record.request_id = getattr(g, "request_id", "-")  # type: ignore[attr-defined]
        else:
            record.request_id = "bg-task"
        return True


def init_correlation(app: Flask) -> None:
    """Register before/after request hooks for correlation IDs.

    Args:
        app: The Flask application to attach hooks to.
    """

    @app.before_request
    def _set_request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    @app.after_request
    def _add_request_id_header(response):  # type: ignore[no-untyped-def]
        """Echo the correlation ID back in the response headers."""
        response.headers["X-Request-ID"] = getattr(g, "request_id", "-")
        return response

    # Add filter to root logger so all log messages include request_id
    logging.root.addFilter(RequestIdFilter())
