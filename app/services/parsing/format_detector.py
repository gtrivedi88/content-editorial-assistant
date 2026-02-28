"""Weighted-scoring format detector for document content.

Examines content patterns and optional filename extension to determine the
most likely FileType.  Each format has a set of regex patterns with
associated weights; the format with the highest cumulative score wins.
"""

import logging
import os
import re
from typing import Optional

from app.models.enums import FileType

logger = logging.getLogger(__name__)

# Maximum number of lines to scan for pattern matching
_MAX_SCAN_LINES = 50

# Extension-to-FileType mapping
_EXTENSION_MAP: dict[str, FileType] = {
    ".adoc": FileType.ASCIIDOC,
    ".asciidoc": FileType.ASCIIDOC,
    ".asc": FileType.ASCIIDOC,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".html": FileType.HTML,
    ".htm": FileType.HTML,
    ".xhtml": FileType.HTML,
    ".xml": FileType.XML,
    ".dita": FileType.DITA,
    ".ditamap": FileType.DITA,
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".txt": FileType.PLAINTEXT,
    ".text": FileType.PLAINTEXT,
    ".rst": FileType.PLAINTEXT,
}

# Patterns: list of (compiled regex, weight) tuples per format
_ASCIIDOC_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^=+\s+"), 5),
    (re.compile(r"^:[\w-]+:"), 5),
    (re.compile(r"^\|={4,}\s*$"), 5),
    (re.compile(r"^\[(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]"), 4),
    (re.compile(r"^\..+"), 3),
    (re.compile(r"^(include|image|link)::"), 3),
    (re.compile(r"^\*{4,}\s*$"), 2),
    (re.compile(r"^={4,}\s*$"), 2),
    (re.compile(r"^-{4,}\s*$"), 2),
    (re.compile(r"^\.{2,}\s*$"), 2),
]

_MARKDOWN_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^#+\s+"), 3),
    (re.compile(r"^```"), 3),
    (re.compile(r"^>\s+"), 3),
    (re.compile(r"^\|\s*[^=].*\s*\|"), 1),
    (re.compile(r"^[*\-+]\s+"), 1),
    (re.compile(r"^\d+\.\s+"), 1),
]

# DITA patterns are checked against the full content (multi-line)
_DITA_FULL_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"<!DOCTYPE\s+\w+\s+PUBLIC.*DITA", re.IGNORECASE | re.DOTALL), 10),
    (re.compile(r"<(concept|task|reference|topic|troubleshooting)[\s>]", re.IGNORECASE), 8),
    (re.compile(r"<(conbody|taskbody|refbody|troublebody)[\s>]", re.IGNORECASE), 6),
    (re.compile(r"<(shortdesc|prereq|context|steps|result)[\s>]", re.IGNORECASE), 4),
    (re.compile(r"<(step|cmd|info|stepresult)[\s>]", re.IGNORECASE), 3),
]

_HTML_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"<html[\s>]", re.IGNORECASE), 3),
    (re.compile(r"<body[\s>]", re.IGNORECASE), 3),
    (re.compile(r"<div[\s>]", re.IGNORECASE), 3),
    (re.compile(r"<!DOCTYPE\s+html", re.IGNORECASE), 5),
    (re.compile(r"<head[\s>]", re.IGNORECASE), 3),
]

_XML_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"<\?xml\s"), 2),
    (re.compile(r"xmlns[:=]"), 2),
    (re.compile(r"<\w+:\w+[\s>]"), 2),
]


def _score_line_patterns(
    line: str,
    patterns: list[tuple[re.Pattern[str], int]],
) -> int:
    """Return the weight of the first matching pattern for a single line."""
    for pattern, weight in patterns:
        if pattern.search(line):
            return weight
    return 0


def _score_full_patterns(
    content: str,
    patterns: list[tuple[re.Pattern[str], int]],
) -> int:
    """Return the sum of weights for patterns matched against full content."""
    total = 0
    for pattern, weight in patterns:
        if pattern.search(content):
            total += weight
    return total


def detect_format(content: str, filename: Optional[str] = None) -> FileType:
    """Detect the file format of *content* using weighted pattern matching.

    If a *filename* is provided its extension is checked first and, for
    unambiguous binary formats (PDF, DOCX), returned immediately.  For
    text-based formats the extension adds a bonus to the scoring but
    content patterns can still override.

    Args:
        content: Raw document content to analyse.
        filename: Optional filename whose extension is used as a hint.

    Returns:
        The detected :class:`FileType` enum member.
    """
    if not content or not content.strip():
        return _filetype_from_extension(filename) or FileType.PLAINTEXT

    # Binary formats are determined solely by extension
    ext_type = _filetype_from_extension(filename)
    if ext_type in (FileType.PDF, FileType.DOCX):
        return ext_type

    scores: dict[FileType, int] = {
        FileType.ASCIIDOC: 0,
        FileType.MARKDOWN: 0,
        FileType.DITA: 0,
        FileType.HTML: 0,
        FileType.XML: 0,
    }

    # Extension bonus (gives a nudge but does not dominate)
    if ext_type in scores:
        scores[ext_type] += 3

    # Full-content patterns (DITA, HTML, XML)
    scores[FileType.DITA] += _score_full_patterns(content, _DITA_FULL_PATTERNS)
    scores[FileType.HTML] += _score_full_patterns(content, _HTML_PATTERNS)
    scores[FileType.XML] += _score_full_patterns(content, _XML_PATTERNS)

    # Line-by-line patterns (AsciiDoc, Markdown)
    lines = content.split("\n")
    scan_limit = min(_MAX_SCAN_LINES, len(lines))
    for line in lines[:scan_limit]:
        stripped = line.strip()
        if not stripped:
            continue
        scores[FileType.ASCIIDOC] += _score_line_patterns(stripped, _ASCIIDOC_PATTERNS)
        scores[FileType.MARKDOWN] += _score_line_patterns(stripped, _MARKDOWN_PATTERNS)

    best_format = max(scores, key=lambda ft: scores[ft])
    best_score = scores[best_format]

    if best_score == 0:
        logger.debug("No markup patterns detected; falling back to PLAINTEXT")
        return FileType.PLAINTEXT

    logger.debug(
        "Format detection scores: %s -> %s",
        {ft.value: s for ft, s in scores.items() if s > 0},
        best_format.value,
    )
    return best_format


def _filetype_from_extension(filename: Optional[str]) -> Optional[FileType]:
    """Return the FileType implied by *filename*'s extension, or None."""
    if not filename:
        return None
    ext = os.path.splitext(filename)[1].lower()
    return _EXTENSION_MAP.get(ext)
