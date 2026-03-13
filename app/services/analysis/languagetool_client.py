"""LanguageTool HTTP client for the Content Editorial Assistant.

Sends prose blocks to a remote LanguageTool instance and maps the
results back to CEA's IssueResponse schema.  Runs as a background
phase in parallel with the LLM granular pass.

The client handles:
- Block filtering (only prose blocks reach LanguageTool)
- Batching (multiple blocks per HTTP call, max ~6000 chars)
- UTF-16 → codepoint offset conversion (Java vs Python mismatch)
- Cross-block boundary match discard
- Inline code and technical content false-positive guards
- Graceful degradation (timeout/connection errors return empty list)
"""

import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any

import requests
import yaml

from app.config import Config
from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import IssueResponse
from app.services.analysis.orchestrator import (
    _compute_content_code_ranges,
    _find_flagged_in_text,
)
from rules.base_rule import in_code_range
from rules.term_registry import is_known_term, is_likely_code

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prose block types eligible for LanguageTool analysis
# ---------------------------------------------------------------------------

_PROSE_BLOCK_TYPES: frozenset[str] = frozenset({
    "paragraph",
    "heading",
    "list_item_ordered",
    "list_item_unordered",
})


# ---------------------------------------------------------------------------
# LT rule IDs known to produce false positives on technical docs
# ---------------------------------------------------------------------------

_LT_SKIP_RULES: frozenset[str] = frozenset({
    "TYPOGRAPHICAL_APOSTROPHE",
    "DASH_RULE",
    "MULTIPLICATION_SIGN",
    "EN_UNPAIRED_BRACKETS",
    "EN_QUOTES",
})


# ---------------------------------------------------------------------------
# Domain-aware spelling allowlist — loaded from YAML
# ---------------------------------------------------------------------------

def _load_spelling_allowlist() -> frozenset[str]:
    """Load technical terms from ``rules/config/spelling_allowlist.yaml``.

    The YAML file contains a ``terms`` list of lowercase words that are
    valid technical terms but absent from standard English dictionaries.
    The frozenset is built once at module import time.

    Returns:
        A frozenset of lowercase terms.  Empty on load failure.
    """
    config_path = os.path.join(
        os.path.dirname(__file__),
        os.pardir, os.pardir, os.pardir,
        "rules", "config", "spelling_allowlist.yaml",
    )
    config_path = os.path.normpath(config_path)
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        terms = data.get("terms", [])
        if not isinstance(terms, list):
            logger.warning("spelling_allowlist.yaml 'terms' is not a list")
            return frozenset()
        return frozenset(t.lower() for t in terms if isinstance(t, str))
    except FileNotFoundError:
        logger.warning("spelling_allowlist.yaml not found at %s", config_path)
        return frozenset()
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse spelling_allowlist.yaml: %s", exc)
        return frozenset()


_SPELLING_ALLOWLIST: frozenset[str] = _load_spelling_allowlist()


# ---------------------------------------------------------------------------
# Category and severity mappings
# ---------------------------------------------------------------------------

_LT_CATEGORY_MAP: dict[str, IssueCategory] = {
    "GRAMMAR": IssueCategory.GRAMMAR,
    "TYPOS": IssueCategory.GRAMMAR,
    "CASING": IssueCategory.STYLE,
    "STYLE": IssueCategory.STYLE,
    "PUNCTUATION": IssueCategory.PUNCTUATION,
    "CONFUSED_WORDS": IssueCategory.GRAMMAR,
    "REDUNDANCY": IssueCategory.WORD_USAGE,
    "MISC": IssueCategory.GRAMMAR,
    "COLLOQUIALISMS": IssueCategory.AUDIENCE,
    "GENDER_NEUTRALITY": IssueCategory.AUDIENCE,
    "SEMANTICS": IssueCategory.GRAMMAR,
}

_LT_SEVERITY_MAP: dict[str, IssueSeverity] = {
    "misspelling": IssueSeverity.HIGH,
    "grammar": IssueSeverity.HIGH,
    "typographical": IssueSeverity.MEDIUM,
    "style": IssueSeverity.LOW,
}

# ---------------------------------------------------------------------------
# Technical content heuristic patterns
# ---------------------------------------------------------------------------

_CAMEL_CASE_RE = re.compile(r"^[a-z]+[A-Z]")
_PASCAL_CASE_RE = re.compile(r"^[A-Z][a-z]+[A-Z]")
_TECH_CHARS_RE = re.compile(r"[a-zA-Z0-9][_./][a-zA-Z0-9]")
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Batch data structures
# ---------------------------------------------------------------------------

@dataclass
class _BatchEntry:
    """Maps a region within a batch string back to its source block."""

    block: Any
    batch_start: int
    batch_end: int
    code_ranges: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class _Batch:
    """A single HTTP request payload with offset tracking."""

    text: str
    entries: list[_BatchEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# UTF-16 offset conversion
# ---------------------------------------------------------------------------

def _utf16_to_codepoint_offset(text: str, utf16_offset: int) -> int:
    """Convert a Java UTF-16 code-unit offset to a Python character index.

    Java strings use UTF-16 internally, so characters outside the Basic
    Multilingual Plane (emojis, math symbols) occupy 2 code units in
    Java but 1 codepoint in Python.  Without conversion, every LT
    offset after such a character would be shifted.

    Args:
        text: The Python string that was sent to LanguageTool.
        utf16_offset: The character offset from LT's JSON response.

    Returns:
        The corresponding Python string index.
    """
    encoded = text.encode("utf-16-le")
    byte_offset = utf16_offset * 2
    if byte_offset > len(encoded):
        byte_offset = len(encoded)
    sliced = encoded[:byte_offset]
    return len(sliced.decode("utf-16-le", errors="replace"))


# ---------------------------------------------------------------------------
# Technical content detection
# ---------------------------------------------------------------------------

def _is_technical_content(text: str) -> bool:
    """Return True if *text* looks like a technical term, not prose.

    Detects file paths, package names, camelCase identifiers, URLs,
    alphanumeric identifiers (k8s, ipv4, x86_64), and all-uppercase
    acronyms (RBAC, YAML).

    Args:
        text: The flagged text from an LT match.

    Returns:
        True if the text should be considered technical content.
    """
    if not text or len(text) > 80:
        return False
    if _URL_RE.search(text):
        return True
    if _CAMEL_CASE_RE.search(text):
        return True
    if _PASCAL_CASE_RE.search(text):
        return True
    if _TECH_CHARS_RE.search(text):
        return True
    # Alphanumeric identifiers: k8s, ipv4, x86_64
    if any(ch.isdigit() for ch in text):
        return True
    # All-uppercase acronyms: RBAC, YAML, API
    if text.isupper() and len(text) >= 2:
        return True
    return False


# ---------------------------------------------------------------------------
# Batch building
# ---------------------------------------------------------------------------

_MAX_BATCH_CHARS = 6000
_BLOCK_SEPARATOR = "\n\n"


def _build_batches(blocks: list) -> list[_Batch]:
    """Group prose blocks into batches for efficient HTTP calls.

    Each batch concatenates block content with ``\\n\\n`` separators
    and tracks the offset range of each block within the batch string.
    A new batch starts when adding another block would exceed
    ``_MAX_BATCH_CHARS``.

    Args:
        blocks: Parsed document blocks (Block dataclass instances).

    Returns:
        List of batches ready to send to LanguageTool.
    """
    batches: list[_Batch] = []
    current_text = ""
    current_entries: list[_BatchEntry] = []

    for block in blocks:
        block_type = getattr(block, "block_type", "")
        if block_type not in _PROSE_BLOCK_TYPES:
            continue
        if getattr(block, "should_skip_analysis", False):
            continue

        content = getattr(block, "content", "")
        if not content or not content.strip():
            continue

        addition = content + _BLOCK_SEPARATOR
        if current_text and len(current_text) + len(addition) > _MAX_BATCH_CHARS:
            batches.append(_Batch(text=current_text, entries=current_entries))
            current_text = ""
            current_entries = []

        batch_start = len(current_text)
        current_text += addition
        batch_end = batch_start + len(content)

        # Pre-compute inline code ranges for FP guard
        inline_content = getattr(block, "inline_content", content)
        char_map = getattr(block, "char_map", None)
        code_ranges = _compute_content_code_ranges(inline_content, char_map)

        current_entries.append(_BatchEntry(
            block=block,
            batch_start=batch_start,
            batch_end=batch_end,
            code_ranges=code_ranges,
        ))

    if current_text and current_entries:
        batches.append(_Batch(text=current_text, entries=current_entries))

    return batches


# ---------------------------------------------------------------------------
# Match resolution
# ---------------------------------------------------------------------------

def _find_entry_for_offset(
    entries: list[_BatchEntry],
    py_offset: int,
    match_length: int,
) -> _BatchEntry | None:
    """Find the batch entry that owns a given offset.

    Discards cross-boundary matches (where the flagged span bleeds
    from one block into the next across the ``\\n\\n`` separator).

    Args:
        entries: Batch entries with offset ranges.
        py_offset: Python codepoint offset within the batch.
        match_length: Length of the flagged text.

    Returns:
        The owning entry, or None if the match spans a boundary.
    """
    for entry in entries:
        if entry.batch_start <= py_offset < entry.batch_end:
            if py_offset + match_length > entry.batch_end:
                logger.debug(
                    "Discarding cross-boundary LT match at offset %d "
                    "(block ends at %d, match length %d)",
                    py_offset, entry.batch_end, match_length,
                )
                return None
            return entry
    return None


def _map_lt_match_to_issue(
    match: dict[str, Any],
    entry: _BatchEntry,
    block_local_offset: int,
    py_length: int,
    flagged_text: str,
    original_text: str,
) -> IssueResponse | None:
    """Convert a single LT match dict into a CEA IssueResponse.

    Maps the block-local offset through ``char_map`` and
    ``start_pos`` to produce original-text span coordinates.
    Falls back to ``_find_flagged_in_text`` for refinement.

    Args:
        match: A single match object from LT's JSON response.
        entry: The batch entry for the owning block.
        block_local_offset: Character offset within block.content.
        py_length: Python codepoint length of the flagged text
            (pre-converted from UTF-16).
        flagged_text: The flagged text already extracted from the batch
            using correct Python offsets.
        original_text: Full original document text for span refinement.

    Returns:
        An IssueResponse, or None if mapping fails.
    """
    block = entry.block
    content = getattr(block, "content", "")

    # Use the pre-computed Python length — not the raw Java UTF-16 length
    end_local = block_local_offset + py_length
    if block_local_offset < 0 or end_local > len(content):
        logger.debug("LT match offset out of block content bounds")
        return None

    # Map to original-text coordinates via char_map
    char_map = getattr(block, "char_map", None)
    start_pos = getattr(block, "start_pos", 0)
    end_pos = getattr(block, "end_pos", start_pos + len(content))

    if char_map and block_local_offset < len(char_map):
        orig_start = start_pos + char_map[block_local_offset]
    else:
        orig_start = start_pos + block_local_offset

    if char_map and end_local < len(char_map):
        orig_end = start_pos + char_map[end_local]
    elif end_local >= len(content):
        orig_end = end_pos
    else:
        orig_end = start_pos + end_local

    # Refine with text search near the approximate position
    if original_text and flagged_text:
        search_from = max(0, orig_start - len(flagged_text) - 20)
        search_to = min(
            len(original_text),
            orig_start + len(flagged_text) * 3 + 200,
        )
        found = _find_flagged_in_text(
            original_text, flagged_text, search_from, search_to,
        )
        if found:
            orig_start, orig_end, flagged_text = found

    # Extract LT rule metadata
    rule_data = match.get("rule", {})
    rule_id = rule_data.get("id", "UNKNOWN")
    category_id = rule_data.get("category", {}).get("id", "MISC")
    issue_type = rule_data.get("issueType", "")

    category = _LT_CATEGORY_MAP.get(category_id, IssueCategory.GRAMMAR)
    severity = _LT_SEVERITY_MAP.get(issue_type, IssueSeverity.MEDIUM)

    # Build suggestions from replacements
    replacements = match.get("replacements", [])
    suggestions = [r["value"] for r in replacements[:5] if r.get("value")]

    # Extract confidence
    confidence = rule_data.get("confidence", 0.95)
    if isinstance(confidence, (int, float)):
        confidence = max(0.0, min(1.0, float(confidence)))
    else:
        confidence = 0.95

    return IssueResponse(
        id=str(uuid.uuid4()),
        source="languagetool",
        category=category,
        rule_name=f"lt_{rule_id.lower()}",
        flagged_text=flagged_text,
        message=match.get("message", ""),
        suggestions=suggestions,
        severity=severity,
        sentence=match.get("sentence", ""),
        sentence_index=0,
        span=[orig_start, orig_end],
        confidence=confidence,
        status=IssueStatus.OPEN,
    )


# ---------------------------------------------------------------------------
# HTTP call
# ---------------------------------------------------------------------------

def _call_languagetool(
    text: str,
    disabled_rules: str = "",
    disabled_categories: str = "",
) -> list[dict[str, Any]]:
    """POST text to the LanguageTool /v2/check endpoint.

    Args:
        text: Plain text to check.
        disabled_rules: Comma-separated rule IDs to skip.
        disabled_categories: Comma-separated category IDs to skip.

    Returns:
        List of match dicts from the LT response, or empty on failure.
    """
    url = f"{Config.LANGUAGETOOL_URL}/v2/check"
    payload = {
        "text": text,
        "language": "en-US",
    }
    if disabled_rules:
        payload["disabledRules"] = disabled_rules
    if disabled_categories:
        payload["disabledCategories"] = disabled_categories

    try:
        resp = requests.post(
            url,
            data=payload,
            timeout=Config.LANGUAGETOOL_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("matches", [])
    except requests.Timeout:
        logger.warning(
            "LanguageTool request timed out after %ds",
            Config.LANGUAGETOOL_TIMEOUT,
        )
        return []
    except requests.ConnectionError:
        logger.warning("Cannot connect to LanguageTool at %s", url)
        return []
    except requests.RequestException as exc:
        logger.warning("LanguageTool request failed: %s", exc)
        return []
    except (ValueError, KeyError) as exc:
        logger.warning("Invalid LanguageTool response: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Per-match guard logic
# ---------------------------------------------------------------------------


def _should_skip_match(
    rule_id: str,
    flagged: str,
    block_local_offset: int,
    code_ranges: list[tuple[int, int]],
    lt_category: str = "",
) -> bool:
    """Return True if a match should be discarded by FP guards.

    Applies the following guards in order:
    1. Hardcoded skip rules (defense in depth)
    2. Inline code range guard
    3. Technical content heuristic guard
    4. Domain-aware spelling allowlist (MORFOLOGIK only)
    5. Unified term registry (TYPOS, CASING, CONFUSED_WORDS, STYLE)
    6. Heuristic code pattern detection

    Args:
        rule_id: LanguageTool rule identifier.
        flagged: The flagged text extracted from the batch.
        block_local_offset: Character offset within block.content.
        code_ranges: Pre-computed inline code ranges for the block.
        lt_category: LanguageTool rule category ID (e.g. TYPOS, GRAMMAR).

    Returns:
        True if the match should be skipped.
    """
    if rule_id in _LT_SKIP_RULES:
        return True

    if in_code_range(block_local_offset, code_ranges):
        logger.debug(
            "Skipping LT match in inline code: rule=%s offset=%d",
            rule_id, block_local_offset,
        )
        return True

    if _is_technical_content(flagged):
        logger.debug(
            "Skipping LT match on technical content: %r", flagged,
        )
        return True

    if rule_id == "MORFOLOGIK_RULE_EN_US":
        clean_word = flagged.strip(".,;:!?()\"'").lower()
        if clean_word in _SPELLING_ALLOWLIST:
            logger.debug(
                "Skipping LT spelling FP on allowlisted term: %r",
                flagged,
            )
            return True

    # Unified term registry — case-sensitive exact match on correct forms.
    # Do NOT suppress GRAMMAR — known terms can still have grammar errors.
    _registry_categories = {"TYPOS", "CASING", "CONFUSED_WORDS", "STYLE"}
    if lt_category in _registry_categories and is_known_term(flagged):
        logger.debug(
            "Skipping LT match on known term: %r (category=%s)",
            flagged, lt_category,
        )
        return True

    # Heuristic code detection for terms not in any config
    if is_likely_code(flagged):
        logger.debug(
            "Skipping LT match on code-like content: %r", flagged,
        )
        return True

    return False


def _process_batch_matches(
    batch: _Batch,
    matches: list[dict[str, Any]],
    original_text: str,
) -> list[IssueResponse]:
    """Convert raw LT matches into filtered IssueResponse objects.

    Handles UTF-16 offset conversion, block resolution, FP guards,
    and mapping to the CEA issue schema.

    Args:
        batch: The batch that produced these matches.
        matches: Raw match dicts from the LT JSON response.
        original_text: Full original document text for span refinement.

    Returns:
        List of IssueResponse objects that survived all guards.
    """
    issues: list[IssueResponse] = []

    for match in matches:
        rule_obj = match.get("rule", {})
        rule_id = rule_obj.get("id", "")
        lt_category = rule_obj.get("category", {}).get("id", "")

        # UTF-16 → codepoint conversion
        raw_offset = match.get("offset", 0)
        py_offset = _utf16_to_codepoint_offset(batch.text, raw_offset)
        match_length_utf16 = match.get("length", 0)
        py_end = _utf16_to_codepoint_offset(
            batch.text, raw_offset + match_length_utf16,
        )
        py_length = py_end - py_offset

        # Find owning block; discard cross-boundary matches
        entry = _find_entry_for_offset(batch.entries, py_offset, py_length)
        if entry is None:
            continue

        block_local_offset = py_offset - entry.batch_start
        flagged = batch.text[py_offset:py_end]

        if _should_skip_match(rule_id, flagged, block_local_offset,
                              entry.code_ranges, lt_category):
            continue

        issue = _map_lt_match_to_issue(
            match, entry, block_local_offset, py_length, flagged,
            original_text,
        )
        if issue is not None:
            issues.append(issue)

    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_blocks(
    blocks: list,
    original_text: str = "",
) -> list[IssueResponse]:
    """Analyze prose blocks via LanguageTool and return CEA issues.

    Filters non-prose blocks, batches the rest into HTTP calls,
    converts LT matches to IssueResponse instances, and applies
    inline-code and technical-content guards.

    Args:
        blocks: Parsed document blocks (Block dataclass instances).
        original_text: Full original document text for span refinement.

    Returns:
        List of IssueResponse objects from LanguageTool analysis.
        Returns an empty list on any failure (graceful degradation).
    """
    if not Config.LANGUAGETOOL_ENABLED:
        return []

    batches = _build_batches(blocks)
    if not batches:
        logger.debug("No prose blocks to send to LanguageTool")
        return []

    logger.info(
        "Sending %d batch(es) to LanguageTool (%d prose blocks)",
        len(batches),
        sum(len(b.entries) for b in batches),
    )

    disabled_rules = Config.LANGUAGETOOL_DISABLED_RULES
    skip_rules = set(disabled_rules.split(",")) if disabled_rules else set()
    skip_rules.update(_LT_SKIP_RULES)
    disabled_rules_str = ",".join(skip_rules - {""})

    disabled_categories = Config.LANGUAGETOOL_DISABLED_CATEGORIES

    all_issues: list[IssueResponse] = []

    for batch_idx, batch in enumerate(batches):
        matches = _call_languagetool(
            batch.text, disabled_rules_str, disabled_categories,
        )
        logger.debug(
            "Batch %d: %d matches from LanguageTool",
            batch_idx, len(matches),
        )
        all_issues.extend(
            _process_batch_matches(batch, matches, original_text),
        )

    logger.info(
        "LanguageTool produced %d issues after filtering", len(all_issues),
    )
    return all_issues
