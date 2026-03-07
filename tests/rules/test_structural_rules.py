"""Tests for inter-block structural analysis rules."""
import importlib
import sys

import pytest
from app.services.parsing.base import Block

# The rules.modular_compliance __init__.py imports legacy modules that depend
# on structural_parsing (not installed).  Pre-register the package so Python
# skips __init__.py when we import our specific module.
if "rules.modular_compliance" not in sys.modules:
    import types
    _pkg = types.ModuleType("rules.modular_compliance")
    _pkg.__path__ = [
        str(
            importlib.resources.files("rules") / "modular_compliance"
            if hasattr(importlib, "resources")
            else __import__("pathlib").Path(__file__).resolve().parents[2]
            / "rules" / "modular_compliance"
        )
    ]
    sys.modules["rules.modular_compliance"] = _pkg

from rules.modular_compliance.structural_rules import (  # noqa: E402
    _check_admonition_placement,
    _check_admonition_stacking,
    _check_empty_section,
    _check_heading_level_skip,
    _check_prerequisites_position,
    _check_procedure_step_count,
    _check_technical_term_markup,
    _check_unit_consistency,
    _check_verification_section,
    _check_where_list_specifies,
    run_structural_rules,
)


def _make_block(
    block_type: str,
    content: str,
    start_pos: int = 0,
    level: int = 0,
    skip: bool = False,
    inline_content: str = "",
) -> Block:
    """Helper to create test Block objects.

    Args:
        block_type: Block type string.
        content: Tier 3 plain text (inline markers stripped).
        start_pos: Character offset.
        level: Heading level.
        skip: Whether to skip analysis.
        inline_content: Tier 2 text (block markers stripped, inline
            markers preserved).  Defaults to ``content`` via
            ``Block.__post_init__``.
    """
    return Block(
        block_type=block_type,
        content=content,
        raw_content=content,
        start_pos=start_pos,
        end_pos=start_pos + len(content),
        level=level,
        should_skip_analysis=skip,
        inline_content=inline_content,
    )


class TestAdmonitionPlacement:
    """Verify admonition placement structural check."""

    def test_admonition_after_heading_flagged(self) -> None:
        """Admonition immediately after heading (no abstract) is flagged."""
        blocks = [
            _make_block("heading", "Configuring shared partition", 0, level=1),
            _make_block(
                "admonition",
                "You must complete this at install time.",
                50,
            ),
        ]

        issues = _check_admonition_placement(blocks)
        assert len(issues) == 1
        assert "admonition" in issues[0].message.lower()
        assert issues[0].rule_name == "admonition_placement"

    def test_admonition_after_paragraph_ok(self) -> None:
        """Admonition after abstract paragraph is acceptable."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("paragraph", "This is the abstract.", 20),
            _make_block("admonition", "Important note.", 60),
        ]

        issues = _check_admonition_placement(blocks)
        assert len(issues) == 0

    def test_skipped_blocks_ignored(self) -> None:
        """Attribute entries between heading and paragraph are transparent."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("attribute_entry", ":context: value", 20),
            _make_block("paragraph", "Abstract text.", 40),
            _make_block("admonition", "Note.", 70),
        ]

        issues = _check_admonition_placement(blocks)
        assert len(issues) == 0

    def test_pre_heading_admonition_flagged(self) -> None:
        """Document fragment starting with admonition before any title."""
        blocks = [
            _make_block(
                "admonition",
                "Technology Preview: this feature is unsupported.",
                0,
            ),
            _make_block("heading", "Configuring ostree", 60, level=1),
        ]

        issues = _check_admonition_placement(blocks)
        assert len(issues) == 1
        assert "title" in issues[0].message.lower()

    def test_issue_has_required_fields(self) -> None:
        """Structural issues have id, source, category, severity enums."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("admonition", "Note text.", 20),
        ]

        issues = _check_admonition_placement(blocks)
        assert len(issues) == 1
        issue = issues[0]
        assert issue.id  # Non-empty UUID
        assert issue.source == "deterministic"
        assert issue.category.value == "structure"
        assert issue.severity.value == "high"


class TestWhereListSpecifies:
    """Verify Where: list formatting check."""

    def test_specify_flagged_after_where(self) -> None:
        """'Specify' (imperative) in Where: list is flagged."""
        blocks = [
            _make_block("paragraph", "Where:", 0),
            _make_block(
                "list_item_unordered",
                "<root_disk>: Specify the root disk.",
                10,
                inline_content="`<root_disk>`: Specify the root disk.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        assert len(issues) == 1
        assert "Specifies" in issues[0].message
        assert issues[0].flagged_text == "Specify"

    def test_specify_with_dash_separator_flagged(self) -> None:
        """'Specify' with dash separator is also flagged."""
        blocks = [
            _make_block("paragraph", "Where:", 0),
            _make_block(
                "list_item_unordered",
                "<partition> - Specify the partition name.",
                10,
                inline_content="`<partition>` - Specify the partition name.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        assert len(issues) == 1

    def test_specifies_not_flagged(self) -> None:
        """'Specifies' (correct form) is not flagged."""
        blocks = [
            _make_block("paragraph", "Where:", 0),
            _make_block(
                "list_item_unordered",
                "<root_disk>: Specifies the root disk.",
                10,
                inline_content="`<root_disk>`: Specifies the root disk.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        assert len(issues) == 0

    def test_no_where_context_not_flagged(self) -> None:
        """'Specify' outside Where: context is not flagged."""
        blocks = [
            _make_block("paragraph", "Some other text.", 0),
            _make_block(
                "list_item_unordered",
                "<var>: Specify something.",
                20,
                inline_content="`<var>`: Specify something.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        assert len(issues) == 0

    def test_tier2_backticks_required_for_match(self) -> None:
        """Regex requires backtick-wrapped vars — uses inline_content (Tier 2).

        In real parsing, block.content (Tier 3) has backticks stripped.
        The fix uses inline_content which preserves them.
        """
        blocks = [
            _make_block("paragraph", "Where:", 0),
            _make_block(
                "list_item_unordered",
                # Tier 3: backticks stripped (what content looks like)
                "<root_disk>: Specify the root disk.",
                10,
                # Tier 2: backticks preserved (what inline_content looks like)
                inline_content="`<root_disk>`: Specify the root disk.",
            ),
            _make_block(
                "list_item_unordered",
                "<start>: Specify the start position.",
                50,
                inline_content="`<start>`: Specify the start position.",
            ),
            _make_block(
                "list_item_unordered",
                "<size>: Specify a minimum size of 500 GB.",
                90,
                inline_content="`<size>`: Specify a minimum size of 500 GB.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        # All three instances should be flagged
        assert len(issues) == 3

    def test_multiple_specify_all_flagged(self) -> None:
        """All 'Specify' instances in a Where: list are flagged."""
        blocks = [
            _make_block("paragraph", "Where:", 0),
            _make_block(
                "list_item_unordered",
                "<a>: Specify A.",
                10,
                inline_content="`<a>`: Specify A.",
            ),
            _make_block(
                "list_item_unordered",
                "<b>: Specify B.",
                30,
                inline_content="`<b>`: Specify B.",
            ),
        ]

        issues = _check_where_list_specifies(blocks, "")
        assert len(issues) == 2


class TestUnitConsistency:
    """Verify unit consistency check between code and prose."""

    def test_mib_vs_mb_flagged(self) -> None:
        """Prose MB with code MiB produces a same-scale mismatch issue."""
        blocks = [
            _make_block("code_block", "sizeMiB: 500000", 0, skip=True),
            _make_block(
                "paragraph",
                "Specify a minimum size of 500 MB.",
                30,
            ),
        ]

        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 1
        assert "mismatch" in issues[0].message.lower()
        assert issues[0].rule_name == "unit_consistency"

    def test_consistent_units_ok(self) -> None:
        """Matching units (MiB in both) produce no issues."""
        blocks = [
            _make_block("code_block", "sizeMiB: 500000", 0, skip=True),
            _make_block(
                "paragraph",
                "Specify a minimum size of 500 MiB.",
                30,
            ),
        ]

        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 0

    def test_no_code_blocks_no_issues(self) -> None:
        """Without code blocks, unit consistency check returns nothing."""
        blocks = [
            _make_block("paragraph", "Use at least 500 GB.", 0),
        ]

        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 0

    def test_cross_scale_mib_vs_gb_flagged(self) -> None:
        """Code MiB with prose GB (different scale) is a system mismatch."""
        blocks = [
            _make_block("code_block", "sizeMiB: 500000", 0, skip=True),
            _make_block(
                "list_item_unordered",
                "Specify a minimum size of 500 GB.",
                30,
            ),
        ]

        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 1
        assert "system mismatch" in issues[0].message.lower()
        assert issues[0].rule_name == "unit_consistency"

    def test_cross_scale_gib_vs_mb_flagged(self) -> None:
        """Code GiB with prose MB is a system mismatch."""
        blocks = [
            _make_block("code_block", "capacity: 100GiB", 0, skip=True),
            _make_block(
                "paragraph",
                "Requires 100000 MB of space.",
                30,
            ),
        ]

        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 1
        assert "system mismatch" in issues[0].message.lower()

    def test_mixed_systems_in_code_not_flagged(self) -> None:
        """Code using both binary and decimal units does not flag prose."""
        blocks = [
            _make_block(
                "code_block",
                "sizeMiB: 500\ncapacityGB: 100",
                0,
                skip=True,
            ),
            _make_block(
                "paragraph",
                "Specify a size of 500 GB.",
                40,
            ),
        ]

        # Code uses both systems so cross-scale check shouldn't fire
        issues = _check_unit_consistency(blocks, "")
        assert len(issues) == 0


class TestTechnicalMarkup:
    """Verify technical term backtick check."""

    def test_ostree_without_backticks_flagged(self) -> None:
        """Technical term 'ostree' without backticks is flagged."""
        blocks = [
            _make_block(
                "heading",
                "Configuring ostree stateroots",
                0,
                level=1,
            ),
        ]

        block_code_ranges: dict[int, list[tuple[int, int]]] = {0: []}
        issues = _check_technical_term_markup(blocks, "", block_code_ranges)
        assert len(issues) == 1
        assert "ostree" in issues[0].flagged_text

    def test_term_in_backticks_not_flagged(self) -> None:
        """Technical term inside backticks (code range) is not flagged."""
        blocks = [
            _make_block(
                "paragraph",
                "Configure the ostree stateroots.",
                0,
            ),
        ]

        # Simulate code ranges covering "ostree" position (index 14-20)
        block_code_ranges: dict[int, list[tuple[int, int]]] = {0: [(14, 20)]}
        issues = _check_technical_term_markup(blocks, "", block_code_ranges)
        assert len(issues) == 0

    def test_case_insensitive_match(self) -> None:
        """Technical terms matched case-insensitively (e.g. 'Ostree')."""
        blocks = [
            _make_block("paragraph", "Ostree is a tool for deployments.", 0),
        ]

        block_code_ranges: dict[int, list[tuple[int, int]]] = {0: []}
        issues = _check_technical_term_markup(blocks, "", block_code_ranges)
        assert len(issues) == 1

    def test_deduplication_across_blocks(self) -> None:
        """Same term in multiple blocks is only flagged once."""
        blocks = [
            _make_block("paragraph", "Configure ostree here.", 0),
            _make_block("paragraph", "Use ostree for updates.", 30),
        ]

        block_code_ranges: dict[int, list[tuple[int, int]]] = {0: [], 1: []}
        issues = _check_technical_term_markup(blocks, "", block_code_ranges)
        assert len(issues) == 1

    def test_code_blocks_skipped(self) -> None:
        """Code blocks are not checked for technical term markup."""
        blocks = [
            _make_block("code_block", "ostree admin deploy", 0, skip=True),
        ]

        block_code_ranges: dict[int, list[tuple[int, int]]] = {0: []}
        issues = _check_technical_term_markup(blocks, "", block_code_ranges)
        assert len(issues) == 0


class TestHeadingLevelSkip:
    """Verify heading level skip check."""

    def test_skip_from_h1_to_h3_flagged(self) -> None:
        """Jumping from level 1 to level 3 (skipping h2) is flagged."""
        blocks = [
            _make_block("heading", "Document Title", 0, level=1),
            _make_block("paragraph", "Abstract text.", 20),
            _make_block("heading", "Deep Section", 40, level=3),
        ]

        issues = _check_heading_level_skip(blocks, "")
        assert len(issues) == 1
        assert "skipped" in issues[0].message.lower()
        assert issues[0].rule_name == "heading_level_skip"

    def test_sequential_levels_ok(self) -> None:
        """Sequential heading levels (1→2→3) produce no issues."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("paragraph", "Text.", 10),
            _make_block("heading", "Section", 20, level=2),
            _make_block("paragraph", "More text.", 30),
            _make_block("heading", "Subsection", 40, level=3),
        ]

        issues = _check_heading_level_skip(blocks, "")
        assert len(issues) == 0

    def test_level_0_block_titles_skipped(self) -> None:
        """Block titles (level 0) are ignored in heading level tracking."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Prerequisites", 20, level=0),
            _make_block("heading", "Section", 40, level=2),
        ]

        issues = _check_heading_level_skip(blocks, "")
        assert len(issues) == 0

    def test_decrease_in_level_ok(self) -> None:
        """Going from h3 back to h1 is acceptable (closing sections)."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Section", 10, level=2),
            _make_block("heading", "Sub", 20, level=3),
            _make_block("heading", "Next Title", 30, level=1),
        ]

        issues = _check_heading_level_skip(blocks, "")
        assert len(issues) == 0


class TestPrerequisitesPosition:
    """Verify prerequisites position check for procedures."""

    def test_prereq_after_procedure_flagged(self) -> None:
        """Prerequisites appearing after Procedure is flagged."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Procedure", 20, level=0),
            _make_block("paragraph", "Step 1.", 30),
            _make_block("heading", "Prerequisites", 50, level=0),
            _make_block("paragraph", "Need X.", 70),
        ]

        issues = _check_prerequisites_position(blocks, "", "procedure")
        assert len(issues) == 1
        assert issues[0].rule_name == "prerequisites_position"

    def test_prereq_before_procedure_ok(self) -> None:
        """Prerequisites before Procedure (correct order) is fine."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Prerequisites", 20, level=0),
            _make_block("paragraph", "Need X.", 40),
            _make_block("heading", "Procedure", 60, level=0),
            _make_block("paragraph", "Step 1.", 80),
        ]

        issues = _check_prerequisites_position(blocks, "", "procedure")
        assert len(issues) == 0

    def test_non_procedure_content_type_skipped(self) -> None:
        """Check does not fire for concept modules."""
        blocks = [
            _make_block("heading", "Procedure", 0, level=0),
            _make_block("heading", "Prerequisites", 20, level=0),
        ]

        issues = _check_prerequisites_position(blocks, "", "concept")
        assert len(issues) == 0


class TestEmptySection:
    """Verify empty section check."""

    def test_heading_with_no_content_flagged(self) -> None:
        """Heading immediately followed by another heading is flagged."""
        blocks = [
            _make_block("heading", "Section A", 0, level=2),
            _make_block("heading", "Section B", 20, level=2),
        ]

        issues = _check_empty_section(blocks, "")
        assert len(issues) == 1
        assert "empty" in issues[0].message.lower()
        assert issues[0].rule_name == "empty_section"

    def test_heading_with_content_ok(self) -> None:
        """Heading followed by paragraph then next heading is fine."""
        blocks = [
            _make_block("heading", "Section A", 0, level=2),
            _make_block("paragraph", "Content here.", 20),
            _make_block("heading", "Section B", 40, level=2),
        ]

        issues = _check_empty_section(blocks, "")
        assert len(issues) == 0

    def test_block_title_not_counted_as_content(self) -> None:
        """Block titles between headings don't count as content."""
        blocks = [
            _make_block("heading", "Section A", 0, level=2),
            _make_block("attribute_entry", ":context: val", 20),
            _make_block("heading", "Section B", 40, level=2),
        ]

        issues = _check_empty_section(blocks, "")
        assert len(issues) == 1

    def test_level_0_headings_ignored(self) -> None:
        """Block titles (level 0) do not trigger empty section check."""
        blocks = [
            _make_block("heading", "Prerequisites", 0, level=0),
            _make_block("heading", "Procedure", 20, level=0),
        ]

        issues = _check_empty_section(blocks, "")
        assert len(issues) == 0


class TestAdmonitionStacking:
    """Verify consecutive admonition detection."""

    def test_two_consecutive_admonitions_flagged(self) -> None:
        """Two admonitions back-to-back are flagged."""
        blocks = [
            _make_block("admonition", "Note one.", 0),
            _make_block("admonition", "Note two.", 20),
            _make_block("paragraph", "Some text.", 40),
        ]

        issues = _check_admonition_stacking(blocks, "")
        assert len(issues) == 1
        assert issues[0].rule_name == "admonition_stacking"
        assert "2" in issues[0].message

    def test_three_consecutive_admonitions_flagged(self) -> None:
        """Three admonitions report the correct count."""
        blocks = [
            _make_block("admonition", "Note one.", 0),
            _make_block("admonition", "Note two.", 20),
            _make_block("admonition", "Note three.", 40),
            _make_block("paragraph", "Text.", 60),
        ]

        issues = _check_admonition_stacking(blocks, "")
        assert len(issues) == 1
        assert "3" in issues[0].message

    def test_admonitions_with_prose_between_ok(self) -> None:
        """Admonitions separated by prose are fine."""
        blocks = [
            _make_block("admonition", "Note one.", 0),
            _make_block("paragraph", "Explanation.", 20),
            _make_block("admonition", "Note two.", 40),
        ]

        issues = _check_admonition_stacking(blocks, "")
        assert len(issues) == 0

    def test_trailing_stacked_admonitions(self) -> None:
        """Stacked admonitions at end of document are still flagged."""
        blocks = [
            _make_block("paragraph", "Text.", 0),
            _make_block("admonition", "Note one.", 20),
            _make_block("admonition", "Note two.", 40),
        ]

        issues = _check_admonition_stacking(blocks, "")
        assert len(issues) == 1


class TestProcedureStepCount:
    """Verify long procedure detection."""

    def test_eleven_steps_flagged(self) -> None:
        """More than 10 consecutive ordered list items triggers advisory."""
        blocks = [
            _make_block("list_item_ordered", f"Step {i}.", i * 10)
            for i in range(11)
        ]
        # End with non-list block to close the sequence
        blocks.append(_make_block("paragraph", "Done.", 110))

        issues = _check_procedure_step_count(blocks, "", "procedure")
        assert len(issues) == 1
        assert issues[0].rule_name == "procedure_step_count"
        assert issues[0].severity.value == "low"

    def test_ten_steps_ok(self) -> None:
        """Exactly 10 steps do not trigger the advisory."""
        blocks = [
            _make_block("list_item_ordered", f"Step {i}.", i * 10)
            for i in range(10)
        ]

        issues = _check_procedure_step_count(blocks, "", "procedure")
        assert len(issues) == 0

    def test_non_procedure_skipped(self) -> None:
        """Step count check does not fire for concept modules."""
        blocks = [
            _make_block("list_item_ordered", f"Step {i}.", i * 10)
            for i in range(15)
        ]

        issues = _check_procedure_step_count(blocks, "", "concept")
        assert len(issues) == 0


class TestVerificationSection:
    """Verify missing .Verification detection."""

    def test_procedure_without_verification_flagged(self) -> None:
        """Procedure module missing .Verification is flagged."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Prerequisites", 20, level=0),
            _make_block("paragraph", "Need X.", 40),
            _make_block("heading", "Procedure", 60, level=0),
            _make_block("paragraph", "Step 1.", 80),
        ]

        issues = _check_verification_section(blocks, "", "procedure")
        assert len(issues) == 1
        assert issues[0].rule_name == "verification_section"

    def test_procedure_with_verification_ok(self) -> None:
        """Procedure module with .Verification is fine."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("heading", "Procedure", 20, level=0),
            _make_block("paragraph", "Step 1.", 40),
            _make_block("heading", "Verification", 60, level=0),
            _make_block("paragraph", "Check output.", 80),
        ]

        issues = _check_verification_section(blocks, "", "procedure")
        assert len(issues) == 0

    def test_non_procedure_skipped(self) -> None:
        """Verification check does not fire for concept modules."""
        blocks = [
            _make_block("heading", "Procedure", 0, level=0),
        ]

        issues = _check_verification_section(blocks, "", "concept")
        assert len(issues) == 0

    def test_no_procedure_section_no_issue(self) -> None:
        """If no .Procedure block title exists, no issue is raised."""
        blocks = [
            _make_block("heading", "Title", 0, level=1),
            _make_block("paragraph", "Some text.", 20),
        ]

        issues = _check_verification_section(blocks, "", "procedure")
        assert len(issues) == 0


class TestRunStructuralRules:
    """Verify the top-level runner function."""

    def test_empty_blocks_returns_empty(self) -> None:
        """No blocks produces no issues."""
        issues = run_structural_rules([], "procedure", "")
        assert issues == []

    def test_runner_filters_skipped_blocks(self) -> None:
        """Blocks with should_skip_analysis=True are filtered."""
        blocks = [
            _make_block("heading", "Title", 0, level=1, skip=True),
            _make_block("admonition", "Note.", 20, skip=True),
        ]

        # Both blocks are skipped, so content_blocks is empty
        issues = run_structural_rules(blocks, "procedure", "")
        assert len(issues) == 0
