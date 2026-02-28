"""Tests for the issue lifecycle API endpoints.

Verifies accept, dismiss, and feedback operations on editorial issues
stored in the session store.
"""

import logging
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestAcceptIssue:
    """Tests for POST /api/v1/issues/{id}/accept."""

    def test_accept_issue(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/accept with valid session_id returns 200.

        Accepting an issue should update its status to 'accepted' and
        return a recalculated score.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        session_id = session_with_issues["session_id"]
        issue_id = session_with_issues["issue_id_1"]

        response = client.post(
            f"/api/v1/issues/{issue_id}/accept",
            json={"session_id": session_id},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "score" in data
        assert "total_issues" in data

    def test_accept_invalid_session(self, client: FlaskClient) -> None:
        """POST /api/v1/issues/{id}/accept with bad session_id returns 404.

        A non-existent session ID should result in a 'not found' error.
        """
        response = client.post(
            "/api/v1/issues/fake-issue-id/accept",
            json={"session_id": "non-existent-session-id"},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_accept_missing_session_id(self, client: FlaskClient) -> None:
        """POST /api/v1/issues/{id}/accept without session_id returns 400.

        The session_id field is required in the request body.
        """
        response = client.post(
            "/api/v1/issues/some-issue-id/accept",
            json={},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_accept_non_json_body(self, client: FlaskClient) -> None:
        """POST /api/v1/issues/{id}/accept with non-JSON body returns 400.

        The request body must be valid JSON.
        """
        response = client.post(
            "/api/v1/issues/some-issue-id/accept",
            data="not json",
            content_type="text/plain",
        )

        assert response.status_code == 400


class TestDismissIssue:
    """Tests for POST /api/v1/issues/{id}/dismiss."""

    def test_dismiss_issue(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/dismiss with valid session_id returns 200.

        Dismissing an issue should update its status to 'dismissed' and
        return a recalculated score.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        session_id = session_with_issues["session_id"]
        issue_id = session_with_issues["issue_id_2"]

        response = client.post(
            f"/api/v1/issues/{issue_id}/dismiss",
            json={"session_id": session_id},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "score" in data
        assert "total_issues" in data

    def test_dismiss_invalid_issue(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/dismiss with bad issue_id returns 404.

        A non-existent issue ID within a valid session should not be found.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        session_id = session_with_issues["session_id"]

        response = client.post(
            "/api/v1/issues/non-existent-issue/dismiss",
            json={"session_id": session_id},
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


class TestFeedback:
    """Tests for POST /api/v1/issues/{id}/feedback."""

    def test_feedback_positive(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback with thumbs_up=true returns 200.

        Positive feedback should be stored successfully.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        issue_id = session_with_issues["issue_id_1"]
        session_id = session_with_issues["session_id"]

        response = client.post(
            f"/api/v1/issues/{issue_id}/feedback",
            json={
                "session_id": session_id,
                "rule_type": "passive_voice",
                "thumbs_up": True,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data.get("status") == "ok"

    def test_feedback_negative(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback with thumbs_up=false returns 200.

        Negative feedback should be stored successfully.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        issue_id = session_with_issues["issue_id_2"]
        session_id = session_with_issues["session_id"]

        response = client.post(
            f"/api/v1/issues/{issue_id}/feedback",
            json={
                "session_id": session_id,
                "rule_type": "contraction_usage",
                "thumbs_up": False,
            },
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data.get("status") == "ok"

    def test_feedback_with_comment(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback with comment returns 200.

        Optional comment field should be accepted alongside the required fields.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        issue_id = session_with_issues["issue_id_1"]
        session_id = session_with_issues["session_id"]

        response = client.post(
            f"/api/v1/issues/{issue_id}/feedback",
            json={
                "session_id": session_id,
                "rule_type": "passive_voice",
                "thumbs_up": False,
                "comment": "This is acceptable in this context.",
            },
        )

        assert response.status_code == 200

    def test_feedback_missing_session_id(self, client: FlaskClient) -> None:
        """POST /api/v1/issues/{id}/feedback without session_id returns 400.

        The session_id field is required.
        """
        response = client.post(
            "/api/v1/issues/some-id/feedback",
            json={
                "rule_type": "passive_voice",
                "thumbs_up": True,
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_feedback_missing_rule_type(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback without rule_type returns 400.

        The rule_type field is required.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        response = client.post(
            "/api/v1/issues/some-id/feedback",
            json={
                "session_id": session_with_issues["session_id"],
                "thumbs_up": True,
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_feedback_missing_thumbs_up(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback without thumbs_up returns 400.

        The thumbs_up field is required and must be boolean.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        response = client.post(
            "/api/v1/issues/some-id/feedback",
            json={
                "session_id": session_with_issues["session_id"],
                "rule_type": "passive_voice",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_feedback_non_boolean_thumbs_up(
        self, client: FlaskClient, session_with_issues: dict[str, Any]
    ) -> None:
        """POST /api/v1/issues/{id}/feedback with non-bool thumbs_up returns 400.

        The thumbs_up field must be a boolean, not a string or integer.

        Args:
            client: The Flask test client.
            session_with_issues: Pre-populated session fixture.
        """
        response = client.post(
            "/api/v1/issues/some-id/feedback",
            json={
                "session_id": session_with_issues["session_id"],
                "rule_type": "passive_voice",
                "thumbs_up": "yes",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
