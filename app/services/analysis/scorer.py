"""Quality scoring engine for the Content Editorial Assistant.

Computes an aggregate quality score from detected issues using a
severity-weighted, category-multiplied formula normalized by document
length. Also produces per-category counts and per-style-guide
compliance percentages.
"""

import logging
from math import log10

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse, ScoreResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

_SEVERITY_WEIGHTS: dict[IssueSeverity, float] = {
    IssueSeverity.HIGH: 3.0,
    IssueSeverity.MEDIUM: 2.0,
    IssueSeverity.LOW: 1.0,
}

_CATEGORY_MULTIPLIERS: dict[IssueCategory, float] = {
    IssueCategory.GRAMMAR: 1.5,
    IssueCategory.STRUCTURE: 1.3,
    IssueCategory.WORD_USAGE: 1.2,
    IssueCategory.STYLE: 1.0,
    IssueCategory.PUNCTUATION: 0.8,
    IssueCategory.NUMBERS: 1.0,
    IssueCategory.TECHNICAL: 1.0,
    IssueCategory.REFERENCES: 1.0,
    IssueCategory.LEGAL: 1.0,
    IssueCategory.AUDIENCE: 1.0,
    IssueCategory.MODULAR: 1.0,
}

_SCORE_FLOOR = 30

# Label thresholds: (min_score, label, color)
_SCORE_LABELS: list[tuple[int, str, str]] = [
    (90, "Excellent", "#3e8635"),
    (75, "Good", "#06c"),
    (60, "Needs Work", "#f0ab00"),
    (0, "Poor", "#c9190b"),
]

# Style guide names used for compliance calculation
_STYLE_GUIDES = [
    "IBM Style Guide",
    "Red Hat Supplementary Style Guide",
    "Getting Started with Accessibility for Writers",
    "Modular Documentation Reference Guide",
]


def calculate_score(
    issues: list[IssueResponse], word_count: int
) -> ScoreResponse:
    """Calculate the aggregate quality score for a document.

    Formula: S = max(30, 100 - sum(W_i * M_i) / (1 + log10(N_w / 100)))
    where W_i is severity weight, M_i is category multiplier, and
    N_w is word count.

    Dismissed and accepted issues are excluded from scoring.

    Args:
        issues: List of all detected issues.
        word_count: Total number of words in the document.

    Returns:
        ScoreResponse with score, label, color, category counts,
        and per-guide compliance percentages.
    """
    scorable = _filter_scorable(issues)
    penalty = _compute_penalty(scorable)
    normalizer = _compute_normalizer(word_count)
    raw_score = 100.0 - (penalty / normalizer)
    score = max(_SCORE_FLOOR, int(round(raw_score)))
    label, color = _get_label_and_color(score)
    category_counts = _count_by_category(issues)
    compliance = _compute_compliance(issues, word_count)

    logger.info(
        "Score: %d (%s), %d scorable issues, penalty=%.2f, normalizer=%.2f",
        score, label, len(scorable), penalty, normalizer,
    )

    return ScoreResponse(
        score=score,
        color=color,
        label=label,
        total_issues=len(issues),
        category_counts=category_counts,
        compliance=compliance,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _filter_scorable(issues: list[IssueResponse]) -> list[IssueResponse]:
    """Filter out dismissed and accepted issues from scoring.

    Args:
        issues: All detected issues.

    Returns:
        Only issues with OPEN status.
    """
    return [
        issue for issue in issues
        if issue.status == IssueStatus.OPEN
    ]


def _compute_penalty(scorable: list[IssueResponse]) -> float:
    """Sum severity-weighted, category-multiplied penalties.

    Args:
        scorable: Issues to include in the penalty calculation.

    Returns:
        Total penalty value.
    """
    total = 0.0
    for issue in scorable:
        weight = _SEVERITY_WEIGHTS.get(issue.severity, 2.0)
        multiplier = _CATEGORY_MULTIPLIERS.get(issue.category, 1.0)
        total += weight * multiplier
    return total


def _compute_normalizer(word_count: int) -> float:
    """Compute the word-count normalizer for the scoring formula.

    Uses 1 + log10(N_w / 100) to scale the penalty relative to
    document length. Ensures the divisor is always at least 1.0.

    Args:
        word_count: Total number of words in the document.

    Returns:
        Normalizer value (minimum 1.0).
    """
    if word_count <= 100:
        return 1.0
    return 1.0 + log10(word_count / 100.0)


def _get_label_and_color(score: int) -> tuple[str, str]:
    """Determine the quality label and color for a numeric score.

    Args:
        score: Quality score (0-100).

    Returns:
        Tuple of (label, color) matching the score threshold.
    """
    for threshold, label, color in _SCORE_LABELS:
        if score >= threshold:
            return label, color
    return "Poor", "#c9190b"


def _count_by_category(issues: list[IssueResponse]) -> dict[str, int]:
    """Count issues per category.

    Args:
        issues: All detected issues.

    Returns:
        Dictionary mapping category value strings to counts.
    """
    counts: dict[str, int] = {}
    for issue in issues:
        key = issue.category.value if isinstance(issue.category, IssueCategory) else str(issue.category)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _compute_compliance(
    issues: list[IssueResponse], word_count: int
) -> dict[str, float]:
    """Compute per-style-guide compliance percentages.

    Compliance is estimated as 1.0 minus the ratio of issues
    citing a given guide to total words, capped at [0.0, 1.0].
    Guides with no issues receive 1.0 compliance.

    Args:
        issues: All detected issues.
        word_count: Total number of words.

    Returns:
        Dictionary mapping guide names to compliance floats.
    """
    guide_issue_counts: dict[str, int] = {}
    for guide in _STYLE_GUIDES:
        guide_issue_counts[guide] = 0

    for issue in issues:
        if issue.status != IssueStatus.OPEN:
            continue
        citation = issue.style_guide_citation
        for guide in _STYLE_GUIDES:
            if guide in citation:
                guide_issue_counts[guide] = guide_issue_counts.get(guide, 0) + 1
                break

    compliance: dict[str, float] = {}
    effective_count = max(word_count, 1)
    for guide in _STYLE_GUIDES:
        count = guide_issue_counts.get(guide, 0)
        ratio = count / effective_count
        compliance[guide] = round(max(0.0, min(1.0, 1.0 - ratio)), 4)

    return compliance
