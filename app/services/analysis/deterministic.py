"""Deterministic analysis engine for the Content Editorial Assistant.

Wraps the RulesRegistry to execute all deterministic style rules against
input text, then normalizes each raw rule error dictionary into a canonical
IssueResponse dataclass with proper category mapping, span calculation,
confidence scoring, and style guide citations.
"""

import logging
import uuid
from typing import Any

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse
from rules import get_registry
from style_guides.registry import (
    format_citation, get_citation, get_confidence_adjustment,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rule directory name -> IssueCategory mapping
# ---------------------------------------------------------------------------
_CATEGORY_MAP: dict[str, IssueCategory] = {
    "word_usage": IssueCategory.WORD_USAGE,
    "language_and_grammar": IssueCategory.GRAMMAR,
    "punctuation": IssueCategory.PUNCTUATION,
    "structure_and_format": IssueCategory.STRUCTURE,
    "audience_and_medium": IssueCategory.AUDIENCE,
    "numbers_and_measurement": IssueCategory.NUMBERS,
    "technical_elements": IssueCategory.TECHNICAL,
    "references": IssueCategory.REFERENCES,
    "legal_information": IssueCategory.LEGAL,
    "modular_compliance": IssueCategory.MODULAR,
}


def analyze(
    text: str,
    sentences: list[str],
    spacy_doc: Any,
    block_type: str = "paragraph",
    content_type: str | None = None,
    original_text: str | None = None,
    inline_code_ranges: list[tuple[int, int]] | None = None,
    bold_code_ranges: list[tuple[int, int, str, str]] | None = None,
    acronym_context: dict[str, str] | None = None,
) -> list[IssueResponse]:
    """Run all deterministic rules and return normalized issues.

    Delegates to the RulesRegistry for rule execution, then converts
    each raw error dict into an IssueResponse with proper category,
    severity, span, confidence, and citation data.

    Args:
        text: Full document text (cleaned and normalized).
        sentences: Pre-split list of sentence strings.
        spacy_doc: SpaCy Doc object for the text.
        block_type: Content block type for rule selection.
        content_type: Modular documentation type (concept, procedure, etc.).
        original_text: Pre-cleaning normalized text for span resolution.
        inline_code_ranges: Backtick ranges in content coordinates.
        bold_code_ranges: Bold/italic-wrapped code ranges in content coords.
        acronym_context: Document-wide acronym definitions for definitions rule.

    Returns:
        List of IssueResponse instances, one per detected issue.
    """
    registry = get_registry()
    raw_errors = registry.analyze(
        text, sentences, spacy_doc, block_type,
        content_type=content_type,
        inline_code_ranges=inline_code_ranges,
        bold_code_ranges=bold_code_ranges,
        acronym_context=acronym_context,
    )
    logger.info(
        "Deterministic analysis found %d raw errors for block_type=%s",
        len(raw_errors),
        block_type,
    )

    # Always resolve spans against cleaned text. The orchestrator remaps
    # spans to original-text coordinates using the preprocessor offset map.
    resolve_text = text
    issues: list[IssueResponse] = []
    for error in raw_errors:
        issue = _normalize_error(error, resolve_text, sentences)
        if issue is not None:
            issues.append(issue)

    # Filter out issues flagging synthetic placeholder text.
    # Uses "contains" check to catch "placeholder command", etc.
    issues = [
        i for i in issues
        if "placeholder" not in i.flagged_text.strip().lower()
    ]

    # Deduplicate issues with identical flagged_text + sentence
    issues = _deduplicate_issues(issues)

    logger.info("Normalized to %d issues after filtering", len(issues))
    return issues


def _normalize_error(
    error: dict[str, Any],
    text: str,
    sentences: list[str],
) -> IssueResponse | None:
    """Convert a raw rule error dict to a canonical IssueResponse.

    Skips system_error entries and errors missing required fields.

    Args:
        error: Raw error dict from a rule's analyze() method.
        text: Full document text for span calculation.
        sentences: List of sentence strings for fallback lookup.

    Returns:
        An IssueResponse instance, or None if the error is invalid.
    """
    rule_type = error.get("type", "")
    if rule_type == "system_error":
        logger.debug("Skipping system error: %s", error.get("message", ""))
        return None

    message = error.get("message", "")
    if not message:
        return None

    category = _resolve_category(rule_type)
    severity = _resolve_severity(error.get("severity", "medium"))
    sentence = str(error.get("sentence", ""))
    sentence_index = int(error.get("sentence_index", 0))
    flagged_text = str(error.get("flagged_text", ""))
    suggestions = _extract_suggestions(error)
    suggestions = _scrub_deterministic_suggestions(suggestions, flagged_text)
    span = _resolve_span(error, text, flagged_text, sentence)
    citation = _resolve_citation(rule_type)
    confidence = _resolve_confidence(rule_type, error)

    return IssueResponse(
        id=str(uuid.uuid4()),
        source="deterministic",
        category=category,
        rule_name=rule_type,
        flagged_text=flagged_text,
        message=message,
        suggestions=suggestions,
        severity=severity,
        sentence=sentence,
        sentence_index=sentence_index,
        span=span,
        style_guide_citation=citation,
        confidence=confidence,
        status=IssueStatus.OPEN,
    )


def _resolve_category(rule_type: str) -> IssueCategory:
    """Map a rule_type to its IssueCategory.

    Checks the category map for a prefix match against known
    rule directory names.

    Args:
        rule_type: The rule's type identifier string.

    Returns:
        Matching IssueCategory, defaulting to STYLE.
    """
    for prefix, category in _CATEGORY_MAP.items():
        if rule_type.startswith(prefix) or prefix in rule_type:
            return category
    return IssueCategory.STYLE


def _resolve_severity(raw: str) -> IssueSeverity:
    """Convert a raw severity string to an IssueSeverity enum.

    Args:
        raw: Severity string from the rule error dict.

    Returns:
        Corresponding IssueSeverity, defaulting to MEDIUM.
    """
    mapping = {
        "low": IssueSeverity.LOW,
        "medium": IssueSeverity.MEDIUM,
        "high": IssueSeverity.HIGH,
    }
    return mapping.get(raw.lower(), IssueSeverity.MEDIUM)


def _extract_suggestions(error: dict[str, Any]) -> list[str]:
    """Extract and sanitize the suggestions list from a raw error.

    Args:
        error: Raw error dict.

    Returns:
        List of suggestion strings.
    """
    raw = error.get("suggestions", [])
    if isinstance(raw, list):
        return [str(s) for s in raw if s is not None]
    return [str(raw)]


_DET_INSTRUCTION_PREFIXES = (
    "rewrite", "consider", "rephrase", "restructure", "replace",
    "remove", "break", "combine", "simplify", "avoid", "insert",
    "add", "move", "split", "write", "do not", "ensure", "verify",
    "check", "make the", "use a ",
)


def _scrub_deterministic_suggestions(
    suggestions: list[str], flagged_text: str,
) -> list[str]:
    """Filter out instruction-style suggestions from deterministic rules.

    Defense-in-depth: the frontend ``_isInstruction()`` already catches
    most instruction text, but scrubbing at the source is safer —
    the ``_autoFetchSuggestion`` path bypasses ``extractReplacement``.

    Args:
        suggestions: Raw suggestion strings from the rule.
        flagged_text: The text span that was flagged.

    Returns:
        Filtered list of concrete replacement suggestions.
    """
    flagged_len = len(flagged_text) if flagged_text else 1
    scrubbed: list[str] = []
    for s in suggestions:
        if not s or not s.strip():
            continue
        lower = s.lower().strip()
        if any(lower.startswith(p) for p in _DET_INSTRUCTION_PREFIXES):
            logger.debug("Scrubbed instruction suggestion: %s", s[:80])
            continue
        if len(s) > 20 and len(s) > flagged_len * 3:
            logger.debug("Scrubbed chatty suggestion: %s", s[:80])
            continue
        scrubbed.append(s)
    return scrubbed


def _resolve_span(
    error: dict[str, Any],
    text: str,
    flagged_text: str,
    sentence: str,
) -> list[int]:
    """Calculate or extract [start, end] character offsets.

    Uses the span from the error dict if available.  Rule spans are
    typically **sentence-relative** (from ``regex.finditer(sentence)``).
    When the sentence is a proper substring of *text*, the span is
    adjusted to text-relative coordinates by adding the sentence's
    position.  A bounds check (``end <= len(sentence)``) prevents
    double-adjustment for rules that already store text-relative spans.

    Falls back to text search for flagged_text or sentence position
    when no span is provided.

    Args:
        error: Raw error dict (may contain a 'span' key).
        text: Full document text.
        flagged_text: The text fragment that triggered the issue.
        sentence: The sentence containing the issue.

    Returns:
        Two-element list [start, end] of character offsets.
    """
    raw_span = error.get("span")
    if raw_span and isinstance(raw_span, (list, tuple)) and len(raw_span) >= 2:
        start, end = int(raw_span[0]), int(raw_span[1])

        if (sentence and text
                and len(sentence) < len(text)
                and 0 <= start < len(sentence)
                and 0 < end <= len(sentence)):
            sent_pos = text.find(sentence)
            if sent_pos > 0:
                start += sent_pos
                end += sent_pos

        return [start, end]

    if flagged_text and flagged_text in text:
        start = text.find(flagged_text)
        return [start, start + len(flagged_text)]

    if sentence and sentence in text:
        start = text.find(sentence)
        return [start, start + len(sentence)]

    return [0, 0]


def _resolve_citation(rule_type: str) -> str:
    """Retrieve the formatted style guide citation for a rule.

    Uses ``format_citation`` first for page-level citations. When
    that falls back to the generic default, attempts ``get_citation``
    to extract a topic-qualified citation instead.

    Args:
        rule_type: The rule's type identifier string.

    Returns:
        Formatted citation string with topic and page when available.
    """
    formatted = format_citation(rule_type)
    if formatted != "IBM Style Guide":
        return formatted

    citation_data = get_citation(rule_type)
    if not citation_data:
        return formatted

    return _format_citation_from_data(citation_data)


def _format_citation_from_data(data: dict) -> str:
    """Build a citation string from a citation data dict.

    Args:
        data: Dict with guide_name, topic, pages keys.

    Returns:
        Formatted citation like ``"IBM Style Guide: Articles (Page 91)"``.
    """
    guide = data.get("guide_name", "IBM Style Guide")
    topic = data.get("topic", "")
    pages = data.get("pages", [])

    parts = [guide]
    if topic:
        parts[0] = f"{guide}: {topic}"
    if pages:
        page_str = ", ".join(str(p) for p in pages)
        label = "Page" if len(pages) == 1 else "Pages"
        parts.append(f"({label} {page_str})")

    return " ".join(parts)


def _resolve_confidence(rule_type: str, error: dict[str, Any]) -> float:
    """Calculate the confidence score for a deterministic issue.

    Starts at 1.0 (deterministic baseline) and applies the
    style-guide confidence adjustment. Respects any confidence_score
    already set in the error dict.

    Args:
        rule_type: The rule's type identifier string.
        error: Raw error dict (may contain 'confidence_score').

    Returns:
        Confidence value clamped to [0.0, 1.0].
    """
    base = float(error.get("confidence_score", 1.0))
    adjustment = get_confidence_adjustment(rule_type)
    return max(0.0, min(1.0, base + adjustment))


def _deduplicate_issues(issues: list[IssueResponse]) -> list[IssueResponse]:
    """Remove duplicate issues with identical flagged text and sentence.

    When the same sentence appears multiple times in a document (e.g.
    repeated prerequisite sections), the same issue can be flagged at
    each occurrence. This keeps only the first occurrence.

    For definition issues, keeps only the first occurrence of each
    acronym across the entire document (not per-sentence).

    Args:
        issues: List of normalized issues.

    Returns:
        Deduplicated list preserving original order.
    """
    seen: set[str] = set()
    seen_defs: set[str] = set()
    unique: list[IssueResponse] = []
    for issue in issues:
        # Definitions rule: keep only first occurrence of each acronym
        if issue.rule_name == "definitions":
            if issue.flagged_text in seen_defs:
                logger.debug(
                    "Dedup: skipping duplicate definition '%s'",
                    issue.flagged_text,
                )
                continue
            seen_defs.add(issue.flagged_text)
        key = f"{issue.rule_name}|{issue.flagged_text}|{issue.sentence}"
        if key in seen:
            logger.debug(
                "Dedup: skipping duplicate %s '%s'",
                issue.rule_name, issue.flagged_text,
            )
            continue
        seen.add(key)
        unique.append(issue)
    return unique
