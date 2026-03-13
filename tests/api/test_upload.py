"""Tests for the file upload API endpoint.

Verifies POST /api/v1/upload behaviour for valid uploads, missing
files, unsupported formats, and oversized files. Upload is extract-only:
it returns content and detected format but does not run analysis.
"""

import io
import logging
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


class TestUploadValidFile:
    """Tests for successful file upload requests."""

    def test_upload_txt_file(self, client: FlaskClient) -> None:
        """POST /api/v1/upload with a .txt file returns 200.

        A valid plaintext file should be accepted, parsed, and the
        extracted content returned without running analysis.
        """
        content = b"The server was restarted by the administrator."

        with patch(
            "app.services.parsing.detect_and_parse"
        ) as mock_parse:
            parse_result = MagicMock()
            parse_result.plain_text = content.decode("utf-8")
            mock_parse.return_value = parse_result

            response = client.post(
                "/api/v1/upload",
                data={
                    "file": (io.BytesIO(content), "test_document.txt"),
                },
                content_type="multipart/form-data",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["content"] == content.decode("utf-8")
        assert "detected_format" in data
        # Extract-only: no analysis results in the response
        assert "issues" not in data
        assert "score" not in data

    def test_upload_md_file(self, client: FlaskClient) -> None:
        """POST /api/v1/upload with a .md file returns 200.

        Markdown files are a supported upload format. The raw markup
        content is returned for editor display.
        """
        content = b"# Heading\n\nThis is a markdown document."

        with patch(
            "app.services.parsing.detect_and_parse"
        ) as mock_parse:
            parse_result = MagicMock()
            parse_result.plain_text = content.decode("utf-8")
            mock_parse.return_value = parse_result

            response = client.post(
                "/api/v1/upload",
                data={
                    "file": (io.BytesIO(content), "readme.md"),
                },
                content_type="multipart/form-data",
            )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["content"] == content.decode("utf-8")


class TestUploadValidation:
    """Tests for upload input validation."""

    def test_upload_no_file(self, client: FlaskClient) -> None:
        """POST /api/v1/upload without file returns 400.

        The request must include a 'file' field in the multipart form.
        """
        response = client.post(
            "/api/v1/upload",
            data={},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_upload_unsupported_format(self, client: FlaskClient) -> None:
        """POST /api/v1/upload with .exe returns 415 Unsupported Media Type.

        Executable files are not in the ALLOWED_EXTENSIONS set and should
        be rejected by the file type validator.
        """
        content = b"MZ\x90\x00"  # Fake EXE header

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(content), "malware.exe"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 415

    def test_upload_oversized_file(self, client: FlaskClient, app: Flask) -> None:
        """POST /api/v1/upload with file >MAX_CONTENT_LENGTH returns 413.

        Files exceeding the configured maximum upload size are rejected
        by the file size validator.

        Args:
            client: The Flask test client.
            app: The Flask test application for config access.
        """
        max_size = app.config.get("MAX_CONTENT_LENGTH", 10485760)
        # Create content slightly over the limit
        oversized_content = b"x" * (max_size + 1)

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(oversized_content), "large_doc.txt"),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 413

    def test_upload_empty_filename(self, client: FlaskClient) -> None:
        """POST /api/v1/upload with empty filename returns 400.

        A file field that has no filename set should be rejected.
        """
        content = b"Some content"

        response = client.post(
            "/api/v1/upload",
            data={
                "file": (io.BytesIO(content), ""),
            },
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
