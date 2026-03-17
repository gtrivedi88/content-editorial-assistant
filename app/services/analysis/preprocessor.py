"""Text preprocessing for the Content Editorial Assistant.

Normalizes whitespace, segments sentences via SpaCy, and computes
basic document statistics (word count, paragraph count, syllable
averages) used by downstream analysis and scoring services.

Builds a character-level offset map during markup cleaning so that
spans computed against the cleaned text can be remapped back to
positions in the original (pre-cleanup) text for accurate frontend
highlighting.
"""

import logging
import re
from typing import Any

from app.extensions import get_nlp

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pre-compiled patterns for syllable counting
# ---------------------------------------------------------------------------
_VOWEL_GROUPS_RE = re.compile(r"[aeiouy]+", re.IGNORECASE)
_SILENT_E_RE = re.compile(r"[^aeiou]e$", re.IGNORECASE)
_LE_ENDING_RE = re.compile(r"le$", re.IGNORECASE)
_ED_ENDING_RE = re.compile(r"[^aeiouy]ed$", re.IGNORECASE)
_ES_ENDING_RE = re.compile(r"[^aeiouy]es$", re.IGNORECASE)

# Whitespace normalization (identical to frontend normalization)
_CRLF_RE = re.compile(r"\r\n")
_TAB_RE = re.compile(r"\t")
_MULTI_SPACE_RE = re.compile(r" {2,}")

# ---------------------------------------------------------------------------
# AsciiDoc / markup cleaning patterns
# Ported from legacy/structural_parsing/asciidoc/types.py:112-143
# ---------------------------------------------------------------------------
_MARKUP_SUBS: list[tuple[re.Pattern[str], str]] = [
    # --- Delimited blocks (must come first to remove non-prose content) ---
    # Delete code/listing blocks: ---- ... ----
    (re.compile(r"^-{4,}\s*$.*?^-{4,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # Delete comment blocks: //// ... ////
    (re.compile(r"^/{4,}\s*$.*?^/{4,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # Delete passthrough blocks: ++++ ... ++++
    (re.compile(r"^\+{4,}\s*$.*?^\+{4,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # Delete example blocks: ==== ... ==== (4+ equals, not headings which use 1-6)
    (re.compile(r"^={4,}\s*$.*?^={4,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # Delete sidebar blocks: **** ... ****
    (re.compile(r"^\*{4,}\s*$.*?^\*{4,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # --- Single-line constructs (must come after delimited blocks) ---
    # Delete single-line comments: // text (not block comment delimiters ////)
    (re.compile(r"^[ \t]*//[^/].*$|^[ \t]*//\s*$", re.MULTILINE), ""),
    # Delete conditional directives: ifdef::, ifndef::, ifeval::, endif::
    (re.compile(r"^[ \t]*(?:ifdef|ifndef|ifeval|endif)::[^\n]*$", re.MULTILINE), ""),
    # --- Block-level elements ---
    # Delete standalone block attribute lines: [source,bash], [id="..."], etc.
    (re.compile(r"^\[[^\]]+\]\s*$", re.MULTILINE), ""),
    # Delete block continuation markers (+ alone on a line)
    (re.compile(r"^\+\s*$", re.MULTILINE), ""),
    # Delete attribute entries: :key: value, :!key: unset (metadata, not prose)
    (re.compile(r"^:!?[\w-]+:.*$", re.MULTILINE), ""),
    # Delete image directives: image::path[alt text]
    (re.compile(r"^image::[^\[]*\[[^\]]*\]\s*$", re.MULTILINE), ""),
    # --- Heading and list markers ---
    # Strip heading markers: "= Title" → "Title"
    (re.compile(r"^(={1,3})\s+", re.MULTILINE), ""),
    # Strip block title prefix: ".Title" → "Title" (no space after dot)
    (re.compile(r"^\.(?=\S)", re.MULTILINE), ""),
    # Strip ordered list markers: ". Step text" → "Step text"
    (re.compile(r"^\.\s+(?=\S)", re.MULTILINE), ""),
    # Strip unordered list markers: "* Item text" → "Item text"
    (re.compile(r"^\*\s+", re.MULTILINE), ""),
    # Strip definition list marker: "term::" → "term"
    (re.compile(r"::(?=\s*$)", re.MULTILINE), ""),
    # --- Inline macros ---
    # Strip xref macro: xref:target[display text] → display text
    (re.compile(r"xref:[^\[]+\[([^\]]*)\]"), r"\1"),
    # Strip link macro: link:URL[display text] → display text
    (re.compile(r"link:https?://[^\s\[\]]+\[([^\]]*)\]"), r"\1"),
    # Strip mailto macro: mailto:addr[text] → text
    (re.compile(r"mailto:[^\[]+\[([^\]]*)\]"), r"\1"),
    # --- Inline formatting ---
    # Strip bold: **text** → text
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    # Strip italic (unconstrained): __text__ → text
    (re.compile(r"__(.+?)__"), r"\1"),
    # Replace backtick monospace with placeholder: `command` → placeholder
    # Code references should not be analysed as prose
    (re.compile(r"`([^`]+)`"), "placeholder"),
    # Replace plus monospace with placeholder: +text+ → placeholder
    (re.compile(r"(?<!\w)\+([^+]+)\+(?!\w)"), "placeholder"),
    # Replace attribute references: {prod-short} → placeholder
    (re.compile(r"\{[a-zA-Z][a-zA-Z0-9_-]*\}"), "placeholder"),
    # Replace angle-bracket variable placeholders: <root_disk> → placeholder
    (re.compile(r"<[a-zA-Z_][\w-]*>"), "placeholder"),
    # Delete standalone URLs (not already handled by link macro)
    (re.compile(r"https?://[^\s\[\]]+"), ""),
    # Collapse runs of blank lines to a single blank line
    (re.compile(r"\n{3,}"), "\n\n"),
]


# Post-cleanup: collapse multi-spaces that markup deletion may leave behind
_POST_CLEANUP_RE = re.compile(r" {2,}")


def _apply_sub_tracked(
    text: str,
    offset_map: list[int],
    pattern: re.Pattern[str],
    replacement: str,
) -> tuple[str, list[int]]:
    """Apply a single regex substitution while maintaining the offset map.

    Tracks how each character in the result maps back to positions in
    the original text, enabling span remapping after all substitutions.

    Three replacement modes are supported:
    - Empty string (``""``) — deletion, no characters emitted.
    - Group reference (``r"\\1"``) — characters map to their group positions.
    - Fixed text (e.g. ``"placeholder"``) — characters map to match start.

    Args:
        text: Current text to apply the substitution to.
        offset_map: Current position mapping (length = len(text) + 1).
        pattern: Compiled regex pattern to match.
        replacement: Replacement string.

    Returns:
        Tuple of (new_text, new_offset_map).
    """
    new_chars: list[str] = []
    new_map: list[int] = []
    last_end = 0
    is_group_ref = replacement == r"\1"

    for match in pattern.finditer(text):
        # Copy unchanged characters before the match
        for i in range(last_end, match.start()):
            new_chars.append(text[i])
            new_map.append(offset_map[i])

        if replacement == "":
            pass  # Deletion — no characters to add
        elif is_group_ref:
            # Group extraction — each char maps to its group position
            group_start = match.start(1)
            group_text = match.group(1)
            for i, ch in enumerate(group_text):
                new_chars.append(ch)
                new_map.append(offset_map[group_start + i])
        else:
            # Fixed replacement (e.g., "placeholder", "\n\n")
            orig_start = offset_map[match.start()]
            for ch in replacement:
                new_chars.append(ch)
                new_map.append(orig_start)

        last_end = match.end()

    # Copy remaining characters after the last match
    for i in range(last_end, len(text)):
        new_chars.append(text[i])
        new_map.append(offset_map[i])

    # End sentinel — maps to the original end position
    new_map.append(offset_map[len(text)])

    return "".join(new_chars), new_map


# Markdown-specific cleanup patterns (lighter than AsciiDoc)
_MARKDOWN_SUBS: list[tuple[re.Pattern[str], str]] = [
    # Delete fenced code blocks: ``` ... ```
    (re.compile(r"^`{3,}[^\n]*$.*?^`{3,}\s*$", re.MULTILINE | re.DOTALL), ""),
    # Strip heading markers: "# Title" → "Title"
    (re.compile(r"^#{1,6}\s+", re.MULTILINE), ""),
    # Strip bold: **text** → text
    (re.compile(r"\*\*(.+?)\*\*"), r"\1"),
    # Strip italic: *text* → text (single asterisk)
    (re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)"), r"\1"),
    # Replace backtick code with placeholder: `code` → placeholder
    (re.compile(r"`([^`]+)`"), "placeholder"),
    # Strip inline links: [text](url) → text
    (re.compile(r"\[([^\]]+)\]\([^\)]+\)"), r"\1"),
    # Delete standalone URLs
    (re.compile(r"https?://[^\s\[\]]+"), ""),
    # Collapse runs of blank lines
    (re.compile(r"\n{3,}"), "\n\n"),
]


def _clean_markup_with_mapping(
    text: str, file_type: str | None = None,
) -> tuple[str, list[int]]:
    """Strip markup while building a character offset map.

    Applies format-specific substitution patterns based on
    ``file_type``, tracking a position-level mapping from each
    character in the cleaned text back to the input text.

    Args:
        text: Normalized input text (after whitespace normalization).
        file_type: File format (``"asciidoc"``, ``"markdown"``, etc.).
            Falls back to AsciiDoc patterns when ``None``.

    Returns:
        Tuple of (cleaned_text, offset_map) where ``offset_map[i]`` is
        the position in the input text corresponding to position *i* in
        the cleaned text. The map has length ``len(cleaned_text) + 1``;
        the final entry is a sentinel mapping to the input text length.
    """
    offset_map = list(range(len(text) + 1))
    current = text

    subs = _select_cleanup_patterns(file_type)
    for pattern, replacement in subs:
        current, offset_map = _apply_sub_tracked(
            current, offset_map, pattern, replacement,
        )

    # Collapse multi-spaces that may result from deletions
    current, offset_map = _apply_sub_tracked(
        current, offset_map, _POST_CLEANUP_RE, " ",
    )

    return current, offset_map


def _select_cleanup_patterns(
    file_type: str | None,
) -> list[tuple[re.Pattern[str], str]]:
    """Return markup cleanup patterns appropriate for the file format.

    Args:
        file_type: File format string or None.

    Returns:
        List of (pattern, replacement) tuples.
    """
    if file_type == "markdown":
        return _MARKDOWN_SUBS
    if file_type in ("plaintext", "html", "dita", "xml", "docx"):
        return []
    # Default: AsciiDoc patterns (also used for paste path with no file_type)
    return _MARKUP_SUBS


# ---------------------------------------------------------------------------
# Lite-markers: Markdown representation for LLM analysis
# ---------------------------------------------------------------------------

# Markdown prefix/suffix by block_type
_MARKDOWN_WRAPPERS: dict[str, tuple[str, str]] = {
    "heading": ("", ""),  # level-dependent, handled in _get_markdown_wrappers
    "list_item_ordered": ("1. ", ""),
    "list_item_unordered": ("- ", ""),
    "list_item": ("- ", ""),
    "code_block": ("```\n", "\n```"),
    "listing": ("```\n", "\n```"),
    "literal": ("```\n", "\n```"),
    "admonition": ("> **Note:** ", ""),
    "blockquote": ("> ", ""),
    "quote": ("> ", ""),
    "table_cell": ("| ", " "),
    "dlist": ("- **Definition:** ", ""),
}


def _get_markdown_wrappers(
    block: object, olist_number: int = 0,
) -> tuple[str, str]:
    """Return Markdown prefix and suffix for a block.

    Headings use level-dependent ``#`` prefixes.  Ordered list items
    use sequential numbering when *olist_number* > 0 so the LLM sees
    correct step numbers (``1. 2. 3.``) instead of all ``1.``.

    Args:
        block: A Block dataclass instance.
        olist_number: Sequential position for ordered list items.
            Pass 0 to use the default ``1.`` from the wrapper table.

    Returns:
        Tuple of (prefix, suffix) strings.
    """
    if block.block_type == "heading":
        if block.level == 0:
            # AsciiDoc block titles (.Prerequisites, .Procedure) are labels,
            # not structural headings.  Render as bold to avoid the LLM
            # misinterpreting them as heading-level errors.
            return "**", "**"
        level = max(1, min(block.level, 6))
        return "#" * level + " ", ""
    if block.block_type == "list_item_ordered" and olist_number > 0:
        return f"{olist_number}. ", ""
    return _MARKDOWN_WRAPPERS.get(block.block_type, ("", ""))


def _block_to_markdown(block: object) -> str:
    """Convert a single Block to its Markdown representation.

    Uses ``block.inline_content`` (Tier 2) so the LLM can see
    backticks, bold, and italic markers — matching the contract
    used by ``_blocks_to_lite_markers()``.

    Args:
        block: A Block dataclass instance.

    Returns:
        Markdown-formatted string for this block.
    """
    prefix, suffix = _get_markdown_wrappers(block)
    text = block.inline_content if block.inline_content else block.content
    return f"{prefix}{text}{suffix}"


def _flatten_blocks(blocks: list) -> list:
    """Recursively flatten a hierarchical block tree into a linear list.

    The AsciiDoc parser produces a tree where sections contain nested
    children (paragraphs, list items, code blocks, etc.).  This helper
    walks the tree depth-first and returns every block in document
    order so that ``_blocks_to_lite_markers`` processes the full
    document content rather than only top-level sections.

    Args:
        blocks: Top-level block list (may contain nested children).

    Returns:
        Flat list of all blocks in depth-first document order.
    """
    flat: list = []
    for block in blocks:
        flat.append(block)
        if hasattr(block, "children") and block.children:
            flat.extend(_flatten_blocks(block.children))
    return flat


def _blocks_to_lite_markers(
    blocks: list,
    original_text: str,
) -> tuple[str, list[int]]:
    """Convert parsed blocks to Markdown with character-level offset tracking.

    Each character in the returned Markdown string has a corresponding
    entry in ``offset_map`` pointing to its position in
    ``original_text``.  Prefix/suffix characters (Markdown syntax) map
    to the block's ``start_pos`` or ``end_pos`` respectively.

    Args:
        blocks: List of Block dataclass instances.
        original_text: The whitespace-normalized original document text.

    Returns:
        Tuple of (markdown_text, offset_map) where ``offset_map[i]``
        is the position in ``original_text`` for character *i* in
        ``markdown_text``. The map has length ``len(markdown_text) + 1``.
    """
    result_chars: list[str] = []
    offset_map: list[int] = []
    orig_len = len(original_text)
    included = 0
    skipped = 0

    flat_blocks = _flatten_blocks(blocks)

    olist_counter = 0  # Sequential counter for ordered list items

    for block in flat_blocks:
        # Skip non-analysable blocks except code_block (kept for LLM context)
        if block.should_skip_analysis and block.block_type != "code_block":
            skipped += 1
            continue
        if not block.content and block.block_type != "code_block":
            skipped += 1
            continue
        included += 1

        # Track sequential numbering for ordered list items.
        # Only reset the counter on structural breaks (headings, different
        # list types).  Code blocks and paragraphs between ordered list
        # items are typically AsciiDoc `+` continuations, not list-ending
        # structures.
        if block.block_type == "list_item_ordered":
            olist_counter += 1
        elif block.block_type in (
            "heading", "list_item_unordered", "list_item",
        ):
            olist_counter = 0

        prefix, suffix = _get_markdown_wrappers(block, olist_counter)

        # Prefix chars map to block.start_pos
        for ch in prefix:
            result_chars.append(ch)
            offset_map.append(min(block.start_pos, orig_len))

        # Content chars use char_map for exact mapping when available
        _append_content_chars(
            block, result_chars, offset_map, orig_len,
        )

        # Suffix chars map to block.end_pos
        for ch in suffix:
            result_chars.append(ch)
            offset_map.append(min(block.end_pos, orig_len))

        # Block separator
        result_chars.extend(["\n", "\n"])
        offset_map.extend([
            min(block.end_pos, orig_len),
            min(block.end_pos, orig_len),
        ])

    # End sentinel
    offset_map.append(orig_len)

    logger.debug(
        "lite_markers: %d top-level, %d flattened, "
        "%d included, %d skipped, result len=%d",
        len(blocks), len(flat_blocks), included, skipped,
        len(result_chars),
    )
    return "".join(result_chars), offset_map


def _append_content_chars(
    block: object,
    result_chars: list[str],
    offset_map: list[int],
    orig_len: int,
) -> None:
    """Append inline_content characters and their offset mappings.

    Uses ``block.inline_content`` (Tier 2 — block markers stripped,
    inline formatting preserved) so the LLM can see backticks, bold,
    and italic markers.  Each ``inline_content[i]`` maps directly to
    ``block.start_pos + i`` in the original text (identity mapping).

    Args:
        block: A Block dataclass instance.
        result_chars: Accumulator for result characters (mutated).
        offset_map: Accumulator for offset entries (mutated).
        orig_len: Length of the original text (for clamping).
    """
    content = block.inline_content
    for i, ch in enumerate(content):
        result_chars.append(ch)
        mapped = block.start_pos + i
        offset_map.append(min(mapped, orig_len))


def preprocess(
    text: str,
    blocks: list | None = None,
    file_type: str | None = None,
) -> dict[str, Any]:
    """Preprocess raw text for analysis.

    Cleans AsciiDoc/markup syntax, normalizes whitespace, splits into
    sentences via SpaCy, and computes document-level statistics used by
    the scoring and analysis pipelines.

    When ``blocks`` are provided (from a parser), also builds a
    lite_markers Markdown representation for LLM analysis with a
    character-level offset map back to the original text.

    Args:
        text: Raw input text (may contain Windows line endings and tabs).
        blocks: Optional list of Block objects from a parser.
        file_type: Original file format string (e.g. ``"asciidoc"``).

    Returns:
        Dictionary with keys including ``text``, ``original_text``,
        ``offset_map``, ``lite_markers``, ``lite_markers_offset_map``,
        ``blocks``, ``sentences``, ``spacy_doc``, and statistics.
    """
    original_normalized = _normalize_whitespace(text)

    cleaned, offset_map = _clean_markup_with_mapping(
        original_normalized, file_type=file_type,
    )

    nlp = get_nlp()
    doc = nlp(cleaned)

    sentences = _extract_sentences(doc)
    words = _extract_words(doc)
    word_count = len(words)
    paragraph_count = _count_paragraphs(cleaned)

    unique_words = len({w.lower() for w in words}) if words else 0
    vocabulary_diversity = round(
        unique_words / word_count if word_count > 0 else 0.0, 4,
    )

    avg_words = _safe_divide(word_count, len(sentences))
    avg_syllables = _compute_avg_syllables(words)

    # Build lite_markers from blocks if available
    if blocks:
        lite_markers, lm_offset_map = _blocks_to_lite_markers(
            blocks, original_normalized,
        )
    else:
        lite_markers = cleaned
        lm_offset_map = list(offset_map)

    logger.debug(
        "preprocessor: original len=%d, cleaned len=%d, "
        "offset_map len=%d, lite_markers len=%d, sentences=%d",
        len(original_normalized), len(cleaned), len(offset_map),
        len(lite_markers), len(sentences),
    )
    if offset_map:
        logger.debug(
            "preprocessor offset_map: first5=%s last5=%s",
            offset_map[:5], offset_map[-5:],
        )
    logger.debug("preprocessor cleaned[:200]=%r", cleaned[:200])
    logger.debug("preprocessor original[:200]=%r", original_normalized[:200])

    return {
        "text": cleaned,
        "original_text": original_normalized,
        "offset_map": offset_map,
        "lite_markers": lite_markers,
        "lite_markers_offset_map": lm_offset_map,
        "blocks": blocks or [],
        "file_type": file_type,
        "sentences": sentences,
        "spacy_doc": doc,
        "word_count": word_count,
        "char_count": len(cleaned),
        "sentence_count": len(sentences),
        "paragraph_count": paragraph_count,
        "avg_words_per_sentence": round(avg_words, 2),
        "avg_syllables_per_word": round(avg_syllables, 2),
        "unique_words": unique_words,
        "vocabulary_diversity": vocabulary_diversity,
        "detected_content_type": _detect_content_type(text),
    }


# ---------------------------------------------------------------------------
# Content-type detection — 4-tier weighted multi-type scoring engine
# ---------------------------------------------------------------------------

# Tier 1: Metadata — instant win (AsciiDoc attribute)
_CONTENT_TYPE_ATTR_RE = re.compile(
    r":_mod-docs-content-type:\s*(CONCEPT|PROCEDURE|REFERENCE|ASSEMBLY)",
    re.IGNORECASE,
)

# Tier 2: Structural markers — high confidence (+20 each)
# Optional dot prefix handles both AsciiDoc (.Procedure) and plain text (Procedure).
# Trap 3 fix: \s*$ handles non-breaking spaces from browser paste.
_STRUCT_PROCEDURE_RE = re.compile(
    r"^(?:\.)?(Procedure|Prerequisites|Verification|Troubleshooting)\s*$",
    re.MULTILINE,
)
_STRUCT_REFERENCE_RE = re.compile(
    r"^(?:\.)?(Additional resources|Related information)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Tier 3: Lexical title guard — medium confidence (+10)
# (?:=\s+)? handles both AsciiDoc headings and plain-text headings.
_CONCEPT_TITLE_RE = re.compile(
    r"^(?:=\s+)?(About|Understanding|Architecture|Introduction)\b",
    re.MULTILINE | re.IGNORECASE,
)
_PROCEDURE_TITLE_RE = re.compile(
    r"^(?:=\s+)?(Configuring|Creating|Installing|Managing|Updating|"
    r"Using|Adding|Removing|Deploying|Enabling|Setting)\b",
    re.MULTILINE | re.IGNORECASE,
)
_REFERENCE_TITLE_RE = re.compile(
    r"^(?:=\s+)?.*(?:Reference|Parameters|Properties|Commands|"
    r"Variables|Attributes)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# Tier 4: Content shape — low confidence (+5)
_NUMBERED_STEPS_RE = re.compile(r"^\d+\.\s+[A-Z]", re.MULTILINE)
_IMPERATIVE_STEPS_RE = re.compile(
    r"^\d+\.\s+(?:Click|Select|Enter|Run|Type|Open|Navigate|Configure|"
    r"Set|Add|Remove|Create|Install|Enable|Disable|Verify|Check|Ensure)\b",
    re.MULTILINE,
)
_OPTIONAL_PREFIX_RE = re.compile(r"^Optional:", re.MULTILINE)
_TABLE_MARKER_RE = re.compile(r"^\|===", re.MULTILINE)
_DEF_LIST_RE = re.compile(r"::\s*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_content_type(text: str) -> str | None:
    """Detect modular documentation content type via 4-tier weighted scoring.

    Uses a multi-type scoring dictionary that tracks points for procedure,
    concept, and reference simultaneously.  The type with the highest score
    wins, provided it meets the minimum threshold of 5 points.

    Tiers (highest to lowest confidence):
        1. Metadata — ``:_mod-docs-content-type:`` attribute (instant win)
        2. Structural markers — standalone headings like Procedure (+20 each)
        3. Lexical title guard — naming conventions like gerund titles (+10)
        4. Content shape — numbered steps, tables, definition lists (+5)

    Args:
        text: Raw input text (before markup cleaning).

    Returns:
        Detected content type string, or None if ambiguous.
    """
    # Tier 1: explicit AsciiDoc attribute → instant win
    attr_match = _CONTENT_TYPE_ATTR_RE.search(text)
    if attr_match:
        return attr_match.group(1).lower()

    # Tiers 2-4: multi-type scoring
    scores: dict[str, int] = {"procedure": 0, "concept": 0, "reference": 0}

    # Tier 2: structural markers (+20 each)
    _score_structural_markers(text, scores)

    # Tier 3: lexical title guard (+10)
    _score_title_patterns(text, scores)

    # Tier 4: content shape (+5)
    _score_content_shape(text, scores)

    # Winner takes all — must meet threshold of 5
    best = max(scores, key=scores.get)
    if scores[best] >= 5:
        return best

    return None


def _score_structural_markers(text: str, scores: dict[str, int]) -> None:
    """Score Tier 2 structural markers into the scores dict.

    Args:
        text: Raw input text.
        scores: Mutable scores dictionary to update.
    """
    proc_markers = _STRUCT_PROCEDURE_RE.findall(text)
    if proc_markers:
        marker_lower = {m.lower() for m in proc_markers}
        if "procedure" in marker_lower:
            scores["procedure"] += 20
        if "prerequisites" in marker_lower:
            scores["procedure"] += 20
        if "verification" in marker_lower:
            scores["procedure"] += 20
        if "troubleshooting" in marker_lower:
            scores["procedure"] += 20

    if _STRUCT_REFERENCE_RE.search(text):
        scores["reference"] += 20


def _score_title_patterns(text: str, scores: dict[str, int]) -> None:
    """Score Tier 3 lexical title patterns into the scores dict.

    Args:
        text: Raw input text.
        scores: Mutable scores dictionary to update.
    """
    if _CONCEPT_TITLE_RE.search(text):
        scores["concept"] += 10
    if _PROCEDURE_TITLE_RE.search(text):
        scores["procedure"] += 10
    if _REFERENCE_TITLE_RE.search(text):
        scores["reference"] += 10


def _score_content_shape(text: str, scores: dict[str, int]) -> None:
    """Score Tier 4 content shape signals into the scores dict.

    Args:
        text: Raw input text.
        scores: Mutable scores dictionary to update.
    """
    numbered = len(_NUMBERED_STEPS_RE.findall(text))
    if numbered >= 3:
        scores["procedure"] += 5
    imperative = len(_IMPERATIVE_STEPS_RE.findall(text))
    if imperative >= 2:
        scores["procedure"] += 5
    if _OPTIONAL_PREFIX_RE.search(text):
        scores["procedure"] += 5

    tables = len(_TABLE_MARKER_RE.findall(text))
    def_lists = len(_DEF_LIST_RE.findall(text))
    if tables > 0 or def_lists > 2:
        scores["reference"] += 5


def _clean_markup(text: str) -> str:
    """Strip AsciiDoc and markup syntax from text before analysis.

    Applies the compiled substitution patterns from ``_MARKUP_SUBS``
    sequentially. This ensures rules see only prose content, not
    structural directives, URLs, attribute references, or inline
    formatting syntax.

    Ported from legacy/structural_parsing/asciidoc/types.py:112-143.

    Args:
        text: Raw input text (may contain AsciiDoc markup).

    Returns:
        Text with markup syntax stripped; prose content preserved.
    """
    result = text
    for pattern, replacement in _MARKUP_SUBS:
        result = pattern.sub(replacement, result)
    return result


def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace to match frontend normalization.

    Converts CRLF to LF, tabs to single space, and collapses
    consecutive spaces into one.

    Args:
        text: Raw input text.

    Returns:
        Text with normalized whitespace.
    """
    result = _CRLF_RE.sub("\n", text)
    result = _TAB_RE.sub(" ", result)
    result = _MULTI_SPACE_RE.sub(" ", result)
    return result


def _extract_sentences(doc: Any) -> list[str]:
    """Extract sentence strings from a SpaCy Doc.

    Post-processes SpaCy output by splitting any sentence that spans
    a newline boundary, ensuring headings, list items, and paragraphs
    separated by newlines become distinct sentences.

    Args:
        doc: SpaCy Doc object with sentence segmentation.

    Returns:
        List of non-empty sentence strings.
    """
    sentences: list[str] = []
    for sent in doc.sents:
        raw = sent.text
        if "\n" in raw:
            for part in raw.split("\n"):
                stripped = part.strip()
                if stripped:
                    sentences.append(stripped)
        else:
            stripped = raw.strip()
            if stripped:
                sentences.append(stripped)
    return sentences if sentences else [""]


def _extract_words(doc: Any) -> list[str]:
    """Extract word tokens from a SpaCy Doc, excluding punctuation and whitespace.

    Args:
        doc: SpaCy Doc object.

    Returns:
        List of word strings.
    """
    return [
        token.text for token in doc
        if not token.is_punct and not token.is_space
    ]


def _count_paragraphs(text: str) -> int:
    """Count paragraphs by splitting on double newlines.

    Args:
        text: Normalized text.

    Returns:
        Number of non-empty paragraphs (minimum 1).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return max(len(paragraphs), 1)


def _safe_divide(numerator: float, denominator: int) -> float:
    """Divide safely, returning 0.0 when the denominator is zero.

    Args:
        numerator: The dividend.
        denominator: The divisor.

    Returns:
        Result of division, or 0.0 if denominator is zero.
    """
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _compute_avg_syllables(words: list[str]) -> float:
    """Compute the average syllable count across a list of words.

    Args:
        words: List of word strings.

    Returns:
        Mean syllables per word, or 0.0 if the list is empty.
    """
    if not words:
        return 0.0
    total = sum(count_syllables(w) for w in words)
    return total / len(words)


def count_syllables(word: str) -> int:
    """Estimate the syllable count of a single English word.

    Uses a regex-based heuristic: counts vowel groups and applies
    adjustments for silent-e, -le endings, and -ed/-es suffixes.

    Args:
        word: A single English word (no spaces).

    Returns:
        Estimated syllable count (minimum 1).
    """
    word = word.lower().strip()
    if not word:
        return 1

    # Count vowel groups
    vowel_groups = _VOWEL_GROUPS_RE.findall(word)
    count = len(vowel_groups)

    # Adjust for silent-e at end (e.g., "make" -> 1 syllable, not 2)
    if _SILENT_E_RE.search(word) and not _LE_ENDING_RE.search(word):
        count -= 1

    # Adjust for -ed ending that does not add a syllable (e.g., "walked")
    if _ED_ENDING_RE.search(word) and len(word) > 3:
        count -= 1

    # Adjust for -es ending that does not add a syllable (e.g., "makes")
    if _ES_ENDING_RE.search(word) and len(word) > 3:
        count -= 1

    return max(count, 1)
