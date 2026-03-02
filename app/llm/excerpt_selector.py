"""Category-triggered style guide excerpt selection.

Maps issue categories detected by deterministic rules to relevant
style guide sections, then selects and budgets excerpts for inclusion
in LLM prompts.  Uses an adaptive token budget that scales inversely
with document size to keep prompt lengths manageable.

Usage:
    from app.llm.excerpt_selector import select_excerpts

    excerpts = select_excerpts(deterministic_issues, "procedure", 2500)
"""

import logging
from typing import Optional

from style_guides.registry import get_excerpt

logger = logging.getLogger(__name__)

# Maps IssueCategory values to lists of (rule_type, category_hint) pairs
# used to look up relevant style guide excerpts.
_CATEGORY_TO_GUIDES: dict[str, list[tuple[str, Optional[str]]]] = {
    "word-usage": [
        ("word_choice", "word_usage"),
        ("terminology", "word_usage"),
        ("product_names", "legal_information"),
    ],
    "punctuation": [
        ("punctuation", "punctuation"),
        ("commas", "punctuation"),
        ("semicolons", "punctuation"),
        ("colons", "punctuation"),
        ("hyphens", "punctuation"),
    ],
    "structure": [
        ("structure", "structure_and_format"),
        ("headings", "structure_and_format"),
        ("lists", "structure_and_format"),
        ("modular_structure", "modular_compliance"),
    ],
    "grammar": [
        ("grammar", "language_and_grammar"),
        ("articles", "language_and_grammar"),
        ("verb_tense", "language_and_grammar"),
        ("subject_verb", "language_and_grammar"),
    ],
    "audience": [
        ("minimalism", "audience_and_medium"),
        ("accessibility", "audience_and_medium"),
        ("task_orientation", "audience_and_medium"),
    ],
    "legal": [
        ("trademarks", "legal_information"),
        ("product_names", "legal_information"),
        ("legal_language", "legal_information"),
    ],
    "style": [
        ("tone", "audience_and_medium"),
        ("voice", "language_and_grammar"),
        ("conciseness", "language_and_grammar"),
    ],
    "numbers": [
        ("numbers", "numbers_and_measurement"),
        ("units", "numbers_and_measurement"),
    ],
    "technical": [
        ("code_elements", "technical_elements"),
        ("ui_elements", "technical_elements"),
    ],
    "references": [
        ("cross_references", "references"),
        ("links", "references"),
    ],
    "modular": [
        ("modular_structure", "modular_compliance"),
        ("prerequisites", "modular_compliance"),
        ("procedures", "modular_compliance"),
    ],
}

# Maps content_type to additional rule lookups that always apply
_CONTENT_TYPE_GUIDES: dict[str, list[tuple[str, Optional[str]]]] = {
    "concept": [
        ("concept_module", "modular_compliance"),
        ("introductions", "structure_and_format"),
    ],
    "procedure": [
        ("procedure_module", "modular_compliance"),
        ("procedures", "modular_compliance"),
        ("steps", "structure_and_format"),
    ],
    "reference": [
        ("reference_module", "modular_compliance"),
        ("tables", "structure_and_format"),
    ],
    "assembly": [
        ("assembly_module", "modular_compliance"),
        ("includes", "modular_compliance"),
    ],
}

# Estimated average tokens per character for budget calculations
_TOKENS_PER_CHAR = 0.25


def select_excerpts(
    deterministic_issues: list,
    content_type: str,
) -> list[dict]:
    """Select relevant style guide excerpts based on deterministic results.

    Maps detected issue categories to style guide sections, fetches
    excerpts, and includes all available excerpts (the total pool is
    ~4K tokens across 188 rules, well within model capacity).

    Args:
        deterministic_issues: List of issue dicts or IssueResponse
            objects from deterministic analysis.
        content_type: Modular documentation type
            (concept/procedure/reference/assembly).

    Returns:
        List of excerpt dicts, each with ``guide_name``, ``category``,
        ``topic``, and ``excerpt`` keys.
    """
    budget = _compute_token_budget()
    category_counts = _count_categories(deterministic_issues)
    lookups = _gather_lookups(category_counts, content_type)
    raw_excerpts = _fetch_excerpts(lookups)

    if not raw_excerpts:
        return []

    prioritized = _prioritize_excerpts(raw_excerpts, category_counts)
    return _apply_budget(prioritized, budget)


# ------------------------------------------------------------------
# Budget computation
# ------------------------------------------------------------------


def _compute_token_budget() -> int:
    """Compute the token budget for style guide excerpts.

    Returns a fixed high budget that accommodates the full excerpt
    pool (~4K tokens across 188 rules).  The previous adaptive budget
    (3K–8K) trimmed excerpts for documents >5K words, but the total
    pool is small enough to include unconditionally.

    Returns:
        Token budget as an integer.
    """
    return 100_000


# ------------------------------------------------------------------
# Category counting
# ------------------------------------------------------------------


def _count_categories(issues: list) -> dict[str, int]:
    """Count how many issues exist per category.

    Handles both plain dicts and objects with a ``category`` attribute.

    Args:
        issues: List of issue dicts or IssueResponse objects.

    Returns:
        Dict mapping category string to count.
    """
    counts: dict[str, int] = {}

    for issue in issues:
        category = _get_category(issue)
        if category:
            counts[category] = counts.get(category, 0) + 1

    return counts


def _get_category(issue: object) -> str:
    """Extract the category string from an issue.

    Args:
        issue: An issue dict or IssueResponse object.

    Returns:
        Category string, or empty string if not found.
    """
    if isinstance(issue, dict):
        cat = issue.get("category", "")
        return cat.value if hasattr(cat, "value") else str(cat)

    cat = getattr(issue, "category", "")
    return cat.value if hasattr(cat, "value") else str(cat)


# ------------------------------------------------------------------
# Lookup gathering
# ------------------------------------------------------------------


def _gather_lookups(
    category_counts: dict[str, int],
    content_type: str,
) -> list[tuple[str, Optional[str], int]]:
    """Build a deduplicated list of excerpt lookups with priority scores.

    Args:
        category_counts: Issue counts per category.
        content_type: Modular documentation content type.

    Returns:
        List of (rule_type, category_hint, priority) tuples, sorted
        by priority descending.
    """
    seen: set[tuple[str, Optional[str]]] = set()
    lookups: list[tuple[str, Optional[str], int]] = []

    # Always include ALL category lookups so the LLM has full style
    # guide context.  Issue count still drives priority ordering.
    for category, guide_list in _CATEGORY_TO_GUIDES.items():
        count = category_counts.get(category, 0)
        priority = max(count, 1)  # baseline 1 even for zero-issue categories
        for rule_type, hint in guide_list:
            key = (rule_type, hint)
            if key not in seen:
                seen.add(key)
                lookups.append((rule_type, hint, priority))

    # Content-type lookups always included with baseline priority
    content_guides = _CONTENT_TYPE_GUIDES.get(content_type, [])
    for rule_type, hint in content_guides:
        key = (rule_type, hint)
        if key not in seen:
            seen.add(key)
            lookups.append((rule_type, hint, 1))

    # Sort by priority (issue count) descending
    lookups.sort(key=lambda x: x[2], reverse=True)
    return lookups


# ------------------------------------------------------------------
# Excerpt fetching
# ------------------------------------------------------------------


def _fetch_excerpts(
    lookups: list[tuple[str, Optional[str], int]],
) -> list[dict]:
    """Fetch excerpts from the style guide registry.

    Args:
        lookups: Prioritized list of (rule_type, category_hint, priority).

    Returns:
        List of excerpt dicts that had non-empty content.
    """
    results: list[dict] = []
    seen_topics: set[str] = set()

    for rule_type, category_hint, priority in lookups:
        excerpt = get_excerpt(rule_type, category_hint)
        if not excerpt:
            continue

        topic = excerpt.get("topic", rule_type)
        if topic in seen_topics:
            continue
        seen_topics.add(topic)

        results.append({
            "guide_name": excerpt.get("guide_name", "Style Guide"),
            "category": category_hint or "general",
            "topic": topic,
            "excerpt": excerpt.get("excerpt", ""),
            "verified": excerpt.get("verified", False),
            "priority": priority,
        })

    return results


# ------------------------------------------------------------------
# Prioritization and budgeting
# ------------------------------------------------------------------


def _prioritize_excerpts(
    excerpts: list[dict],
    category_counts: dict[str, int],
) -> list[dict]:
    """Sort excerpts by priority: issue count first, verified second.

    Args:
        excerpts: List of excerpt dicts with ``priority`` and
            ``verified`` fields.
        category_counts: Issue counts per category (for tie-breaking).

    Returns:
        Sorted list of excerpt dicts (highest priority first).
    """
    def sort_key(item: dict) -> tuple[int, int]:
        priority = item.get("priority", 0)
        verified_bonus = 1 if item.get("verified", False) else 0
        return (priority, verified_bonus)

    return sorted(excerpts, key=sort_key, reverse=True)


def _apply_budget(excerpts: list[dict], budget: int) -> list[dict]:
    """Trim the excerpt list to fit within the token budget.

    Args:
        excerpts: Priority-sorted list of excerpt dicts.
        budget: Maximum token budget.

    Returns:
        Subset of excerpts that fits within the budget.
    """
    selected: list[dict] = []
    used_tokens = 0

    for item in excerpts:
        excerpt_text = item.get("excerpt", "")
        estimated_tokens = int(len(excerpt_text) * _TOKENS_PER_CHAR)

        if used_tokens + estimated_tokens > budget:
            logger.debug(
                "Excerpt budget exhausted at %d/%d tokens; skipping '%s'",
                used_tokens, budget, item.get("topic", "")[:40],
            )
            continue

        used_tokens += estimated_tokens
        # Return clean dicts without internal priority field
        selected.append({
            "guide_name": item["guide_name"],
            "category": item["category"],
            "topic": item["topic"],
            "excerpt": excerpt_text,
        })

    logger.info(
        "Selected %d excerpts using %d/%d tokens",
        len(selected), used_tokens, budget,
    )
    return selected
