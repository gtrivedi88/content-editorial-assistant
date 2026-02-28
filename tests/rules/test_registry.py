"""Tests for the rules registry and rule discovery system.

Validates that the RulesRegistry correctly discovers rule modules,
that every discovered rule has a rule_type, that analyze() returns
a list, and that individual rule failures are isolated.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class TestRulesRegistry:
    """Tests for the RulesRegistry class."""

    def test_registry_discovers_rules(self) -> None:
        """RulesRegistry.discover() finds rules with count greater than zero.

        The auto-discovery mechanism should locate at least one concrete
        rule class under the rules/ directory tree.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()
        all_rules: Dict[str, BaseRule] = registry.get_all_rules()

        assert len(all_rules) > 0, (
            "Registry should discover at least one rule"
        )

    def test_each_rule_has_rule_type(self) -> None:
        """Every discovered rule has a non-empty rule_type attribute.

        The rule_type is used throughout the pipeline for category
        mapping, citation lookup, and issue identification.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()
        all_rules: Dict[str, BaseRule] = registry.get_all_rules()

        for rule_type, rule_instance in all_rules.items():
            assert hasattr(rule_instance, "rule_type"), (
                f"Rule {rule_instance.__class__.__name__} missing rule_type attribute"
            )
            assert rule_instance.rule_type, (
                f"Rule {rule_instance.__class__.__name__} has empty rule_type"
            )
            assert rule_instance.rule_type == rule_type, (
                f"Rule type mismatch: registered as '{rule_type}' "
                f"but instance reports '{rule_instance.rule_type}'"
            )

    def test_analyze_returns_list(self) -> None:
        """Registry analyze() returns a list of error dicts.

        Calling analyze() with valid text should return a list (possibly
        empty) of dictionaries representing detected issues.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()

        text: str = "This is a simple test sentence."
        sentences: List[str] = [text]

        result: List[Dict[str, Any]] = registry.analyze(
            text, sentences, spacy_doc=None, block_type="paragraph"
        )

        assert isinstance(result, list), (
            f"analyze() should return a list, got {type(result)}"
        )

    def test_exception_isolation(self) -> None:
        """One rule failing does not crash the entire analysis.

        When a single rule raises an exception during analyze(), the
        registry should catch it and continue running remaining rules.
        The failing rule's error should appear as a system_error entry.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()

        # Inject a deliberately broken rule
        broken_rule: MagicMock = MagicMock(spec=BaseRule)
        broken_rule.rule_type = "broken_test_rule"
        broken_rule.analyze.side_effect = ValueError("Intentional test failure")
        broken_rule._make_serializable = MagicMock(side_effect=lambda x: x)

        original_rules = dict(registry.rules)
        registry.rules["broken_test_rule"] = broken_rule

        # Ensure the broken rule is in the applicable list
        original_bt_rules = dict(registry.block_type_rules)
        if "paragraph" in registry.block_type_rules:
            registry.block_type_rules["paragraph"] = (
                list(registry.block_type_rules["paragraph"]) + ["broken_test_rule"]
            )

        try:
            text: str = "This is a test sentence for error isolation."
            sentences: List[str] = [text]

            result: List[Dict[str, Any]] = registry.analyze(
                text, sentences, spacy_doc=None, block_type="paragraph"
            )

            # Should not raise; returns a list
            assert isinstance(result, list)

            # Should contain a system_error for the broken rule
            system_errors = [
                e for e in result if e.get("type") == "system_error"
            ]
            assert len(system_errors) >= 1, (
                "Expected at least one system_error for the broken rule"
            )
        finally:
            # Restore original state
            registry.rules = original_rules
            registry.block_type_rules = original_bt_rules

    def test_skip_block_types_produce_no_results(self) -> None:
        """Block types in _SKIP_BLOCK_TYPES return empty results.

        Code blocks, inline code, and similar block types should
        produce zero issues when analyzed.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()

        text: str = "print('hello world')"
        sentences: List[str] = [text]

        result: List[Dict[str, Any]] = registry.analyze(
            text, sentences, spacy_doc=None, block_type="code_block"
        )

        assert result == [], (
            "code_block should be skipped and produce empty results"
        )

    def test_list_discovered_rules_structure(self) -> None:
        """list_discovered_rules() returns expected summary structure.

        The summary should contain total_rules count, rules grouped
        by location, and a flat list of all rule type identifiers.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()
        summary: Dict[str, Any] = registry.list_discovered_rules()

        assert "total_rules" in summary
        assert "rules_by_location" in summary
        assert "all_rule_types" in summary
        assert isinstance(summary["total_rules"], int)
        assert summary["total_rules"] > 0
        assert isinstance(summary["all_rule_types"], list)
        assert len(summary["all_rule_types"]) == summary["total_rules"]

    def test_get_rule_returns_instance_or_none(self) -> None:
        """get_rule() returns a rule instance for known types and None for unknown.

        The method should not raise exceptions for unknown rule types.
        """
        from rules import RulesRegistry

        registry: RulesRegistry = RulesRegistry()

        all_rules = registry.get_all_rules()
        if all_rules:
            first_type = next(iter(all_rules))
            rule = registry.get_rule(first_type)
            assert rule is not None
            assert isinstance(rule, BaseRule)

        unknown = registry.get_rule("nonexistent_rule_type_xyz")
        assert unknown is None
