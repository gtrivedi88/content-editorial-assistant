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


def parse_analysis_response_ex(raw_text: str) -> tuple[list[dict], bool]:
    """Parse raw LLM text and report whether the response was truncated.

    Behaves identically to :func:`parse_analysis_response` but returns
    a ``(issues, truncated)`` tuple.  The *truncated* flag is ``True``
    when the parser had to salvage complete objects from a broken JSON
    response — indicating the output was cut off and some issues may
    have been lost.

    Args:
        raw_text: Raw text string from the LLM provider.

    Returns:
        Tuple of (validated issue list, truncated flag).
    """
    meta: dict = {}
    parsed = _parse_json_text(raw_text, _parse_meta=meta)
    truncated = meta.get("truncated", False)
    if parsed is None:
        return [], truncated

    issues = _normalize_to_list(parsed)
    if issues is None:
        return [], truncated

    return _validate_and_filter_issues(issues), truncated


def parse_suggestion_response(
    raw_text: str, flagged_text: str = "",
) -> dict:
    """Parse raw LLM text output into a suggestion dict.

    Expects the text to contain a JSON object with
    ``rewritten_text``, ``explanation``, and ``confidence`` fields.

    When ``flagged_text`` is provided, the validator checks whether
    the rewrite is disproportionately long relative to the flagged
    span and sets ``scope: "sentence"`` accordingly.

    Args:
        raw_text: Raw text string from the LLM provider.
        flagged_text: Original flagged text for scope detection.

    Returns:
        Dict with ``rewritten_text``, ``explanation``, ``confidence``
        keys (and optionally ``scope``), or an error dict if parsing
        fails.
    """
    parsed = _parse_json_text(raw_text)
    if parsed is None:
        return {"error": "Could not parse LLM response as JSON"}

    return _validate_suggestion(parsed, flagged_text=flagged_text)


# ------------------------------------------------------------------
# JSON parsing
# ------------------------------------------------------------------


def _parse_json_text(
    text: str,
    _parse_meta: dict | None = None,
) -> Any:
    """Parse a JSON string from LLM output.

    Handles common LLM quirks: markdown code fences, trailing commas,
    and truncated responses (salvages complete objects from partial
    JSON arrays).

    Args:
        text: Raw text that should contain JSON.
        _parse_meta: Optional mutable dict that will be updated with
            ``{"truncated": True}`` when salvage paths are used.
            Callers that do not pass this argument see no change.

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
        if _parse_meta is not None:
            _parse_meta["truncated"] = True
        return salvaged

    # Attempt to salvage from a truncated wrapper object ({"reasoning":...,"issues":[...
    salvaged = _salvage_truncated_object(cleaned)
    if salvaged is not None:
        logger.info(
            "Salvaged %d complete items from truncated wrapper object",
            len(salvaged),
        )
        if _parse_meta is not None:
            _parse_meta["truncated"] = True
        return {"issues": salvaged}

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


def _salvage_truncated_object(text: str) -> list[dict] | None:
    """Extract complete issue objects from a truncated wrapper response.

    When the LLM returns ``{"reasoning": "...", "issues": [...]`` but
    the response is cut off mid-array, this finds the ``"issues"``
    array start and salvages complete ``{ ... }`` objects from it.

    Args:
        text: Potentially truncated JSON wrapper object text.

    Returns:
        List of parsed issue dicts, or None if nothing could be salvaged.
    """
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None

    # Find the "issues" key followed by ':'  and '['
    match = re.search(r'"issues"\s*:\s*\[', stripped)
    if match is None:
        return None

    array_start = match.end() - 1  # position of '['
    array_text = stripped[array_start:]

    spans = _find_object_spans(array_text)
    items = _parse_object_spans(array_text, spans)
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
            logger.info(
                "Dropped LLM issue at parse (confidence %.2f < %.2f): %s",
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


def _scrub_suggestions(suggestions: list, flagged_text: str) -> list[str]:
    """Drop suggestions that are explanatory text, not replacements.

    A concrete replacement should be roughly the same length as the
    flagged span.  Suggestions >3× longer AND >20 chars are almost
    certainly instructions or explanations rather than drop-in text.

    Args:
        suggestions: Raw suggestion list from LLM output.
        flagged_text: The text the issue flagged.

    Returns:
        Filtered list containing only plausible replacements.
    """
    flagged_len = len(flagged_text) if flagged_text else 1
    scrubbed: list[str] = []
    for s in suggestions:
        if not isinstance(s, str) or not s.strip():
            continue
        if len(s) > 20 and len(s) > flagged_len * 3:
            logger.debug(
                "Scrubbed chatty suggestion (len=%d vs flagged_len=%d): %s",
                len(s), flagged_len, s[:80],
            )
            continue
        scrubbed.append(s)
    return scrubbed


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
    item["suggestions"] = _scrub_suggestions(
        item["suggestions"], item.get("flagged_text", ""),
    )

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


def _validate_suggestion(
    parsed: Any, flagged_text: str = "",
) -> dict:
    """Validate a parsed suggestion response.

    Expects a dict with ``rewritten_text``, ``explanation``, and
    ``confidence`` fields.  When ``flagged_text`` is provided, sets
    ``scope: "sentence"`` if the rewrite is disproportionately long
    relative to the flagged span (signal only — no trimming).

    Args:
        parsed: Parsed JSON from the LLM suggestion response.
        flagged_text: Original flagged text for scope detection.

    Returns:
        Validated suggestion dict, or error dict if invalid.
    """
    if not isinstance(parsed, dict):
        logger.warning("LLM suggestion response is not a dict")
        return {"error": "Invalid suggestion format"}

    rewritten = (
        parsed.get("rewritten_text")
        or parsed.get("suggestion")
        or parsed.get("rewrite")
        or parsed.get("corrected_text")
    )
    if not rewritten:
        logger.warning("LLM suggestion missing rewritten_text")
        return {"error": "No rewritten text in suggestion"}

    explanation = parsed.get("explanation", "")

    try:
        confidence = float(parsed.get("confidence", 0.8))
    except (ValueError, TypeError):
        confidence = 0.8

    result: dict = {
        "rewritten_text": str(rewritten),
        "explanation": str(explanation),
        "confidence": confidence,
    }

    # Scope detection: flag sentence-level rewrites so the frontend
    # can display them differently (e.g., "Apply rewrite" button
    # instead of showing the full sentence as chip text).
    if flagged_text:
        flagged_len = len(flagged_text)
        rewrite_len = len(str(rewritten))
        if rewrite_len > flagged_len * 3 and rewrite_len >= 40:
            result["scope"] = "sentence"

    return result


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
