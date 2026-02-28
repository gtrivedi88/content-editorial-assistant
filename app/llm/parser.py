"""Response parsers for LLM output.

Extracts structured issue data and suggestion data from raw text
returned by the model provider.  Handles malformed responses
gracefully -- returns empty results and logs warnings rather than
raising exceptions.

Usage:
    from app.llm.parser import parse_analysis_response

    issues = parse_analysis_response(raw_text)
"""

import json
import logging
import re
from typing import Any

from app.config import Config

logger = logging.getLogger(__name__)

# Fields that every issue dict MUST contain
_REQUIRED_ISSUE_FIELDS = frozenset({
    "flagged_text",
    "message",
    "severity",
    "category",
})

# Valid severity values
_VALID_SEVERITIES = frozenset({"low", "medium", "high"})

# Valid category values for LLM issues
_VALID_CATEGORIES = frozenset({
    "style", "grammar", "word-usage", "punctuation",
    "structure", "numbers", "technical", "references",
    "legal", "audience", "modular",
})


def parse_analysis_response(raw_text: str) -> list[dict]:
    """Parse raw LLM text output into validated issue dicts.

    Strips code fences, parses embedded JSON, validates required
    fields, filters by confidence threshold, and stamps
    ``source="llm"`` on every issue.

    Args:
        raw_text: Raw text string from the LLM provider.

    Returns:
        List of validated issue dicts, or empty list on any failure.
    """
    parsed = _parse_json_text(raw_text)
    if parsed is None:
        return []

    issues = _normalize_to_list(parsed)
    if issues is None:
        return []

    return _validate_and_filter_issues(issues)


def parse_suggestion_response(raw_text: str) -> dict:
    """Parse raw LLM text output into a suggestion dict.

    Expects the text to contain a JSON object with
    ``rewritten_text``, ``explanation``, and ``confidence`` fields.

    Args:
        raw_text: Raw text string from the LLM provider.

    Returns:
        Dict with ``rewritten_text``, ``explanation``, ``confidence``
        keys, or an error dict if parsing fails.
    """
    parsed = _parse_json_text(raw_text)
    if parsed is None:
        return {"error": "Could not parse LLM response as JSON"}

    return _validate_suggestion(parsed)


# ------------------------------------------------------------------
# JSON parsing
# ------------------------------------------------------------------


def _parse_json_text(text: str) -> Any:
    """Parse a JSON string from LLM output.

    Handles common LLM quirks: markdown code fences, trailing commas,
    and truncated responses (salvages complete objects from partial
    JSON arrays).

    Args:
        text: Raw text that should contain JSON.

    Returns:
        Parsed Python object (list or dict), or None on failure.
    """
    cleaned = _strip_code_fences(text)
    cleaned = _strip_trailing_commas(cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt to salvage complete objects from a truncated JSON array
    salvaged = _salvage_truncated_array(cleaned)
    if salvaged is not None:
        logger.info(
            "Salvaged %d complete items from truncated LLM response",
            len(salvaged),
        )
        return salvaged

    logger.warning(
        "Failed to parse LLM response as JSON (first 200 chars: %s)",
        cleaned[:200],
    )
    return None


def _strip_trailing_commas(text: str) -> str:
    """Remove trailing commas before closing braces and brackets.

    LLMs sometimes produce JSON with trailing commas which is invalid
    per the JSON spec but common in generated output.

    Args:
        text: JSON text that may contain trailing commas.

    Returns:
        Cleaned text with trailing commas removed.
    """
    return re.sub(r',\s*([\]}])', r'\1', text)


def _salvage_truncated_array(text: str) -> list[dict] | None:
    """Extract complete JSON objects from a truncated array response.

    When the LLM response is cut off mid-array, this function finds
    all complete ``{ ... }`` objects and returns them as a list.

    Args:
        text: Potentially truncated JSON array text.

    Returns:
        List of parsed dicts, or None if nothing could be salvaged.
    """
    stripped = text.strip()
    if not stripped.startswith("["):
        return None

    spans = _find_object_spans(stripped)
    items = _parse_object_spans(stripped, spans)
    return items if items else None


def _find_object_spans(text: str) -> list[tuple[int, int]]:
    """Find start/end positions of top-level ``{ ... }`` blocks.

    Args:
        text: Text starting with ``[``.

    Returns:
        List of (start, end) tuples for each complete brace pair.
    """
    spans: list[tuple[int, int]] = []
    depth = 0
    obj_start = -1

    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and obj_start >= 0:
                spans.append((obj_start, i + 1))
                obj_start = -1

    return spans


def _parse_object_spans(
    text: str, spans: list[tuple[int, int]],
) -> list[dict]:
    """Parse JSON objects from identified text spans.

    Args:
        text: Full text containing JSON objects.
        spans: List of (start, end) positions.

    Returns:
        List of successfully parsed dicts.
    """
    items: list[dict] = []
    for start, end in spans:
        candidate = _strip_trailing_commas(text[start:end])
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                items.append(parsed)
        except json.JSONDecodeError:
            pass
    return items


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences from LLM output.

    Strips leading ``json`` or bare triple-backtick fences that LLMs
    sometimes include despite being told not to.

    Args:
        text: Raw LLM text output.

    Returns:
        Text with code fences removed and whitespace trimmed.
    """
    stripped = text.strip()

    if stripped.startswith("```json"):
        stripped = stripped[7:]
    elif stripped.startswith("```"):
        stripped = stripped[3:]

    if stripped.endswith("```"):
        stripped = stripped[:-3]

    return stripped.strip()


# ------------------------------------------------------------------
# Issue validation
# ------------------------------------------------------------------


def _normalize_to_list(parsed: Any) -> list[dict] | None:
    """Ensure the parsed JSON is a list of dicts.

    Args:
        parsed: Parsed JSON value from the LLM.

    Returns:
        List of dicts, or None if the structure is invalid.
    """
    if isinstance(parsed, list):
        return parsed

    if isinstance(parsed, dict):
        # Some LLMs wrap the array in a wrapper object
        for key in ("issues", "results", "data"):
            if key in parsed and isinstance(parsed[key], list):
                return parsed[key]
        logger.warning("LLM returned a dict without a recognized array key")
        return None

    logger.warning("LLM response is neither list nor dict: %s", type(parsed).__name__)
    return None


def _validate_and_filter_issues(issues: list) -> list[dict]:
    """Validate required fields, filter by confidence, stamp source.

    Args:
        issues: List of raw issue dicts from the LLM.

    Returns:
        List of validated issue dicts with ``source="llm"``.
    """
    threshold = Config.LLM_CONFIDENCE_THRESHOLD
    validated: list[dict] = []

    for item in issues:
        if not isinstance(item, dict):
            continue

        if not _has_required_fields(item):
            continue

        _normalize_issue_fields(item)

        confidence = item.get("confidence", 0.0)
        if confidence < threshold:
            logger.debug(
                "Filtered LLM issue below threshold (%.2f < %.2f): %s",
                confidence, threshold, item.get("flagged_text", "")[:80],
            )
            continue

        item["source"] = "llm"
        validated.append(item)

    return validated


def _has_required_fields(item: dict) -> bool:
    """Check that all required fields are present and non-empty.

    Allows empty string for ``flagged_text`` so that document-level
    global issues (SK-12) without a text anchor are not dropped.

    Args:
        item: A single issue dict.

    Returns:
        True if all required fields are present.
    """
    for field_name in _REQUIRED_ISSUE_FIELDS:
        value = item.get(field_name)
        # Allow empty string for flagged_text (global/document-level issues)
        if value is None or (not value and field_name != "flagged_text"):
            logger.debug("LLM issue missing or empty required field '%s'", field_name)
            return False
    return True


def _normalize_issue_fields(item: dict) -> None:
    """Normalize and default optional fields on an issue dict.

    Ensures ``suggestions`` is a list, ``sentence_index`` is an int,
    ``confidence`` is a float, and enum values are valid.

    Args:
        item: Issue dict to normalize in place.
    """
    # Suggestions
    suggestions = item.get("suggestions")
    if not isinstance(suggestions, list):
        item["suggestions"] = [suggestions] if suggestions else []

    # Sentence
    if "sentence" not in item:
        item["sentence"] = item.get("flagged_text", "")

    # Sentence index
    try:
        item["sentence_index"] = int(item.get("sentence_index", 0))
    except (ValueError, TypeError):
        item["sentence_index"] = 0

    # Confidence
    try:
        item["confidence"] = float(item.get("confidence", 0.8))
    except (ValueError, TypeError):
        item["confidence"] = 0.8

    # Severity validation
    severity = item.get("severity", "medium").lower()
    if severity not in _VALID_SEVERITIES:
        item["severity"] = "medium"
    else:
        item["severity"] = severity

    # Category validation
    category = item.get("category", "style").lower()
    if category not in _VALID_CATEGORIES:
        item["category"] = "style"
    else:
        item["category"] = category


# ------------------------------------------------------------------
# Suggestion validation
# ------------------------------------------------------------------


def _validate_suggestion(parsed: Any) -> dict:
    """Validate a parsed suggestion response.

    Expects a dict with ``rewritten_text``, ``explanation``, and
    ``confidence`` fields.

    Args:
        parsed: Parsed JSON from the LLM suggestion response.

    Returns:
        Validated suggestion dict, or error dict if invalid.
    """
    if not isinstance(parsed, dict):
        logger.warning("LLM suggestion response is not a dict")
        return {"error": "Invalid suggestion format"}

    rewritten = parsed.get("rewritten_text")
    if not rewritten:
        logger.warning("LLM suggestion missing rewritten_text")
        return {"error": "No rewritten text in suggestion"}

    explanation = parsed.get("explanation", "")

    try:
        confidence = float(parsed.get("confidence", 0.8))
    except (ValueError, TypeError):
        confidence = 0.8

    return {
        "rewritten_text": str(rewritten),
        "explanation": str(explanation),
        "confidence": confidence,
    }


def parse_judge_response(
    raw_text: str, total_issues: int,
) -> tuple[list[int], list[int]]:
    """Parse the judge self-correction response.

    Expects a JSON object with ``keep`` and ``drop`` arrays of
    zero-based issue indices.

    Args:
        raw_text: Raw text from the LLM judge call.
        total_issues: Total number of issues submitted for review.

    Returns:
        Tuple of (keep_indices, drop_indices).  On parse failure,
        returns all indices as kept (fail-open).
    """
    all_indices = list(range(total_issues))
    parsed = _parse_json_text(raw_text)
    if parsed is None or not isinstance(parsed, dict):
        logger.warning("Judge response not parseable; keeping all issues")
        return all_indices, []

    keep_raw = parsed.get("keep", [])
    drop_raw = parsed.get("drop", [])

    if not isinstance(keep_raw, list) or not isinstance(drop_raw, list):
        logger.warning("Judge response has invalid keep/drop types")
        return all_indices, []

    keep = _validate_indices(keep_raw, total_issues)
    drop = _validate_indices(drop_raw, total_issues)

    # Indices not mentioned in either list are kept by default
    mentioned = set(keep) | set(drop)
    for idx in all_indices:
        if idx not in mentioned:
            keep.append(idx)

    logger.info(
        "Judge verdict: keep=%d, drop=%d (of %d)",
        len(keep), len(drop), total_issues,
    )
    return keep, drop


def _validate_indices(indices: list, total: int) -> list[int]:
    """Filter index list to valid integers within range.

    Args:
        indices: Raw index values from the LLM.
        total: Maximum valid index (exclusive).

    Returns:
        List of valid integer indices.
    """
    valid: list[int] = []
    for val in indices:
        try:
            idx = int(val)
            if 0 <= idx < total:
                valid.append(idx)
        except (ValueError, TypeError):
            continue
    return valid
