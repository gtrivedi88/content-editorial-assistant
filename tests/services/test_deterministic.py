"""Tests for the deterministic analysis engine.

Validates that the deterministic analyzer correctly executes all rules,
normalizes raw error dicts into IssueResponse instances, and properly
filters excepted/technical content.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse

logger = logging.getLogger(__name__)


def _make_raw_error(
    rule_type: str = "word_usage_test",
    message: str = "Test issue found",
    severity: str = "medium",
    flagged_text: str = "utilize",
    sentence: str = "Please utilize the tool.",
    sentence_index: int = 0,
    suggestions: list[str] | None = None,
    span: list[int] | None = None,
) -> Dict[str, Any]:
    """Create a raw error dict as returned by rules.

    Args:
        rule_type: Rule type identifier string.
        message: Human-readable error message.
        severity: Severity level string.
        flagged_text: The flagged text span.
        sentence: Containing sentence.
        sentence_index: Sentence index in the document.
        suggestions: Suggested corrections.
        span: Character offset span.

    Returns:
        A raw error dictionary matching the format produced by BaseRule._create_error.
    """
    if suggestions is None:
        suggestions = ["use"]
    error: Dict[str, Any] = {
        "type": rule_type,
        "message": message,
        "severity": severity,
        "flagged_text": flagged_text,
        "sentence": sentence,
        "sentence_index": sentence_index,
        "suggestions": suggestions,
    }
    if span is not None:
        error["span"] = span
    return error


class TestDeterministicAnalyzer:
    """Tests for deterministic.analyze()."""

    @patch("app.services.analysis.deterministic.get_registry")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    def test_returns_issue_dicts(
        self,
        mock_confidence: MagicMock,
        mock_citation: MagicMock,
        mock_get_registry: MagicMock,
    ) -> None:
        """Run deterministic analysis returns list of properly formatted IssueResponse objects.

        Each returned item should be an IssueResponse with all required
        fields populated, including id, source, category, message, etc.
        """
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(
                rule_type="word_usage_test",
                message="Avoid 'utilize'; use 'use' instead.",
                flagged_text="utilize",
                sentence="Please utilize the tool.",
                span=[7, 14],
            ),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        text = "Please utilize the tool."
        sentences = ["Please utilize the tool."]
        spacy_doc = MagicMock()

        issues: List[IssueResponse] = analyze(text, sentences, spacy_doc)

        assert len(issues) >= 1
        issue = issues[0]
        assert isinstance(issue, IssueResponse)
        assert issue.source == "deterministic"
        assert issue.message != ""
        assert issue.id != ""
        assert isinstance(issue.span, list)
        assert len(issue.span) == 2

    @patch("app.services.analysis.deterministic.get_registry")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    def test_protected_terms_skipped(
        self,
        mock_confidence: MagicMock,
        mock_citation: MagicMock,
        mock_get_registry: MagicMock,
    ) -> None:
        """System errors and empty-message errors are filtered out.

        Errors with type 'system_error' or missing message fields should
        not appear in the normalized output.
        """
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(
                rule_type="system_error",
                message="Rule XYZ failed: index error",
            ),
            _make_raw_error(
                rule_type="word_usage_test",
                message="",
            ),
            _make_raw_error(
                rule_type="word_usage_test",
                message="Valid issue",
                flagged_text="utilize",
            ),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        text = "Please utilize the tool."
        sentences = ["Please utilize the tool."]
        spacy_doc = MagicMock()

        issues: List[IssueResponse] = analyze(text, sentences, spacy_doc)

        # system_error and empty-message should be filtered out
        assert len(issues) == 1
        assert issues[0].message == "Valid issue"

    @patch("app.services.analysis.deterministic.get_registry")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    def test_categories_are_valid(
        self,
        mock_confidence: MagicMock,
        mock_citation: MagicMock,
        mock_get_registry: MagicMock,
    ) -> None:
        """All returned issue categories are valid IssueCategory values.

        The _CATEGORY_MAP must map rule_type prefixes to valid
        IssueCategory enum members, and unrecognized types should
        default to IssueCategory.STYLE.
        """
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(rule_type="word_usage_articles"),
            _make_raw_error(rule_type="language_and_grammar_passive"),
            _make_raw_error(rule_type="punctuation_commas"),
            _make_raw_error(rule_type="unknown_rule_type"),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        text = "Test text for category validation."
        sentences = ["Test text for category validation."]
        spacy_doc = MagicMock()

        issues: List[IssueResponse] = analyze(text, sentences, spacy_doc)

        valid_categories = set(IssueCategory)
        for issue in issues:
            assert issue.category in valid_categories, (
                f"Issue category {issue.category} is not a valid IssueCategory"
            )

    @patch("app.services.analysis.deterministic.get_registry")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    def test_severity_resolution(
        self,
        mock_confidence: MagicMock,
        mock_citation: MagicMock,
        mock_get_registry: MagicMock,
    ) -> None:
        """Severity strings are correctly mapped to IssueSeverity enums.

        Raw severity values from rule errors should map to LOW, MEDIUM,
        or HIGH enum values. Unknown values default to MEDIUM.
        """
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(severity="high", flagged_text="error1", sentence="Sentence one."),
            _make_raw_error(severity="low", flagged_text="error2", sentence="Sentence two."),
            _make_raw_error(severity="unknown_severity", flagged_text="error3", sentence="Sentence three."),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        issues: List[IssueResponse] = analyze("test", ["test"], MagicMock())

        assert issues[0].severity == IssueSeverity.HIGH
        assert issues[1].severity == IssueSeverity.LOW
        assert issues[2].severity == IssueSeverity.MEDIUM

    @patch("app.services.analysis.deterministic.get_registry")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    def test_span_resolution_from_flagged_text(
        self,
        mock_confidence: MagicMock,
        mock_citation: MagicMock,
        mock_get_registry: MagicMock,
    ) -> None:
        """Span is calculated from flagged_text when not provided explicitly.

        When a raw error does not include a 'span' key, the normalizer
        should locate the flagged_text within the full text and compute
        the character offsets.
        """
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(
                flagged_text="utilize",
                sentence="Please utilize the tool.",
            ),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        text = "Please utilize the tool."
        issues: List[IssueResponse] = analyze(text, [text], MagicMock())

        assert len(issues) == 1
        span = issues[0].span
        assert span[0] == text.find("utilize")
        assert span[1] == span[0] + len("utilize")


# ===================================================================
# Placeholder filter — contains check
# ===================================================================


class TestPlaceholderFilter:
    """Validate the strengthened placeholder filter uses contains check."""

    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_registry")
    def test_exact_placeholder_filtered(
        self,
        mock_get_registry: MagicMock,
        mock_citation: MagicMock,
        mock_confidence: MagicMock,
    ) -> None:
        """Issue with flagged_text exactly 'placeholder' is filtered."""
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(flagged_text="placeholder"),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        issues = analyze("Some placeholder text.", ["Some placeholder text."], MagicMock())
        assert len(issues) == 0, "Exact 'placeholder' should be filtered"

    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_registry")
    def test_placeholder_substring_filtered(
        self,
        mock_get_registry: MagicMock,
        mock_citation: MagicMock,
        mock_confidence: MagicMock,
    ) -> None:
        """Issue containing 'placeholder' as substring is also filtered."""
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(flagged_text="placeholder command"),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        issues = analyze(
            "Run placeholder command now.",
            ["Run placeholder command now."],
            MagicMock(),
        )
        assert len(issues) == 0, "'placeholder command' should be filtered (contains check)"

    @patch("app.services.analysis.deterministic.get_confidence_adjustment")
    @patch("app.services.analysis.deterministic.format_citation")
    @patch("app.services.analysis.deterministic.get_registry")
    def test_legitimate_text_not_filtered(
        self,
        mock_get_registry: MagicMock,
        mock_citation: MagicMock,
        mock_confidence: MagicMock,
    ) -> None:
        """Issues without 'placeholder' in flagged_text survive the filter."""
        mock_confidence.return_value = 0.0
        mock_citation.return_value = "IBM Style Guide"

        mock_registry = MagicMock()
        mock_registry.analyze.return_value = [
            _make_raw_error(flagged_text="utilize"),
        ]
        mock_get_registry.return_value = mock_registry

        from app.services.analysis.deterministic import analyze

        issues = analyze("Please utilize the tool.", ["Please utilize the tool."], MagicMock())
        assert len(issues) == 1, "'utilize' should NOT be filtered"


# ===================================================================
# _resolve_span — sentence-relative to text-relative adjustment
# ===================================================================


class TestResolveSpanSentenceRelative:
    """Verify _resolve_span adjusts sentence-relative spans."""

    def test_multi_sentence_block_adjusts_span(self) -> None:
        """Span in second sentence is adjusted to text-relative."""
        from app.services.analysis.deterministic import _resolve_span

        text = "First sentence here. It then sends a request."
        sentence = "It then sends a request."
        error = {"span": [3, 7]}
        result = _resolve_span(error, text, "then", sentence)
        sent_pos = text.find(sentence)
        assert result == [sent_pos + 3, sent_pos + 7]
        assert text[result[0]:result[1]] == "then"

    def test_single_sentence_no_adjustment(self) -> None:
        """Span at document start (sent_pos=0) is not adjusted."""
        from app.services.analysis.deterministic import _resolve_span

        text = "It then sends a request."
        sentence = "It then sends a request."
        error = {"span": [3, 7]}
        result = _resolve_span(error, text, "then", sentence)
        assert result == [3, 7]

    def test_text_relative_span_not_double_adjusted(self) -> None:
        """Span already text-relative (end > sentence length) stays as-is."""
        from app.services.analysis.deterministic import _resolve_span

        text = "Hello world. Second sentence. Bold code at end."
        sentence = "Second sentence."
        error = {"span": [35, 42]}
        result = _resolve_span(error, text, "code at", sentence)
        assert result == [35, 42]

    def test_no_span_falls_back_to_text_search(self) -> None:
        """Without a span, falls back to text.find(flagged_text)."""
        from app.services.analysis.deterministic import _resolve_span

        text = "Use active voice instead of passive."
        error: Dict[str, Any] = {}
        result = _resolve_span(error, text, "active", "Use active voice instead of passive.")
        assert result == [4, 10]
