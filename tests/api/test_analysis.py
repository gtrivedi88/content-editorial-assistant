"""Tests for the content analysis API endpoint.

Verifies POST /api/v1/analyze behaviour for valid inputs, validation
errors, content type handling, and response structure.
"""

import logging
from unittest.mock import patch

import pytest
from flask.testing import FlaskClient

from app.models.schemas import (
    AnalyzeResponse,
    ReportResponse,
    ScoreResponse,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: build a mock AnalyzeResponse for patching the orchestrator
# ---------------------------------------------------------------------------


def _build_mock_response(session_id: str = "test-session-123") -> AnalyzeResponse:
    """Build a minimal AnalyzeResponse for mocking the analysis pipeline.

    Args:
        session_id: The session ID to assign.

    Returns:
        A fully populated AnalyzeResponse instance.
    """
    return AnalyzeResponse(
        session_id=session_id,
        issues=[],
        score=ScoreResponse(
            score=95,
            color="#3e8635",
            label="Excellent",
            total_issues=0,
            category_counts={},
            compliance={},
        ),
        report=ReportResponse(
            word_count=50,
            sentence_count=3,
            paragraph_count=1,
            avg_words_per_sentence=16.67,
            avg_syllables_per_word=1.5,
        ),
        partial=False,
    )


class TestAnalyzeValidText:
    """Tests for successful text analysis requests."""

    def test_analyze_valid_text(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze with valid text returns 200 with expected keys.

        Verifies that the response contains issues, score, and report
        keys, and that the HTTP status code is 200.
        """
        with patch(
            "app.services.analysis.orchestrator.analyze",
            return_value=_build_mock_response(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "The server was restarted by the administrator."},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "issues" in data
        assert "score" in data
        assert "report" in data


class TestAnalyzeValidation:
    """Tests for input validation on the analysis endpoint."""

    def test_analyze_empty_text(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze with empty text returns 400.

        An empty string should be rejected before analysis begins.
        """
        response = client.post(
            "/api/v1/analyze",
            json={"text": ""},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_analyze_missing_text(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze without text field returns 400.

        A JSON body that omits the required 'text' field is invalid.
        """
        response = client.post(
            "/api/v1/analyze",
            json={"content_type": "concept"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_analyze_text_too_long(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze with >50000 chars returns 422.

        The validator raises UnprocessableEntity when the text exceeds
        the configured MAX_TEXT_LENGTH (50000 characters).
        """
        long_text = "a " * 25001  # 50002 characters
        response = client.post(
            "/api/v1/analyze",
            json={"text": long_text},
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "error" in data

    def test_analyze_non_json_body(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze with non-JSON body returns 400.

        A form-encoded or plain text body should be rejected.
        """
        response = client.post(
            "/api/v1/analyze",
            data="not json",
            content_type="text/plain",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestAnalyzeContentTypes:
    """Tests for content_type parameter handling."""

    @pytest.mark.parametrize("content_type", ["concept", "procedure", "reference", "assembly"])
    def test_analyze_content_types(self, client: FlaskClient, content_type: str) -> None:
        """POST /api/v1/analyze with each valid content_type returns 200.

        All four modular documentation types should be accepted without
        validation errors.

        Args:
            client: The Flask test client.
            content_type: The content type to test.
        """
        with patch(
            "app.services.analysis.orchestrator.analyze",
            return_value=_build_mock_response(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "This is a test document.", "content_type": content_type},
            )

        assert response.status_code == 200

    def test_analyze_invalid_content_type(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze with invalid content_type returns 400.

        An unrecognized content_type should be rejected with an error
        listing the valid options.
        """
        response = client.post(
            "/api/v1/analyze",
            json={"text": "This is a test.", "content_type": "invalid_type"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data


class TestAnalyzeResponseStructure:
    """Tests for the structure and content of analysis responses."""

    def test_analyze_returns_session_id(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze response includes session_id.

        Every analysis response must include a session_id for subsequent
        issue lifecycle operations (accept, dismiss, feedback).
        """
        with patch(
            "app.services.analysis.orchestrator.analyze",
            return_value=_build_mock_response(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "The server was restarted by the administrator."},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "session_id" in data
        assert isinstance(data["session_id"], str)
        assert len(data["session_id"]) > 0

    def test_analyze_returns_partial_flag(self, client: FlaskClient) -> None:
        """POST /api/v1/analyze response includes partial field.

        The partial flag indicates whether LLM analysis results will
        follow asynchronously via Socket.IO.
        """
        with patch(
            "app.services.analysis.orchestrator.analyze",
            return_value=_build_mock_response(),
        ):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "The server was restarted by the administrator."},
            )

        assert response.status_code == 200
        data = response.get_json()
        assert "partial" in data
        assert isinstance(data["partial"], bool)
