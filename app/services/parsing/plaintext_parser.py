"""Plain-text parser with paragraph splitting and heuristic heading detection.

Splits on double newlines to identify paragraphs and uses simple heuristics
(ALL-CAPS lines, short lines followed by blanks) to detect headings.
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
        """Classify a text chunk as heading or paragraph.

        Args:
            stripped: Whitespace-trimmed chunk text.
            raw: Original chunk text (preserving internal whitespace).
            start_pos: Character offset of the chunk start.
            end_pos: Character offset of the chunk end.

        Returns:
            A Block instance typed as either ``heading`` or ``paragraph``.
        """
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


def _is_heading_line(text: str) -> bool:
    """Return True if *text* looks like a heading.

    Heuristics applied:
    * Single line (no embedded newlines).
    * Shorter than the maximum heading length.
    * Either ALL-CAPS or does not end with sentence-terminating punctuation.
    """
    if "\n" in text:
        return False
    if len(text) > _HEADING_MAX_LENGTH:
        return False
    if _ALL_CAPS_RE.match(text):
        return True
    if not text.endswith((".", "!", "?", ":")):
        # Short single line without terminal punctuation is a likely heading
        return len(text) <= 60
    return False
