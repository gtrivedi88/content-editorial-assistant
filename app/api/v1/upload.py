"""Upload route — accepts file uploads for editorial review.

Handles POST /api/v1/upload which validates the uploaded file,
detects its format, parses it into blocks, extracts plain text,
and delegates to the analysis orchestrator.
"""

import logging
import os
import re
import unicodedata
from typing import Tuple

from flask import Response, jsonify, request

from app.api.v1 import bp
from app.api.middleware.request_validator import (
    validate_file_size,
    validate_file_type,
)
from app.config import Config
from app.models.enums import ContentType

logger = logging.getLogger(__name__)

# Extensions that require binary mode reading
_BINARY_EXTENSIONS = frozenset({".pdf", ".docx"})


@bp.route("/upload", methods=["POST"])
def upload() -> Tuple[Response, int]:
    """Upload a file for editorial analysis.

    Expects a multipart form upload with a ``file`` field. Validates
    file presence, extension, and size before parsing and analysis.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Include a 'file' field in the upload."}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"error": "Uploaded file has no filename"}), 400

    filename = uploaded.filename
    validate_file_type(filename)
    validate_file_size(uploaded, Config.MAX_CONTENT_LENGTH)

    content_type = _resolve_content_type(request.form.get("content_type", "concept"))

    return _parse_and_analyze(uploaded, filename, content_type)


def _resolve_content_type(raw_value: str) -> str:
    """Convert a raw string to a validated content type value.

    Args:
        raw_value: The string value from the form data.

    Returns:
        The validated content type string, defaulting to ``"concept"``.
    """
    try:
        return ContentType(raw_value).value
    except ValueError:
        return ContentType.CONCEPT.value


def _parse_and_analyze(
    uploaded: object, filename: str, content_type: str
) -> Tuple[Response, int]:
    """Parse the uploaded file and run analysis.

    Args:
        uploaded: The uploaded FileStorage object.
        filename: Original filename for format detection.
        content_type: Validated content type string value.

    Returns:
        Tuple of (JSON response, HTTP status code).
    """
    from app.services.analysis.orchestrator import analyze as run_analysis
    from app.services.parsing import detect_and_parse

    try:
        content = _read_file_content(uploaded, filename)
        parse_result = detect_and_parse(content, filename)
        plain_text = _extract_text(parse_result)

        if not plain_text.strip():
            return jsonify({"error": "No analyzable text found in the uploaded file"}), 422

        # Override content_type if the file declares one (e.g. AsciiDoc attribute)
        file_content_type = _extract_content_type_from_file(content)
        if file_content_type is not None:
            content_type = file_content_type

        file_type = _detect_file_type(filename)
        blocks = parse_result.blocks if hasattr(parse_result, "blocks") else []
        logger.debug(
            "file=%s file_type=%s blocks=%d plain_text_len=%d",
            filename, file_type, len(blocks), len(plain_text),
        )
        for i, b in enumerate(blocks[:20]):
            logger.debug(
                "block[%d]: type=%s skip=%s content=%.80r",
                i, b.block_type, b.should_skip_analysis,
                (b.content or "")[:80],
            )
        logger.debug("plain_text[:300]=%.300r", plain_text[:300])
        response = run_analysis(
            plain_text, content_type,
            file_type=file_type,
            blocks=blocks,
        )
        result = response.to_dict()

        # Include the file content for the editor and the detected format.
        # For binary formats (PDF, DOCX) return extracted plain text since
        # the raw content is a temp file path, not displayable text.
        ext = _get_extension(filename)
        result["content"] = plain_text if ext in _BINARY_EXTENSIONS else content
        result["detected_format"] = file_type or "auto"

        return jsonify(result), 200
    except (RuntimeError, OSError, ValueError) as exc:
        logger.error("Upload processing failed for '%s': %s", filename, exc, exc_info=True)
        return jsonify({"error": f"Failed to process file: {exc}"}), 500


def _read_file_content(uploaded: object, filename: str) -> str:
    """Read content from the uploaded file storage.

    Binary formats (PDF, DOCX) are saved to a temp path and the path
    string is returned for downstream parsers that handle binary I/O.

    Args:
        uploaded: The uploaded FileStorage object.
        filename: Original filename for extension detection.

    Returns:
        File content as a string, or a temp file path for binary formats.
    """
    ext = _get_extension(filename)
    if ext in _BINARY_EXTENSIONS:
        return _save_temp_binary(uploaded, filename)
    raw_bytes = uploaded.read()
    return unicodedata.normalize("NFC", raw_bytes.decode("utf-8", errors="replace"))


def _save_temp_binary(uploaded: object, filename: str) -> str:
    """Save a binary upload to a temporary file and return its path.

    Args:
        uploaded: The uploaded FileStorage object.
        filename: Original filename for the temp file suffix.

    Returns:
        Absolute path to the saved temporary file.
    """
    import tempfile
    ext = _get_extension(filename)
    fd, temp_path = tempfile.mkstemp(suffix=ext)
    try:
        os.close(fd)
        uploaded.save(temp_path)
        return temp_path
    except OSError:
        _cleanup_temp(temp_path)
        raise


def _cleanup_temp(path: str) -> None:
    """Remove a temporary file if it exists.

    Args:
        path: Path to the temporary file.
    """
    try:
        os.unlink(path)
    except OSError:
        pass


def _extract_text(parse_result: object) -> str:
    """Extract plain text from a ParseResult.

    Uses the ``plain_text`` attribute if available, otherwise
    concatenates text from non-skippable blocks.

    Args:
        parse_result: The ParseResult from the parser.

    Returns:
        Extracted plain text suitable for analysis.
    """
    if hasattr(parse_result, "plain_text") and parse_result.plain_text:
        return parse_result.plain_text

    parts = []
    for block in parse_result.blocks:
        if not block.should_skip_analysis and block.content:
            parts.append(block.content)
    return "\n\n".join(parts)


def _detect_file_type(filename: str) -> str | None:
    """Detect the file type string from the filename extension.

    Args:
        filename: The original filename.

    Returns:
        A FileType value string, or None if detection fails.
    """
    from app.services.parsing.format_detector import detect_format
    try:
        file_type = detect_format("", filename)
        return file_type.value
    except (ValueError, AttributeError):
        return None


def _get_extension(filename: str) -> str:
    """Extract the lowercased file extension from a filename.

    Args:
        filename: The original filename.

    Returns:
        The extension including the leading dot, or empty string.
    """
    dot_index = filename.rfind(".")
    if dot_index == -1:
        return ""
    return filename[dot_index:].lower()


_RE_MOD_DOCS_TYPE = re.compile(
    r":_mod-docs-content-type:\s*(CONCEPT|PROCEDURE|REFERENCE|ASSEMBLY)",
    re.IGNORECASE,
)


def _extract_content_type_from_file(content: str) -> str | None:
    """Extract modular documentation content type from file content.

    Looks for the ``:_mod-docs-content-type:`` AsciiDoc attribute entry
    and returns the normalized content type string.

    Args:
        content: Raw file content string.

    Returns:
        Lowercase content type string, or None if not found.
    """
    match = _RE_MOD_DOCS_TYPE.search(content)
    if match:
        return match.group(1).lower()
    return None
