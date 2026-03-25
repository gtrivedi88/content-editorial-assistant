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
    _find_block_text_position,
    _find_bold_code_in_inline,
    _find_closest_match,
    _find_flagged_in_text,
    _map_block_issues_to_original,
    _map_ranges_to_content,
    _resolve_llm_span,
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


# ===================================================================
# _resolve_llm_span — sentence-context priority (F1)
# ===================================================================


class TestResolveLlmSpanSentenceContextPriority:
    """Tests that sentence-context search runs before naive text.find."""

    def test_sentence_context_disambiguates_duplicate_word(self) -> None:
        """When flagged_text appears multiple times, sentence anchors to correct one.

        Simulates the real bug: the word 'using' appears in both the intro
        paragraph and a bullet item.  The LLM provides a sentence that
        contains the bullet's 'using', so the span must land there — not
        on the first document-wide occurrence.
        """
        text = (
            "You can manage network settings using a web browser. "
            "Configuring a network bond by using the RHEL web console."
        )
        # The LLM flagged "using" in the second sentence
        issue = _make_issue(
            flagged_text="using",
            sentence="Configuring a network bond by using the RHEL web console.",
        )
        _resolve_llm_span(issue, text)

        # Must resolve to the second "using" (pos 80), not the first (pos 36)
        assert issue.span != [0, 0], "Span should be resolved"
        matched = text[issue.span[0]:issue.span[1]]
        assert matched == "using"
        # The second "using" starts after "by " in the second sentence
        assert issue.span[0] > 50, (
            f"Expected span in second sentence, got pos {issue.span[0]}"
        )

    def test_falls_back_to_text_find_without_sentence(self) -> None:
        """Without issue.sentence, falls back to text.find (first occurrence).

        When the LLM does not provide a sentence, the first occurrence
        is the best available guess.
        """
        text = "Click Save to continue. Click Save again to confirm."
        issue = _make_issue(
            flagged_text="Save",
            sentence="",  # no sentence context
        )
        _resolve_llm_span(issue, text)

        assert issue.span != [0, 0], "Span should be resolved"
        matched = text[issue.span[0]:issue.span[1]]
        assert matched == "Save"
        # Falls back to first occurrence
        assert issue.span[0] == 6


# ===================================================================
# _find_closest_match — hint-aware substring search
# ===================================================================


class TestFindClosestMatch:
    """Tests for _find_closest_match hint-aware search."""

    def test_picks_closest_to_hint(self) -> None:
        """When multiple matches exist, returns the one closest to hint."""
        text = "use the tool. then use it again. finally use it once more."
        #       ^pos 0          ^pos 19                 ^pos 41
        # "use" appears at 0, 19, 41 — hint=40 should pick pos 41
        idx = _find_closest_match(text, "use", 0, len(text), 40)
        assert idx == 41

    def test_returns_first_when_hint_is_zero(self) -> None:
        """Hint near zero picks the first occurrence."""
        text = "apple banana apple cherry"
        idx = _find_closest_match(text, "apple", 0, len(text), 0)
        assert idx == 0

    def test_returns_neg1_when_not_found(self) -> None:
        """Returns -1 when pattern is not in the region."""
        text = "no match here"
        idx = _find_closest_match(text, "xyz", 0, len(text), 5)
        assert idx == -1

    def test_respects_search_bounds(self) -> None:
        """Only considers matches within [search_from, search_to)."""
        text = "aaa bbb aaa ccc aaa"
        # Only search [8, 15) — middle "aaa" at pos 8
        idx = _find_closest_match(text, "aaa", 8, 15, 12)
        assert idx == 8


# ===================================================================
# _find_flagged_in_text with position_hint
# ===================================================================


class TestFindFlaggedPositionHint:
    """Tests for _find_flagged_in_text with position_hint parameter."""

    def test_hint_picks_closest_occurrence(self) -> None:
        """position_hint picks the closest match, not the first."""
        text = "manage settings using a browser. bond by using the console."
        #                   ^pos 16                      ^pos 41
        # "using" at 16 and 41; hint=40 should pick pos 41
        result = _find_flagged_in_text(
            text, "using", position_hint=40,
        )
        assert result is not None
        assert result[0] == 41

    def test_no_hint_picks_first(self) -> None:
        """Without position_hint, picks the first occurrence."""
        text = "manage settings using a browser. bond by using the console."
        result = _find_flagged_in_text(text, "using")
        assert result is not None
        assert result[0] == 16

    def test_hint_with_search_bounds(self) -> None:
        """position_hint works correctly within search bounds."""
        text = "using this. ignore. using that. skip. using more."
        #       ^pos 0              ^pos 20             ^pos 38
        # Restrict to [15, 45), hint=22 — should find pos 20
        result = _find_flagged_in_text(
            text, "using", search_from=15, search_to=45,
            position_hint=22,
        )
        assert result is not None
        assert result[0] == 20

    def test_hint_case_insensitive_fallback(self) -> None:
        """position_hint applies to case-insensitive fallback too."""
        text = "Save your work. Click Save to continue."
        #                              ^pos 22
        # "save" (lowercase) at pos 0 and 22 — hint=25 picks pos 22
        result = _find_flagged_in_text(
            text, "save", position_hint=25,
        )
        assert result is not None
        # Case-insensitive match at position 22 (closest to hint=25)
        assert result[0] == 22
        assert result[2] == "Save"


# ===================================================================
# _find_block_text_position — content-based block anchor
# ===================================================================


class TestFindBlockTextPosition:
    """Tests for _find_block_text_position content-based anchor."""

    def test_finds_exact_block_content(self) -> None:
        """Finds block content exactly in the text."""
        text = "Intro paragraph. Configure the bridge settings. More text."
        pos = _find_block_text_position(
            "Configure the bridge settings.", text, 0,
        )
        assert pos == 17

    def test_returns_neg1_for_short_content(self) -> None:
        """Returns -1 when block content is too short to anchor."""
        text = "Some text here."
        pos = _find_block_text_position("Hi", text, 0)
        assert pos == -1

    def test_picks_closest_when_duplicate(self) -> None:
        """When content appears twice, picks closest to hint."""
        text = (
            "Install the package on the server. "
            "Extra padding here. "
            "Install the package on the server."
        )
        # First occurrence at 0, second at 55
        pos = _find_block_text_position(
            "Install the package on the server.", text, 50,
        )
        assert pos == 55

    def test_returns_neg1_when_not_found(self) -> None:
        """Returns -1 when content is not in the text."""
        text = "Completely different content here."
        pos = _find_block_text_position(
            "This text does not appear anywhere.", text, 0,
        )
        assert pos == -1

    def test_prefix_match_handles_trailing_diffs(self) -> None:
        """Prefix matching handles trailing whitespace differences."""
        # Block content has slightly different trailing text
        text = "Configure the bridge settings for the network interface properly."
        pos = _find_block_text_position(
            "Configure the bridge settings for the network interface properly!",
            text, 0,
        )
        # Full match fails but prefix (first 50 chars) succeeds
        assert pos == 0


# ===================================================================
# _map_block_issues_to_original — HTML coordinate mismatch fix
# ===================================================================


class TestMapBlockIssuesHtmlMismatch:
    """Tests for _map_block_issues_to_original with coordinate mismatch.

    Simulates HTML paste where block.start_pos is in raw HTML
    coordinates but original_text is browser-extracted plain text.
    """

    def test_content_anchor_fixes_html_coordinate_mismatch(self) -> None:
        """Content anchor resolves HTML→plain text coordinate mismatch.

        block.start_pos is in HTML coordinates (much larger than
        the plain text position).  Content-based anchor search finds
        the correct position in plain text.
        """
        # Simulate plain text that the browser extracted
        original_text = (
            "Manage network settings using a web browser. "
            "Configure a bond by using the console."
        )
        # The paragraph block has content from the HTML parser.
        # start_pos is in HTML coordinates (e.g., 200) but the
        # actual position in plain text is 0.
        # "using" in content is at position 24.

        class FakeBlock:
            content = "Manage network settings using a web browser."
            start_pos = 200  # HTML coordinate — wrong for plain text!
            end_pos = 350
            char_map = None

        block = FakeBlock()
        issues = [
            _make_issue(flagged_text="using", span=[24, 29]),
        ]

        _map_block_issues_to_original(issues, block, original_text)

        assert issues[0].span != [-1, -1], "Should resolve successfully"
        matched = original_text[issues[0].span[0]:issues[0].span[1]]
        assert matched == "using"
        # Must be the first "using" (pos 24), not the second (pos 65)
        assert issues[0].span[0] == 24

    def test_hint_prevents_wrong_occurrence(self) -> None:
        """position_hint prevents snapping to wrong occurrence.

        Even with correct coordinates, a wide search window could
        include multiple occurrences.  position_hint picks closest.
        """
        original_text = (
            "Use the using pattern here. "
            "Also using there. "
            "And using everywhere."
        )

        class FakeBlock:
            content = "Also using there."
            start_pos = 28  # Correct plain-text coordinate
            end_pos = 45
            char_map = None

        block = FakeBlock()
        issues = [
            _make_issue(flagged_text="using", span=[5, 10]),
        ]

        _map_block_issues_to_original(issues, block, original_text)

        assert issues[0].span != [-1, -1]
        matched = original_text[issues[0].span[0]:issues[0].span[1]]
        assert matched == "using"
        # Must be the second "using" (in "Also using there"),
        # not the first or third
        assert issues[0].span[0] == 33

    def test_fallback_to_start_pos_for_asciidoc(self) -> None:
        """Falls back to block.start_pos when content anchor fails.

        For AsciiDoc, block.content has markers stripped but
        original_text has markup, so content search returns -1.
        block.start_pos is already in the correct coordinate space.
        """
        # AsciiDoc original text with inline markup
        original_text = "Click **Save** to continue."

        class FakeBlock:
            content = "Click Save to continue."  # Stripped
            start_pos = 0  # Correct AsciiDoc coordinate
            end_pos = 27
            char_map = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11,
                        14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                        24, 25, 26]

        block = FakeBlock()
        issues = [
            _make_issue(flagged_text="Save", span=[6, 10]),
        ]

        _map_block_issues_to_original(issues, block, original_text)

        assert issues[0].span != [-1, -1]
        matched = original_text[issues[0].span[0]:issues[0].span[1]]
        assert matched == "Save"


# ---------------------------------------------------------------------------
# _collect_block_results — cancellation check
# ---------------------------------------------------------------------------


class TestCollectBlockResultsCancellation:
    """Verify _collect_block_results respects session cancellation."""

    def test_stops_collecting_on_cancellation(self) -> None:
        """When session is cancelled, stops collecting remaining blocks."""
        from concurrent.futures import Future
        from unittest.mock import patch

        from app.services.analysis.orchestrator import _collect_block_results

        f1: Future = Future()
        f2: Future = Future()
        f1.set_result([{"flagged_text": "a", "message": "m"}])
        f2.set_result([{"flagged_text": "b", "message": "m"}])

        futures = {f1: 0, f2: 1}

        call_count = 0

        def mock_cancelled(sid: str) -> bool:
            nonlocal call_count
            call_count += 1
            return call_count > 1

        with patch(
            "app.services.analysis.orchestrator._is_cancelled",
            side_effect=mock_cancelled,
        ):
            results = _collect_block_results(
                futures, session_id="test-session",
            )

        assert len(results) <= 1
