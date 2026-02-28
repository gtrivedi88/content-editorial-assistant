"""API package — registers versioned blueprint groups with the Flask app."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)


def register_blueprints(app: "Flask") -> None:
    """Discover and register all API version blueprints and view routes.

    Currently registers:
        - /api/v1  — version 1 endpoints
        - /       — HTML view routes (landing page, review editor)

    Args:
        app: The Flask application instance.
    """
    from app.api.v1 import bp as v1_bp  # noqa: F811
    from app.api.v1.views import register_views

    app.register_blueprint(v1_bp, url_prefix="/api/v1")
    logger.info("Registered API v1 blueprint at /api/v1")

    register_views(app)
    logger.info("Registered HTML view routes")
