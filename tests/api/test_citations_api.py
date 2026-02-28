"""Tests for the citation API endpoint.

Verifies GET /api/v1/citations/<rule_type> behaviour for known rules,
unknown rules, and response structure validation.
"""

import logging
from unittest.mock import patch

from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestCitationsKnownRule:
    """Tests for citation retrieval of known rule types."""

    def test_known_rule_returns_citation_data(self, client: FlaskClient) -> None:
        """GET /api/v1/citations/<rule_type> with known rule returns 200.

        When the registry has citation and excerpt data for a rule,
        the endpoint should return a combined response with citation,
        excerpt, and guide fields.
        """
        mock_citation = {
            "guide_name": "IBM Style Guide",
            "topic": "Articles",
            "pages": [42],
            "verified": True,
            "citation_text": "Use articles consistently in technical writing.",
        }
        mock_excerpt = {
            "excerpt": "Articles (a, an, the) should be used consistently...",
        }

        with patch(
            "style_guides.registry.get_citation",
            return_value=mock_citation,
        ), patch(
            "style_guides.registry.get_excerpt",
            return_value=mock_excerpt,
        ):
            response = client.get("/api/v1/citations/articles")

        assert response.status_code == 200
        data = response.get_json()
        assert "citation" in data
        assert "excerpt" in data
        assert "guide" in data

    def test_response_has_expected_field_values(self, client: FlaskClient) -> None:
        """GET /api/v1/citations/<rule_type> response fields match registry data.

        The combined response should map citation_text to 'citation',
        excerpt to 'excerpt', and guide_name to 'guide'.
        """
        mock_citation = {
            "guide_name": "Red Hat Supplementary Style Guide",
            "topic": "Inclusive Language",
            "pages": [15, 16],
            "verified": True,
            "citation_text": "Use inclusive language in all documentation.",
        }
        mock_excerpt = {
            "excerpt": "Avoid terms that reinforce stereotypes or biases...",
        }

        with patch(
            "style_guides.registry.get_citation",
            return_value=mock_citation,
        ), patch(
            "style_guides.registry.get_excerpt",
            return_value=mock_excerpt,
        ):
            response = client.get("/api/v1/citations/inclusive_language")

        assert response.status_code == 200
        data = response.get_json()
        assert data["citation"] == "Use inclusive language in all documentation."
        assert data["excerpt"] == "Avoid terms that reinforce stereotypes or biases..."
        assert data["guide"] == "Red Hat Supplementary Style Guide"


class TestCitationsUnknownRule:
    """Tests for citation retrieval of unknown rule types."""

    def test_unknown_rule_returns_404(self, client: FlaskClient) -> None:
        """GET /api/v1/citations/<rule_type> with unknown rule returns 404.

        When the registry has no citation or excerpt data for the
        requested rule type, the endpoint should return a 404 error.
        """
        with patch(
            "style_guides.registry.get_citation",
            return_value={},
        ), patch(
            "style_guides.registry.get_excerpt",
            return_value={},
        ):
            response = client.get("/api/v1/citations/nonexistent_rule")

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_citation_only_no_excerpt(self, client: FlaskClient) -> None:
        """GET /api/v1/citations/<rule_type> with citation but no excerpt returns 200.

        When the registry has citation data but no excerpt, the
        endpoint should still return 200 with an empty excerpt field.
        """
        mock_citation = {
            "guide_name": "IBM Style Guide",
            "topic": "Verbs",
            "pages": [100],
            "verified": True,
            "citation_text": "Use active voice in technical writing.",
        }

        with patch(
            "style_guides.registry.get_citation",
            return_value=mock_citation,
        ), patch(
            "style_guides.registry.get_excerpt",
            return_value={},
        ):
            response = client.get("/api/v1/citations/verbs")

        assert response.status_code == 200
        data = response.get_json()
        assert data["citation"] == "Use active voice in technical writing."
        assert data["excerpt"] == ""
        assert data["guide"] == "IBM Style Guide"
