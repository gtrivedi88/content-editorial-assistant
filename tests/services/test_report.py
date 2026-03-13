"""Tests for reporting services: readability metrics and report builder.

Validates that readability calculations return all four standard metrics
with explanatory help text, and that the report builder produces
complete ReportResponse objects with document statistics.
"""

import logging
from typing import Any, Dict

import pytest

from app.models.schemas import ReportResponse
from app.services.reporting.readability import calculate_readability

logger = logging.getLogger(__name__)

# Sample text long enough for meaningful readability analysis
_SAMPLE_TEXT: str = (
    "Technical documentation should be clear and concise. "
    "Writers must consider their audience carefully when creating content. "
    "Each paragraph should focus on a single topic to improve readability. "
    "Use short sentences and familiar words whenever possible. "
    "Active voice is preferred over passive voice in most technical writing."
)

# All four expected readability metric names
_EXPECTED_METRICS: list[str] = [
    "Flesch Reading Ease",
    "Flesch-Kincaid Grade",
    "Gunning Fog",
    "Coleman-Liau",
]


class TestReadability:
    """Tests for the readability metric calculation module."""

    def test_readability_all_metrics_present(self) -> None:
        """All four readability scores are present in the result.

        The calculate_readability function must return entries for
        Flesch Reading Ease, Flesch-Kincaid Grade, Gunning Fog,
        and Coleman-Liau.
        """
        result: Dict[str, Dict[str, object]] = calculate_readability(_SAMPLE_TEXT)

        for metric_name in _EXPECTED_METRICS:
            assert metric_name in result, (
                f"Missing readability metric: {metric_name}"
            )
            assert "score" in result[metric_name], (
                f"Metric '{metric_name}' missing 'score' key"
            )

    def test_readability_help_text_present(self) -> None:
        """Each readability metric has a non-empty help_text field.

        Help text provides the user with context for interpreting
        the numeric score, so it must always be present.
        """
        result: Dict[str, Dict[str, object]] = calculate_readability(_SAMPLE_TEXT)

        for metric_name in _EXPECTED_METRICS:
            assert metric_name in result
            metric_data = result[metric_name]
            assert "help_text" in metric_data, (
                f"Metric '{metric_name}' missing 'help_text' key"
            )
            assert isinstance(metric_data["help_text"], str)
            assert len(str(metric_data["help_text"])) > 0, (
                f"Metric '{metric_name}' has empty help_text"
            )

    def test_readability_scores_are_numeric(self) -> None:
        """All readability scores are numeric (float or int).

        Scores produced by textstat must be convertible to float.
        """
        result: Dict[str, Dict[str, object]] = calculate_readability(_SAMPLE_TEXT)

        for metric_name in _EXPECTED_METRICS:
            score = result[metric_name]["score"]
            assert isinstance(score, (int, float)), (
                f"Metric '{metric_name}' score is not numeric: {type(score)}"
            )

    def test_readability_short_text_returns_zeros(self) -> None:
        """Very short text returns zero scores for all metrics.

        Text with fewer than 3 words is too short for meaningful
        readability analysis and should return 0.0 for all metrics.
        """
        result: Dict[str, Dict[str, object]] = calculate_readability("Hi.")

        for metric_name in _EXPECTED_METRICS:
            assert metric_name in result
            assert result[metric_name]["score"] == 0.0

    def test_readability_empty_text_returns_zeros(self) -> None:
        """Empty text returns zero scores for all metrics.

        An empty string input should not raise an error but return
        all-zero scores with help text still present.
        """
        result: Dict[str, Dict[str, object]] = calculate_readability("")

        for metric_name in _EXPECTED_METRICS:
            assert metric_name in result
            assert result[metric_name]["score"] == 0.0
            assert "help_text" in result[metric_name]


class TestReportBuilder:
    """Tests for the report builder module."""

    def test_report_has_word_count(self) -> None:
        """Report includes word_count in the response.

        The ReportResponse must contain the total word count passed
        to the builder function.
        """
        from app.services.reporting.builder import build_report

        report: ReportResponse = build_report(
            issues=[],
            word_count=150,
            sentence_count=10,
            paragraph_count=3,
            avg_words_per_sentence=15.0,
            avg_syllables_per_word=1.5,
            text=_SAMPLE_TEXT,
        )

        assert report.word_count == 150

    def test_report_has_sentence_count(self) -> None:
        """Report includes sentence_count in the response.

        The ReportResponse must contain the total sentence count
        passed to the builder function.
        """
        from app.services.reporting.builder import build_report

        report: ReportResponse = build_report(
            issues=[],
            word_count=150,
            sentence_count=10,
            paragraph_count=3,
            avg_words_per_sentence=15.0,
            avg_syllables_per_word=1.5,
            text=_SAMPLE_TEXT,
        )

        assert report.sentence_count == 10

    def test_report_has_readability_metrics(self) -> None:
        """Report includes readability metrics from calculate_readability.

        The readability dict should contain entries for all four
        standard metrics.
        """
        from app.services.reporting.builder import build_report

        report: ReportResponse = build_report(
            issues=[],
            word_count=150,
            sentence_count=10,
            paragraph_count=3,
            avg_words_per_sentence=15.0,
            avg_syllables_per_word=1.5,
            text=_SAMPLE_TEXT,
        )

        assert isinstance(report.readability, dict)
        for metric_name in _EXPECTED_METRICS:
            assert metric_name in report.readability, (
                f"Report readability missing metric: {metric_name}"
            )

    def test_report_has_compliance(self) -> None:
        """Report includes per-guide compliance percentages.

        The compliance dict should map guide identifiers to float
        percentages between 0.0 and 1.0.
        """
        from app.services.reporting.builder import build_report

        report: ReportResponse = build_report(
            issues=[],
            word_count=150,
            sentence_count=10,
            paragraph_count=3,
            avg_words_per_sentence=15.0,
            avg_syllables_per_word=1.5,
            text=_SAMPLE_TEXT,
        )

        assert isinstance(report.compliance, dict)
        for guide, value in report.compliance.items():
            assert 0.0 <= value <= 1.0, (
                f"Compliance for '{guide}' out of range: {value}"
            )

    def test_report_to_dict_serialization(self) -> None:
        """Report can be serialized to a JSON-compatible dict.

        The to_dict() method should produce a dictionary with all
        expected top-level keys.
        """
        from app.services.reporting.builder import build_report

        report: ReportResponse = build_report(
            issues=[],
            word_count=100,
            sentence_count=5,
            paragraph_count=2,
            avg_words_per_sentence=20.0,
            avg_syllables_per_word=1.3,
            text=_SAMPLE_TEXT,
        )

        report_dict: Dict[str, Any] = report.to_dict()

        assert "word_count" in report_dict
        assert "sentence_count" in report_dict
        assert "readability" in report_dict
        assert "category_breakdown" in report_dict
        assert "compliance" in report_dict
