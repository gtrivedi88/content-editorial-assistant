"""Tests for the suggestion API endpoint.

Verifies POST /api/v1/suggestions behaviour for validation errors,
session lookup failures, and successful suggestion retrieval from
both deterministic and LLM paths.
"""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestSuggestionsValidation:
    """Tests for input validation on the suggestions endpoint."""

    def test_missing_session_id_returns_400(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions without session_id returns 400.

        The session_id field is required in the request body.
        Omitting it should return a clear validation error.
        """
        response = client.post(
            "/api/v1/suggestions",
            json={"issue_id": "some-issue-id"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "session_id" in data["error"]

    def test_missing_issue_id_returns_400(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions without issue_id returns 400.

        The issue_id field is required in the request body.
        Omitting it should return a clear validation error.
        """
        response = client.post(
            "/api/v1/suggestions",
            json={"session_id": "some-session-id"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "issue_id" in data["error"]

    def test_non_json_body_returns_400(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions with non-JSON body returns 400.

        A plain-text or form-encoded body should be rejected with an
        error indicating JSON is required.
        """
        response = client.post(
            "/api/v1/suggestions",
            data="not json",
            content_type="text/plain",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestSuggestionsLookup:
    """Tests for suggestion retrieval via the engine."""

    def test_session_not_found_returns_404(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions with unknown session_id returns 404.

        When the suggestion engine raises KeyError or ValueError for
        an unknown session, the endpoint should return 404.
        """
        with patch(
            "app.services.suggestions.engine.get_suggestion",
            side_effect=KeyError("Session not found"),
        ):
            response = client.post(
                "/api/v1/suggestions",
                json={
                    "session_id": "non-existent-session",
                    "issue_id": "some-issue-id",
                },
            )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_valid_deterministic_suggestion(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions returns deterministic suggestion data.

        When the suggestion engine returns a successful result with
        rewritten_text, explanation, and confidence, the endpoint
        should return 200 with that data.
        """
        mock_result = {
            "rewritten_text": "use",
            "explanation": "Use simple words instead of complex alternatives.",
            "confidence": 1.0,
        }

        with patch(
            "app.services.suggestions.engine.get_suggestion",
            return_value=mock_result,
        ):
            response = client.post(
                "/api/v1/suggestions",
                json={
                    "session_id": "test-session-123",
                    "issue_id": "test-issue-456",
                },
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["rewritten_text"] == "use"
        assert data["explanation"] == "Use simple words instead of complex alternatives."
        assert abs(data["confidence"] - 1.0) < 1e-9

    def test_llm_unavailable_returns_fallback(self, client: FlaskClient) -> None:
        """POST /api/v1/suggestions returns error dict when LLM is unavailable.

        When the suggestion engine returns a dict with an 'error' key
        (e.g., LLM not available), the endpoint should return 200 with
        that error payload and optional deterministic suggestions.
        """
        mock_result = {
            "error": "LLM not available",
            "suggestions": ["should not"],
        }

        with patch(
            "app.services.suggestions.engine.get_suggestion",
            return_value=mock_result,
        ):
            response = client.post(
                "/api/v1/suggestions",
                json={
                    "session_id": "test-session-123",
                    "issue_id": "test-issue-789",
                },
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "LLM not available"
        assert "suggestions" in data
