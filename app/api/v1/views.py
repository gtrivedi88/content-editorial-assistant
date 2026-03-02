"""View routes — serves the frontend HTML templates.

Handles GET / and GET /review (review editor) and GET /help
(help & support page).  These are registered on the Flask app
directly (not the API blueprint) since they serve HTML pages rather
than JSON API responses.  Documentation is served separately via
Antora (built by CI/CD and deployed to GitLab Pages).
"""

import logging

from flask import render_template

logger = logging.getLogger(__name__)


def register_views(app: object) -> None:
    """Register HTML view routes on the Flask application.

    Adds routes for the landing page, review editor, and help page
    outside the API blueprint since they serve rendered HTML templates.

    Args:
        app: The Flask application instance.
    """

    @app.route("/")
    def index() -> str:
        """Redirect root to the review page.

        Returns:
            Rendered HTML template string.
        """
        return render_template("review.html")

    @app.route("/review")
    def analyze_page() -> str:
        """Render the content review editor page.

        Returns:
            Rendered HTML template string.
        """
        return render_template("review.html")

    @app.route("/help")
    def help_support() -> str:
        """Render the help and support page.

        Returns:
            Rendered HTML template string.
        """
        return render_template("help_support.html")
