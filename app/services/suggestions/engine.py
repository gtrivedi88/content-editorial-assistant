"""Suggestion engine for the Content Editorial Assistant.

Retrieves rewrite suggestions for flagged issues, using cached or
deterministic results when available and falling back to the LLM
for complex cases that need context-aware rewrites.

Usage:
    from app.services.suggestions.engine import get_suggestion

    result = get_suggestion(session_id, issue_id)
"""

import logging
import re
from typing import Optional

from app.llm.client import LLMClient
from app.models.schemas import AnalyzeResponse, IssueResponse
from app.services.session.store import get_session_store

logger = logging.getLogger(__name__)


def get_suggestion(session_id: str, issue_id: str) -> dict:
    """Get a rewrite suggestion for a specific flagged issue.

    Checks the session suggestion cache first, then determines whether
    the issue can be resolved with a simple deterministic replacement
    or requires an LLM-generated suggestion with surrounding context.

    Args:
        session_id: The analysis session identifier.
        issue_id: The issue identifier to get a suggestion for.

    Returns:
        Dict with ``rewritten_text``, ``explanation``, and ``confidence``
        keys on success. On failure, returns a dict with ``error`` and
        optionally ``suggestions`` (the deterministic suggestions list).
    """
    store = get_session_store()

    cached = store.get_cached_suggestion(session_id, issue_id)
    if cached is not None:
        logger.debug("Returning cached suggestion for issue %s", issue_id)
        return cached

    response = store.get_session(session_id)
    if response is None:
        logger.warning("Session %s not found for suggestion request", session_id)
        return {"error": "Session not found or expired"}

    issue = _find_issue(response, issue_id)
    if issue is None:
        logger.warning("Issue %s not found in session %s", issue_id, session_id)
        return {"error": "Issue not found"}

    if _is_simple_replacement(issue):
        suggestion = _build_deterministic_suggestion(issue)
        store.cache_suggestion(session_id, issue_id, suggestion)
        return suggestion

    suggestion = _request_llm_suggestion(issue, response)
    store.cache_suggestion(session_id, issue_id, suggestion)
    return suggestion


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _find_issue(response: AnalyzeResponse, issue_id: str) -> Optional[IssueResponse]:
    """Find an issue by ID within an analysis response.

    Args:
        response: The analysis response to search.
        issue_id: The issue identifier to find.

    Returns:
        The matching IssueResponse, or None if not found.
    """
    for issue in response.issues:
        if issue.id == issue_id:
            return issue
    return None


def _is_simple_replacement(issue: IssueResponse) -> bool:
    """Determine whether an issue has a single deterministic suggestion.

    Simple replacements are direct word/phrase swaps from deterministic
    rules (e.g. "utilize" -> "use") that do not need LLM involvement.
    Instruction-style suggestions (e.g. "Rewrite in active voice...")
    are NOT simple replacements and should be routed to the LLM.

    Args:
        issue: The issue to evaluate.

    Returns:
        True if the issue has exactly one suggestion from a
        deterministic source that is a direct replacement.
    """
    if issue.source != "deterministic" or len(issue.suggestions) != 1:
        return False

    suggestion = issue.suggestions[0]
    return not _is_instruction_suggestion(suggestion)


_INSTRUCTION_PREFIXES = (
    "rewrite", "consider", "rephrase", "restructure", "replace",
    "remove", "break", "combine", "simplify", "avoid", "insert",
    "add", "move", "split", "write", "do not", "ensure", "verify",
    "check", "make the", "use a ",
)


def _is_instruction_suggestion(suggestion: str) -> bool:
    """Check if a suggestion is guidance rather than a direct replacement.

    Instruction-style suggestions start with imperative verbs or
    contain phrases like "active voice" that indicate the user must
    manually rewrite the text.

    Args:
        suggestion: The suggestion string to check.

    Returns:
        True if the suggestion is guidance, not a direct replacement.
    """
    lower = suggestion.lower().strip()
    for prefix in _INSTRUCTION_PREFIXES:
        if lower.startswith(prefix):
            return True
    return False


_CHANGE_TO_RE = re.compile(
    r"(?:(?<!\bnot )(?<!\bnot\s)[Uu]se|[Cc]hange\s+to|[Rr]eplace\s+with|"
    r"[Rr]efer\s+to\s+\S+\s+\S+\s+as|[Ww]rite)\s+['\"`]([^'\"`]+)['\"`]",
)


def _extract_alternative_from_message(message: str) -> Optional[str]:
    """Extract a concrete alternative from an issue message.

    Many rule messages embed the alternative as a quoted term
    (e.g. ``Use 'inactive' instead``).  This function extracts the
    first such quoted alternative.

    Args:
        message: The issue's human-readable message.

    Returns:
        The extracted alternative text, or ``None`` if not found.
    """
    match = _CHANGE_TO_RE.search(message)
    if match:
        return match.group(1)
    return None


def _match_case_engine(replacement: str, flagged_text: str) -> str:
    """Capitalise replacement if the flagged text starts uppercase.

    Args:
        replacement: The extracted alternative.
        flagged_text: The original flagged text from the issue.

    Returns:
        Case-adjusted replacement string.
    """
    if flagged_text and flagged_text[0].isupper() and replacement:
        return replacement[0].upper() + replacement[1:]
    return replacement


def _build_deterministic_suggestion(issue: IssueResponse) -> dict:
    """Build a suggestion response from a deterministic replacement.

    Args:
        issue: The issue with a single deterministic suggestion.

    Returns:
        Dict with rewritten_text, explanation, and confidence.
    """
    replacement = issue.suggestions[0]
    logger.debug(
        "Using deterministic suggestion for issue %s: '%s' -> '%s'",
        issue.id, issue.flagged_text, replacement,
    )
    return {
        "rewritten_text": replacement,
        "explanation": issue.message,
        "confidence": 1.0,
    }


def _request_llm_suggestion(issue: IssueResponse, response: AnalyzeResponse) -> dict:
    """Request a rewrite suggestion from the LLM.

    Builds context from surrounding sentences, rule details, and style
    guide excerpts, then calls the LLM client. Falls back to
    deterministic suggestions if the LLM is unavailable.

    Args:
        issue: The issue to get a suggestion for.
        response: The full analysis response for sentence context.

    Returns:
        Dict with rewritten_text, explanation, and confidence on
        success. Dict with error and suggestions on failure.
    """
    client = LLMClient()

    if not client.is_available():
        logger.info("LLM not available; returning deterministic suggestions for issue %s", issue.id)
        suggestions = list(issue.suggestions)
        if not suggestions:
            extracted = _extract_alternative_from_message(issue.message)
            if extracted:
                adjusted = _match_case_engine(extracted, issue.flagged_text)
                return {
                    "rewritten_text": adjusted,
                    "explanation": issue.message,
                    "confidence": 0.7,
                }
        return {
            "error": "LLM not available",
            "suggestions": suggestions,
        }

    context_sentences = _extract_context_sentences(issue, response)
    rule_info = _build_rule_info(issue)
    style_guide_excerpt = _build_style_guide_excerpt(issue)

    result = client.suggest(
        flagged_text=issue.flagged_text,
        context_sentences=context_sentences,
        rule_info=rule_info,
        style_guide_excerpt=style_guide_excerpt,
    )

    if "error" in result:
        logger.warning("LLM suggestion failed for issue %s: %s", issue.id, result.get("error"))
        # Try extracting a concrete alternative from the issue message
        extracted = _extract_alternative_from_message(issue.message)
        if extracted:
            adjusted = _match_case_engine(extracted, issue.flagged_text)
            return {
                "rewritten_text": adjusted,
                "explanation": issue.message,
                "confidence": 0.7,
            }
        return {
            "error": result.get("error", "LLM request failed"),
            "suggestions": list(issue.suggestions),
        }

    logger.info("LLM suggestion generated for issue %s", issue.id)
    return result


def _extract_context_sentences(
    issue: IssueResponse, response: AnalyzeResponse
) -> list[str]:
    """Extract the flagged sentence and surrounding context.

    Retrieves the flagged sentence plus up to 2 sentences before
    and 2 sentences after from the same analysis response.

    Args:
        issue: The issue containing sentence_index.
        response: The analysis response with all issues.

    Returns:
        List of context sentences (3-5 sentences typically).
    """
    all_sentences = _collect_unique_sentences(response)

    if not all_sentences:
        return [issue.sentence] if issue.sentence else []

    target_idx = _find_sentence_index(all_sentences, issue)
    start = max(0, target_idx - 2)
    end = min(len(all_sentences), target_idx + 3)

    return all_sentences[start:end]


def _collect_unique_sentences(response: AnalyzeResponse) -> list[str]:
    """Collect unique sentences from all issues, ordered by sentence_index.

    Args:
        response: The analysis response with all issues.

    Returns:
        Sorted list of unique sentence strings.
    """
    sentence_map: dict[int, str] = {}
    for resp_issue in response.issues:
        if resp_issue.sentence and resp_issue.sentence_index not in sentence_map:
            sentence_map[resp_issue.sentence_index] = resp_issue.sentence

    sorted_indices = sorted(sentence_map.keys())
    return [sentence_map[idx] for idx in sorted_indices]


def _find_sentence_index(all_sentences: list[str], issue: IssueResponse) -> int:
    """Find the position of the issue's sentence in the sentence list.

    Uses the sentence text for matching. Falls back to 0 if not found.

    Args:
        all_sentences: Ordered list of unique sentences.
        issue: The issue to locate.

    Returns:
        Zero-based index of the sentence in the list.
    """
    for idx, sentence in enumerate(all_sentences):
        if sentence == issue.sentence:
            return idx
    return 0


def _build_rule_info(issue: IssueResponse) -> dict:
    """Build the rule information dict for the LLM prompt.

    Args:
        issue: The issue to extract rule details from.

    Returns:
        Dict with rule_name, category, message, and severity keys.
    """
    return {
        "rule_name": issue.rule_name,
        "category": issue.category.value if hasattr(issue.category, "value") else str(issue.category),
        "message": issue.message,
        "severity": issue.severity.value if hasattr(issue.severity, "value") else str(issue.severity),
    }


def _build_style_guide_excerpt(issue: IssueResponse) -> dict:
    """Build a style guide excerpt dict for the LLM prompt.

    Uses the issue's style_guide_citation field and attempts to fetch
    the full excerpt from the registry.

    Args:
        issue: The issue to build an excerpt for.

    Returns:
        Dict with guide_name, topic, and excerpt keys.
    """
    excerpt = _fetch_excerpt_for_rule(issue.rule_name, issue.category)
    if excerpt:
        return excerpt

    return {
        "guide_name": issue.style_guide_citation or "Style Guide",
        "topic": issue.rule_name,
        "excerpt": "",
    }


def _fetch_excerpt_for_rule(rule_name: str, category: object) -> Optional[dict]:
    """Attempt to fetch a style guide excerpt from the registry.

    Args:
        rule_name: The rule identifier.
        category: The issue category (enum or string).

    Returns:
        Excerpt dict if found, or None.
    """
    try:
        from style_guides.registry import get_excerpt

        category_str = category.value if hasattr(category, "value") else str(category)
        return get_excerpt(rule_name, category_str) or None
    except ImportError:
        logger.debug("Style guides registry not available")
        return None
