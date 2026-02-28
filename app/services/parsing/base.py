"""Base parser classes and data structures for file format parsing.

Provides the Block, ParseResult, and BaseParser abstractions
used by all format-specific parsers in the parsing package.
"""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Valid block type values for reference
VALID_BLOCK_TYPES = frozenset({
    "heading", "paragraph", "code_block", "list", "list_item",
    "list_item_ordered", "list_item_unordered", "table", "table_row",
    "table_cell", "admonition", "blockquote", "image", "attribute_entry",
    "comment", "dlist", "preamble", "section", "sidebar", "quote",
    "example", "verse", "open", "listing", "literal",
})


@dataclass
class Block:
    """A structural block extracted from a parsed document.

    Attributes:
        block_type: Semantic type of the block (heading, paragraph, etc.).
        content: Extracted text content with markup removed.
        raw_content: Original markup as it appeared in the source.
        start_pos: Character offset of the block start in the original text.
        end_pos: Character offset of the block end in the original text.
        inline_content: Text with block-level markers stripped but inline
            formatting preserved (e.g. ``**bold**``, ```code```).
            Tier 2 in the 3-tier block contract:
            ``raw_content`` (Tier 1) -> ``inline_content`` (Tier 2)
            -> ``content`` (Tier 3).
        level: Heading level or nesting depth (0 for non-hierarchical blocks).
        children: Nested child blocks for hierarchical structures.
        should_skip_analysis: True if the block should not be style-checked
            (e.g. code blocks, comments, unresolved references).
        metadata: Arbitrary key-value data specific to the format or block.
        char_map: Maps each character index in ``content`` to its
            corresponding index in ``inline_content``. ``None`` means
            identity mapping (content equals inline_content with no
            inline markup stripped).
    """

    block_type: str
    content: str
    raw_content: str
    start_pos: int
    end_pos: int
    inline_content: str = ""
    level: int = 0
    children: list["Block"] = field(default_factory=list)
    should_skip_analysis: bool = False
    metadata: dict = field(default_factory=dict)
    char_map: list[int] | None = None

    def __post_init__(self) -> None:
        """Default inline_content to content for non-AsciiDoc parsers."""
        if not self.inline_content:
            self.inline_content = self.content


@dataclass
class ParseResult:
    """Result of parsing a document into blocks.

    Attributes:
        blocks: Ordered list of top-level blocks found in the document.
        metadata: Format-specific metadata (warnings, unresolved refs, etc.).
        plain_text: Concatenated text content of all blocks for analysis.
    """

    blocks: list[Block]
    metadata: dict = field(default_factory=dict)
    plain_text: str = ""


class BaseParser(ABC):
    """Abstract base class for format-specific document parsers.

    Subclasses must implement :meth:`parse` to convert raw text (or binary
    content represented as a string path) into a :class:`ParseResult`.
    """

    @abstractmethod
    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse document content and return structured blocks.

        Args:
            content: Raw document content as a string.
            filename: Optional filename for context or error reporting.

        Returns:
            A ParseResult containing blocks and metadata.
        """


# ---------------------------------------------------------------------------
# Shared inline-marker stripping (SK-3 / SK-4)
# ---------------------------------------------------------------------------


def strip_inline_markers(
    text: str,
    patterns: list[tuple[re.Pattern[str], int]],
) -> tuple[str, list[int]]:
    """Strip inline formatting markers from text with char-level tracking.

    Finds all matches for the given patterns, removes the marker
    characters, keeps the captured content, and builds a ``char_map``
    that maps each character index in the clean output to the
    corresponding index in the original *text*.

    Matches are processed left-to-right; overlapping matches are
    discarded (first match wins).

    Args:
        text: Raw text possibly containing inline markers.
        patterns: List of ``(compiled_regex, group_number)`` tuples.
            *group_number* identifies the capture group whose content
            should be kept.

    Returns:
        Tuple of ``(clean_text, char_map)`` where ``char_map[i]`` is the
        index in *text* for character ``i`` in *clean_text*.
    """
    # Collect all non-overlapping matches, sorted by position
    all_matches: list[tuple[int, int, int, int]] = []
    for pattern, group_num in patterns:
        for m in pattern.finditer(text):
            all_matches.append((
                m.start(), m.end(),
                m.start(group_num), m.end(group_num),
            ))

    all_matches.sort(key=lambda x: x[0])

    # Remove overlapping matches (keep first)
    filtered: list[tuple[int, int, int, int]] = []
    last_end = 0
    for match_start, match_end, content_start, content_end in all_matches:
        if match_start >= last_end:
            filtered.append((match_start, match_end, content_start, content_end))
            last_end = match_end

    # Build output character-by-character
    result: list[str] = []
    char_map: list[int] = []
    pos = 0

    for match_start, match_end, content_start, content_end in filtered:
        # Characters before this match: keep as-is
        for i in range(pos, match_start):
            result.append(text[i])
            char_map.append(i)

        # Content within the matched group: keep
        for i in range(content_start, content_end):
            result.append(text[i])
            char_map.append(i)

        pos = match_end

    # Remaining characters after the last match
    for i in range(pos, len(text)):
        result.append(text[i])
        char_map.append(i)

    return "".join(result), char_map


# ---------------------------------------------------------------------------
# XML/HTML char_map builder (SK-4 for lxml-based parsers)
# ---------------------------------------------------------------------------


def build_xml_char_map(raw_xml: str, clean_text: str) -> list[int] | None:
    """Build a char_map from serialised XML/HTML to extracted text.

    Maps each character position in *clean_text* to its approximate
    position in *raw_xml* by tracking text-character positions
    (characters outside ``<…>`` tags) and greedily aligning them.

    Used by DITA, HTML, and XML parsers where ``Block.content`` is
    text extracted from the parsed tree and ``Block.raw_content`` is
    the serialised element markup.

    Args:
        raw_xml: Serialised XML or HTML string (``Block.raw_content``).
        clean_text: Extracted text (``Block.content``).

    Returns:
        List mapping ``clean_text[i]`` to a position in *raw_xml*,
        or ``None`` if either input is empty.
    """
    if not clean_text or not raw_xml:
        return None

    text_chars, text_positions = _extract_xml_text_positions(raw_xml)
    if not text_chars:
        return None

    return _align_text_to_positions(clean_text, text_chars, text_positions)


def _extract_xml_text_positions(
    raw_xml: str,
) -> tuple[list[str], list[int]]:
    """Extract non-tag characters and their positions from serialised XML.

    Args:
        raw_xml: Serialised XML or HTML string.

    Returns:
        Tuple of (characters, positions) for text outside tags.
    """
    text_chars: list[str] = []
    text_positions: list[int] = []
    in_tag = False
    for i, ch in enumerate(raw_xml):
        if ch == "<":
            in_tag = True
        elif ch == ">" and in_tag:
            in_tag = False
        elif not in_tag:
            text_chars.append(ch)
            text_positions.append(i)
    return text_chars, text_positions


def _align_text_to_positions(
    clean_text: str,
    text_chars: list[str],
    text_positions: list[int],
) -> list[int]:
    """Greedily align clean text characters to raw XML positions.

    Args:
        clean_text: Extracted text to align.
        text_chars: Characters extracted from raw XML (outside tags).
        text_positions: Source positions for each extracted character.

    Returns:
        List mapping each clean_text index to a raw XML position.
    """
    char_map: list[int] = []
    raw_idx = 0
    raw_len = len(text_chars)

    for ch in clean_text:
        pos = _find_char_in_raw(ch, text_chars, text_positions, raw_idx, raw_len)
        if pos is not None:
            char_map.append(pos[0])
            raw_idx = pos[1]
        else:
            fallback = text_positions[min(raw_idx, raw_len - 1)]
            char_map.append(fallback)

    return char_map


def _find_char_in_raw(
    ch: str,
    text_chars: list[str],
    text_positions: list[int],
    start: int,
    length: int,
) -> tuple[int, int] | None:
    """Find the next matching character in the raw text sequence.

    Args:
        ch: Character to find.
        text_chars: Extracted text characters.
        text_positions: Positions of extracted characters in raw XML.
        start: Index to start searching from.
        length: Total number of extracted characters.

    Returns:
        Tuple of (position_in_raw_xml, next_search_index) or None.
    """
    idx = start
    while idx < length:
        raw_ch = text_chars[idx]
        if raw_ch == ch:
            return text_positions[idx], idx + 1
        if ch == " " and raw_ch in (" ", "\t", "\n", "\r"):
            return text_positions[idx], idx + 1
        idx += 1
    return None
