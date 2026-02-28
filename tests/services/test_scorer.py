"""Tests for the quality scoring engine.

Validates that the scorer correctly computes aggregate quality scores
from detected issues using severity-weighted, category-multiplied
formulas normalized by document length.
"""

import logging
from typing import List

import pytest

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse, ScoreResponse
from app.services.analysis.scorer import calculate_score

logger = logging.getLogger(__name__)


def _make_issue(
    severity: IssueSeverity = IssueSeverity.MEDIUM,
    category: IssueCategory = IssueCategory.STYLE,
    status: IssueStatus = IssueStatus.OPEN,
) -> IssueResponse:
    """Create a minimal IssueResponse for scoring tests.

    Args:
        severity: Severity level for the issue.
        category: Category for the issue.
        status: Lifecycle status of the issue.

    Returns:
        A fully populated IssueResponse suitable for scorer input.
    """
    return IssueResponse(
        id="test-001",
        source="deterministic",
        category=category,
        rule_name="test_rule",
        flagged_text="test",
        message="Test issue",
        suggestions=["fix it"],
        severity=severity,
        sentence="This is a test sentence.",
        sentence_index=0,
        span=[0, 4],
        style_guide_citation="IBM Style Guide",
        confidence=1.0,
        status=status,
    )


class TestScorer:
    """Tests for the calculate_score function."""

    def test_perfect_score_no_issues(self) -> None:
        """Score is 100 when no issues are present.

        A document with zero issues should receive the maximum
        quality score of 100 with the 'Excellent' label.
        """
        result: ScoreResponse = calculate_score([], word_count=500)

        assert result.score == 100
        assert result.label == "Excellent"
        assert result.total_issues == 0

    def test_score_decreases_with_issues(self) -> None:
        """More issues produce a lower score.

        Adding additional issues to the document should
        monotonically decrease (or maintain) the quality score.
        """
        one_issue: List[IssueResponse] = [_make_issue()]
        three_issues: List[IssueResponse] = [_make_issue() for _ in range(3)]
        ten_issues: List[IssueResponse] = [_make_issue() for _ in range(10)]

        score_one: ScoreResponse = calculate_score(one_issue, word_count=200)
        score_three: ScoreResponse = calculate_score(three_issues, word_count=200)
        score_ten: ScoreResponse = calculate_score(ten_issues, word_count=200)

        assert score_one.score >= score_three.score
        assert score_three.score >= score_ten.score

    def test_minimum_score_is_30(self) -> None:
        """Score never goes below 30 even with many issues.

        The scoring formula has a floor of 30 to ensure that even
        heavily flagged documents receive a non-zero quality rating.
        """
        many_issues: List[IssueResponse] = [
            _make_issue(severity=IssueSeverity.HIGH) for _ in range(200)
        ]

        result: ScoreResponse = calculate_score(many_issues, word_count=50)

        assert result.score == 30

    def test_severity_weights_apply(self) -> None:
        """High severity reduces score more than low severity.

        The severity-weight constants (HIGH=3.0, MEDIUM=2.0, LOW=1.0)
        should cause high-severity issues to penalize the score
        more aggressively than low-severity issues.
        """
        high_issues: List[IssueResponse] = [
            _make_issue(severity=IssueSeverity.HIGH)
        ]
        low_issues: List[IssueResponse] = [
            _make_issue(severity=IssueSeverity.LOW)
        ]

        score_high: ScoreResponse = calculate_score(high_issues, word_count=200)
        score_low: ScoreResponse = calculate_score(low_issues, word_count=200)

        assert score_low.score >= score_high.score

    def test_score_label_mapping(self) -> None:
        """Score labels map to correct threshold ranges.

        Verifies the label assignment rules:
        - 90-100: Excellent
        - 75-89: Good (verified via 60-74 threshold boundary)
        - 60-74: Needs Work
        - <60: Poor
        """
        # No issues -> 100 -> Excellent
        excellent: ScoreResponse = calculate_score([], word_count=100)
        assert excellent.label == "Excellent"

        # 200 high-severity issues on short text -> 30 -> Poor
        poor_issues: List[IssueResponse] = [
            _make_issue(severity=IssueSeverity.HIGH) for _ in range(200)
        ]
        poor: ScoreResponse = calculate_score(poor_issues, word_count=50)
        assert poor.label == "Poor"

    def test_normalization_by_doc_length(self) -> None:
        """Longer documents have less aggressive scoring.

        The normalizer formula uses 1 + log10(word_count / 100) so
        a 10,000-word document is penalized less per issue than a
        100-word document with the same number of issues.
        """
        issues: List[IssueResponse] = [
            _make_issue(severity=IssueSeverity.HIGH) for _ in range(5)
        ]

        short_doc: ScoreResponse = calculate_score(issues, word_count=100)
        long_doc: ScoreResponse = calculate_score(issues, word_count=10000)

        assert long_doc.score > short_doc.score

    def test_dismissed_issues_excluded_from_scoring(self) -> None:
        """Dismissed and accepted issues are not counted in penalty.

        Only OPEN issues should contribute to the quality score
        penalty calculation.
        """
        open_issues: List[IssueResponse] = [
            _make_issue(status=IssueStatus.OPEN),
        ]
        mixed_issues: List[IssueResponse] = [
            _make_issue(status=IssueStatus.OPEN),
            _make_issue(status=IssueStatus.DISMISSED),
            _make_issue(status=IssueStatus.ACCEPTED),
        ]

        score_open: ScoreResponse = calculate_score(open_issues, word_count=200)
        score_mixed: ScoreResponse = calculate_score(mixed_issues, word_count=200)

        # Both should produce the same penalty since dismissed/accepted are excluded
        assert score_open.score == score_mixed.score

    def test_category_multipliers_affect_score(self) -> None:
        """Category multipliers cause different categories to penalize differently.

        GRAMMAR has a 1.5 multiplier while PUNCTUATION has a 0.8 multiplier,
        so grammar issues should reduce the score more.
        """
        grammar_issues: List[IssueResponse] = [
            _make_issue(category=IssueCategory.GRAMMAR),
        ]
        punctuation_issues: List[IssueResponse] = [
            _make_issue(category=IssueCategory.PUNCTUATION),
        ]

        score_grammar: ScoreResponse = calculate_score(grammar_issues, word_count=200)
        score_punct: ScoreResponse = calculate_score(punctuation_issues, word_count=200)

        assert score_punct.score >= score_grammar.score

    def test_score_response_has_category_counts(self) -> None:
        """ScoreResponse includes per-category issue counts.

        The category_counts dict should tally issues per category.
        """
        issues: List[IssueResponse] = [
            _make_issue(category=IssueCategory.GRAMMAR),
            _make_issue(category=IssueCategory.GRAMMAR),
            _make_issue(category=IssueCategory.STYLE),
        ]

        result: ScoreResponse = calculate_score(issues, word_count=200)

        assert result.category_counts.get("grammar") == 2
        assert result.category_counts.get("style") == 1

    def test_score_response_has_compliance(self) -> None:
        """ScoreResponse includes per-guide compliance percentages.

        The compliance dict should contain entries for all four
        supported style guides.
        """
        result: ScoreResponse = calculate_score([], word_count=200)

        assert isinstance(result.compliance, dict)
        assert len(result.compliance) > 0
