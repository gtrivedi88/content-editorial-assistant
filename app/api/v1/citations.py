"""Citation route — retrieves style guide citations and excerpts.

Handles GET /api/v1/citations/<rule_type> which looks up the
citation text and excerpt from the style guide registry for a
given rule type identifier.
"""

import logging
from typing import Tuple

from flask import Response, jsonify

from app.api.v1 import bp

logger = logging.getLogger(__name__)


@bp.route("/citations/<rule_type>", methods=["GET"])
def get_citation(rule_type: str) -> Tuple[Response, int]:
    """Retrieve citation and excerpt data for a rule type.

    Looks up the citation and excerpt from the style guide registry
    and returns a combined response.

    Args:
        rule_type: Rule identifier (e.g., ``"articles"``, ``"inclusive_language"``).

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    from style_guides.registry import get_citation as registry_get_citation
    from style_guides.registry import get_excerpt

    citation_data = registry_get_citation(rule_type)
    excerpt_data = get_excerpt(rule_type)

    if not citation_data and not excerpt_data:
        return jsonify({"error": f"No citation found for rule type: {rule_type}"}), 404

    return jsonify(_build_response(citation_data, excerpt_data)), 200


def _build_response(
    citation_data: dict, excerpt_data: dict
) -> dict:
    """Build the combined citation response from registry lookups.

    Args:
        citation_data: Citation dict from ``get_citation()``.
        excerpt_data: Excerpt dict from ``get_excerpt()``.

    Returns:
        Combined response dict with citation, excerpt, and guide fields.
    """
    citation_text = citation_data.get("citation_text", "") if citation_data else ""
    guide_name = citation_data.get("guide_name", "") if citation_data else ""
    excerpt_text = excerpt_data.get("excerpt", "") if isinstance(excerpt_data, dict) else ""

    return {
        "citation": citation_text,
        "excerpt": excerpt_text,
        "guide": guide_name,
    }
