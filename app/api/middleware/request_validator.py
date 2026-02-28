"""Input validation and sanitization utilities for API requests.

Provides reusable validation functions that route handlers call before
forwarding data to the service layer.  Raises ``werkzeug.exceptions``
so that the global error handlers produce proper JSON responses.
"""

import logging
import re
import unicodedata
from typing import Set

from werkzeug.datastructures import FileStorage
from werkzeug.exceptions import RequestEntityTooLarge, UnsupportedMediaType, UnprocessableEntity

logger = logging.getLogger(__name__)

# File extensions accepted for upload
ALLOWED_EXTENSIONS: Set[str] = {
    ".txt", ".md", ".adoc", ".html", ".htm",
    ".xml", ".dita", ".ditamap",
    ".pdf", ".docx", ".rst",
}

# Regex matching ASCII and Unicode control characters except common whitespace
_CONTROL_CHAR_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)


def validate_text_length(text: str, max_length: int) -> str:
    """Validate that text does not exceed the maximum allowed length.

    Args:
        text: The input text to validate.
        max_length: Maximum number of characters allowed.

    Returns:
        The validated text (unchanged).

    Raises:
        UnprocessableEntity: If the text exceeds *max_length*.
    """
    if len(text) > max_length:
        logger.warning(
            "Text length %d exceeds maximum %d",
            len(text),
            max_length,
        )
        raise UnprocessableEntity(
            f"Text length ({len(text)} characters) exceeds "
            f"maximum allowed ({max_length} characters)"
        )
    return text


def validate_file_size(file: FileStorage, max_size: int) -> FileStorage:
    """Validate that an uploaded file does not exceed the size limit.

    Reads the stream to measure its byte length, then seeks back to the
    start so downstream consumers can read it normally.

    Args:
        file: The uploaded file from the request.
        max_size: Maximum file size in bytes.

    Returns:
        The validated FileStorage (stream reset to start).

    Raises:
        RequestEntityTooLarge: If the file exceeds *max_size*.
    """
    file.stream.seek(0, 2)  # seek to end
    size = file.stream.tell()
    file.stream.seek(0)  # reset for downstream readers

    if size > max_size:
        logger.warning(
            "Uploaded file '%s' size %d exceeds maximum %d",
            file.filename,
            size,
            max_size,
        )
        raise RequestEntityTooLarge(
            f"File size ({size} bytes) exceeds maximum allowed ({max_size} bytes)"
        )
    return file


def validate_file_type(filename: str, allowed_extensions: Set[str] | None = None) -> str:
    """Validate that the filename has an allowed extension.

    Args:
        filename: Original filename from the upload.
        allowed_extensions: Set of lowercase extensions including the dot
            (e.g., ``{'.txt', '.md'}``).  Defaults to ``ALLOWED_EXTENSIONS``.

    Returns:
        The validated filename.

    Raises:
        UnsupportedMediaType: If the extension is not in the allowed set.
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS

    # Extract extension (lowercased)
    dot_index = filename.rfind(".")
    ext = filename[dot_index:].lower() if dot_index != -1 else ""

    if ext not in allowed_extensions:
        logger.warning(
            "File type '%s' not allowed. Accepted: %s",
            ext,
            ", ".join(sorted(allowed_extensions)),
        )
        raise UnsupportedMediaType(
            f"File type '{ext}' is not supported. "
            f"Accepted types: {', '.join(sorted(allowed_extensions))}"
        )
    return filename


def sanitize_input(text: str) -> str:
    """Sanitize user-provided text for safe processing.

    Performs the following transformations:
        1. Normalize Unicode to NFC form.
        2. Strip ASCII/Unicode control characters (preserving newlines,
           tabs, and carriage returns which are normalized separately).
        3. Normalize line endings (``\\r\\n`` -> ``\\n``).
        4. Convert tabs to spaces.
        5. Strip leading/trailing whitespace.

    Args:
        text: Raw user input text.

    Returns:
        Cleaned text safe for analysis pipelines.
    """
    # Unicode normalization (NFC)
    text = unicodedata.normalize("NFC", text)

    # Remove control characters (keep \n, \r, \t for now)
    text = _CONTROL_CHAR_RE.sub("", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Tabs to spaces
    text = text.replace("\t", " ")

    # Strip outer whitespace
    text = text.strip()

    return text
