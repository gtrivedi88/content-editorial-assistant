"""Markdown parser using markdown-it-py for token-based parsing.

Converts CommonMark tokens produced by markdown-it-py into the unified
Block data structure used by the analysis pipeline.
"""

import logging
import re
from typing import Optional

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.services.parsing.base import (
    BaseParser, Block, ParseResult, strip_inline_markers,
)

logger = logging.getLogger(__name__)

# Pre-compiled Markdown inline patterns for stripping (SK-3).
# Order matters: longer delimiters first to avoid partial matches.
_MD_INLINE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    # ~~strikethrough~~
    (re.compile(r"~~(.+?)~~"), 1),
    # **bold**
    (re.compile(r"\*\*(.+?)\*\*"), 1),
    # *italic* (but not **)
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), 1),
    # `code`
    (re.compile(r"`([^`]+)`"), 1),
    # [text](url) → text
    (re.compile(r"\[([^\]]+)\]\([^)]+\)"), 1),
]


def _strip_md_inline(text: str) -> tuple[str, list[int]]:
    """Strip Markdown inline formatting and build char_map.

    Args:
        text: Raw Markdown text with inline markers.

    Returns:
        Tuple of (clean_text, char_map).
    """
    return strip_inline_markers(text, _MD_INLINE_PATTERNS)


# Token type -> block_type string
_TOKEN_TYPE_MAP: dict[str, str] = {
    "heading_open": "heading",
    "paragraph_open": "paragraph",
    "blockquote_open": "blockquote",
    "bullet_list_open": "list",
    "ordered_list_open": "list",
    "list_item_open": "list_item",
    "table_open": "table",
    "tr_open": "table_row",
    "td_open": "table_cell",
    "th_open": "table_cell",
    "code_block": "code_block",
    "fence": "code_block",
    "hr": "paragraph",
    "html_block": "paragraph",
}


class MarkdownParser(BaseParser):
    """Parser for Markdown documents using markdown-it-py.

    Handles headings, paragraphs, code fences (with language metadata),
    ordered and unordered lists, tables, blockquotes, and images.
    """

    def __init__(self) -> None:
        """Initialise the markdown-it engine with CommonMark defaults."""
        self._md = MarkdownIt("commonmark", {"html": True})
        self._md.enable(["table", "strikethrough"])

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse Markdown content into structured blocks.

        Args:
            content: Raw Markdown text.
            filename: Optional filename for logging.

        Returns:
            ParseResult with typed blocks and metadata.
        """
        logger.debug("MarkdownParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        tokens = self._md.parse(content)
        content_lines = content.split("\n")
        blocks = self._tokens_to_blocks(tokens, content_lines)
        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("MarkdownParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Token processing
    # ------------------------------------------------------------------

    def _tokens_to_blocks(
        self, tokens: list[Token], content_lines: list[str]
    ) -> list[Block]:
        """Walk the token stream and emit top-level blocks."""
        blocks: list[Block] = []
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]

            # Skip closing tokens
            if token.nesting == -1:
                idx += 1
                continue

            block = self._token_to_block(token, content_lines)
            if block is None:
                idx += 1
                continue

            if token.nesting == 1:
                idx = self._process_container(
                    token, tokens, idx, block, content_lines
                )
            else:
                idx += 1

            blocks.append(block)
        return blocks

    def _process_container(
        self,
        open_token: Token,
        tokens: list[Token],
        open_idx: int,
        parent_block: Block,
        content_lines: list[str],
    ) -> int:
        """Consume child tokens up to the matching close and return new index."""
        depth = 1
        child_tokens: list[Token] = []
        j = open_idx + 1
        while j < len(tokens) and depth > 0:
            if tokens[j].nesting == 1:
                depth += 1
            elif tokens[j].nesting == -1:
                depth -= 1
            if depth > 0:
                child_tokens.append(tokens[j])
            j += 1

        if child_tokens:
            parent_block.children = self._process_children(
                child_tokens, content_lines, parent_block.block_type
            )
            # For list containers, derive content from children
            if parent_block.block_type == "list":
                parent_block.content = "\n".join(
                    c.content for c in parent_block.children if c.content
                )
        return j

    def _process_children(
        self,
        tokens: list[Token],
        content_lines: list[str],
        parent_type: str,
    ) -> list[Block]:
        """Convert child tokens into child blocks."""
        blocks: list[Block] = []
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token.nesting == -1:
                idx += 1
                continue

            # For list_item containers, extract inline content directly
            if token.type == "list_item_open":
                idx, item_block = self._extract_list_item(tokens, idx, content_lines)
                blocks.append(item_block)
                continue

            block = self._token_to_block(token, content_lines)
            if block is not None:
                if token.nesting == 1:
                    idx = self._process_container(
                        token, tokens, idx, block, content_lines
                    )
                else:
                    idx += 1
                blocks.append(block)
            else:
                idx += 1
        return blocks

    def _extract_list_item(
        self, tokens: list[Token], open_idx: int, content_lines: list[str]
    ) -> tuple[int, Block]:
        """Extract a list_item block and return (next_index, block)."""
        token = tokens[open_idx]
        depth = 1
        j = open_idx + 1
        item_content = ""
        item_type = "list_item"

        # Determine ordered vs unordered from parent context
        parent_token = tokens[open_idx]
        if parent_token.info and parent_token.info.strip():
            item_type = "list_item_ordered"

        while j < len(tokens) and depth > 0:
            if tokens[j].nesting == 1:
                depth += 1
            elif tokens[j].nesting == -1:
                depth -= 1
            if tokens[j].type == "inline":
                item_content = tokens[j].content
            j += 1

        start_line = token.map[0] if token.map else 0
        end_line = token.map[1] if token.map else start_line + 1
        start_pos, end_pos = _line_offsets(content_lines, start_line, end_line)
        raw_content = _raw_from_lines(content_lines, start_line, end_line)

        # Advance start_pos past the list marker (- , * , 1. , etc.)
        start_pos += _content_offset_in_raw(raw_content, item_content)

        # SK-3/SK-4: strip inline markers and build char_map
        clean_content, char_map = _strip_md_inline(item_content)

        block = Block(
            block_type=item_type,
            content=clean_content,
            raw_content=raw_content,
            start_pos=start_pos,
            end_pos=end_pos,
            char_map=char_map,
        )
        return j, block

    # ------------------------------------------------------------------
    # Single-token conversion
    # ------------------------------------------------------------------

    def _token_to_block(
        self, token: Token, content_lines: list[str]
    ) -> Optional[Block]:
        """Create a Block from a single markdown-it Token."""
        block_type = _TOKEN_TYPE_MAP.get(token.type)
        if block_type is None:
            return None

        start_line = token.map[0] if token.map else 0
        end_line = token.map[1] if token.map else start_line + 1
        raw_content = _raw_from_lines(content_lines, start_line, end_line)
        start_pos, end_pos = _line_offsets(content_lines, start_line, end_line)

        content = self._extract_content(token, block_type, raw_content)
        level = _heading_level(token)
        skip = block_type == "code_block"

        # Advance start_pos past markers/whitespace stripped during
        # content extraction so char_map indices align with the source.
        if not skip:
            start_pos += _content_offset_in_raw(raw_content, content)

        metadata: dict = {}
        if token.type == "fence" and token.info:
            metadata["language"] = token.info.strip()

        # SK-3/SK-4: strip inline markers from prose blocks and build char_map
        char_map: list[int] | None = None
        if not skip and block_type not in ("table", "table_row"):
            content, char_map = _strip_md_inline(content)

        return Block(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            start_pos=start_pos,
            end_pos=end_pos,
            level=level,
            should_skip_analysis=skip,
            metadata=metadata,
            char_map=char_map,
        )

    @staticmethod
    def _extract_content(
        token: Token, block_type: str, raw_content: str
    ) -> str:
        """Extract clean text content from a token or its raw content."""
        if block_type == "heading":
            return _strip_heading_markers(raw_content)
        if block_type == "code_block":
            return _strip_code_fences(raw_content)
        if block_type == "blockquote":
            return _strip_blockquote_markers(raw_content)

        # For inline-only tokens the content lives on the token itself
        if token.content:
            return token.content.strip()

        return raw_content.strip()


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _raw_from_lines(content_lines: list[str], start: int, end: int) -> str:
    """Join *content_lines[start:end]* back into a string."""
    end = min(end, len(content_lines))
    start = max(0, start)
    return "\n".join(content_lines[start:end])


def _line_offsets(
    content_lines: list[str], start_line: int, end_line: int
) -> tuple[int, int]:
    """Compute character offsets for a range of lines."""
    start_pos = sum(len(content_lines[i]) + 1 for i in range(min(start_line, len(content_lines))))
    end_pos = sum(len(content_lines[i]) + 1 for i in range(min(end_line, len(content_lines))))
    return start_pos, max(start_pos, end_pos - 1)


def _heading_level(token: Token) -> int:
    """Extract heading level (1-6) from a heading_open token."""
    if token.type == "heading_open" and token.tag:
        try:
            return int(token.tag[1])
        except (IndexError, ValueError):
            pass
    return 0


def _strip_heading_markers(raw: str) -> str:
    """Remove ``#`` markers and return the heading text."""
    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.startswith("#"):
            text = stripped.lstrip("#").strip().rstrip("#").strip()
            if text:
                return text
    return raw.strip()


def _strip_code_fences(raw: str) -> str:
    """Remove opening/closing triple-backtick fences."""
    lines = raw.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)


def _strip_blockquote_markers(raw: str) -> str:
    """Remove leading ``>`` from blockquote lines."""
    cleaned: list[str] = []
    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.startswith(">"):
            cleaned.append(stripped.lstrip(">").strip())
        elif stripped:
            cleaned.append(stripped)
    return "\n".join(cleaned)


def _content_offset_in_raw(raw: str, content: str) -> int:
    """Find where extracted content starts within raw source text.

    Handles heading markers (``#``), blockquote markers (``>``),
    list markers, and leading whitespace stripped during extraction.

    Args:
        raw: The raw source text for the block.
        content: The extracted content (before inline stripping).

    Returns:
        Character offset of *content* within *raw*, or 0 if the
        content is empty or starts at position 0.
    """
    if not content:
        return 0
    idx = raw.find(content)
    if idx >= 0:
        return idx
    # Multi-line content (blockquote): try first line
    first_line = content.split("\n")[0]
    if first_line:
        idx = raw.find(first_line)
        if idx >= 0:
            return idx
    return len(raw) - len(raw.lstrip())


