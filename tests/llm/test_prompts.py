"""Tests for LLM prompt builders and helpers.

Validates content-type guidance, acronym section formatting,
multi-shot example selection, and prompt construction.
"""

import logging
from unittest.mock import patch

import pytest

from app.llm.prompts import (
    _content_type_guidance,
    _format_acronym_section,
    _format_examples_section,
    _select_examples,
    build_global_prompt,
    build_granular_prompt,
    build_suggestion_prompt,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# _content_type_guidance
# ---------------------------------------------------------------------------


class TestContentTypeGuidance:
    """Tests for _content_type_guidance()."""

    def test_procedure_guidance(self) -> None:
        """Procedure guidance mentions imperative voice and steps."""
        result = _content_type_guidance("procedure")
        assert "procedure" in result.lower()
        assert "imperative" in result.lower()
        assert "DO NOT flag" in result

    def test_concept_guidance(self) -> None:
        """Concept guidance mentions passive voice and state-of-being."""
        result = _content_type_guidance("concept")
        assert "concept" in result.lower()
        assert "state-of-being" in result.lower() or "State-of-being" in result

    def test_reference_guidance(self) -> None:
        """Reference guidance mentions formal language."""
        result = _content_type_guidance("reference")
        assert "reference" in result.lower()
        assert "formal" in result.lower()

    def test_release_notes_guidance(self) -> None:
        """Release notes guidance allows past tense passive."""
        result = _content_type_guidance("release_notes")
        assert "release notes" in result.lower()
        assert "was fixed" in result

    def test_assembly_guidance(self) -> None:
        """Assembly guidance mentions coherence and transitions."""
        result = _content_type_guidance("assembly")
        assert "assembly" in result.lower()
        assert "coherence" in result.lower()

    def test_unknown_type_falls_back_to_concept(self) -> None:
        """Unknown content types fall back to concept guidance."""
        result = _content_type_guidance("unknown_type")
        concept = _content_type_guidance("concept")
        assert result == concept

    def test_all_types_return_non_empty(self) -> None:
        """All known content types return non-empty guidance strings."""
        for ctype in ("procedure", "concept", "reference", "release_notes", "assembly"):
            result = _content_type_guidance(ctype)
            assert len(result) > 20, f"Guidance for {ctype} is too short"


# ---------------------------------------------------------------------------
# _format_acronym_section
# ---------------------------------------------------------------------------


class TestFormatAcronymSection:
    """Tests for _format_acronym_section()."""

    def test_none_context_returns_empty(self) -> None:
        """None acronym context returns empty string."""
        result = _format_acronym_section(None, "some text")
        assert result == ""

    def test_empty_context_returns_empty(self) -> None:
        """Empty acronym dict returns empty string."""
        result = _format_acronym_section({}, "some text")
        assert result == ""

    def test_relevant_acronyms_included(self) -> None:
        """Only acronyms present in the block text are included."""
        context = {
            "CSI": "Container Storage Interface",
            "OCP": "OpenShift Container Platform",
            "API": "Application Programming Interface",
        }
        block_text = "The CSI driver provides storage. The API is documented."
        result = _format_acronym_section(context, block_text)

        assert "CSI" in result
        assert "Container Storage Interface" in result
        assert "API" in result
        assert "Application Programming Interface" in result
        assert "OCP" not in result

    def test_no_matching_acronyms_returns_empty(self) -> None:
        """When no acronyms match the block, return empty string."""
        context = {"OCP": "OpenShift Container Platform"}
        result = _format_acronym_section(context, "No acronyms here.")
        assert result == ""

    def test_includes_do_not_flag_instruction(self) -> None:
        """Output includes instruction not to flag defined acronyms."""
        context = {"CSI": "Container Storage Interface"}
        result = _format_acronym_section(context, "The CSI driver")
        assert "Do NOT flag" in result

    def test_case_insensitive_matching(self) -> None:
        """Acronym matching works for text containing the acronym."""
        context = {"API": "Application Programming Interface"}
        result = _format_acronym_section(context, "The API endpoint")
        assert "API" in result


# ---------------------------------------------------------------------------
# _select_examples (with mocked _EXAMPLES_DB)
# ---------------------------------------------------------------------------


_MOCK_EXAMPLES_DB = {
    "passive_voice": [
        {
            "before": "The file was deleted.",
            "after": "Delete the file.",
            "difficulty": "simple",
            "success_rate": 0.95,
            "reasoning": "Convert passive to active.",
        },
        {
            "before": "The configuration was updated by the admin.",
            "after": "The admin updated the configuration.",
            "difficulty": "medium",
            "success_rate": 0.88,
            "reasoning": "Move actor to subject position.",
        },
        {
            "before": "It was determined that the server had been compromised.",
            "after": "Investigation revealed that the server was compromised.",
            "difficulty": "complex",
            "success_rate": 0.75,
            "reasoning": "Restructure to identify actor.",
        },
    ],
    "contractions": [
        {
            "before": "Don't use contractions.",
            "after": "Do not use contractions.",
            "difficulty": "simple",
            "success_rate": 0.99,
            "reasoning": "Expand contraction.",
        },
    ],
}


class TestSelectExamples:
    """Tests for _select_examples()."""

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_selects_by_difficulty(self, mock_load: object) -> None:
        """Selects one example per difficulty level."""
        result = _select_examples("verbs", max_count=3)
        difficulties = [ex["difficulty"] for ex in result]
        assert "simple" in difficulties
        assert "medium" in difficulties
        assert "complex" in difficulties

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_respects_max_count(self, mock_load: object) -> None:
        """Does not return more than max_count examples."""
        result = _select_examples("verbs", max_count=2)
        assert len(result) <= 2

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_rule_name_mapping(self, mock_load: object) -> None:
        """Maps rule names to example keys via _RULE_TO_EXAMPLE_KEY."""
        result = _select_examples("passive_voice")
        assert len(result) > 0

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_unknown_rule_returns_empty(self, mock_load: object) -> None:
        """Unknown rule names return an empty list."""
        result = _select_examples("nonexistent_rule")
        assert result == []

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_single_difficulty_category(self, mock_load: object) -> None:
        """Categories with only one difficulty level still return results."""
        result = _select_examples("contractions")
        assert len(result) == 1
        assert result[0]["difficulty"] == "simple"


# ---------------------------------------------------------------------------
# _format_examples_section
# ---------------------------------------------------------------------------


class TestFormatExamplesSection:
    """Tests for _format_examples_section()."""

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_formats_examples(self, mock_load: object) -> None:
        """Produces a formatted section with Before/After pairs."""
        result = _format_examples_section("verbs")
        assert "## Examples" in result
        assert "Before:" in result
        assert "After:" in result
        assert "Reasoning:" in result

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_empty_for_unknown_rule(self, mock_load: object) -> None:
        """Unknown rules produce an empty section."""
        result = _format_examples_section("nonexistent_rule")
        assert result == ""

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_includes_difficulty_label(self, mock_load: object) -> None:
        """Each example includes its difficulty label."""
        result = _format_examples_section("verbs")
        assert "(simple)" in result or "(medium)" in result or "(complex)" in result


# ---------------------------------------------------------------------------
# build_granular_prompt with acronym_context
# ---------------------------------------------------------------------------


class TestBuildGranularPrompt:
    """Tests for build_granular_prompt() with new parameters."""

    def test_includes_skip_and_flag_guidance(self) -> None:
        """Prompt includes narrowed SKIP list and objective flagging guidance."""
        system_prompt, user_prompt = build_granular_prompt(
            "Test text.", ["Test text."], [],
        )
        combined = system_prompt + user_prompt
        assert "SKIP" in combined
        assert "spelling" in combined.lower()
        assert "flag all clear violations" in combined.lower()

    def test_includes_content_type_guidance(self) -> None:
        """Prompt includes content-type-specific guidance."""
        system_prompt, user_prompt = build_granular_prompt(
            "Test text.", ["Test text."], [],
            content_type="procedure",
        )
        combined = (system_prompt + user_prompt).lower()
        assert "procedure" in combined
        assert "imperative" in combined

    def test_acronym_context_injected(self) -> None:
        """Acronym context appears in the prompt when relevant."""
        acronyms = {"CSI": "Container Storage Interface"}
        _, user_prompt = build_granular_prompt(
            "The CSI driver provides storage.",
            ["The CSI driver provides storage."],
            [],
            acronym_context=acronyms,
        )
        assert "CSI" in user_prompt
        assert "Container Storage Interface" in user_prompt
        assert "Do NOT flag" in user_prompt

    def test_acronym_context_none_no_section(self) -> None:
        """No acronym section when acronym_context is None."""
        _, user_prompt = build_granular_prompt(
            "Simple text.", ["Simple text."], [],
            acronym_context=None,
        )
        assert "Known Acronym Definitions" not in user_prompt

    def test_release_notes_content_type(self) -> None:
        """Release notes content type includes appropriate guidance."""
        system_prompt, user_prompt = build_granular_prompt(
            "Bug was fixed.", ["Bug was fixed."], [],
            content_type="release_notes",
        )
        combined = (system_prompt + user_prompt).lower()
        assert "release notes" in combined
        assert "was fixed" in combined


# ---------------------------------------------------------------------------
# build_suggestion_prompt with examples
# ---------------------------------------------------------------------------


class TestBuildSuggestionPrompt:
    """Tests for build_suggestion_prompt() with multi-shot examples."""

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_includes_examples_for_known_rule(self, mock_load: object) -> None:
        """Suggestion prompt includes examples for a known rule."""
        rule_info = {
            "rule_name": "verbs",
            "category": "grammar",
            "message": "Consider active voice.",
            "severity": "medium",
        }
        _, user_prompt = build_suggestion_prompt(
            "was deleted",
            ["The file was deleted by the admin."],
            rule_info,
            {},
        )
        assert "## Examples" in user_prompt
        assert "Before:" in user_prompt

    @patch("app.llm.prompts._load_examples", return_value=_MOCK_EXAMPLES_DB)
    def test_no_examples_for_unknown_rule(self, mock_load: object) -> None:
        """Suggestion prompt omits examples section for unknown rules."""
        rule_info = {
            "rule_name": "unknown_rule_xyz",
            "category": "style",
            "message": "Some issue.",
            "severity": "low",
        }
        _, user_prompt = build_suggestion_prompt(
            "some text",
            ["Some context sentence."],
            rule_info,
            {},
        )
        assert "## Examples" not in user_prompt


# ---------------------------------------------------------------------------
# Suggestion mandate in prompts (Fix 2)
# ---------------------------------------------------------------------------


class TestSuggestionMandate:
    """Verify granular and global prompts mandate non-empty suggestions."""

    def test_granular_prompt_mandates_suggestions(self) -> None:
        """Granular prompt system message requires non-empty suggestions."""
        system_prompt, _ = build_granular_prompt(
            "Test text.", ["Test text."], [],
        )
        assert "suggestions must contain" in system_prompt, (
            "Granular prompt should mandate non-empty suggestions"
        )
        assert "Do not leave" in system_prompt
        assert "suggestions empty" in system_prompt

    def test_granular_prompt_scope_constraint(self) -> None:
        """Granular prompt includes scope constraint for suggestions."""
        system_prompt, _ = build_granular_prompt(
            "Test text.", ["Test text."], [],
        )
        assert "scoped to the flagged_text" in system_prompt, (
            "Granular prompt should scope suggestions to flagged_text span"
        )

    def test_global_prompt_mandates_suggestions(self) -> None:
        """Global prompt system message requires non-empty suggestions."""
        system_prompt, _ = build_global_prompt(
            "Test document text.", "concept", [],
        )
        assert "suggestions must contain" in system_prompt, (
            "Global prompt should mandate non-empty suggestions"
        )
        assert "Do not leave" in system_prompt

    def test_global_prompt_scope_constraint(self) -> None:
        """Global prompt includes scope constraint for suggestions."""
        system_prompt, _ = build_global_prompt(
            "Test document text.", "concept", [],
        )
        assert "scoped to the flagged_text" in system_prompt, (
            "Global prompt should scope suggestions to flagged_text span"
        )

    def test_granular_prompt_uses_corrected_text_format(self) -> None:
        """Granular prompt uses 'corrected text' not 'fix' in format example."""
        system_prompt, _ = build_granular_prompt(
            "Test text.", ["Test text."], [],
        )
        assert '"corrected text"' in system_prompt, (
            "Granular prompt should use 'corrected text' in format example"
        )

    def test_global_prompt_uses_corrected_text_format(self) -> None:
        """Global prompt uses 'corrected text' not 'fix' in format example."""
        system_prompt, _ = build_global_prompt(
            "Test document text.", "concept", [],
        )
        assert '"corrected text"' in system_prompt, (
            "Global prompt should use 'corrected text' in format example"
        )
