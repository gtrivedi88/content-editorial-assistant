"""AsciiDoc parser with Ruby Asciidoctor subprocess and regex fallback.

Attempts to parse via the Ruby Asciidoctor gem using a subprocess. Falls
back to a basic regex-based parser when Ruby or Asciidoctor is unavailable.
Concurrent Asciidoctor invocations are limited by a threading semaphore.
"""

import json
import logging
import os
import re
import subprocess
import tempfile
import threading
from typing import Optional

from app.config import Config
from app.services.parsing.base import (
    BaseParser, Block, ParseResult, strip_inline_markers,
)

logger = logging.getLogger(__name__)

_ASCIIDOCTOR_TIMEOUT = 30  # seconds

# Semaphore limiting concurrent Asciidoctor subprocesses
_semaphore = threading.Semaphore(Config.ASCIIDOCTOR_MAX_CONCURRENT)

# Pre-compiled patterns for the regex fallback parser
_RE_HEADING = re.compile(r"^(={1,6})\s+(.+)$")
_RE_CODE_OPEN = re.compile(r"^-{4,}\s*$")
_RE_TABLE_DELIM = re.compile(r"^\|={3,}\s*$")
_RE_ADMONITION = re.compile(
    r"^\[(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*$", re.IGNORECASE
)
_RE_ATTR_ENTRY = re.compile(r"^:(!?[\w-]+):\s*(.*)")
_RE_ULIST = re.compile(r"^(\*{1,5})\s+(.+)")
_RE_OLIST = re.compile(r"^(\.{1,5})\s+(.+)")
_RE_INCLUDE = re.compile(r"^include::(.+)\[")
_RE_IMAGE = re.compile(r"^image::(.+)\[")
_RE_BLOCK_ANCHOR = re.compile(r"^\[id=[\"'][^\"']*[\"']\]\s*$")
_RE_ROLE_ATTR = re.compile(r"^\[role=[\"'][^\"']*[\"']\]\s*$")
# AsciiDoc block title: single dot followed immediately by a letter.
# Distinguishes from ordered list items which require a space after the dot.
_RE_BLOCK_TITLE = re.compile(r"^\.([A-Za-z].*)")
# List continuation marker (+ on its own line)
_RE_LIST_CONTINUATION = re.compile(r"^\+\s*$")
# Generic block attribute [source,bash] [bash,subs=...] [%collapsible] etc.
_RE_GENERIC_BLOCK_ATTR = re.compile(r"^\[[\w,%#\"'=\s.+-]+\]\s*$")
# AsciiDoc table cell separator (for SK-6 per-cell decomposition)
_RE_TABLE_CELL = re.compile(r"\|")
# Block delimiter line (====, ****, etc.) — used to strip from admonitions
_RE_BLOCK_DELIM = re.compile(r"^[=*]{4,}\s*$")
# Single-line comment (// not followed by another /)
_RE_SINGLE_LINE_COMMENT = re.compile(r"^[ \t]*//(?!/)")
# Conditional directives: ifdef::, ifndef::, ifeval::, endif::
_RE_CONDITIONAL = re.compile(r"^[ \t]*(?:ifdef|ifndef|ifeval|endif)::")
# Definition list term: "term::" or "term:::" (nested) at end of line
_RE_DLIST = re.compile(r"^(.+?):{2,4}\s*$")
# Definition list term with inline description: "term:: description"
_RE_DLIST_INLINE = re.compile(r"^(.+?):{2,4}\s+(.+)$")
# Literal block delimiter (4+ dots)
_RE_LITERAL_OPEN = re.compile(r"^\.{4,}\s*$")
# Comment block delimiter (4+ slashes)
_RE_COMMENT_BLOCK = re.compile(r"^/{4,}\s*$")
# Passthrough block delimiter (4+ plus signs)
_RE_PASSTHROUGH_OPEN = re.compile(r"^\+{4,}\s*$")
# Sidebar block delimiter (4+ asterisks)
_RE_SIDEBAR_OPEN = re.compile(r"^\*{4,}\s*$")
# Example block delimiter (4+ equals signs)
_RE_EXAMPLE_OPEN = re.compile(r"^={4,}\s*$")
# Quote/verse block delimiter (4+ underscores)
_RE_QUOTE_OPEN = re.compile(r"^_{4,}\s*$")
# Open block delimiter (exactly 2 dashes)
_RE_OPEN_BLOCK = re.compile(r"^--\s*$")

# Delimited block patterns: (regex, block_type, should_skip_analysis)
# Order matters: _RE_CODE_OPEN (4+ dashes) must precede _RE_OPEN_BLOCK (2 dashes).
_DELIMITED_BLOCK_PATTERNS: list[tuple[re.Pattern[str], str, bool]] = [
    (_RE_CODE_OPEN, "code_block", True),
    (_RE_LITERAL_OPEN, "literal", True),
    (_RE_COMMENT_BLOCK, "comment", True),
    (_RE_PASSTHROUGH_OPEN, "comment", True),
    (_RE_SIDEBAR_OPEN, "sidebar", False),
    (_RE_EXAMPLE_OPEN, "example", False),
    (_RE_QUOTE_OPEN, "quote", False),
    (_RE_TABLE_DELIM, "table", False),
    (_RE_OPEN_BLOCK, "open_block", False),
]

# Single-line patterns that produce skip-analysis blocks
_SKIP_LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_RE_SINGLE_LINE_COMMENT, "comment"),
    (_RE_CONDITIONAL, "comment"),
    (_RE_IMAGE, "image"),
    (_RE_BLOCK_ANCHOR, "comment"),
    (_RE_ROLE_ATTR, "comment"),
    (_RE_INCLUDE, "comment"),
    (_RE_LIST_CONTINUATION, "comment"),
    (_RE_GENERIC_BLOCK_ATTR, "comment"),
]

# Patterns that stop paragraph accumulation (any block-level construct)
_PARAGRAPH_STOP_PATTERNS: list[re.Pattern[str]] = [
    _RE_CODE_OPEN,
    _RE_LITERAL_OPEN,
    _RE_COMMENT_BLOCK,
    _RE_PASSTHROUGH_OPEN,
    _RE_SIDEBAR_OPEN,
    _RE_EXAMPLE_OPEN,
    _RE_QUOTE_OPEN,
    _RE_TABLE_DELIM,
    _RE_LIST_CONTINUATION,
    _RE_GENERIC_BLOCK_ATTR,
    _RE_BLOCK_TITLE,
    _RE_SINGLE_LINE_COMMENT,
    _RE_CONDITIONAL,
    _RE_HEADING,
    _RE_ADMONITION,
    _RE_BLOCK_ANCHOR,
    _RE_ROLE_ATTR,
    _RE_DLIST,
    _RE_OPEN_BLOCK,
]

# Pre-compiled AsciiDoc inline patterns for stripping (SK-3).
# Inline macros first, then formatting markers (longer delimiters first).
# strip_inline_markers() resolves overlaps by position (leftmost wins),
# so list order is a readability convention, not functional priority.
_ADOC_INLINE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    # link:URL[display text] → display text
    (re.compile(r"link:https?://[^\s\[\]]+\[([^\]]*)\]"), 1),
    # xref:target[display text] → display text
    (re.compile(r"xref:[^\[]+\[([^\]]*)\]"), 1),
    # **unconstrained bold**
    (re.compile(r"\*\*(.+?)\*\*"), 1),
    # *constrained bold*
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), 1),
    # __unconstrained italic__
    (re.compile(r"__(.+?)__"), 1),
    # _constrained italic_
    (re.compile(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)"), 1),
    # `monospace`
    (re.compile(r"`([^`]+)`"), 1),
    # +passthrough+
    (re.compile(r"\+([^+]+)\+"), 1),
    # ^superscript^
    (re.compile(r"\^([^^]+)\^"), 1),
    # ~subscript~
    (re.compile(r"~([^~]+)~"), 1),
]


def _strip_adoc_inline(text: str) -> tuple[str, list[int]]:
    """Strip AsciiDoc inline formatting and build char_map.

    Args:
        text: Raw AsciiDoc text with inline markers.

    Returns:
        Tuple of (clean_text, char_map).
    """
    return strip_inline_markers(text, _ADOC_INLINE_PATTERNS)


class AsciidocParser(BaseParser):
    """Parser for AsciiDoc documents.

    Tries the Ruby Asciidoctor gem first (via subprocess) for full-fidelity
    parsing.  If Asciidoctor is unavailable, falls back to a lightweight
    regex-based parser that covers the most common block types.
    """

    def __init__(self) -> None:
        """Probe for Ruby/Asciidoctor availability."""
        self._asciidoctor_available: Optional[bool] = None

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse AsciiDoc content into blocks.

        Args:
            content: Raw AsciiDoc text.
            filename: Optional source filename.

        Returns:
            ParseResult with typed blocks and metadata.
        """
        logger.debug("AsciidocParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        # Always use the regex parser.  The Asciidoctor AST path
        # produces hierarchical blocks whose start_pos values are not
        # adjusted past markup markers, causing incorrect offset maps
        # in _blocks_to_lite_markers.  The regex parser yields a flat
        # block list with correct offsets.
        return self._parse_with_regex(content, filename)

    # ------------------------------------------------------------------
    # Asciidoctor availability check
    # ------------------------------------------------------------------

    def _is_asciidoctor_available(self) -> bool:
        """Check (once) whether the ``asciidoctor`` gem is installed."""
        if self._asciidoctor_available is not None:
            return self._asciidoctor_available
        try:
            subprocess.run(
                ["ruby", "-e", 'require "asciidoctor"'],
                check=True,
                capture_output=True,
                timeout=5,
            )
            self._asciidoctor_available = True
            logger.info("AsciidocParser: Asciidoctor is available")
        except FileNotFoundError:
            self._asciidoctor_available = False
            logger.info("AsciidocParser: Ruby not found on PATH")
        except subprocess.CalledProcessError:
            self._asciidoctor_available = False
            logger.info("AsciidocParser: asciidoctor gem not installed")
        except subprocess.TimeoutExpired:
            self._asciidoctor_available = False
            logger.info("AsciidocParser: Ruby availability check timed out")
        except OSError as exc:
            self._asciidoctor_available = False
            logger.info("AsciidocParser: OS error checking Ruby: %s", exc)
        return self._asciidoctor_available

    # ------------------------------------------------------------------
    # Asciidoctor subprocess path
    # ------------------------------------------------------------------

    def _parse_with_asciidoctor(
        self, content: str, filename: Optional[str]
    ) -> Optional[ParseResult]:
        """Run Asciidoctor via subprocess and convert the AST JSON to blocks.

        Returns None on any subprocess or parsing failure so the caller
        can fall back to the regex parser.
        """
        input_path: Optional[str] = None
        output_path: Optional[str] = None

        _semaphore.acquire()
        try:
            input_path, output_path = _write_temp_files(content)

            ruby_code = _build_ruby_script(input_path, output_path)
            subprocess.run(
                ["ruby", "-e", ruby_code],
                capture_output=True,
                text=True,
                timeout=_ASCIIDOCTOR_TIMEOUT,
            )

            if not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
                logger.warning("AsciidocParser: Asciidoctor produced no output")
                return None

            with open(output_path, "r", encoding="utf-8") as fh:
                ast_data = json.load(fh)

            return self._ast_to_parse_result(ast_data, filename)

        except subprocess.TimeoutExpired:
            logger.warning("AsciidocParser: Asciidoctor timed out after %ds", _ASCIIDOCTOR_TIMEOUT)
            return None
        except subprocess.CalledProcessError as exc:
            logger.warning("AsciidocParser: Asciidoctor process error: %s", exc)
            return None
        except FileNotFoundError:
            logger.warning("AsciidocParser: Ruby executable not found")
            return None
        except OSError as exc:
            logger.warning("AsciidocParser: OS error running Asciidoctor: %s", exc)
            return None
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.warning("AsciidocParser: Failed to parse Asciidoctor output: %s", exc)
            return None
        finally:
            _cleanup_temp(input_path)
            _cleanup_temp(output_path)
            _semaphore.release()

    def _ast_to_parse_result(
        self, ast: dict, filename: Optional[str]
    ) -> ParseResult:
        """Convert a raw Asciidoctor JSON AST into a ParseResult."""
        blocks: list[Block] = []
        offset = 0
        for child in ast.get("children", []):
            offset = self._ast_node_to_blocks(child, blocks, offset)

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
            metadata={"parser": "asciidoctor", "filename": filename},
        )

    def _ast_node_to_blocks(
        self, node: dict, blocks: list[Block], offset: int, depth: int = 0
    ) -> int:
        """Recursively convert an AST node dict into Block objects."""
        context = node.get("context", "")
        block_type = _context_to_block_type(context)
        text = _node_content(node, context)
        raw = node.get("source", "") or ""
        start = offset
        end = offset + max(len(raw), 1)

        skip = block_type in ("code_block", "listing", "literal")

        # SK-3/SK-4: strip inline markers and build char_map
        char_map: list[int] | None = None
        inline_content = text  # Tier 2: block markers gone, inline preserved
        if not skip and text:
            text, char_map = _strip_adoc_inline(text)

        children_blocks: list[Block] = []
        child_offset = start
        for child in node.get("children", []):
            child_offset = self._ast_node_to_blocks(child, children_blocks, child_offset, depth + 1)

        level = node.get("level", depth)

        blocks.append(Block(
            block_type=block_type,
            content=text,
            raw_content=raw,
            start_pos=start,
            end_pos=max(end, child_offset),
            inline_content=inline_content,
            level=level,
            children=children_blocks,
            should_skip_analysis=skip,
            metadata={"context": context},
            char_map=char_map,
        ))
        return max(end, child_offset)

    # ------------------------------------------------------------------
    # Regex fallback parser
    # ------------------------------------------------------------------

    def _parse_with_regex(
        self, content: str, filename: Optional[str]
    ) -> ParseResult:
        """Parse AsciiDoc with lightweight regex-based heuristics."""
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        lines = normalized.split("\n")
        blocks: list[Block] = []
        idx = 0

        while idx < len(lines):
            idx = self._consume_line(lines, idx, blocks, normalized)

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("AsciidocParser (regex): produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
            metadata={"parser": "regex", "filename": filename},
        )

    def _consume_line(
        self,
        lines: list[str],
        idx: int,
        blocks: list[Block],
        full_text: str,
    ) -> int:
        """Consume one or more lines starting at *idx* and emit a block.

        Returns the next line index to process.
        """
        line = lines[idx]
        stripped = line.strip()

        if not stripped:
            return idx + 1

        start_pos = _char_offset(lines, idx)

        # Heading
        match = _RE_HEADING.match(stripped)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            return _append_block(
                blocks, "heading", text, line, start_pos, idx, lines, level=level
            )

        # Delimited blocks (code, literal, comment, passthrough, sidebar,
        # example, quote, table) — matched via lookup table.
        for pattern, block_type, skip in _DELIMITED_BLOCK_PATTERNS:
            if pattern.match(stripped):
                return self._consume_delimited(
                    lines, idx, stripped, blocks, block_type, start_pos, skip=skip
                )

        # Admonition
        admon = _RE_ADMONITION.match(stripped)
        if admon:
            return self._consume_admonition(lines, idx, admon.group(1), blocks, start_pos)

        # Attribute entry — skip analysis (metadata, not prose)
        attr = _RE_ATTR_ENTRY.match(stripped)
        if attr:
            return _append_block(
                blocks, "attribute_entry", f":{attr.group(1)}: {attr.group(2)}",
                line, start_pos, idx, lines, skip=True,
            )

        # Single-line skip patterns (comments, directives, images, anchors)
        for pattern, block_type in _SKIP_LINE_PATTERNS:
            if pattern.match(stripped):
                return _append_block(
                    blocks, block_type, stripped, line, start_pos, idx, lines, skip=True
                )

        # Definition lists, list items, and block titles
        result = self._try_consume_list_like(
            stripped, line, start_pos, idx, lines, blocks
        )
        if result is not None:
            return result

        # Default: paragraph (accumulate contiguous non-blank lines)
        return self._consume_paragraph(lines, idx, blocks, start_pos)

    def _try_consume_list_like(
        self,
        stripped: str,
        line: str,
        start_pos: int,
        idx: int,
        lines: list[str],
        blocks: list[Block],
    ) -> int | None:
        """Try to consume definition list, list item, or block title.

        Returns the next line index, or None if no pattern matched.
        """
        # Definition list with inline description: "term:: description"
        dlist_inline = _RE_DLIST_INLINE.match(stripped)
        if dlist_inline:
            desc = dlist_inline.group(2).strip()
            return _append_block(
                blocks, "dlist", desc, line, start_pos, idx, lines,
            )

        # Definition list term only: "term::" (description on next line)
        dlist = _RE_DLIST.match(stripped)
        if dlist:
            return _append_block(
                blocks, "dlist", dlist.group(1).strip(), line, start_pos,
                idx, lines, skip=True,
            )

        # Unordered list item
        ulist = _RE_ULIST.match(stripped)
        if ulist:
            level = len(ulist.group(1))
            return _append_block(
                blocks, "list_item_unordered", ulist.group(2), line,
                start_pos, idx, lines, level=level,
            )

        # Ordered list item
        olist = _RE_OLIST.match(stripped)
        if olist:
            level = len(olist.group(1))
            return _append_block(
                blocks, "list_item_ordered", olist.group(2), line,
                start_pos, idx, lines, level=level,
            )

        # AsciiDoc block title (.Prerequisites, .Procedure, etc.)
        block_title = _RE_BLOCK_TITLE.match(stripped)
        if block_title:
            return _append_block(
                blocks, "heading", block_title.group(1).strip(),
                line, start_pos, idx, lines, level=0,
            )

        return None

    def _consume_delimited(
        self,
        lines: list[str],
        idx: int,
        delimiter: str,
        blocks: list[Block],
        block_type: str,
        start_pos: int,
        skip: bool = False,
    ) -> int:
        """Consume a delimited block (code, table) up to the closing delimiter."""
        body_lines: list[str] = [lines[idx]]
        j = idx + 1
        while j < len(lines):
            body_lines.append(lines[j])
            if lines[j].strip() == delimiter:
                j += 1
                break
            j += 1

        raw = "\n".join(body_lines)
        inner = body_lines[1:-1] if len(body_lines) >= 2 else body_lines

        # SK-6: decompose tables into per-cell blocks
        if block_type == "table" and not skip:
            inner_start = start_pos + len(body_lines[0]) + 1
            _decompose_table_cells(inner, blocks, inner_start)
            return j

        # Open blocks: recursively re-parse inner content so that
        # attribute entries, includes, lists, headings, etc. are
        # recognized with their correct block types.
        if block_type == "open_block":
            inner_start = start_pos + len(body_lines[0]) + 1
            _reparse_open_block(inner, blocks, inner_start)
            return j

        content = "\n".join(inner)
        end_pos = start_pos + len(raw)
        blocks.append(Block(
            block_type=block_type,
            content=content,
            raw_content=raw,
            start_pos=start_pos,
            end_pos=end_pos,
            should_skip_analysis=skip,
        ))
        return j

    @staticmethod
    def _consume_admonition(
        lines: list[str],
        idx: int,
        admonition_type: str,
        blocks: list[Block],
        start_pos: int,
    ) -> int:
        """Consume an admonition marker and the following paragraph."""
        body_lines: list[str] = [lines[idx]]
        j = idx + 1
        while j < len(lines) and lines[j].strip():
            body_lines.append(lines[j])
            j += 1
        raw = "\n".join(body_lines)
        # Body excludes the [NOTE] marker line
        body = body_lines[1:]
        # Strip block delimiters (==== / **** lines) from content tiers.
        # These are structure, not prose — content should be plain text.
        leading_skip = 0
        content_body = _strip_admonition_delimiters(body)
        if body and body[0] != (content_body[0] if content_body else ""):
            leading_skip = len(body[0]) + 1  # +1 for newline
        prose = "\n".join(content_body)
        # Tier 2: preserve inline markers before stripping
        inline_content = prose
        # SK-3/SK-4: strip inline markers and build char_map
        content, char_map = _strip_adoc_inline(prose)
        end_pos = start_pos + len(raw)
        # Advance start_pos past the [NOTE] marker line and any leading
        # delimiter so char_map indices align with the source.
        content_start = start_pos + len(body_lines[0]) + 1 + leading_skip
        blocks.append(Block(
            block_type="admonition",
            content=content,
            raw_content=raw,
            start_pos=content_start,
            end_pos=end_pos,
            inline_content=inline_content,
            metadata={"admonition_type": admonition_type.upper()},
            char_map=char_map,
        ))
        return j

    @staticmethod
    def _consume_paragraph(
        lines: list[str],
        idx: int,
        blocks: list[Block],
        start_pos: int,
    ) -> int:
        """Accumulate contiguous non-blank lines into a paragraph block."""
        para_lines: list[str] = []
        j = idx
        while j < len(lines) and lines[j].strip():
            stripped_line = lines[j].strip()
            # Defense: stop at any block-level construct
            if _is_paragraph_break(stripped_line):
                break
            para_lines.append(lines[j])
            j += 1
        raw = "\n".join(para_lines)
        raw_stripped = raw.strip()
        # Tier 2: preserve inline markers before stripping
        inline_content = raw_stripped
        # SK-3/SK-4: strip inline markers and build char_map
        content, char_map = _strip_adoc_inline(raw_stripped)
        end_pos = start_pos + len(raw)
        # Advance start_pos past leading whitespace stripped from raw
        # so char_map indices align with the original source.
        leading_ws = len(raw) - len(raw.lstrip())
        blocks.append(Block(
            block_type="paragraph",
            content=content,
            raw_content=raw,
            start_pos=start_pos + leading_ws,
            end_pos=end_pos,
            inline_content=inline_content,
            char_map=char_map,
        ))
        return j


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _is_paragraph_break(stripped_line: str) -> bool:
    """Return True if *stripped_line* is a block-level construct.

    Used by ``_consume_paragraph()`` to stop accumulating lines when
    a new block-level element is encountered.
    """
    for pattern in _PARAGRAPH_STOP_PATTERNS:
        if pattern.match(stripped_line):
            return True
    return False


def _write_temp_files(content: str) -> tuple[str, str]:
    """Write *content* to a temp .adoc file and create a temp .json output file.

    Returns (input_path, output_path).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".adoc", delete=False
    ) as inp:
        inp.write(content)
        input_path = inp.name

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as out:
        output_path = out.name

    return input_path, output_path


def _cleanup_temp(path: Optional[str]) -> None:
    """Remove a temporary file if it exists."""
    if path is None:
        return
    try:
        os.unlink(path)
    except OSError:
        pass


def _build_ruby_script(input_path: str, output_path: str) -> str:
    """Return a Ruby one-liner that parses AsciiDoc and writes JSON AST."""
    return (
        'require "asciidoctor"; require "json"; '
        f'doc = Asciidoctor.load_file("{input_path}", safe: :safe); '
        "def node_to_hash(n); "
        "h = {context: n.context.to_s, source: (n.respond_to?(:source) ? n.source.to_s : ''), "
        "level: (n.respond_to?(:level) ? n.level : 0), "
        "title: (n.respond_to?(:title) ? n.title.to_s : ''), "
        "children: []}; "
        "if n.respond_to?(:blocks); n.blocks.each{|b| h[:children] << node_to_hash(b)}; end; "
        "h; end; "
        f'File.write("{output_path}", JSON.generate(node_to_hash(doc)))'
    )


def _context_to_block_type(context: str) -> str:
    """Map an Asciidoctor context string to a block_type."""
    mapping: dict[str, str] = {
        "section": "heading",
        "paragraph": "paragraph",
        "listing": "code_block",
        "literal": "code_block",
        "ulist": "list",
        "olist": "list",
        "list_item": "list_item",
        "dlist": "dlist",
        "table": "table",
        "admonition": "admonition",
        "sidebar": "sidebar",
        "quote": "quote",
        "verse": "verse",
        "example": "example",
        "open": "open",
        "preamble": "preamble",
        "image": "image",
        "pass": "paragraph",
        "toc": "comment",
    }
    return mapping.get(context, "paragraph")


def _node_content(node: dict, context: str) -> str:
    """Extract the best text content from a JSON AST node."""
    if context == "list_item":
        return node.get("text", "")
    if context == "section":
        return node.get("title", "")
    if context in ("listing", "literal"):
        return node.get("source", "")
    return node.get("content", "") or node.get("source", "") or node.get("title", "")


def _char_offset(lines: list[str], line_idx: int) -> int:
    """Compute the character offset of the start of *lines[line_idx]*."""
    return sum(len(lines[i]) + 1 for i in range(line_idx))


def _strip_admonition_delimiters(body: list[str]) -> list[str]:
    """Remove leading and trailing block delimiter lines from admonition body.

    AsciiDoc admonition blocks may be enclosed in ``====`` or ``****``
    delimiters.  These are structural markers and should not appear in
    the block's ``content`` or ``inline_content`` tiers.

    Args:
        body: Lines of the admonition body (excluding the ``[NOTE]`` marker).

    Returns:
        Body lines with leading/trailing delimiter lines removed.
    """
    if not body:
        return body
    result = body
    if _RE_BLOCK_DELIM.match(result[0]):
        result = result[1:]
    if result and _RE_BLOCK_DELIM.match(result[-1]):
        result = result[:-1]
    return result


def _append_block(
    blocks: list[Block],
    block_type: str,
    content: str,
    raw: str,
    start_pos: int,
    idx: int,
    lines: list[str],
    level: int = 0,
    skip: bool = False,
) -> int:
    """Create and append a single-line block; return the next line index."""
    original_start = start_pos
    # SK-3/SK-4: strip inline markers for prose blocks (not skip-analysis)
    char_map: list[int] | None = None
    inline_content = content  # Tier 2: block markers gone, inline preserved
    if not skip:
        # Advance start_pos past markers stripped during extraction
        # (e.g., "= " for headings, "* " for list items) so that
        # char_map indices align with the original source.
        content_offset = raw.find(content)
        if content_offset > 0:
            start_pos += content_offset
        content, char_map = _strip_adoc_inline(content)
    end_pos = original_start + len(raw)  # Full block range from original start
    blocks.append(Block(
        block_type=block_type,
        content=content,
        raw_content=raw,
        start_pos=start_pos,
        end_pos=end_pos,
        inline_content=inline_content,
        level=level,
        should_skip_analysis=skip,
        char_map=char_map,
    ))
    return idx + 1


def _reparse_open_block(
    inner_lines: list[str],
    blocks: list[Block],
    inner_start: int,
) -> None:
    """Recursively re-parse lines inside an AsciiDoc open block (``--``).

    Feeds inner lines back through the main ``_consume_line`` dispatch
    so every construct the parser already handles (attribute entries,
    includes, lists, headings, admonitions, nested delimited blocks)
    is recognised with its correct block type and skip flag.

    Args:
        inner_lines: Lines between the opening and closing ``--``.
        blocks: Accumulator for discovered blocks (mutated).
        inner_start: Character offset of the first inner line.
    """
    if not inner_lines:
        return

    # Build a synthetic content string from the inner lines so that
    # _char_offset (which sums line lengths) produces offsets relative
    # to inner_start.  We re-create a parser instance to call
    # _consume_line which needs the full_text for offset computation.
    inner_text = "\n".join(inner_lines)
    parser = AsciidocParser()
    parser._asciidoctor_available = False

    inner_blocks: list[Block] = []
    idx = 0
    while idx < len(inner_lines):
        idx = parser._consume_line(inner_lines, idx, inner_blocks, inner_text)

    # Shift start_pos / end_pos by inner_start so they reference the
    # original document, not the synthetic inner string.
    for blk in inner_blocks:
        blk.start_pos += inner_start
        blk.end_pos += inner_start
    blocks.extend(inner_blocks)


def _decompose_table_cells(
    inner_lines: list[str],
    blocks: list[Block],
    row_start_pos: int,
) -> None:
    """Decompose AsciiDoc table rows into per-cell Block objects (SK-6).

    Splits each row on ``|`` separators and creates a ``table_cell``
    block for every non-empty cell.

    Args:
        inner_lines: Table body lines (between ``|===`` delimiters).
        blocks: Accumulator for discovered blocks (mutated).
        row_start_pos: Character offset of the first inner line.
    """
    pos = row_start_pos
    row_idx = 0
    for line in inner_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("|==="):
            pos += len(line) + 1
            continue
        _decompose_single_row(stripped, blocks, pos, row_idx)
        row_idx += 1
        pos += len(line) + 1


def _decompose_single_row(
    stripped: str,
    blocks: list[Block],
    row_pos: int,
    row_idx: int,
) -> None:
    """Parse cells from a single AsciiDoc table row.

    Args:
        stripped: Stripped row text (e.g. ``"| A | B | C"``).
        blocks: Accumulator for discovered blocks (mutated).
        row_pos: Character offset of this row in the source.
        row_idx: Zero-based row index for metadata.
    """
    parts = stripped.split("|")
    col_idx = 0
    cell_pos = row_pos
    for part in parts:
        if col_idx == 0 and not part.strip():
            cell_pos += len(part) + 1
            col_idx += 1
            continue
        cell_text = part.strip()
        if cell_text:
            clean_text, char_map = _strip_adoc_inline(cell_text)
            blocks.append(Block(
                block_type="table_cell",
                content=clean_text,
                raw_content=part,
                start_pos=cell_pos,
                end_pos=cell_pos + len(part),
                inline_content=cell_text,
                metadata={"row": row_idx, "col": col_idx - 1},
                char_map=char_map,
            ))
        col_idx += 1
        cell_pos += len(part) + 1


