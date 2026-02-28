"""Report builder — assembles statistical reports from analysis results.

Combines document statistics, readability metrics, category breakdowns,
and per-guide compliance percentages into a single ReportResponse.
"""

import logging
from typing import Any

from app.models.enums import IssueCategory
from app.models.schemas import ReportResponse
from app.services.reporting.readability import calculate_readability

logger = logging.getLogger(__name__)

# Maps each style guide to the IssueCategory values it covers.
# Used to compute per-guide compliance percentages.
_GUIDE_CATEGORY_MAP: dict[str, list[str]] = {
    "ibm": [
        IssueCategory.STYLE.value,
        IssueCategory.GRAMMAR.value,
        IssueCategory.WORD_USAGE.value,
        IssueCategory.PUNCTUATION.value,
        IssueCategory.NUMBERS.value,
    ],
    "red_hat": [
        IssueCategory.TECHNICAL.value,
        IssueCategory.REFERENCES.value,
        IssueCategory.LEGAL.value,
    ],
    "accessibility": [
        IssueCategory.AUDIENCE.value,
    ],
    "modular_docs": [
        IssueCategory.MODULAR.value,
        IssueCategory.STRUCTURE.value,
    ],
}

# Total expected rules per guide, used as the denominator for compliance.
# These are approximations based on the rule catalog size per guide.
_GUIDE_RULE_COUNTS: dict[str, int] = {
    "ibm": 50,
    "red_hat": 25,
    "accessibility": 15,
    "modular_docs": 20,
}


def build_report(
    issues: list[Any],
    word_count: int,
    sentence_count: int,
    paragraph_count: int,
    avg_words_per_sentence: float,
    avg_syllables_per_word: float,
    text: str,
) -> ReportResponse:
    """Build the complete statistical report from analysis results.

    Assembles document-level statistics, readability scores, per-category
    issue counts, and per-guide compliance percentages into a single
    ReportResponse dataclass.

    Args:
        issues: List of IssueResponse instances from the analysis.
        word_count: Total word count for the document.
        sentence_count: Total sentence count for the document.
        paragraph_count: Total paragraph count for the document.
        avg_words_per_sentence: Mean words per sentence.
        avg_syllables_per_word: Mean syllables per word.
        text: The full document text, used for readability scoring.

    Returns:
        A fully populated ReportResponse instance.
    """
    readability = calculate_readability(text)
    category_breakdown = _count_issues_by_category(issues)
    compliance = _calculate_compliance(category_breakdown)

    logger.debug(
        "Built report: %d words, %d issues, %d categories",
        word_count,
        len(issues),
        len(category_breakdown),
    )

    return ReportResponse(
        word_count=word_count,
        sentence_count=sentence_count,
        paragraph_count=paragraph_count,
        avg_words_per_sentence=round(avg_words_per_sentence, 2),
        avg_syllables_per_word=round(avg_syllables_per_word, 2),
        readability=readability,
        category_breakdown=category_breakdown,
        compliance=compliance,
    )


def _count_issues_by_category(issues: list[Any]) -> dict[str, int]:
    """Count the number of issues in each editorial category.

    Handles both IssueCategory enum instances and plain string values
    for the category field on each issue.

    Args:
        issues: List of IssueResponse instances.

    Returns:
        Dictionary mapping category name strings to issue counts.
    """
    counts: dict[str, int] = {}
    for issue in issues:
        category = _extract_category_value(issue)
        counts[category] = counts.get(category, 0) + 1
    return counts


def _extract_category_value(issue: Any) -> str:
    """Extract the string value of an issue's category.

    Supports IssueCategory enum instances, plain strings, and objects
    with a `.value` attribute.

    Args:
        issue: An IssueResponse or compatible object.

    Returns:
        The category as a plain string.
    """
    category = getattr(issue, "category", "style")
    if isinstance(category, IssueCategory):
        return category.value
    if hasattr(category, "value"):
        return str(category.value)
    return str(category)


def _calculate_compliance(category_breakdown: dict[str, int]) -> dict[str, float]:
    """Calculate per-guide compliance percentages.

    For each style guide, compliance is computed as:
        1.0 - (issues_in_guide_categories / total_rules_for_guide)

    The result is clamped to the range [0.0, 1.0].

    Args:
        category_breakdown: Issue counts keyed by category name.

    Returns:
        Dictionary mapping guide names to compliance floats (0.0-1.0).
    """
    compliance: dict[str, float] = {}

    for guide_name, categories in _GUIDE_CATEGORY_MAP.items():
        issue_count = _sum_issues_for_categories(category_breakdown, categories)
        total_rules = _GUIDE_RULE_COUNTS.get(guide_name, 1)
        raw_compliance = 1.0 - (issue_count / total_rules)
        compliance[guide_name] = round(max(0.0, min(1.0, raw_compliance)), 4)

    return compliance


def _sum_issues_for_categories(
    category_breakdown: dict[str, int],
    categories: list[str],
) -> int:
    """Sum issue counts across the specified category names.

    Args:
        category_breakdown: Issue counts keyed by category name.
        categories: List of category name strings to include.

    Returns:
        Total issue count across the specified categories.
    """
    total = 0
    for category in categories:
        total += category_breakdown.get(category, 0)
    return total
