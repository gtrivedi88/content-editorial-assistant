"""Plain-text parser with paragraph splitting and heuristic heading detection.

Splits on double newlines to identify paragraphs and uses simple heuristics
(ALL-CAPS lines, short lines followed by blanks) to detect headings.
Includes fallback detection for admonitions, UI artifacts, table captions,
browser-injected bullets, and structured headings.
"""

import logging
import re
from typing import Optional

from app.services.parsing.base import BaseParser, Block, ParseResult

logger = logging.getLogger(__name__)

# A line is considered a potential heading if it is shorter than this limit
_HEADING_MAX_LENGTH = 80

# Regex for lines that are entirely upper-case letters, digits, and spaces
_ALL_CAPS_RE = re.compile(r"^[A-Z0-9][A-Z0-9 :,\-]{2,}$")

# Admonition labels (single-word chunks from pasted docs)
_ADMONITION_LABELS = frozenset({
    "note", "tip", "important", "warning", "caution",
})

# UI chrome artifacts that should not be analysed
_UI_ARTIFACTS = frozenset({
    "expand", "collapse", "show more", "show less",
    "copy", "download", "back to top", "table of contents",
})

# Table captions like "Table 1.2. Kernel parameters"
_TABLE_CAPTION_RE = re.compile(r"^Table\s+\d+[\.\d]*\.\s+")

# Structured headings: "Chapter 1.", "1.2.3. Title", "Appendix A"
_STRUCTURED_HEADING_RE = re.compile(
    r"^(Chapter\s+\d+\.|"
    r"\d+\.\d+[\.\d]*\.\s|"
    r"(Appendix|Part|Section)\s+[A-Z0-9])"
)

# Browser-injected Unicode bullet characters (Chrome/Edge paste)
_BROWSER_BULLET_RE = re.compile(r"^[•○▪►‣◦⁃∙]\s+")


class PlaintextParser(BaseParser):
    """Parser for unstructured plain-text documents.

    Detects paragraph boundaries by splitting on blank lines and applies
    lightweight heuristics to identify likely heading lines.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse plain-text content into paragraph and heading blocks.

        Args:
            content: Raw plain-text string.
            filename: Optional source filename for logging.

        Returns:
            ParseResult with blocks and metadata.
        """
        logger.debug("PlaintextParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        chunks = re.split(r"\n{2,}", normalized)

        blocks: list[Block] = []
        search_start = 0

        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue

            start_pos = normalized.find(chunk, search_start)
            if start_pos == -1:
                start_pos = search_start
            end_pos = start_pos + len(chunk)
            search_start = end_pos

            # Advance start_pos past leading whitespace so the identity
            # offset path (start_pos + i) maps content[i] to the correct
            # character in the source, not the stripped whitespace.
            leading_ws = len(chunk) - len(chunk.lstrip())
            block = self._classify_chunk(stripped, chunk, start_pos + leading_ws, end_pos)
            blocks.append(block)

        plain_text = "\n\n".join(b.content for b in blocks if not b.should_skip_analysis)

        logger.debug("PlaintextParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_chunk(
        stripped: str, raw: str, start_pos: int, end_pos: int
    ) -> Block:
        """Classify a text chunk by heuristic type detection.

        Classification order (first match wins):
        1. UI artifacts → skip
        2. Admonition labels → skip
        3. Table captions → skip
        4. Tabular data (2+ tabs per line) → skip
        5. Browser bullet lines → list_item_unordered
        6. Structured heading → heading
        7. ALL-CAPS / short heading → heading
        8. Default → paragraph

        Args:
            stripped: Whitespace-trimmed chunk text.
            raw: Original chunk text (preserving internal whitespace).
            start_pos: Character offset of the chunk start.
            end_pos: Character offset of the chunk end.

        Returns:
            A Block instance with the detected type.
        """
        skip_type = _detect_skip_type(stripped)
        if skip_type is not None:
            return Block(
                block_type=skip_type,
                content=stripped,
                raw_content=raw,
                start_pos=start_pos,
                end_pos=end_pos,
                should_skip_analysis=True,
            )

        bullet_match = _BROWSER_BULLET_RE.match(stripped)
        if bullet_match:
            content = stripped[bullet_match.end():]
            return Block(
                block_type="list_item_unordered",
                content=content,
                raw_content=raw,
                start_pos=start_pos,
                end_pos=end_pos,
            )

        if _is_heading_line(stripped):
            return Block(
                block_type="heading",
                content=stripped,
                raw_content=raw,
                start_pos=start_pos,
                end_pos=end_pos,
                level=1,
            )

        return Block(
            block_type="paragraph",
            content=stripped,
            raw_content=raw,
            start_pos=start_pos,
            end_pos=end_pos,
        )


def _detect_skip_type(text: str) -> str | None:
    """Return a block type string if *text* should be skipped, else None.

    Detects UI artifacts, admonition labels, table captions, and tabular data.
    """
    lower = text.lower()
    if lower in _UI_ARTIFACTS:
        return "ui_artifact"
    if lower in _ADMONITION_LABELS:
        return "admonition"
    if _TABLE_CAPTION_RE.match(text):
        return "table_caption"
    # Tabular data: lines with 2+ tab characters
    if "\t" in text and text.count("\t") >= 2:
        return "table"
    return None


def _is_heading_line(text: str) -> bool:
    """Return True if *text* looks like a heading.

    Heuristics applied:
    * Single line (no embedded newlines).
    * Shorter than the maximum heading length.
    * Structured heading pattern (Chapter N., 1.2.3., Appendix A).
    * Either ALL-CAPS or does not end with sentence-terminating punctuation.
    """
    if "\n" in text:
        return False
    if len(text) > _HEADING_MAX_LENGTH:
        return False
    if _STRUCTURED_HEADING_RE.match(text):
        return True
    if _ALL_CAPS_RE.match(text):
        return True
    if not text.endswith((".", "!", "?", ":")):
        # Short single line without terminal punctuation is a likely heading
        return len(text) <= 60
    return False
