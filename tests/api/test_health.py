"""Tests for the health check API endpoint.

Verifies GET /api/v1/health returns correct status and expected fields,
including LLM availability caching behaviour.
"""

import logging
from unittest.mock import patch

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

    def test_llm_check_cached_on_repeated_calls(
        self, client: FlaskClient
    ) -> None:
        """LLM availability is cached — repeated probes skip TLS round-trip.

        The second health check within the TTL window should return the
        cached result without calling ``LLMClient.is_available()`` again.
        """
        import app.api.v1.health as health_mod

        # Reset cache so the first call is a real check
        health_mod._llm_cache_timestamp = 0.0

        with patch(
            "app.llm.client.LLMClient"
        ) as mock_cls:
            mock_cls.return_value.is_available.return_value = True

            resp1 = client.get("/api/v1/health")
            resp2 = client.get("/api/v1/health")

            assert resp1.status_code == 200
            assert resp2.status_code == 200
            # Only one real call — second was served from cache
            assert mock_cls.return_value.is_available.call_count == 1

    def test_llm_cache_expires_after_ttl(
        self, client: FlaskClient
    ) -> None:
        """LLM cache expires after TTL — next probe triggers a real check.

        Simulates cache expiry by backdating the timestamp, then
        verifies that a fresh ``is_available()`` call is made.
        """
        import app.api.v1.health as health_mod

        # Reset cache
        health_mod._llm_cache_timestamp = 0.0

        with patch(
            "app.llm.client.LLMClient"
        ) as mock_cls:
            mock_cls.return_value.is_available.return_value = True

            # First call — real check
            client.get("/api/v1/health")
            assert mock_cls.return_value.is_available.call_count == 1

            # Expire the cache by backdating timestamp
            health_mod._llm_cache_timestamp = 0.0

            # Second call — cache expired, real check again
            client.get("/api/v1/health")
            assert mock_cls.return_value.is_available.call_count == 2
