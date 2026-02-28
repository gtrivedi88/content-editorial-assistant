"""Tests for the global HTTP error handlers.

Verifies that error handlers registered in
``app.api.middleware.error_handlers`` return consistent JSON responses
for 400, 404, 413, and 500 status codes, and that browser asset
requests are suppressed from 404 logs.
"""

import logging
from unittest.mock import patch

from flask import Flask
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestErrorHandler400:
    """Tests for 400 Bad Request error responses."""

    def test_400_returns_json(self, client: FlaskClient) -> None:
        """400 Bad Request returns JSON with 'error' and 'code' fields.

        Sending a non-JSON body to an endpoint that requires JSON
        should trigger a 400 error handler returning structured JSON.
        """
        response = client.post(
            "/api/v1/analyze",
            data="not json",
            content_type="text/plain",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data is not None
        assert "error" in data


class TestErrorHandler404:
    """Tests for 404 Not Found error responses."""

    def test_404_returns_json(self, client: FlaskClient) -> None:
        """404 Not Found returns JSON with 'error' and 'code' fields.

        Requesting a non-existent route should trigger the 404
        error handler and return a JSON response body.
        """
        response = client.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert "error" in data
        assert data["code"] == 404

    def test_404_browser_asset_suppressed_in_logs(
        self, client: FlaskClient, caplog: "pytest.LogCaptureFixture"
    ) -> None:
        """404 for /favicon.ico does not log 'Resource not found'.

        Browser-generated asset requests listed in _BROWSER_ASSET_PATHS
        should return 404 JSON but NOT produce an info log entry, to
        avoid polluting production logs.
        """
        with caplog.at_level(logging.INFO, logger="app.api.middleware.error_handlers"):
            response = client.get("/favicon.ico")

        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert "error" in data

        # Verify no 'Resource not found' log for the browser asset path
        resource_not_found_logs = [
            record for record in caplog.records
            if "Resource not found" in record.message
            and record.name == "app.api.middleware.error_handlers"
        ]
        assert len(resource_not_found_logs) == 0

    def test_404_non_asset_path_is_logged(
        self, client: FlaskClient, caplog: "pytest.LogCaptureFixture"
    ) -> None:
        """404 for a non-asset path logs 'Resource not found'.

        Regular 404 errors (not browser assets) should produce a log
        entry so operators can investigate missing endpoints.
        """
        with caplog.at_level(logging.INFO, logger="app.api.middleware.error_handlers"):
            response = client.get("/api/v1/nonexistent-endpoint")

        assert response.status_code == 404

        resource_not_found_logs = [
            record for record in caplog.records
            if "Resource not found" in record.message
            and record.name == "app.api.middleware.error_handlers"
        ]
        assert len(resource_not_found_logs) >= 1


class TestErrorHandler413:
    """Tests for 413 Content Too Large error responses."""

    def test_413_returns_json(self, app: Flask) -> None:
        """413 Content Too Large returns JSON with 'error' and 'code' fields.

        Uploading a file that exceeds MAX_CONTENT_LENGTH should
        trigger the 413 error handler returning structured JSON.
        """
        # Set a very small max content length to trigger 413
        app.config["MAX_CONTENT_LENGTH"] = 10

        with app.test_client() as small_client:
            response = small_client.post(
                "/api/v1/analyze",
                json={"text": "A" * 1000},
            )

        # Flask may return 413 for oversized requests
        assert response.status_code == 413
        data = response.get_json()
        assert data is not None
        assert "error" in data
        assert data["code"] == 413


class TestErrorHandler500:
    """Tests for 500 Internal Server Error responses."""

    def test_500_returns_json(self, app: Flask) -> None:
        """500 Internal Server Error returns JSON with 'error' and 'code' fields.

        When an unhandled exception reaches the global 500 handler,
        it should return structured JSON with 'error' and 'code' fields.
        Temporarily disables PROPAGATE_EXCEPTIONS so Flask invokes the
        registered error handler instead of re-raising.
        """
        app.config["PROPAGATE_EXCEPTIONS"] = False

        with app.test_client() as test_client:
            with patch(
                "app.api.v1.analysis._run_analysis",
                side_effect=TypeError("Unexpected failure"),
            ):
                response = test_client.post(
                    "/api/v1/analyze",
                    json={"text": "The server was restarted by the administrator."},
                )

        assert response.status_code == 500
        data = response.get_json()
        assert data is not None
        assert "error" in data
        assert data["code"] == 500
