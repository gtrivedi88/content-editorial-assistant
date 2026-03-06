"""Structural sequence rules — inter-block deterministic analysis.

These rules inspect the ordering and relationships between blocks
in the parsed document, not individual block text. They enforce
Red Hat SSG and IBM Style Guide structural requirements.
"""

import logging
import re
import uuid
from typing import Any

from app.models.enums import IssueCategory, IssueSeverity
from app.models.schemas import IssueResponse

logger = logging.getLogger(__name__)


def run_structural_rules(
    blocks: list,
    content_type: str,
    original_text: str,
) -> list[IssueResponse]:
    """Run all structural sequence checks on the block array.

    Args:
        blocks: Full list of parsed Block objects.
        content_type: Modular documentation type.
        original_text: Original document text.

    Returns:
        List of structural issues.
    """
    issues: list[IssueResponse] = []

    # Filter to analyzable blocks (skip comments, attributes, etc.)
    content_blocks = [b for b in blocks if not b.should_skip_analysis]

    if not content_type:
        logger.debug("content_type is empty/unknown — procedure-specific rules will not fire")

    issues.extend(_check_admonition_placement(content_blocks, original_text))
    issues.extend(_check_where_list_specifies(content_blocks, original_text))
    issues.extend(_check_heading_level_skip(content_blocks, original_text))
    issues.extend(_check_prerequisites_position(content_blocks, original_text, content_type))
    issues.extend(_check_empty_section(content_blocks, original_text))
    issues.extend(_check_admonition_stacking(content_blocks, original_text))
    issues.extend(_check_procedure_step_count(content_blocks, original_text, content_type))
    issues.extend(_check_verification_section(content_blocks, original_text, content_type))

    # Pre-compute inline code ranges per block for technical markup check.
    # Reuses _compute_content_code_ranges from orchestrator.py (same function
    # that powers in_code_range() for all 31 deterministic rules).
    from app.services.analysis.orchestrator import _compute_content_code_ranges
    block_code_ranges: dict[int, list[tuple[int, int]]] = {}
    for i, b in enumerate(content_blocks):
        block_code_ranges[i] = _compute_content_code_ranges(
            b.inline_content or b.content or "", b.char_map,
        )

    # IMPORTANT: pass content_blocks (not unfiltered blocks) so enumerate()
    # indices inside the function match block_code_ranges keys exactly.
    issues.extend(
        _check_technical_term_markup(content_blocks, original_text, block_code_ranges)
    )
    # Pass unfiltered blocks — code blocks have should_skip_analysis=True
    # but _check_unit_consistency needs them to extract unit references.
    issues.extend(_check_unit_consistency(blocks, original_text))

    return issues


# ---------------------------------------------------------------------------
# 2a. Admonition Placement Check
# ---------------------------------------------------------------------------


def _check_admonition_placement(
    blocks: list,
    original_text: str,
) -> list[IssueResponse]:
    """Flag admonitions that appear before the first paragraph (abstract).

    Red Hat SSG p29: "Do not start a module or assembly with an
    admonition, even when adding the Technology Preview admonition.
    Always include a short description before including an admonition."

    Logic: After the first heading, the next content block must be
    a paragraph (the abstract), not an admonition. Also catches
    document fragments that start with an admonition before any title.
    """
    issues: list[IssueResponse] = []
    found_heading = False
    found_paragraph_after_heading = False

    for block in blocks:
        # Pre-heading admonition: module starts with admonition before title
        if not found_heading and block.block_type == "admonition":
            admonition_text = (block.content or "")[:80]
            issues.append(IssueResponse(
                id=str(uuid.uuid4()),
                source="deterministic",
                category=IssueCategory.STRUCTURE,
                rule_name="admonition_placement",
                message=(
                    "Do not start a module with an admonition. A title and "
                    "short description (abstract) must appear before the "
                    "first admonition. (Red Hat SSG)"
                ),
                severity=IssueSeverity.HIGH,
                flagged_text=admonition_text,
                sentence=admonition_text,
                sentence_index=0,
                suggestions=[
                    "Add a title and short description paragraph before "
                    "this admonition.",
                ],
                span=[block.start_pos, block.start_pos + len(admonition_text)],
                confidence=0.95,
            ))
            return issues  # One flag is enough

        if block.block_type == "heading":
            found_heading = True
            found_paragraph_after_heading = False
            continue

        if not found_heading:
            continue

        # Skip non-content blocks (block titles, attributes, etc.)
        if block.block_type in ("attribute_entry", "comment", "block_title"):
            continue

        if block.block_type == "paragraph":
            found_paragraph_after_heading = True
            continue

        if block.block_type == "admonition" and not found_paragraph_after_heading:
            # Admonition appears before any paragraph after heading
            admonition_text = (block.content or "")[:80]
            issues.append(IssueResponse(
                id=str(uuid.uuid4()),
                source="deterministic",
                category=IssueCategory.STRUCTURE,
                rule_name="admonition_placement",
                message=(
                    "Do not start a module with an admonition. Include a "
                    "short description (abstract) between the title and the "
                    "first admonition. (Red Hat SSG)"
                ),
                severity=IssueSeverity.HIGH,
                flagged_text=admonition_text,
                sentence=admonition_text,
                sentence_index=0,
                suggestions=[
                    "Add a short description paragraph before this admonition.",
                    "The abstract should describe WHAT the user will do and "
                    "WHY it matters.",
                ],
                span=[block.start_pos, block.start_pos + len(admonition_text)],
                confidence=0.95,
            ))
            break  # Only flag the first occurrence per heading

    return issues


# ---------------------------------------------------------------------------
# 2b. Where-List "Specifies" Check
# ---------------------------------------------------------------------------

# Regex: backtick-wrapped variable followed by colon/dash and "Specify"
# (not "Specifies").  Supports both `: Specify` and `- Specify` separators
# (Red Hat uses both).
_SPECIFY_PATTERN = re.compile(
    r'`[^`]+`\s*[:：\-–—]\s*Specify\b(?!ing|ies)',
)


def _check_where_list_specifies(
    blocks: list,
    _original_text: str,
) -> list[IssueResponse]:
    """Flag variable descriptions using 'Specify' instead of 'Specifies'.

    Red Hat SSG p20: "Introduce definition lists with 'where:' and
    begin each variable description with 'Specifies'."

    Logic: Find paragraph blocks containing "Where:" or "where:".
    Check subsequent list items for "Specify" vs "Specifies".
    Uses ``inline_content`` (Tier 2) so backtick-wrapped variable names
    are visible to the regex pattern.

    Args:
        blocks: Filtered content blocks.
        _original_text: Original document text (unused, kept for
            consistent check-function signature).

    Returns:
        List of where-list format issues.
    """
    issues: list[IssueResponse] = []
    in_where_context = False

    for block in blocks:
        if block.block_type == "paragraph":
            in_where_context = _is_where_paragraph(block)
            if in_where_context:
                continue

        if not in_where_context:
            continue

        if not _is_where_list_block(block):
            in_where_context = _preserves_where_context(block)
            continue

        _check_specify_in_block(block, issues)

    return issues


def _is_where_paragraph(block: Any) -> bool:
    """Check whether a paragraph block is a 'Where:' introducer.

    Args:
        block: A parsed Block object.

    Returns:
        True if the block text ends with 'where:'.
    """
    text = (block.inline_content or block.content or "").strip()
    return bool(re.search(r'\bwhere\s*:\s*$', text, re.IGNORECASE))


def _is_where_list_block(block: Any) -> bool:
    """Check whether a block type is valid inside a Where: list.

    Args:
        block: A parsed Block object.

    Returns:
        True if the block is a list item or paragraph.
    """
    return block.block_type in (
        "list_item_unordered", "list_item_ordered",
        "list_item", "paragraph",
    )


def _preserves_where_context(block: Any) -> bool:
    """Check whether a non-list block should preserve Where: context.

    Structural noise (comments, attribute entries, continuation markers)
    should not end the Where: context.

    Args:
        block: A parsed Block object.

    Returns:
        True if the block is structural noise that preserves context.
    """
    return block.block_type in ("comment", "attribute_entry", "continuation")


def _check_specify_in_block(
    block: Any, issues: list[IssueResponse],
) -> None:
    """Check a single block for 'Specify' instead of 'Specifies'.

    Uses ``inline_content`` (Tier 2) to preserve backticks so the
    regex pattern can match backtick-wrapped variable names.

    Args:
        block: A parsed Block with variable descriptions.
        issues: Issue list to append to (mutated in place).
    """
    content = block.inline_content or block.content or ""
    match = _SPECIFY_PATTERN.search(content)
    if not match:
        return

    specify_start = content.find("Specify", match.start())
    if specify_start < 0:
        return

    orig_pos = block.start_pos + specify_start
    issues.append(IssueResponse(
        id=str(uuid.uuid4()),
        source="deterministic",
        category=IssueCategory.STRUCTURE,
        rule_name="where_list_format",
        message=(
            "Use 'Specifies' (third person declarative) instead "
            "of 'Specify' (imperative) in variable description "
            "lists after 'Where:'. (Red Hat SSG)"
        ),
        severity=IssueSeverity.LOW,
        flagged_text="Specify",
        sentence=content.strip(),
        sentence_index=0,
        suggestions=[
            "Change 'Specify' to 'Specifies'.",
        ],
        span=[orig_pos, orig_pos + 7],
        confidence=0.95,
    ))


# ---------------------------------------------------------------------------
# 2c. Technical Term Markup Check
# ---------------------------------------------------------------------------

# Technical terms that must be in backtick monospace (Red Hat/OpenShift)
_TECHNICAL_TERMS = frozenset({
    "ostree", "rpm-ostree", "systemd", "bootc", "podman", "buildah",
    "skopeo", "crio", "crictl", "kubelet", "etcd", "coredns",
    "haproxy", "keepalived", "firewalld", "NetworkManager",
    "nmcli", "nmstatectl", "butane", "ignition", "coreos",
    "rhcos", "fcos", "microshift", "crun", "runc",
})

# Pattern: word boundary + term + word boundary, case-insensitive
# to catch "Ostree" at sentence start, "SYSTEMD" in caps, etc.
_TERM_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(t) for t in _TECHNICAL_TERMS) + r')\b',
    re.IGNORECASE,
)


def _check_technical_term_markup(
    blocks: list,
    original_text: str,
    block_code_ranges: dict[int, list[tuple[int, int]]],
) -> list[IssueResponse]:
    """Flag technical terms in prose that lack backtick formatting.

    IBM Style Guide p184-191: Commands, utilities, and system
    components should use monospace formatting.

    Logic: Search paragraph/heading content for known technical terms.
    Uses pre-computed inline code ranges (from _compute_content_code_ranges)
    and in_code_range() to verify the term is NOT already inside backticks.
    This is the same guard logic used by all 31 deterministic rules.

    IMPORTANT: ``blocks`` must be the same filtered list used to build
    ``block_code_ranges`` (i.e., ``content_blocks`` from the caller).
    Passing the unfiltered block list will cause index mismatches.
    """
    from rules.base_rule import in_code_range

    issues: list[IssueResponse] = []
    seen_terms: set[str] = set()  # Deduplicate across blocks

    for idx, block in enumerate(blocks):
        if block.block_type not in ("paragraph", "heading", "preamble"):
            continue

        content = block.content or ""
        code_ranges = block_code_ranges.get(idx, [])

        for match in _TERM_PATTERN.finditer(content):
            term = match.group(1)

            # Skip if already flagged this term
            if term.lower() in seen_terms:
                continue

            # Skip if term is inside inline code (backticks)
            # Uses the same in_code_range() guard as all deterministic rules
            if in_code_range(match.start(), code_ranges):
                continue

            seen_terms.add(term.lower())
            orig_pos = block.start_pos + match.start()
            issues.append(IssueResponse(
                id=str(uuid.uuid4()),
                source="deterministic",
                category=IssueCategory.TECHNICAL,
                rule_name="technical_markup",
                message=(
                    f"Format '{term}' as inline code (`{term}`) — technical "
                    f"terms, commands, and system components should use "
                    f"monospace formatting. (IBM Style Guide)"
                ),
                severity=IssueSeverity.LOW,
                flagged_text=term,
                sentence=content.strip()[:120],
                sentence_index=0,
                suggestions=[f"`{term}`"],
                span=[orig_pos, orig_pos + len(term)],
                confidence=0.9,
            ))

    return issues


# ---------------------------------------------------------------------------
# 2d. Unit Consistency Check (Code Block vs. Prose)
# ---------------------------------------------------------------------------

# Binary unit prefixes in code
_CODE_UNIT_RE = re.compile(
    r'\b(size|capacity|limit|max|min|memory|disk|storage|partition)'
    r'[_-]?'
    r'(Ki?B|Mi?B|Gi?B|Ti?B|bytes?|KB|MB|GB|TB)\b',
    re.IGNORECASE,
)

# Units mentioned in prose
_PROSE_UNIT_RE = re.compile(
    r'(\d+[\d,.]*)\s*(KiB|MiB|GiB|TiB|KB|MB|GB|TB|bytes?)\b',
    re.IGNORECASE,
)

# Binary <-> decimal mismatch pairs (same-scale)
_UNIT_CONFLICTS: dict[str, str] = {
    "kib": "kb", "kb": "kib",
    "mib": "mb", "mb": "mib",
    "gib": "gb", "gb": "gib",
    "tib": "tb", "tb": "tib",
}

# Unit system classification
_BINARY_UNITS = frozenset({"kib", "mib", "gib", "tib"})
_DECIMAL_UNITS = frozenset({"kb", "mb", "gb", "tb"})


def _check_unit_consistency(
    blocks: list,
    _original_text: str,
) -> list[IssueResponse]:
    """Flag mismatched binary/decimal units between code blocks and prose.

    IBM Style Guide p161-164: Use consistent unit prefixes.
    Detects two types of mismatch:

    1. **Same-scale**: prose uses MB but code uses MiB (or vice versa).
    2. **Cross-scale system**: prose uses GB (decimal) but code only uses
       binary units like MiB — different unit systems in the same section.

    Args:
        blocks: Full (unfiltered) list of parsed Block objects.
        _original_text: Original document text (unused, kept for
            consistent check-function signature).

    Returns:
        List of unit-consistency issues.
    """
    code_units = _collect_code_units(blocks)
    if not code_units:
        return []

    code_has_binary = bool(code_units & _BINARY_UNITS)
    code_has_decimal = bool(code_units & _DECIMAL_UNITS)

    return _check_prose_units(blocks, code_units, code_has_binary, code_has_decimal)


def _collect_code_units(blocks: list) -> set[str]:
    """Collect all unit references from code blocks.

    Scans ALL blocks (including skipped) since code blocks have
    ``should_skip_analysis=True`` but contain unit references.

    Args:
        blocks: Full list of parsed Block objects.

    Returns:
        Set of lowercase unit strings found in code blocks.
    """
    code_units: set[str] = set()
    for block in blocks:
        if block.block_type not in ("code_block", "listing", "literal"):
            continue
        raw = block.raw_content or block.content or ""
        for m in _CODE_UNIT_RE.finditer(raw):
            code_units.add(m.group(2).lower())
        # Also check for bare unit field names like "sizeMiB"
        for m in re.finditer(r'(MiB|GiB|KiB|TiB|MB|GB|KB|TB)', raw):
            code_units.add(m.group(1).lower())
    return code_units


def _check_prose_units(
    blocks: list,
    code_units: set[str],
    code_has_binary: bool,
    code_has_decimal: bool,
) -> list[IssueResponse]:
    """Check prose blocks for unit conflicts against code block units.

    Args:
        blocks: Full list of parsed Block objects.
        code_units: Unit strings found in code blocks.
        code_has_binary: True if code contains binary units.
        code_has_decimal: True if code contains decimal units.

    Returns:
        List of unit-consistency issues.
    """
    issues: list[IssueResponse] = []

    for block in blocks:
        if block.block_type not in (
            "paragraph", "list_item_unordered",
            "list_item_ordered", "list_item",
        ):
            continue

        content = block.content or ""
        for m in _PROSE_UNIT_RE.finditer(content):
            issue = _evaluate_unit_match(
                m, block, code_units, code_has_binary, code_has_decimal, content,
            )
            if issue:
                issues.append(issue)

    return issues


def _evaluate_unit_match(
    m: re.Match,
    block: Any,
    code_units: set[str],
    code_has_binary: bool,
    code_has_decimal: bool,
    content: str,
) -> IssueResponse | None:
    """Evaluate a single prose unit match for conflicts.

    Args:
        m: Regex match of a unit in prose.
        block: The block containing the match.
        code_units: Unit strings from code blocks.
        code_has_binary: True if code uses binary units.
        code_has_decimal: True if code uses decimal units.
        content: Full text of the block.

    Returns:
        An IssueResponse if conflict detected, else None.
    """
    prose_unit = m.group(2).lower()

    # Check 1: same-scale conflict (e.g., MiB in code, MB in prose)
    conflicting = _UNIT_CONFLICTS.get(prose_unit)
    if conflicting and conflicting in code_units:
        return _create_unit_issue(
            m, block, content,
            f"Unit mismatch: prose uses '{m.group(2)}' but code "
            f"blocks use '{conflicting.upper()}'. Use consistent "
            f"unit prefixes — do not mix binary (KiB/MiB/GiB) "
            f"with decimal (KB/MB/GB). (IBM Style Guide)",
            f"Change '{m.group(2)}' to '{conflicting.upper()}' "
            f"to match the code block units.",
        )

    # Check 2: cross-scale system conflict (e.g., MiB in code, GB in prose)
    prose_is_decimal = prose_unit in _DECIMAL_UNITS
    prose_is_binary = prose_unit in _BINARY_UNITS
    if (prose_is_decimal and code_has_binary and not code_has_decimal) or \
       (prose_is_binary and code_has_decimal and not code_has_binary):
        code_system = "binary (KiB/MiB/GiB)" if code_has_binary else "decimal (KB/MB/GB)"
        return _create_unit_issue(
            m, block, content,
            f"Unit system mismatch: prose uses '{m.group(2)}' ({_unit_system_label(prose_unit)}) "
            f"but code blocks use {code_system}. Use consistent "
            f"unit systems throughout. (IBM Style Guide)",
            f"Change '{m.group(2)}' to the {code_system.split(' ')[0]} equivalent, "
            f"or update the code block to use {_unit_system_label(prose_unit)} units.",
        )

    return None


def _unit_system_label(unit: str) -> str:
    """Return 'binary' or 'decimal' label for a unit.

    Args:
        unit: Lowercase unit string.

    Returns:
        System label string.
    """
    if unit in _BINARY_UNITS:
        return "binary"
    return "decimal"


def _create_unit_issue(
    m: re.Match,
    block: Any,
    content: str,
    message: str,
    suggestion: str,
) -> IssueResponse:
    """Create a unit-consistency IssueResponse.

    Args:
        m: Regex match of the prose unit.
        block: The block containing the match.
        content: Full text of the block.
        message: Issue message.
        suggestion: Suggested fix.

    Returns:
        A populated IssueResponse.
    """
    orig_pos = block.start_pos + m.start()
    flagged = m.group(0)
    return IssueResponse(
        id=str(uuid.uuid4()),
        source="deterministic",
        category=IssueCategory.NUMBERS,
        rule_name="unit_consistency",
        message=message,
        severity=IssueSeverity.MEDIUM,
        flagged_text=flagged,
        sentence=content.strip()[:120],
        sentence_index=0,
        suggestions=[suggestion],
        span=[orig_pos, orig_pos + len(flagged)],
        confidence=0.85,
    )


# ---------------------------------------------------------------------------
# 2e. Heading Level Skip Check
# ---------------------------------------------------------------------------


def _check_heading_level_skip(
    blocks: list,
    original_text: str,
) -> list[IssueResponse]:
    """Flag headings that skip levels (e.g., h1 directly to h3).

    IBM Style Guide p181-183: Heading levels must be sequential.
    AsciiDoc heading levels are 1-based (count of ``=`` symbols).
    Block titles (``.Prerequisites``) have level 0 and are skipped.

    Args:
        blocks: Filtered content blocks.
        original_text: Original document text.

    Returns:
        List of heading-level-skip issues.
    """
    issues: list[IssueResponse] = []
    prev_level = 0

    for block in blocks:
        if block.block_type != "heading":
            continue
        level = getattr(block, "level", 0)
        # Skip level 0 (block titles like .Prerequisites — not structural headings)
        if level == 0:
            continue
        if prev_level > 0 and level > prev_level + 1:
            heading_text = (block.content or "")[:80]
            issues.append(IssueResponse(
                id=str(uuid.uuid4()),
                source="deterministic",
                category=IssueCategory.STRUCTURE,
                rule_name="heading_level_skip",
                message=(
                    f"Heading level skipped: jumped from level {prev_level} to "
                    f"level {level}. Do not skip heading levels — add "
                    f"intermediate headings for proper document hierarchy. "
                    f"(IBM Style Guide)"
                ),
                severity=IssueSeverity.MEDIUM,
                flagged_text=heading_text,
                sentence=heading_text,
                sentence_index=0,
                suggestions=[
                    f"Add a level {prev_level + 1} heading before this "
                    f"level {level} heading.",
                ],
                span=[block.start_pos, block.start_pos + len(heading_text)],
                confidence=0.95,
            ))
        prev_level = level

    return issues


# ---------------------------------------------------------------------------
# 2f. Prerequisites Position Check
# ---------------------------------------------------------------------------


def _check_prerequisites_position(
    blocks: list,
    original_text: str,
    content_type: str,
) -> list[IssueResponse]:
    """Flag procedures where .Procedure appears before .Prerequisites.

    Modular Docs Reference Guide: In procedure modules,
    ``.Prerequisites`` must appear before ``.Procedure``.

    Only fires when ``content_type == "procedure"``.

    Args:
        blocks: Filtered content blocks.
        original_text: Original document text.
        content_type: Modular documentation type.

    Returns:
        List of prerequisites-position issues.
    """
    if content_type != "procedure":
        return []

    issues: list[IssueResponse] = []
    procedure_pos = -1
    prereq_pos = -1

    for idx, block in enumerate(blocks):
        if block.block_type != "heading" or getattr(block, "level", 1) != 0:
            continue
        title = (block.content or "").strip().lower()
        if title == "procedure" and procedure_pos < 0:
            procedure_pos = idx
        elif title == "prerequisites" and prereq_pos < 0:
            prereq_pos = idx

    if procedure_pos >= 0 and prereq_pos > procedure_pos:
        prereq_block = blocks[prereq_pos]
        flagged = (prereq_block.content or "")[:80]
        issues.append(IssueResponse(
            id=str(uuid.uuid4()),
            source="deterministic",
            category=IssueCategory.STRUCTURE,
            rule_name="prerequisites_position",
            message=(
                "Prerequisites section appears after the Procedure section. "
                "Move .Prerequisites before .Procedure so readers see "
                "requirements before starting the task. "
                "(Modular Documentation Reference Guide)"
            ),
            severity=IssueSeverity.MEDIUM,
            flagged_text=flagged,
            sentence=flagged,
            sentence_index=0,
            suggestions=[
                "Move the .Prerequisites section before .Procedure.",
            ],
            span=[prereq_block.start_pos, prereq_block.start_pos + len(flagged)],
            confidence=0.95,
        ))

    return issues


# ---------------------------------------------------------------------------
# 2g. Empty Section Check
# ---------------------------------------------------------------------------


def _check_empty_section(
    blocks: list,
    original_text: str,
) -> list[IssueResponse]:
    """Flag headings with no content before the next heading.

    IBM Style Guide p181: Every heading should introduce content.

    Args:
        blocks: Filtered content blocks.
        original_text: Original document text.

    Returns:
        List of empty-section issues.
    """
    issues: list[IssueResponse] = []
    last_heading = None
    has_content = False

    for block in blocks:
        is_heading = block.block_type == "heading" and getattr(block, "level", 0) > 0
        if is_heading:
            if last_heading is not None and not has_content:
                heading_text = (last_heading.content or "")[:80]
                issues.append(IssueResponse(
                    id=str(uuid.uuid4()),
                    source="deterministic",
                    category=IssueCategory.STRUCTURE,
                    rule_name="empty_section",
                    message=(
                        "Empty section — this heading has no content before "
                        "the next heading. Add content or remove the empty "
                        "heading. (IBM Style Guide)"
                    ),
                    severity=IssueSeverity.MEDIUM,
                    flagged_text=heading_text,
                    sentence=heading_text,
                    sentence_index=0,
                    suggestions=[
                        "Add content under this heading, or remove it if "
                        "it is unnecessary.",
                    ],
                    span=[
                        last_heading.start_pos,
                        last_heading.start_pos + len(heading_text),
                    ],
                    confidence=0.9,
                ))
            last_heading = block
            has_content = False
        elif last_heading is not None:
            # Any non-heading content counts
            if block.block_type not in ("attribute_entry", "comment", "block_title"):
                has_content = True

    return issues


# ---------------------------------------------------------------------------
# 2h. Admonition Stacking Check
# ---------------------------------------------------------------------------


def _check_admonition_stacking(
    blocks: list,
    original_text: str,
) -> list[IssueResponse]:
    """Flag consecutive admonitions without prose between them.

    Red Hat SSG: Do not stack admonitions. Separate them with
    explanatory prose or consolidate into a single admonition.

    Args:
        blocks: Filtered content blocks.
        original_text: Original document text.

    Returns:
        List of admonition-stacking issues.
    """
    issues: list[IssueResponse] = []
    consecutive_admonitions = 0
    first_stacked_block = None

    for block in blocks:
        if block.block_type == "admonition":
            consecutive_admonitions += 1
            if consecutive_admonitions == 2:
                first_stacked_block = block
        else:
            if consecutive_admonitions >= 2 and first_stacked_block is not None:
                flagged = (first_stacked_block.content or "")[:80]
                issues.append(IssueResponse(
                    id=str(uuid.uuid4()),
                    source="deterministic",
                    category=IssueCategory.STRUCTURE,
                    rule_name="admonition_stacking",
                    message=(
                        f"Stacked admonitions — {consecutive_admonitions} "
                        f"consecutive admonitions without prose between them. "
                        f"Add explanatory text between admonitions or "
                        f"consolidate them. (Red Hat SSG)"
                    ),
                    severity=IssueSeverity.LOW,
                    flagged_text=flagged,
                    sentence=flagged,
                    sentence_index=0,
                    suggestions=[
                        "Add prose between these admonitions, or consolidate "
                        "them into a single admonition.",
                    ],
                    span=[
                        first_stacked_block.start_pos,
                        first_stacked_block.start_pos + len(flagged),
                    ],
                    confidence=0.9,
                ))
            consecutive_admonitions = 0
            first_stacked_block = None

    # Handle trailing stacked admonitions at end of document
    if consecutive_admonitions >= 2 and first_stacked_block is not None:
        flagged = (first_stacked_block.content or "")[:80]
        issues.append(IssueResponse(
            id=str(uuid.uuid4()),
            source="deterministic",
            category=IssueCategory.STRUCTURE,
            rule_name="admonition_stacking",
            message=(
                f"Stacked admonitions — {consecutive_admonitions} "
                f"consecutive admonitions at end of section. "
                f"Add explanatory text or consolidate. (Red Hat SSG)"
            ),
            severity=IssueSeverity.LOW,
            flagged_text=flagged,
            sentence=flagged,
            sentence_index=0,
            suggestions=[
                "Add prose between these admonitions, or consolidate "
                "them into a single admonition.",
            ],
            span=[
                first_stacked_block.start_pos,
                first_stacked_block.start_pos + len(flagged),
            ],
            confidence=0.9,
        ))

    return issues


# ---------------------------------------------------------------------------
# 2i. Procedure Step Count Check
# ---------------------------------------------------------------------------


def _check_procedure_step_count(
    blocks: list,
    original_text: str,
    content_type: str,
) -> list[IssueResponse]:
    """Flag procedures with more than 10 consecutive ordered list items.

    Minimalism principles: Long procedures should be broken into
    smaller tasks.  Advisory severity (LOW).

    Only fires when ``content_type == "procedure"``.

    Args:
        blocks: Filtered content blocks.
        original_text: Original document text.
        content_type: Modular documentation type.

    Returns:
        List of step-count issues.
    """
    if content_type != "procedure":
        return []

    issues: list[IssueResponse] = []
    consecutive_steps = 0
    first_step_block = None

    for block in blocks:
        if block.block_type == "list_item_ordered":
            consecutive_steps += 1
            if consecutive_steps == 1:
                first_step_block = block
        else:
            if consecutive_steps > 10 and first_step_block is not None:
                _append_step_count_issue(issues, consecutive_steps, first_step_block)
            consecutive_steps = 0
            first_step_block = None

    # Handle trailing steps at end of document
    if consecutive_steps > 10 and first_step_block is not None:
        _append_step_count_issue(issues, consecutive_steps, first_step_block)

    return issues


def _append_step_count_issue(
    issues: list,
    step_count: int,
    first_block: Any,
) -> None:
    """Append a procedure-step-count issue to the list.

    Args:
        issues: List to append to (mutated in place).
        step_count: Number of consecutive steps.
        first_block: The first step block (for span).
    """
    flagged = (first_block.content or "")[:80]
    issues.append(IssueResponse(
        id=str(uuid.uuid4()),
        source="deterministic",
        category=IssueCategory.STRUCTURE,
        rule_name="procedure_step_count",
        message=(
            f"Long procedure — {step_count} consecutive steps. "
            f"Consider breaking this into smaller sub-procedures "
            f"or grouping related steps. (Minimalism principles)"
        ),
        severity=IssueSeverity.LOW,
        flagged_text=flagged,
        sentence=flagged,
        sentence_index=0,
        suggestions=[
            "Break this procedure into smaller sub-tasks, each with "
            "7-10 steps maximum.",
        ],
        span=[first_block.start_pos, first_block.start_pos + len(flagged)],
        confidence=0.8,
    ))


# ---------------------------------------------------------------------------
# 2j. Verification Section Check
# ---------------------------------------------------------------------------


def _check_verification_section(
    blocks: list,
    _original_text: str,
    content_type: str,
) -> list[IssueResponse]:
    """Flag procedure modules missing a .Verification section.

    Modular Documentation Reference Guide: Procedure modules should
    include a ``.Verification`` block title so readers can confirm
    the task completed successfully.

    Only fires when ``content_type == "procedure"``.

    Args:
        blocks: Filtered content blocks.
        _original_text: Original document text (unused, kept for
            consistent check-function signature).
        content_type: Modular documentation type.

    Returns:
        List of missing-verification issues.
    """
    if content_type != "procedure":
        return []

    has_verification = False
    procedure_block = None

    for block in blocks:
        if block.block_type != "heading" or getattr(block, "level", 1) != 0:
            continue
        title = (block.content or "").strip().lower()
        if title == "verification":
            has_verification = True
            break
        if title == "procedure" and procedure_block is None:
            procedure_block = block

    if has_verification or procedure_block is None:
        return []

    flagged = (procedure_block.content or "")[:80]
    return [IssueResponse(
        id=str(uuid.uuid4()),
        source="deterministic",
        category=IssueCategory.STRUCTURE,
        rule_name="verification_section",
        message=(
            "Procedure module is missing a .Verification section. "
            "Add a verification section so readers can confirm "
            "the task completed successfully. "
            "(Modular Documentation Reference Guide)"
        ),
        severity=IssueSeverity.LOW,
        flagged_text=flagged,
        sentence=flagged,
        sentence_index=0,
        suggestions=[
            "Add a '.Verification' section after the procedure steps "
            "with commands or checks to verify success.",
        ],
        span=[procedure_block.start_pos, procedure_block.start_pos + len(flagged)],
        confidence=0.85,
    )]
