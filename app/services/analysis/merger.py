"""Issue deduplication and merging for the Content Editorial Assistant.

Merges deterministic and LLM-generated issues into a single list,
ensuring deterministic results always take priority. LLM issues are
kept only when they meet the confidence threshold and do not duplicate
any existing issue (by span overlap or flagged text match).

Deduplication strategies:
1. Span overlap -- used when both issues have valid character offsets.
2. Flagged text match -- used when spans are missing or [0, 0], which
   is common with LLM providers that do not return character offsets.
3. LLM-to-LLM dedup -- removes duplicates between granular and global
   LLM passes before merging with deterministic issues.
"""

import logging
import re

from app.models.schemas import IssueResponse

logger = logging.getLogger(__name__)


def merge(
    deterministic: list[IssueResponse],
    llm_issues: list[IssueResponse],
    confidence_threshold: float = 0.7,
    blocks: list | None = None,
) -> list[IssueResponse]:
    """Merge deterministic and LLM issues with deduplication.

    Deterministic issues always take priority. LLM issues are included
    only if their confidence meets the threshold and they are not
    duplicates of any deterministic issue or previously accepted LLM
    issue.

    When ``blocks`` are provided, LLM issues that span across block
    boundaries are demoted (suggestion disabled) to prevent DOM errors.

    Args:
        deterministic: Issues from the deterministic rules engine.
        llm_issues: Issues from the LLM analysis passes.
        confidence_threshold: Minimum confidence for LLM issues.
        blocks: Optional list of Block objects for cross-block safety.

    Returns:
        Merged, deduplicated list sorted by sentence_index then span[0].
    """
    if not llm_issues:
        return _sort_issues(deterministic)

    det_spans = _extract_valid_spans(deterministic)
    accepted_texts = _extract_flagged_texts(deterministic)
    accepted = list(deterministic)

    block_boundaries = _extract_block_boundaries(blocks) if blocks else []

    # Deduplicate LLM issues against each other first (granular vs global)
    unique_llm = _deduplicate_llm_issues(llm_issues)
    llm_deduped = len(llm_issues) - len(unique_llm)

    kept = 0
    skipped_confidence = 0
    skipped_overlap = 0

    for issue in unique_llm:
        if issue.confidence < confidence_threshold:
            skipped_confidence += 1
            continue
        if _is_duplicate(issue, det_spans, accepted_texts):
            skipped_overlap += 1
            continue
        # SK-15: demote cross-block spans (disable Accept button)
        if block_boundaries and _span_crosses_block_boundary(issue.span, block_boundaries):
            issue.suggestions = []
            logger.debug("Demoted cross-block issue: span=%s", issue.span)
        accepted.append(issue)
        accepted_texts.add(_normalize_text(issue.flagged_text))
        kept += 1

    logger.info(
        "Merge: %d deterministic + %d LLM kept "
        "(%d below threshold, %d overlapping, %d LLM-to-LLM deduped)",
        len(deterministic), kept, skipped_confidence,
        skipped_overlap, llm_deduped,
    )

    return _sort_issues(accepted)


# ---------------------------------------------------------------------------
# LLM-to-LLM deduplication
# ---------------------------------------------------------------------------


def _deduplicate_llm_issues(
    issues: list[IssueResponse],
) -> list[IssueResponse]:
    """Remove duplicate LLM issues (e.g., granular vs global overlap).

    Keeps the first occurrence when two LLM issues flag the same or
    overlapping text. Uses composite ``(source, normalized_text)`` keys
    so that global and granular issues with the same text are kept as
    separate entries. Also applies span-based dedup for overlapping
    chunks that produce semantically identical issues with different
    ``flagged_text``.

    Args:
        issues: Combined LLM issues from all passes.

    Returns:
        Deduplicated list preserving original order.
    """
    seen_keys: set[tuple[str, str]] = set()
    seen_spans: list[tuple[int, int]] = []
    unique: list[IssueResponse] = []

    for issue in issues:
        normalized = _normalize_text(issue.flagged_text)
        source = getattr(issue, "source", "unknown")
        if not normalized:
            unique.append(issue)
            continue

        composite_key = (source, normalized)

        # Text-based dedup with source awareness
        if _composite_text_matches_any(normalized, source, seen_keys):
            continue

        # Span-based dedup for overlapping chunks
        if _has_valid_span(issue.span) and _span_overlaps_seen(
            issue.span, seen_spans,
        ):
            continue

        seen_keys.add(composite_key)
        if _has_valid_span(issue.span):
            seen_spans.append((issue.span[0], issue.span[1]))
        unique.append(issue)

    return unique


def _composite_text_matches_any(
    normalized: str,
    source: str,
    seen_keys: set[tuple[str, str]],
) -> bool:
    """Check if a (source, text) composite key matches any seen key.

    Exact text matches are cross-source — if granular and global flag
    the same text, the duplicate is removed.  Word-overlap matching
    remains source-aware to prevent fuzzy cross-source false matches.

    Args:
        normalized: Lowercase, stripped candidate text.
        source: The LLM source identifier (e.g., 'granular', 'global').
        seen_keys: Set of previously seen (source, text) tuples.

    Returns:
        True if a match is found.
    """
    for seen_source, seen_text in seen_keys:
        # Exact text match across all sources
        if normalized == seen_text:
            return True
        # Fuzzy word-overlap only within the same source
        if seen_source == source and _words_overlap(
            _to_words(normalized), _to_words(seen_text),
        ):
            return True
    return False


def _span_overlaps_seen(
    span: list[int], seen_spans: list[tuple[int, int]],
) -> bool:
    """Check if span overlaps any seen span by >80%.

    Two issues with more than 80% span overlap (measured by the shorter
    span's length) are considered duplicates.

    Args:
        span: The candidate [start, end] span.
        seen_spans: List of previously seen (start, end) tuples.

    Returns:
        True if the span overlaps a seen span by more than 80%.
    """
    s1, e1 = span[0], span[1]
    for s2, e2 in seen_spans:
        overlap_start = max(s1, s2)
        overlap_end = min(e1, e2)
        if overlap_end <= overlap_start:
            continue
        overlap = overlap_end - overlap_start
        shorter = min(e1 - s1, e2 - s2)
        if shorter > 0 and overlap / shorter > 0.8:
            return True
    return False


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


def _is_duplicate(
    issue: IssueResponse,
    det_spans: list[list[int]],
    accepted_texts: set[str],
) -> bool:
    """Check whether an LLM issue duplicates an already-accepted issue.

    When the issue has a valid span, the span-based check is
    authoritative and its result is returned directly.  Text matching
    is only used as a fallback when spans are missing or invalid.

    Args:
        issue: The candidate LLM issue.
        det_spans: Valid spans from deterministic issues.
        accepted_texts: Normalized flagged texts of all accepted issues.

    Returns:
        True if the issue is a duplicate.
    """
    if _has_valid_span(issue.span):
        # Span check is authoritative when spans exist
        return _is_span_duplicate(issue, det_spans)
    # Fallback to text matching for spanless issues
    return _text_matches_any(_normalize_text(issue.flagged_text), accepted_texts)


def _is_span_duplicate(
    issue: IssueResponse,
    det_spans: list[list[int]],
) -> bool:
    """Check span-based duplication — any overlap is a duplicate.

    When an LLM issue overlaps an existing issue on any span,
    it is treated as a duplicate regardless of category.  The
    deterministic issue already flags the problem; duplicate
    cards from different categories are user-hostile.

    Args:
        issue: The candidate LLM issue with a valid span.
        det_spans: Valid spans from accepted issues.

    Returns:
        True if the issue should be treated as a duplicate.
    """
    llm_start, llm_end = issue.span[0], issue.span[1]

    for det_span in det_spans:
        if len(det_span) < 2:
            continue
        d_start, d_end = det_span[0], det_span[1]

        # Any overlap → duplicate
        if llm_start < d_end and d_start < llm_end:
            return True

    return False


# ---------------------------------------------------------------------------
# Span helpers
# ---------------------------------------------------------------------------


def _extract_valid_spans(issues: list[IssueResponse]) -> list[list[int]]:
    """Extract spans that have meaningful (non-zero) positions.

    Args:
        issues: List of IssueResponse instances.

    Returns:
        List of [start, end] span pairs with non-zero positions.
    """
    return [
        issue.span for issue in issues
        if _has_valid_span(issue.span)
    ]


def _has_valid_span(span: list[int]) -> bool:
    """Check whether a span has meaningful (non-zero) positions.

    Args:
        span: Two-element [start, end] list.

    Returns:
        True if the span has at least 2 elements and is not [0, 0].
    """
    if len(span) < 2:
        return False
    return span[0] != 0 or span[1] != 0


def _has_span_overlap(
    span: list[int], existing_spans: list[list[int]],
) -> bool:
    """Check whether a span overlaps with any existing span.

    Two spans [a_start, a_end] and [b_start, b_end] overlap when
    a_start < b_end and b_start < a_end.

    Args:
        span: The candidate span to test.
        existing_spans: List of already-accepted valid spans.

    Returns:
        True if the span overlaps with at least one existing span.
    """
    if len(span) < 2:
        return False

    a_start, a_end = span[0], span[1]
    for existing in existing_spans:
        if len(existing) < 2:
            continue
        b_start, b_end = existing[0], existing[1]
        if a_start < b_end and b_start < a_end:
            return True
    return False


# ---------------------------------------------------------------------------
# Cross-block boundary safety (SK-15)
# ---------------------------------------------------------------------------


def _extract_block_boundaries(blocks: list) -> list[int]:
    """Extract end positions from all blocks to detect cross-block spans.

    Includes all block types (including code blocks) so that
    cross-boundary detection is not blind to skipped blocks.

    Args:
        blocks: List of Block dataclass instances.

    Returns:
        Sorted list of block end positions.
    """
    boundaries: list[int] = []
    for block in blocks:
        if hasattr(block, "end_pos"):
            boundaries.append(block.end_pos)
    return sorted(boundaries)


def _span_crosses_block_boundary(
    span: list[int], boundaries: list[int],
) -> bool:
    """Check whether a span crosses a block boundary.

    A span crosses a boundary when a block end position falls
    strictly between the span's start and end.

    Args:
        span: Two-element [start, end] list.
        boundaries: Sorted list of block end positions.

    Returns:
        True if any boundary falls within the span.
    """
    if len(span) < 2 or not boundaries:
        return False
    start, end = span[0], span[1]
    for boundary in boundaries:
        if boundary <= start:
            continue
        if boundary >= end:
            break
        return True
    return False


# ---------------------------------------------------------------------------
# Text-based deduplication (word-level matching)
# ---------------------------------------------------------------------------

# Extracts alphanumeric word tokens for comparison
_WORD_RE = re.compile(r"[a-z0-9]+")


def _extract_flagged_texts(issues: list[IssueResponse]) -> set[str]:
    """Extract normalized flagged text strings for text-based dedup.

    Args:
        issues: List of IssueResponse instances.

    Returns:
        Mutable set of lowercase, stripped flagged text strings.
    """
    return {
        _normalize_text(issue.flagged_text)
        for issue in issues
        if issue.flagged_text
    }


def _normalize_text(text: str) -> str:
    """Normalize text for deduplication comparison.

    Args:
        text: Raw flagged text string.

    Returns:
        Lowercase, stripped version of the text.
    """
    return text.strip().lower()


def _to_words(text: str) -> list[str]:
    """Extract lowercase alphanumeric words from text.

    Strips all punctuation so that ``"But,"`` and ``"but"`` both
    produce ``["but"]``.  This prevents single-character flagged
    texts like ``"I"`` from matching inside unrelated words.

    Args:
        text: Normalized text string.

    Returns:
        List of lowercase word tokens.
    """
    return _WORD_RE.findall(text.lower())


def _text_matches_any(normalized: str, existing: set[str]) -> bool:
    """Check whether a normalized text matches any existing text.

    Uses word-level containment: the word tokens of the shorter text
    must appear as a contiguous subsequence in the longer text.  This
    prevents single-character flags like ``"I"`` from matching inside
    random words (e.g. ``"disable"``).

    Args:
        normalized: Lowercase, stripped candidate text.
        existing: Set of previously accepted normalized texts.

    Returns:
        True if the text matches at least one existing text.
    """
    if not normalized:
        return False
    norm_words = _to_words(normalized)
    if not norm_words:
        return False
    for text in existing:
        if not text:
            continue
        if normalized == text:
            return True
        if _words_overlap(norm_words, _to_words(text)):
            return True
    return False


def _words_overlap(words_a: list[str], words_b: list[str]) -> bool:
    """Check if one word sequence is a contiguous subsequence of the other.

    Handles both directions: ``["be", "used"]`` inside
    ``["the", "program", "is", "ready", "to", "be", "used"]`` and
    vice versa.

    Args:
        words_a: First word list.
        words_b: Second word list.

    Returns:
        True if one list is a contiguous subsequence of the other.
    """
    shorter, longer = _order_by_length(words_a, words_b)
    if not shorter:
        return False
    slen = len(shorter)
    for i in range(len(longer) - slen + 1):
        if longer[i:i + slen] == shorter:
            return True
    return False


def _order_by_length(
    seq_a: list[str], seq_b: list[str],
) -> tuple[list[str], list[str]]:
    """Return (shorter, longer) tuple by list length.

    Args:
        seq_a: First sequence.
        seq_b: Second sequence.

    Returns:
        Tuple of (shorter_list, longer_list).
    """
    if len(seq_a) <= len(seq_b):
        return seq_a, seq_b
    return seq_b, seq_a


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------


def _sort_issues(issues: list[IssueResponse]) -> list[IssueResponse]:
    """Sort issues by sentence_index, then by span start position.

    Args:
        issues: Unsorted list of issues.

    Returns:
        Sorted list of issues.
    """
    return sorted(
        issues,
        key=lambda i: (i.sentence_index, i.span[0] if i.span else 0),
    )
