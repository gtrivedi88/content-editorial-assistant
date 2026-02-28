"""View routes — serves the frontend HTML templates.

Handles GET / and GET /review which render the main editor UI.
These are registered on the Flask app directly (not the API blueprint)
since they serve HTML pages rather than JSON API responses.
"""

import logging

from flask import current_app, render_template

logger = logging.getLogger(__name__)


def register_views(app: object) -> None:
    """Register HTML view routes on the Flask application.

    Adds routes for the landing page and review editor outside
    the API blueprint since they serve rendered HTML templates.

    Args:
        app: The Flask application instance.
    """

    @app.route("/")
    def index() -> str:
        """Render the application landing page.

        Returns:
            Rendered HTML template string.
        """
        return _render_page()

    @app.route("/review")
    def analyze_page() -> str:
        """Render the content review editor page.

        Returns:
            Rendered HTML template string.
        """
        return _render_page()

    @app.route("/help")
    def help_support() -> str:
        """Render the help and support page.

        Returns:
            Rendered HTML template string.
        """
        return _render_page()


def _render_page() -> str:
    """Render the review page template with a fallback.

    Attempts to render ``review.html`` first, then falls back to
    ``home.html``, and finally returns a minimal HTML page.

    Returns:
        Rendered HTML string.
    """
    try:
        return render_template("review.html")
    except (FileNotFoundError, OSError):
        logger.debug("review.html not found, trying home.html")

    try:
        return render_template("home.html")
    except (FileNotFoundError, OSError):
        logger.debug("home.html not found, returning minimal page")

    return _minimal_page()


def _minimal_page() -> str:
    """Return a minimal HTML page when no templates are available.

    Returns:
        A basic HTML string indicating the service is running.
    """
    return (
        "<!DOCTYPE html><html><head><title>CEA</title></head>"
        "<body><h1>Content Editorial Assistant</h1>"
        "<p>Service is running. Templates not yet deployed.</p>"
        "</body></html>"
    )
