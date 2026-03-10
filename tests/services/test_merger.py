"""Tests for the issue merger module.

Validates deduplication and merging of deterministic and LLM-generated
issues, including span overlap detection, text-based matching,
cross-block boundary demotion, source-aware composite keys, and
category-aware deduplication.
"""

import uuid
from unittest.mock import MagicMock

import pytest

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse
from app.services.analysis.merger import (
    _broad_category,
    _deduplicate_llm_issues,
    _extract_block_boundaries,
    _extract_flagged_texts,
    _extract_valid_spans,
    _has_span_overlap,
    _has_valid_span,
    _is_duplicate,
    _is_span_duplicate,
    _merge_lt_tier,
    _merge_llm_tier,
    _normalize_text,
    _span_crosses_block_boundary,
    _words_overlap,
    merge,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_issue(
    source: str = "deterministic",
    category: IssueCategory = IssueCategory.STYLE,
    rule_name: str = "test_rule",
    flagged_text: str = "test text",
    message: str = "Test message.",
    suggestions: list[str] | None = None,
    severity: IssueSeverity = IssueSeverity.MEDIUM,
    sentence: str = "This is a test sentence.",
    sentence_index: int = 0,
    span: list[int] | None = None,
    confidence: float = 1.0,
) -> IssueResponse:
    """Create an IssueResponse with sensible defaults for testing.

    Args:
        source: Issue source identifier.
        category: Editorial category.
        rule_name: Name of the triggering rule.
        flagged_text: The flagged text span.
        message: Human-readable explanation.
        suggestions: Replacement suggestions.
        severity: Issue severity level.
        sentence: Full sentence containing the issue.
        sentence_index: Zero-based sentence index.
        span: Character offset pair [start, end].
        confidence: Confidence score between 0.0 and 1.0.

    Returns:
        A populated IssueResponse instance.
    """
    return IssueResponse(
        id=str(uuid.uuid4()),
        source=source,
        category=category,
        rule_name=rule_name,
        flagged_text=flagged_text,
        message=message,
        suggestions=suggestions if suggestions is not None else ["fix"],
        severity=severity,
        sentence=sentence,
        sentence_index=sentence_index,
        span=span if span is not None else [0, 0],
        confidence=confidence,
        status=IssueStatus.OPEN,
    )


def _make_block(start_pos: int, end_pos: int, block_type: str = "paragraph") -> MagicMock:
    """Create a mock Block object with start_pos and end_pos attributes.

    Args:
        start_pos: Character offset where the block starts.
        end_pos: Character offset where the block ends.
        block_type: Type of block (paragraph, code, heading, etc.).

    Returns:
        A MagicMock configured with block attributes.
    """
    block = MagicMock()
    block.start_pos = start_pos
    block.end_pos = end_pos
    block.block_type = block_type
    return block


# ---------------------------------------------------------------------------
# merge() basic operation
# ---------------------------------------------------------------------------


class TestMergeBasicOperation:
    """Tests for merge() with empty and single-source inputs."""

    def test_merge_empty_lists(self) -> None:
        """Merging two empty lists returns an empty list."""
        result = merge([], [])
        assert result == []

    def test_merge_deterministic_only(self) -> None:
        """When no LLM issues exist, deterministic issues are returned sorted."""
        det_1 = _make_issue(sentence_index=1, span=[50, 60])
        det_0 = _make_issue(sentence_index=0, span=[10, 20])
        result = merge([det_1, det_0], [])
        assert len(result) == 2
        assert result[0].sentence_index == 0
        assert result[1].sentence_index == 1

    def test_merge_llm_only(self) -> None:
        """When no deterministic issues exist, qualifying LLM issues are kept."""
        llm = _make_issue(
            source="llm",
            flagged_text="utilize",
            span=[10, 17],
            confidence=0.9,
        )
        result = merge([], [llm])
        assert len(result) == 1
        assert result[0].source == "llm"

    def test_merge_llm_below_confidence_threshold(self) -> None:
        """LLM issues below the confidence threshold are excluded."""
        llm = _make_issue(source="llm", confidence=0.5, span=[10, 17])
        result = merge([], [llm], confidence_threshold=0.7)
        assert len(result) == 0

    def test_merge_llm_at_confidence_threshold(self) -> None:
        """LLM issues exactly at the confidence threshold are kept."""
        llm = _make_issue(source="llm", confidence=0.7, span=[10, 17])
        result = merge([], [llm], confidence_threshold=0.7)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _deduplicate_llm_issues()
# ---------------------------------------------------------------------------


class TestDeduplicateLlmIssues:
    """Tests for LLM-to-LLM deduplication strategies."""

    def test_text_dedup_same_source(self) -> None:
        """Two LLM issues from the same source with identical text are deduped."""
        issue_a = _make_issue(source="granular", flagged_text="utilize")
        issue_b = _make_issue(source="granular", flagged_text="utilize")
        result = _deduplicate_llm_issues([issue_a, issue_b])
        assert len(result) == 1

    def test_text_dedup_different_source_exact_match_deduped(self) -> None:
        """LLM issues from different sources with identical text are deduped.

        Cross-source exact text matching ensures granular and global issues
        with the same flagged_text are collapsed to avoid duplicate cards.
        """
        granular = _make_issue(source="granular", flagged_text="utilize")
        global_issue = _make_issue(source="global", flagged_text="utilize")
        result = _deduplicate_llm_issues([granular, global_issue])
        assert len(result) == 1

    def test_span_overlap_dedup_above_80_percent(self) -> None:
        """Two same-source LLM issues with >80% span overlap are deduped."""
        issue_a = _make_issue(
            source="granular",
            flagged_text="the quick brown fox",
            span=[100, 120],
        )
        issue_b = _make_issue(
            source="granular",
            flagged_text="quick brown fox jumps",
            span=[104, 124],
        )
        # Overlap: [104, 120] = 16 chars. Shorter span = 20. 16/20 = 0.80
        # Threshold is > 0.80 so at exactly 0.80 both should be kept
        result = _deduplicate_llm_issues([issue_a, issue_b])
        assert len(result) == 2

    def test_span_overlap_dedup_above_threshold(self) -> None:
        """Two same-source LLM issues with >80% span overlap are deduped."""
        issue_a = _make_issue(
            source="granular",
            flagged_text="the quick brown fox",
            span=[100, 120],
        )
        issue_b = _make_issue(
            source="granular",
            flagged_text="quick brown fox jumps",
            span=[103, 123],
        )
        # Overlap: [103, 120] = 17 chars. Shorter span = 20. 17/20 = 0.85
        result = _deduplicate_llm_issues([issue_a, issue_b])
        assert len(result) == 1

    def test_empty_flagged_text_not_deduped(self) -> None:
        """Issues with empty flagged_text are kept without dedup checks."""
        issue_a = _make_issue(source="granular", flagged_text="")
        issue_b = _make_issue(source="granular", flagged_text="")
        result = _deduplicate_llm_issues([issue_a, issue_b])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# _is_span_duplicate()
# ---------------------------------------------------------------------------


class TestIsSpanDuplicate:
    """Tests for span-based duplicate detection."""

    def test_full_overlap_is_duplicate(self) -> None:
        """An LLM issue fully contained within a det span is a duplicate."""
        det = _make_issue(category=IssueCategory.STYLE, span=[100, 200])
        llm = _make_issue(
            source="llm",
            category=IssueCategory.STYLE,
            span=[120, 180],
        )
        det_spans = _extract_valid_spans([det])
        assert _is_span_duplicate(llm, det_spans) is True

    def test_partial_overlap_is_duplicate(self) -> None:
        """An LLM issue partially overlapping a det span is a duplicate."""
        det = _make_issue(category=IssueCategory.GRAMMAR, span=[100, 150])
        llm = _make_issue(
            source="llm",
            category=IssueCategory.GRAMMAR,
            span=[130, 200],
        )
        det_spans = _extract_valid_spans([det])
        assert _is_span_duplicate(llm, det_spans) is True

    def test_no_overlap(self) -> None:
        """Non-overlapping spans are not duplicates."""
        det = _make_issue(span=[100, 150])
        llm = _make_issue(source="llm", span=[200, 250])
        det_spans = _extract_valid_spans([det])
        assert _is_span_duplicate(llm, det_spans) is False

    def test_adjacent_spans_no_overlap(self) -> None:
        """Spans that are exactly adjacent (no shared character) are not duplicates."""
        det = _make_issue(span=[100, 150])
        llm = _make_issue(source="llm", span=[150, 200])
        det_spans = _extract_valid_spans([det])
        assert _is_span_duplicate(llm, det_spans) is False


# ---------------------------------------------------------------------------
# _is_duplicate() — span-authoritative behavior (4I fix)
# ---------------------------------------------------------------------------


class TestIsDuplicate:
    """Tests for the main duplicate detection dispatch logic."""

    def test_span_overlap_same_category_is_duplicate(self) -> None:
        """Same broad category + span overlap → duplicate."""
        det = _make_issue(
            flagged_text="completely different text",
            span=[100, 150],
            category=IssueCategory.STYLE,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="overlapping issue text",
            span=[120, 170],
            category=IssueCategory.STYLE,
        )
        result = _is_duplicate(llm, [det])
        assert result is True

    def test_span_overlap_different_broad_category_not_duplicate(self) -> None:
        """Different broad category + span overlap → NOT duplicate.

        A deterministic 'technical formatting' issue should not suppress
        an LLM 'language/capitalization' issue on the same text.
        """
        det = _make_issue(
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.TECHNICAL,
            rule_name="command_syntax",
        )
        llm = _make_issue(
            source="llm",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.STYLE,
            rule_name="llm_style",
        )
        result = _is_duplicate(llm, [det])
        assert result is False

    def test_text_fallback_for_spanless_issues(self) -> None:
        """When the LLM issue has [0, 0] span, exact text match is used."""
        det = _make_issue(
            flagged_text="utilize the system",
            span=[50, 68],
            category=IssueCategory.STYLE,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="utilize the system",
            span=[0, 0],
            category=IssueCategory.STYLE,
        )
        result = _is_duplicate(llm, [det])
        assert result is True

    def test_text_fallback_no_match(self) -> None:
        """Spanless LLM issue with different text is not a duplicate."""
        det = _make_issue(
            flagged_text="utilize the system",
            span=[50, 68],
            category=IssueCategory.STYLE,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="completely unrelated phrase",
            span=[0, 0],
            category=IssueCategory.STYLE,
        )
        result = _is_duplicate(llm, [det])
        assert result is False

    def test_text_fallback_different_category_not_duplicate(self) -> None:
        """Exact same text but different broad category → NOT duplicate.

        'ostree' flagged for code formatting (TECHNICAL) should not
        suppress 'ostree' flagged for capitalization (STYLE).
        """
        det = _make_issue(
            flagged_text="ostree",
            span=[0, 0],
            category=IssueCategory.TECHNICAL,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="ostree",
            span=[0, 0],
            category=IssueCategory.STYLE,
        )
        result = _is_duplicate(llm, [det])
        assert result is False

    def test_word_subsequence_not_duplicate(self) -> None:
        """Word subsequences are no longer treated as duplicates.

        'be used' (passive voice) should NOT suppress 'will be used'
        (future tense) via text matching — these are different
        editorial concerns even within the same category.
        """
        det = _make_issue(
            flagged_text="be used",
            span=[200, 207],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="will be used",
            span=[0, 0],
            category=IssueCategory.GRAMMAR,
        )
        # Text-only check: "will be used" ≠ "be used" (no exact match)
        result = _is_duplicate(llm, [det])
        assert result is False


# ---------------------------------------------------------------------------
# Category-aware span overlap deduplication
# ---------------------------------------------------------------------------


class TestSpanOverlapDedup:
    """Tests for span overlap deduplication with category awareness."""

    def test_same_broad_category_deduped_on_overlap(self) -> None:
        """Same broad category (STYLE and GRAMMAR → 'language') + span
        overlap → duplicate via _is_duplicate.
        """
        det = _make_issue(
            category=IssueCategory.STYLE,
            rule_name="passive_voice",
            flagged_text="was configured",
            span=[100, 114],
        )
        llm = _make_issue(
            source="llm",
            category=IssueCategory.GRAMMAR,
            rule_name="llm_grammar",
            flagged_text="was configured by the admin",
            span=[100, 127],
        )
        result = _is_duplicate(llm, [det])
        assert result is True

    def test_different_broad_category_not_deduped_on_overlap(self) -> None:
        """Different broad categories (TECHNICAL vs STYLE) + span overlap
        → NOT duplicate.  These represent different editorial concerns.
        """
        det = _make_issue(
            category=IssueCategory.TECHNICAL,
            rule_name="command_syntax",
            flagged_text="ostree",
            span=[100, 106],
        )
        llm = _make_issue(
            source="llm",
            category=IssueCategory.STYLE,
            rule_name="llm_style",
            flagged_text="ostree",
            span=[100, 106],
        )
        result = _is_duplicate(llm, [det])
        assert result is False

    def test_same_category_with_overlap_is_duplicate(self) -> None:
        """Overlapping spans with the same category are duplicates."""
        det = _make_issue(
            category=IssueCategory.STYLE,
            span=[100, 150],
        )
        llm = _make_issue(
            source="llm",
            category=IssueCategory.STYLE,
            span=[110, 160],
        )
        result = _is_duplicate(llm, [det])
        assert result is True

    def test_unknown_category_with_overlap_is_duplicate(self) -> None:
        """When both categories are None (same 'unknown'), span overlap dedupes."""
        det = _make_issue(span=[100, 150])
        det.category = None
        llm = _make_issue(source="llm", span=[110, 160])
        llm.category = None
        result = _is_duplicate(llm, [det])
        assert result is True

    def test_raw_span_duplicate_is_category_agnostic(self) -> None:
        """The low-level _is_span_duplicate helper remains category-agnostic.

        It checks raw span overlap only.  Category filtering is handled
        by _is_duplicate which wraps it.
        """
        det = _make_issue(
            category=IssueCategory.TECHNICAL,
            span=[100, 106],
        )
        llm = _make_issue(
            source="llm",
            category=IssueCategory.STYLE,
            span=[100, 106],
        )
        det_spans = _extract_valid_spans([det])
        result = _is_span_duplicate(llm, det_spans)
        assert result is True


# ---------------------------------------------------------------------------
# Cross-block boundary detection and demotion
# ---------------------------------------------------------------------------


class TestCrossBlockBoundary:
    """Tests for cross-block boundary detection and issue demotion."""

    def test_span_crosses_boundary(self) -> None:
        """A span straddling a block boundary is detected."""
        boundaries = [100, 200, 300]
        assert _span_crosses_block_boundary([90, 110], boundaries) is True

    def test_span_within_single_block(self) -> None:
        """A span fully within one block does not cross any boundary."""
        boundaries = [100, 200, 300]
        assert _span_crosses_block_boundary([110, 190], boundaries) is False

    def test_span_ending_at_boundary(self) -> None:
        """A span ending exactly at a boundary does not cross it."""
        boundaries = [100, 200, 300]
        assert _span_crosses_block_boundary([80, 100], boundaries) is False

    def test_span_starting_at_boundary(self) -> None:
        """A span starting exactly at a boundary does not cross it."""
        boundaries = [100, 200, 300]
        assert _span_crosses_block_boundary([100, 150], boundaries) is False

    def test_empty_boundaries(self) -> None:
        """No boundaries means no crossing is possible."""
        assert _span_crosses_block_boundary([50, 150], []) is False

    def test_short_span_no_crossing(self) -> None:
        """A span with fewer than 2 elements cannot cross boundaries."""
        assert _span_crosses_block_boundary([50], [100]) is False

    def test_extract_block_boundaries_includes_code_blocks(self) -> None:
        """Block boundary extraction includes code blocks (4E fix).

        The 4E boundary blindness fix ensures that code blocks contribute
        their end positions to the boundary list, preventing LLM issues
        from spanning across code block boundaries undetected.
        """
        blocks = [
            _make_block(0, 100, "paragraph"),
            _make_block(100, 200, "code"),
            _make_block(200, 300, "paragraph"),
        ]
        boundaries = _extract_block_boundaries(blocks)
        assert boundaries == [100, 200, 300]

    def test_cross_block_demotion_clears_suggestions(self) -> None:
        """LLM issue crossing a code block boundary gets suggestions=[] via merge.

        When blocks are provided and an LLM issue spans across a block
        boundary, the merger demotes it by clearing its suggestions list
        to disable the Accept button in the UI.
        """
        blocks = [
            _make_block(0, 100, "paragraph"),
            _make_block(100, 200, "code"),
            _make_block(200, 300, "paragraph"),
        ]
        llm = _make_issue(
            source="llm",
            flagged_text="text spanning code block",
            span=[90, 210],
            suggestions=["rewritten text"],
            confidence=0.9,
        )
        result = merge([], [llm], blocks=blocks)
        assert len(result) == 1
        assert result[0].suggestions == []


# ---------------------------------------------------------------------------
# _normalize_text()
# ---------------------------------------------------------------------------


class TestNormalizeText:
    """Tests for text normalization used in deduplication."""

    def test_lowercase(self) -> None:
        """Uppercase text is lowered."""
        assert _normalize_text("UTILIZE") == "utilize"

    def test_strip_whitespace(self) -> None:
        """Leading and trailing whitespace is removed."""
        assert _normalize_text("  utilize  ") == "utilize"

    def test_mixed_case_and_whitespace(self) -> None:
        """Combined case and whitespace normalization works."""
        assert _normalize_text("  The System  ") == "the system"


# ---------------------------------------------------------------------------
# _words_overlap()
# ---------------------------------------------------------------------------


class TestWordsOverlap:
    """Tests for word-level contiguous subsequence matching."""

    def test_subsequence_match(self) -> None:
        """Shorter word list found as contiguous subsequence of longer."""
        short = ["be", "used"]
        long = ["the", "system", "can", "be", "used", "effectively"]
        assert _words_overlap(short, long) is True

    def test_no_subsequence(self) -> None:
        """Word lists with no contiguous match return False."""
        words_a = ["the", "dog"]
        words_b = ["a", "cat", "sleeps"]
        assert _words_overlap(words_a, words_b) is False

    def test_empty_shorter_list(self) -> None:
        """An empty word list does not match anything."""
        assert _words_overlap([], ["some", "words"]) is False

    def test_identical_lists(self) -> None:
        """Identical word lists are a match."""
        words = ["utilize", "the", "system"]
        assert _words_overlap(words, words) is True

    def test_non_contiguous_words_no_match(self) -> None:
        """Words present but not contiguous do not match."""
        short = ["use", "system"]
        long = ["use", "the", "system"]
        assert _words_overlap(short, long) is False


# ---------------------------------------------------------------------------
# Sort order
# ---------------------------------------------------------------------------


class TestSortOrder:
    """Tests for deterministic-before-LLM and positional sort order."""

    def test_sorted_by_sentence_index_then_span(self) -> None:
        """Merged output is sorted by sentence_index, then span start."""
        det = _make_issue(
            sentence_index=2,
            span=[50, 60],
        )
        llm = _make_issue(
            source="llm",
            sentence_index=0,
            span=[10, 20],
            confidence=0.9,
            flagged_text="unique llm text",
        )
        result = merge([det], [llm])
        assert result[0].sentence_index == 0
        assert result[1].sentence_index == 2

    def test_same_sentence_sorted_by_span_start(self) -> None:
        """Issues in the same sentence are sorted by span start position."""
        det_a = _make_issue(sentence_index=0, span=[50, 60])
        det_b = _make_issue(
            sentence_index=0,
            span=[10, 20],
            flagged_text="different text",
        )
        result = merge([det_a, det_b], [])
        assert result[0].span[0] == 10
        assert result[1].span[0] == 50


# ---------------------------------------------------------------------------
# Critical: Global/Granular Coexistence
# ---------------------------------------------------------------------------


class TestGlobalGranularCoexistence:
    """Tests for global and granular LLM issue coexistence through merge."""

    def test_global_and_granular_same_text_deduped(self) -> None:
        """Global and granular issues with identical flagged_text are deduped.

        Cross-source exact text matching collapses duplicate cards —
        the same text flagged by both passes produces a single issue.
        """
        granular = _make_issue(
            source="granular",
            flagged_text="This section provides an overview",
            message="Avoid vague introductory phrases.",
            span=[100, 134],
            confidence=0.9,
            category=IssueCategory.STYLE,
            rule_name="llm_style",
        )
        global_issue = _make_issue(
            source="global",
            flagged_text="This section provides an overview",
            message="Document tone is inconsistent with reference style.",
            span=[0, 0],
            confidence=0.85,
            category=IssueCategory.AUDIENCE,
            rule_name="llm_audience",
        )
        result = _deduplicate_llm_issues([granular, global_issue])
        assert len(result) == 1
        assert result[0].source == "granular"

    def test_global_and_granular_different_text_both_survive_merge(self) -> None:
        """Global and granular issues with different flagged_text both survive
        the full merge pipeline.

        When the texts differ, text-based dedup in the merge loop does not
        collapse them, and both issues are retained in the final output.
        """
        granular = _make_issue(
            source="granular",
            flagged_text="utilize the system",
            span=[100, 118],
            confidence=0.9,
            category=IssueCategory.STYLE,
        )
        global_issue = _make_issue(
            source="global",
            flagged_text="overall document tone is too informal",
            span=[0, 0],
            confidence=0.85,
            category=IssueCategory.AUDIENCE,
        )
        result = merge([], [granular, global_issue])
        assert len(result) == 2

    def test_global_and_granular_same_span_deduped_by_span(self) -> None:
        """Global and granular issues with identical span are deduped by span
        overlap in _deduplicate_llm_issues even though text-based dedup
        would keep them (source-aware keys). Span-based dedup is not
        source-aware and catches overlapping chunks.
        """
        granular = _make_issue(
            source="granular",
            flagged_text="This section provides an overview",
            span=[0, 34],
            confidence=0.9,
        )
        global_issue = _make_issue(
            source="global",
            flagged_text="This section provides an overview",
            span=[0, 34],
            confidence=0.85,
        )
        result = _deduplicate_llm_issues([granular, global_issue])
        # Span-based dedup removes the second one (>80% overlap)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Critical: Repeated Error Survival
# ---------------------------------------------------------------------------


class TestRepeatedErrorSurvival:
    """Tests for preserving repeated errors at different document positions."""

    def test_same_flagged_text_same_broad_category_deduped(self) -> None:
        """Deterministic 'utilizes' (WORD_USAGE) and LLM 'utilizes' (STYLE)
        are deduped via exact text match because both map to the 'language'
        broad category.
        """
        det = _make_issue(
            source="deterministic",
            flagged_text="utilizes",
            rule_name="word_usage",
            span=[100, 108],
            category=IssueCategory.WORD_USAGE,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="utilizes",
            rule_name="llm_style",
            span=[5000, 5008],
            confidence=0.9,
            category=IssueCategory.STYLE,
        )
        result = merge([det], [llm])
        assert len(result) == 1
        assert result[0].source == "deterministic"

    def test_same_flagged_text_different_broad_category_both_survive(self) -> None:
        """Deterministic 'ostree' (TECHNICAL) and LLM 'ostree' (STYLE)
        both survive because TECHNICAL and STYLE map to different broad
        categories ('technical' vs 'language').
        """
        det = _make_issue(
            source="deterministic",
            flagged_text="ostree",
            rule_name="command_syntax",
            span=[100, 106],
            category=IssueCategory.TECHNICAL,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="ostree",
            rule_name="llm_style",
            span=[100, 106],
            confidence=0.9,
            category=IssueCategory.STYLE,
        )
        result = merge([det], [llm])
        assert len(result) == 2

    def test_same_text_overlapping_spans_same_category_deduped(self) -> None:
        """Same flagged text at the same span, same category → deduped."""
        det = _make_issue(
            source="deterministic",
            flagged_text="utilizes",
            span=[100, 108],
            category=IssueCategory.WORD_USAGE,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="utilizes",
            span=[100, 108],
            confidence=0.9,
            category=IssueCategory.WORD_USAGE,
        )
        result = merge([det], [llm])
        assert len(result) == 1
        assert result[0].source == "deterministic"


# ---------------------------------------------------------------------------
# Critical: Cross-Block Boundary Demotion with code blocks
# ---------------------------------------------------------------------------


class TestCrossBlockBoundaryDemotion:
    """Tests for LLM issue demotion when spanning code block boundaries."""

    def test_llm_issue_crossing_code_block_boundary_demoted(self) -> None:
        """An LLM issue whose span crosses a code block boundary gets its
        suggestions cleared to prevent DOM errors from range-based replacement.

        The blocks list includes a code block, verifying that the 4E fix
        (boundary blindness) ensures code blocks contribute boundaries.
        """
        blocks = [
            _make_block(0, 150, "paragraph"),
            _make_block(150, 300, "code"),
            _make_block(300, 450, "paragraph"),
        ]
        llm = _make_issue(
            source="llm",
            flagged_text="text that crosses into code block",
            span=[140, 310],
            suggestions=["rewritten suggestion"],
            confidence=0.9,
        )
        result = merge([], [llm], blocks=blocks)
        assert len(result) == 1
        assert result[0].suggestions == []

    def test_llm_issue_within_single_block_not_demoted(self) -> None:
        """An LLM issue fully within a single block retains its suggestions."""
        blocks = [
            _make_block(0, 150, "paragraph"),
            _make_block(150, 300, "code"),
            _make_block(300, 450, "paragraph"),
        ]
        llm = _make_issue(
            source="llm",
            flagged_text="safe text",
            span=[10, 140],
            suggestions=["improved text"],
            confidence=0.9,
        )
        result = merge([], [llm], blocks=blocks)
        assert len(result) == 1
        assert result[0].suggestions == ["improved text"]


# ---------------------------------------------------------------------------
# _has_valid_span() and _has_span_overlap() edge cases
# ---------------------------------------------------------------------------


class TestSpanHelpers:
    """Tests for low-level span helper functions."""

    def test_has_valid_span_zero_zero(self) -> None:
        """[0, 0] is not a valid span."""
        assert _has_valid_span([0, 0]) is False

    def test_has_valid_span_positive(self) -> None:
        """A span with non-zero positions is valid."""
        assert _has_valid_span([10, 20]) is True

    def test_has_valid_span_zero_start_nonzero_end(self) -> None:
        """[0, N] where N > 0 is a valid span (issue at document start)."""
        assert _has_valid_span([0, 15]) is True

    def test_has_valid_span_short(self) -> None:
        """A span with fewer than 2 elements is not valid."""
        assert _has_valid_span([10]) is False

    def test_has_span_overlap_true(self) -> None:
        """Overlapping spans are detected."""
        assert _has_span_overlap([10, 30], [[20, 40]]) is True

    def test_has_span_overlap_false(self) -> None:
        """Non-overlapping spans return False."""
        assert _has_span_overlap([10, 20], [[30, 40]]) is False

    def test_has_span_overlap_short_span(self) -> None:
        """A span with fewer than 2 elements cannot overlap."""
        assert _has_span_overlap([10], [[5, 15]]) is False


# ---------------------------------------------------------------------------
# _extract_flagged_texts() and _extract_valid_spans()
# ---------------------------------------------------------------------------


class TestExtractHelpers:
    """Tests for span and text extraction utilities."""

    def test_extract_valid_spans_filters_zero_zero(self) -> None:
        """[0, 0] spans are excluded from the valid spans list."""
        issue_valid = _make_issue(span=[10, 20])
        issue_invalid = _make_issue(span=[0, 0])
        spans = _extract_valid_spans([issue_valid, issue_invalid])
        assert len(spans) == 1
        assert spans[0] == [10, 20]

    def test_extract_flagged_texts_normalized(self) -> None:
        """Extracted flagged texts are normalized (lowered, stripped)."""
        issue = _make_issue(flagged_text="  UTILIZE  ")
        texts = _extract_flagged_texts([issue])
        assert "utilize" in texts

    def test_extract_flagged_texts_skips_empty(self) -> None:
        """Empty flagged_text values are excluded."""
        issue = _make_issue(flagged_text="")
        texts = _extract_flagged_texts([issue])
        assert len(texts) == 0


# ---------------------------------------------------------------------------
# _broad_category() mapping
# ---------------------------------------------------------------------------


class TestBroadCategory:
    """Tests for the broad category mapping used in dedup decisions."""

    def test_style_and_grammar_same_group(self) -> None:
        """STYLE and GRAMMAR both map to 'language'."""
        assert _broad_category(IssueCategory.STYLE) == "language"
        assert _broad_category(IssueCategory.GRAMMAR) == "language"
        assert _broad_category(IssueCategory.WORD_USAGE) == "language"

    def test_technical_group(self) -> None:
        """TECHNICAL, NUMBERS, REFERENCES map to 'technical'."""
        assert _broad_category(IssueCategory.TECHNICAL) == "technical"
        assert _broad_category(IssueCategory.NUMBERS) == "technical"
        assert _broad_category(IssueCategory.REFERENCES) == "technical"

    def test_structure_group(self) -> None:
        """STRUCTURE and MODULAR map to 'structure'."""
        assert _broad_category(IssueCategory.STRUCTURE) == "structure"
        assert _broad_category(IssueCategory.MODULAR) == "structure"

    def test_audience_group(self) -> None:
        """AUDIENCE and LEGAL map to 'audience'."""
        assert _broad_category(IssueCategory.AUDIENCE) == "audience"
        assert _broad_category(IssueCategory.LEGAL) == "audience"

    def test_punctuation_group(self) -> None:
        """PUNCTUATION maps to 'punctuation'."""
        assert _broad_category(IssueCategory.PUNCTUATION) == "punctuation"

    def test_none_category(self) -> None:
        """None category maps to 'unknown'."""
        assert _broad_category(None) == "unknown"

    def test_technical_vs_language_are_different(self) -> None:
        """TECHNICAL and STYLE are in different broad categories."""
        assert _broad_category(IssueCategory.TECHNICAL) != _broad_category(IssueCategory.STYLE)


# ---------------------------------------------------------------------------
# Three-tier merge: deterministic > LanguageTool > LLM
# ---------------------------------------------------------------------------


class TestThreeTierMerge:
    """Tests for 3-tier merge hierarchy with LanguageTool (Tier 2)."""

    def test_three_tier_all_unique(self) -> None:
        """All three tiers with non-overlapping issues are all kept."""
        det = _make_issue(
            source="deterministic",
            flagged_text="utilize",
            span=[10, 17],
            category=IssueCategory.WORD_USAGE,
        )
        lt = _make_issue(
            source="languagetool",
            flagged_text="their going",
            span=[50, 61],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="very unique",
            span=[100, 111],
            confidence=0.9,
            category=IssueCategory.STYLE,
        )
        result = merge([det], [llm], lt_issues=[lt])
        assert len(result) == 3

    def test_lt_deduped_against_deterministic(self) -> None:
        """LT issue overlapping a deterministic issue (same category) is dropped."""
        det = _make_issue(
            source="deterministic",
            flagged_text="utilize",
            span=[10, 17],
            category=IssueCategory.WORD_USAGE,
        )
        lt = _make_issue(
            source="languagetool",
            flagged_text="utilize",
            span=[10, 17],
            category=IssueCategory.GRAMMAR,
        )
        result = merge([det], [], lt_issues=[lt])
        assert len(result) == 1
        assert result[0].source == "deterministic"

    def test_llm_deduped_against_lt(self) -> None:
        """LLM issue overlapping an LT issue (same category) is dropped."""
        lt = _make_issue(
            source="languagetool",
            flagged_text="their going",
            span=[50, 61],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="their going to",
            span=[50, 64],
            confidence=0.9,
            category=IssueCategory.GRAMMAR,
        )
        result = merge([], [llm], lt_issues=[lt])
        assert len(result) == 1
        assert result[0].source == "languagetool"

    def test_lt_survives_different_category(self) -> None:
        """LT issue with different broad category than deterministic survives."""
        det = _make_issue(
            source="deterministic",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.TECHNICAL,
        )
        lt = _make_issue(
            source="languagetool",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.GRAMMAR,
        )
        result = merge([det], [], lt_issues=[lt])
        assert len(result) == 2

    def test_cross_category_all_survive(self) -> None:
        """LT grammar + LLM audience on the same span both survive."""
        det = _make_issue(
            source="deterministic",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.TECHNICAL,
        )
        lt = _make_issue(
            source="languagetool",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="ostree",
            span=[100, 106],
            confidence=0.9,
            category=IssueCategory.AUDIENCE,
        )
        result = merge([det], [llm], lt_issues=[lt])
        # All three are different broad categories: technical, language, audience
        assert len(result) == 3

    def test_lt_cross_block_demotion(self) -> None:
        """LT issue crossing a block boundary gets suggestions cleared."""
        blocks = [
            _make_block(0, 100, "paragraph"),
            _make_block(100, 200, "code"),
        ]
        lt = _make_issue(
            source="languagetool",
            flagged_text="text crossing boundary",
            span=[90, 110],
            suggestions=["fixed text"],
            category=IssueCategory.GRAMMAR,
        )
        result = merge([], [], blocks=blocks, lt_issues=[lt])
        assert len(result) == 1
        assert result[0].suggestions == []

    def test_lt_none_treated_as_empty(self) -> None:
        """Passing lt_issues=None behaves like an empty list."""
        det = _make_issue(span=[10, 20])
        result = merge([det], [], lt_issues=None)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _merge_lt_tier() helper
# ---------------------------------------------------------------------------


class TestMergeLtTier:
    """Tests for the _merge_lt_tier() helper function."""

    def test_all_unique_lt_accepted(self) -> None:
        """LT issues with no deterministic overlap are all accepted."""
        det = _make_issue(
            flagged_text="utilize", span=[10, 17],
            category=IssueCategory.WORD_USAGE,
        )
        lt_a = _make_issue(
            source="languagetool", flagged_text="their",
            span=[50, 55], category=IssueCategory.GRAMMAR,
        )
        lt_b = _make_issue(
            source="languagetool", flagged_text="alot",
            span=[80, 84], category=IssueCategory.GRAMMAR,
        )
        accepted, kept, skipped = _merge_lt_tier([lt_a, lt_b], [det], [])
        assert kept == 2
        assert skipped == 0
        assert len(accepted) == 2

    def test_duplicate_lt_skipped(self) -> None:
        """LT issue duplicating a deterministic issue is skipped."""
        det = _make_issue(
            flagged_text="utilize",
            span=[10, 17],
            category=IssueCategory.WORD_USAGE,
        )
        lt = _make_issue(
            source="languagetool",
            flagged_text="utilize",
            span=[10, 17],
            category=IssueCategory.STYLE,
        )
        accepted, kept, skipped = _merge_lt_tier([lt], [det], [])
        assert kept == 0
        assert skipped == 1
        assert len(accepted) == 0

    def test_lt_to_lt_dedup_within_tier(self) -> None:
        """Two LT issues with same text are deduped within Tier 2."""
        lt_a = _make_issue(
            source="languagetool",
            flagged_text="their going",
            span=[50, 61],
            category=IssueCategory.GRAMMAR,
        )
        lt_b = _make_issue(
            source="languagetool",
            flagged_text="their going",
            span=[50, 61],
            category=IssueCategory.GRAMMAR,
        )
        _, kept, skipped = _merge_lt_tier([lt_a, lt_b], [], [])
        assert kept == 1
        assert skipped == 1


# ---------------------------------------------------------------------------
# _merge_llm_tier() with LT in priority pool
# ---------------------------------------------------------------------------


class TestMergeLlmTierWithLt:
    """Tests for _merge_llm_tier() when LT issues are in the priority pool."""

    def test_llm_deduped_against_lt_in_pool(self) -> None:
        """LLM issue with same text as LT in priority pool is dropped."""
        lt = _make_issue(
            source="languagetool",
            flagged_text="their going",
            span=[50, 61],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="their going",
            span=[50, 61],
            confidence=0.9,
            category=IssueCategory.GRAMMAR,
        )
        # Priority pool = deterministic + accepted LT
        _, kept, stats = _merge_llm_tier([llm], [lt], 0.7, [])
        assert kept == 0
        assert stats["skipped_overlap"] == 1

    def test_llm_survives_different_category_from_lt(self) -> None:
        """LLM with different broad category from LT survives."""
        lt = _make_issue(
            source="languagetool",
            flagged_text="ostree",
            span=[100, 106],
            category=IssueCategory.GRAMMAR,
        )
        llm = _make_issue(
            source="llm",
            flagged_text="ostree",
            span=[100, 106],
            confidence=0.9,
            category=IssueCategory.AUDIENCE,
        )
        _, kept, stats = _merge_llm_tier([llm], [lt], 0.7, [])
        assert kept == 1
        assert stats["skipped_overlap"] == 0
