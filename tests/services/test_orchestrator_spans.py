"""Tests for span-resolution functions in the analysis orchestrator.

Covers _find_flagged_in_text (multi-strategy span finder),
_compute_content_code_ranges (backtick range mapping),
_strip_lite_markers / _strip_markdown_inline (Markdown prefix/inline removal),
_resolve_llm_span_fuzzy (fuzzy matching with threshold and min-length),
and sentinel [-1, -1] handling for failed remaps.

These are pure functions (no Flask app context needed), imported directly
from the orchestrator module.
"""

import uuid

import pytest

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse
from app.services.analysis.orchestrator import (
    _compute_bold_code_ranges,
    _compute_content_code_ranges,
    _find_bold_code_in_inline,
    _find_flagged_in_text,
    _map_ranges_to_content,
    _resolve_llm_span_fuzzy,
    _strip_lite_markers,
    _strip_markdown_inline,
)


# ---------------------------------------------------------------------------
# Helper: create a minimal IssueResponse for span-resolution tests
# ---------------------------------------------------------------------------


def _make_issue(
    flagged_text: str = "",
    span: list[int] | None = None,
    sentence: str = "",
) -> IssueResponse:
    """Build a minimal IssueResponse for testing span resolution.

    Args:
        flagged_text: The text that the rule flagged.
        span: Starting span — defaults to [0, 0] (unresolved).
        sentence: Sentence context for the issue.

    Returns:
        An IssueResponse suitable for span-resolution function inputs.
    """
    return IssueResponse(
        id=str(uuid.uuid4()),
        source="llm_granular",
        category=IssueCategory.STYLE,
        rule_name="llm_style",
        flagged_text=flagged_text,
        message="Test issue message.",
        suggestions=[],
        severity=IssueSeverity.MEDIUM,
        sentence=sentence,
        sentence_index=0,
        span=span if span is not None else [0, 0],
    )


# ===================================================================
# _find_flagged_in_text — multi-strategy span finder
# ===================================================================


class TestFindFlaggedInText:
    """Tests for the _find_flagged_in_text multi-strategy span finder."""

    def test_exact_match(self) -> None:
        """Strategy 1: exact substring match returns correct span."""
        text = "The server was restarted by the administrator."
        result = _find_flagged_in_text(text, "was restarted")
        assert result is not None
        start, end, matched = result
        assert start == 11
        assert end == 24
        assert matched == "was restarted"

    def test_case_insensitive_match(self) -> None:
        """Strategy 2: case-insensitive match finds text with different casing."""
        text = "Use the OpenShift CLI to manage resources."
        result = _find_flagged_in_text(text, "openshift cli")
        assert result is not None
        start, end, matched = result
        assert start == 8
        assert end == 21
        # matched text is taken from the original text at found position
        assert matched == "OpenShift CLI"

    def test_position_hint_narrows_search(self) -> None:
        """search_from / search_to restrict the search region."""
        text = "foo bar baz foo bar baz"
        # Without restriction, finds first occurrence at index 0
        result_any = _find_flagged_in_text(text, "foo")
        assert result_any is not None
        assert result_any[0] == 0

        # With search_from=4, skips first "foo" and finds second at 12
        result_hint = _find_flagged_in_text(text, "foo", search_from=4)
        assert result_hint is not None
        assert result_hint[0] == 12

    def test_search_to_excludes_late_match(self) -> None:
        """search_to prevents matching text beyond the search window."""
        text = "alpha beta gamma delta alpha"
        # "alpha" at index 0 is within [0, 10), but the second "alpha" at 22 is not
        result = _find_flagged_in_text(text, "alpha", search_from=10, search_to=20)
        assert result is None

    def test_lite_marker_stripping(self) -> None:
        """Strategy 3: strips Markdown heading prefix from flagged text."""
        text = "Install the packages before proceeding."
        flagged_with_prefix = "## Install the packages"
        result = _find_flagged_in_text(text, flagged_with_prefix)
        assert result is not None
        assert result[2] == "Install the packages"

    def test_not_found_returns_none(self) -> None:
        """Returns None when no strategy finds the text."""
        text = "The quick brown fox jumps over the lazy dog."
        result = _find_flagged_in_text(text, "nonexistent phrase xyz")
        assert result is None


# ===================================================================
# _compute_content_code_ranges — backtick range mapping
# ===================================================================


class TestComputeContentCodeRanges:
    """Tests for _compute_content_code_ranges backtick range mapping."""

    def test_single_backtick_range(self) -> None:
        """Single backtick-delimited range is found correctly."""
        inline = "Run the `oc get pods` command."
        ranges = _compute_content_code_ranges(inline, None)
        assert len(ranges) == 1
        # `oc get pods` starts at index 8, ends at 21 (including backticks)
        start, end = ranges[0]
        assert inline[start:end] == "`oc get pods`"

    def test_multiple_backtick_ranges(self) -> None:
        """Multiple backtick-delimited ranges are all detected."""
        inline = "Use `curl` or `wget` to download."
        ranges = _compute_content_code_ranges(inline, None)
        assert len(ranges) == 2
        assert inline[ranges[0][0]:ranges[0][1]] == "`curl`"
        assert inline[ranges[1][0]:ranges[1][1]] == "`wget`"

    def test_no_backticks_returns_empty(self) -> None:
        """Text with no backticks produces an empty range list."""
        inline = "No code references here."
        ranges = _compute_content_code_ranges(inline, None)
        assert ranges == []

    def test_empty_inline_content(self) -> None:
        """Empty string returns an empty range list."""
        ranges = _compute_content_code_ranges("", None)
        assert ranges == []

    def test_identity_mapping_no_char_map(self) -> None:
        """Without char_map, raw ranges are returned as-is (identity)."""
        inline = "prefix `code` suffix"
        ranges = _compute_content_code_ranges(inline, None)
        assert len(ranges) == 1
        s, e = ranges[0]
        assert inline[s:e] == "`code`"

    def test_with_char_map(self) -> None:
        """With a char_map, ranges are translated to content coordinates.

        Simulates inline_content = "**bold** `code`" where the parser
        stripped "**" markers, producing content = "bold code" with
        char_map mapping each content position to inline_content position.
        """
        # inline_content: "**bold** `code`"
        # content (stripped): "bold code"
        # char_map: content[0]->2, [1]->3, [2]->4, [3]->5,
        #           content[4]->7 (space after **),  wait — let's be precise
        #
        # inline =  * * b o l d * *   ` c o d e `
        # index  =  0 1 2 3 4 5 6 7 8 9 10 11 12 13
        # content = b o l d   c o d e
        # index  =  0 1 2 3 4 5 6 7 8
        # char_map = [2, 3, 4, 5, 8, 10, 11, 12, 13]
        #   (content[0] -> inline[2]='b', content[4] -> inline[8]=' ',
        #    content[5] -> inline[10]='c')
        inline_content = "**bold** `code`"
        char_map = [2, 3, 4, 5, 8, 10, 11, 12, 13]
        ranges = _compute_content_code_ranges(inline_content, char_map)
        # The backtick range in inline_content is [9, 15) for "`code`"
        # char_map positions 5..8 map to inline positions 10,11,12,13
        # which are all inside the backtick range [9,15).
        # But char_map[4] = 8 which is the space — not inside backticks.
        # So the code range in content coordinates should be (5, 9).
        assert len(ranges) == 1
        assert ranges[0] == (5, 9)


# ===================================================================
# _strip_lite_markers — Markdown prefix removal
# ===================================================================


class TestStripLiteMarkers:
    """Tests for _strip_lite_markers Markdown prefix removal."""

    def test_unordered_list_marker(self) -> None:
        """Strips '- ' prefix from unordered list items."""
        assert _strip_lite_markers("- Install the package.") == "Install the package."

    def test_ordered_list_marker(self) -> None:
        """Strips '1. ' prefix from ordered list items."""
        assert _strip_lite_markers("1. Run the command.") == "Run the command."

    def test_blockquote_marker(self) -> None:
        """Strips '> ' prefix from blockquotes."""
        assert _strip_lite_markers("> This is a note.") == "This is a note."

    def test_heading_marker(self) -> None:
        """Strips '## ' prefix from headings."""
        assert _strip_lite_markers("## Prerequisites") == "Prerequisites"

    def test_triple_heading_marker(self) -> None:
        """Strips '### ' prefix from level-3 headings."""
        assert _strip_lite_markers("### Configuration options") == "Configuration options"

    def test_no_marker_unchanged(self) -> None:
        """Text without markers is returned unchanged."""
        assert _strip_lite_markers("Plain text content.") == "Plain text content."


# ===================================================================
# _strip_markdown_inline — inline formatting removal
# ===================================================================


class TestStripMarkdownInline:
    """Tests for _strip_markdown_inline Markdown inline formatting removal."""

    def test_backtick_removal(self) -> None:
        """Single backticks are removed from text."""
        assert _strip_markdown_inline("`curl`") == "curl"

    def test_bold_removal(self) -> None:
        """Double asterisks (bold) are removed from text."""
        assert _strip_markdown_inline("**important**") == "important"

    def test_mixed_inline_removal(self) -> None:
        """Both backticks and bold markers are removed together."""
        result = _strip_markdown_inline("Use `oc` to run **commands**")
        assert result == "Use oc to run commands"

    def test_no_markers_unchanged(self) -> None:
        """Text without inline markers is returned unchanged."""
        assert _strip_markdown_inline("plain text") == "plain text"


# ===================================================================
# _resolve_llm_span_fuzzy — fuzzy matching
# ===================================================================


class TestResolveLlmSpanFuzzy:
    """Tests for fuzzy span matching with threshold and minimum length."""

    def test_short_string_rejected(self) -> None:
        """A 5-char string 'apply' must NOT fuzzy-match (min length = 8)."""
        text = "You should apply the patch before restarting."
        issue = _make_issue(flagged_text="apply")
        _resolve_llm_span_fuzzy(issue, text)
        # Span should remain [0, 0] — not matched
        assert issue.span == [0, 0]

    def test_long_string_high_similarity_accepted(self) -> None:
        """A 10+ char string with >0.85 similarity should match.

        Source has 'utilizess' (typo), LLM reports 'utilizes'.
        SequenceMatcher('utilizess', 'utilizes ') should exceed 0.85.
        """
        text = "We should not utilizess this approach in production code."
        issue = _make_issue(flagged_text="utilizes t")
        # "utilizes t" (10 chars) vs "utilizess " (10 chars)
        # high similarity, should fuzzy-match
        _resolve_llm_span_fuzzy(issue, text)
        # Should have found a match — span is no longer [0, 0]
        assert issue.span != [0, 0]
        assert issue.span[0] >= 0
        assert issue.span[1] > issue.span[0]

    def test_low_similarity_rejected(self) -> None:
        """Strings with similarity below 0.85 are rejected."""
        text = "The container orchestration platform manages workloads."
        # "completely different" has very low similarity to any 19-char window
        issue = _make_issue(flagged_text="completely different")
        _resolve_llm_span_fuzzy(issue, text)
        assert issue.span == [0, 0]


# ===================================================================
# Sentinel [-1, -1] handling for failed remaps
# ===================================================================


class TestSentinelHandling:
    """Tests verifying that failed remaps produce [-1, -1] sentinel spans."""

    def test_remap_failure_produces_sentinel(self) -> None:
        """_remap_single_issue sets [-1, -1] when text search fails.

        Import and call _remap_single_issue directly, giving it
        an offset_map and original_text where the flagged text cannot
        be found.
        """
        from app.services.analysis.orchestrator import _remap_single_issue

        issue = _make_issue(
            flagged_text="nonexistent text that does not appear anywhere",
            span=[5, 50],
        )
        # offset_map: identity mapping of length 100
        offset_map = list(range(100))
        original_text = "This is a completely different document with unrelated content."

        _remap_single_issue(issue, offset_map, original_text, len(offset_map), len(original_text))
        assert issue.span == [-1, -1]

    def test_sentinel_filtered_by_validate(self) -> None:
        """_validate_llm_issues drops issues with [-1, -1] sentinel spans."""
        from app.services.analysis.orchestrator import _validate_llm_issues

        good_issue = _make_issue(flagged_text="some text", span=[10, 19])
        sentinel_issue = _make_issue(flagged_text="lost text", span=[-1, -1])
        zero_span_issue = _make_issue(flagged_text="hallucinated", span=[0, 0])

        result = _validate_llm_issues([good_issue, sentinel_issue, zero_span_issue])
        # Only the good_issue should survive; sentinel and [0,0] with flagged_text are dropped
        assert len(result) == 1
        assert result[0].span == [10, 19]


# ===================================================================
# _compute_bold_code_ranges — bold wrapping inline code detection
# ===================================================================


class TestComputeBoldCodeRanges:
    """Tests for _compute_bold_code_ranges and its helpers."""

    def test_bold_code_detected(self) -> None:
        """**`curl`** pattern is detected as bold-wrapped code."""
        inline = "Run **`curl`** to fetch data."
        result = _compute_bold_code_ranges(inline, None)
        assert len(result) == 1
        start, end, fmt, code_text = result[0]
        assert fmt == "bold"
        assert code_text == "curl"
        assert inline[start:end] == "**`curl`**"

    def test_italic_code_not_detected(self) -> None:
        """_`curl`_ is NOT detected — italic detection disabled due to FP risk."""
        inline = "Run _`curl`_ to fetch data."
        result = _compute_bold_code_ranges(inline, None)
        assert result == []

    def test_no_bold_code_returns_empty(self) -> None:
        """Plain text without bold+code returns empty list."""
        result = _compute_bold_code_ranges("No special formatting here.", None)
        assert result == []

    def test_plain_backtick_not_detected(self) -> None:
        """`curl` without bold wrapper is not detected."""
        result = _compute_bold_code_ranges("Run `curl` to fetch.", None)
        assert result == []

    def test_plain_bold_not_detected(self) -> None:
        """**important** without backticks is not detected."""
        result = _compute_bold_code_ranges("This is **important** info.", None)
        assert result == []

    def test_multiple_patterns(self) -> None:
        """Multiple bold+code patterns in one block."""
        inline = "Use **`curl`** or **`wget`** to download."
        result = _compute_bold_code_ranges(inline, None)
        assert len(result) == 2
        assert result[0][3] == "curl"
        assert result[1][3] == "wget"

    def test_empty_content(self) -> None:
        """Empty inline_content returns empty list."""
        result = _compute_bold_code_ranges("", None)
        assert result == []

    def test_with_char_map(self) -> None:
        """Ranges are correctly mapped via char_map to content coordinates."""
        # inline_content: "**`curl`** command"
        # After stripping: "curl command" (char_map maps positions)
        inline = "**`curl`** command"
        # char_map: content[0]='c' -> inline[3], content[1]='u' -> inline[4],
        #           content[2]='r' -> inline[5], content[3]='l' -> inline[6],
        #           content[4]=' ' -> inline[11], content[5..11]='command' -> inline[12..18]
        char_map = [3, 4, 5, 6, 11, 12, 13, 14, 15, 16, 17, 18]
        result = _compute_bold_code_ranges(inline, char_map)
        assert len(result) == 1
        c_start, c_end, fmt, code_text = result[0]
        assert fmt == "bold"
        assert code_text == "curl"
        # The mapped range should cover "curl" in content coordinates
        assert c_start == 0
        assert c_end <= 5  # up to and possibly including the space

    def test_find_bold_code_in_inline_helper(self) -> None:
        """_find_bold_code_in_inline returns raw inline_content positions."""
        inline = "Use **`git`** for versioning."
        result = _find_bold_code_in_inline(inline)
        assert len(result) == 1
        assert result[0][2] == "bold"
        assert result[0][3] == "git"
        # Verify the start/end positions match the inline string
        assert inline[result[0][0]:result[0][1]] == "**`git`**"

    def test_map_ranges_to_content_helper(self) -> None:
        """_map_ranges_to_content translates inline positions via char_map."""
        # inline positions (0, 10) -> content positions via char_map
        ranges = [(0, 10, "bold", "curl")]
        # Identity-ish char_map — just slightly offset
        char_map = [0, 1, 2, 3, 4, 10, 11, 12]
        result = _map_ranges_to_content(ranges, char_map)
        assert len(result) == 1
        assert result[0][2] == "bold"
