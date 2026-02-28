"""Tests for the health check API endpoint.

Verifies GET /api/v1/health returns correct status and expected fields.
"""

import logging

import pytest
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestHealthCheck:
    """Tests for GET /api/v1/health."""

    def test_health_returns_ok(self, client: FlaskClient) -> None:
        """GET /api/v1/health returns 200 with status 'ok'.

        The health endpoint should always return a 200 response with
        an 'ok' status when the application is running.
        """
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"

    def test_health_has_expected_fields(self, client: FlaskClient) -> None:
        """GET /api/v1/health response has status, spacy_loaded, llm_available, rules_count.

        The health response must include all monitoring-relevant fields
        so that external health checkers can assess service readiness.
        """
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.get_json()

        assert "status" in data
        assert "spacy_loaded" in data
        assert "llm_available" in data
        assert "rules_count" in data

    def test_health_field_types(self, client: FlaskClient) -> None:
        """GET /api/v1/health response fields have correct types.

        Ensures that the health response fields are properly typed
        for downstream monitoring integrations.
        """
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.get_json()

        assert isinstance(data["status"], str)
        assert isinstance(data["spacy_loaded"], bool)
        assert isinstance(data["llm_available"], bool)
        assert isinstance(data["rules_count"], int)

    def test_health_has_uptime(self, client: FlaskClient) -> None:
        """GET /api/v1/health response includes uptime_seconds.

        The uptime field reports how long the application has been running.
        """
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.get_json()

        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
