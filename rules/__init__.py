"""
Rules Registry -- Discovers, loads, and orchestrates all writing rules.

The ``RulesRegistry`` class is the single entry point for running deterministic
style checks.  It auto-discovers concrete rule classes at construction time
using ``rules.loader.discover_rules`` and maps them to applicable block types
via ``rule_mappings.yaml``.

Usage::

    from rules import RulesRegistry

    registry = RulesRegistry()
    errors = registry.analyze(text, sentences)
"""

import logging
import os
from typing import Any, Dict, List, Optional

import yaml

from rules.base_rule import BaseRule
from rules.loader import discover_rules

logger = logging.getLogger(__name__)

# Block types that should never be analyzed
_SKIP_BLOCK_TYPES = frozenset([
    "listing",
    "literal",
    "code_block",
    "inline_code",
    "pass",
    "attribute_entry",
    "html_block",
    "html_inline",
    "horizontal_rule",
    "softbreak",
    "hardbreak",
])


class RulesRegistry:
    """Registry that discovers and manages all writing rules.

    Attributes:
        rules: Mapping of rule_type to rule instance.
        rule_locations: Mapping of rule_type to human-readable location.
        block_type_rules: Block type to applicable rule types (from YAML).
        rule_exclusions: Block type to excluded rule types (from YAML).
    """

    def __init__(
        self,
        confidence_threshold: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the registry with auto-discovery.

        Args:
            confidence_threshold: If set, errors whose ``confidence_score``
                falls below this value are filtered out.
            **kwargs: Reserved for future use.
        """
        self.rules: Dict[str, BaseRule] = {}
        self.rule_locations: Dict[str, str] = {}
        self.block_type_rules: Dict[str, List[str]] = {}
        self.rule_exclusions: Dict[str, List[str]] = {}
        self.confidence_threshold = confidence_threshold

        self._load_rule_mappings()
        self._discover_all_rules()

    # ------------------------------------------------------------------
    # Rule discovery
    # ------------------------------------------------------------------

    def _discover_all_rules(self) -> None:
        """Discover and register all concrete rules via the loader."""
        rules_dir = os.path.dirname(os.path.abspath(__file__))
        self.rules, self.rule_locations = discover_rules(rules_dir)

    # ------------------------------------------------------------------
    # Rule mappings
    # ------------------------------------------------------------------

    def _load_rule_mappings(self) -> None:
        """Load block-type-to-rule mappings from ``rule_mappings.yaml``."""
        rules_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(rules_dir, "rule_mappings.yaml")

        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Rule mappings not found: {config_path}"
            )

        with open(config_path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        if not isinstance(config, dict):
            raise ValueError("rule_mappings.yaml must contain a dictionary")
        for key in ("block_type_rules", "rule_exclusions"):
            if key not in config or not isinstance(config[key], dict):
                raise ValueError(f"Missing or invalid key in rule_mappings.yaml: {key}")

        self.block_type_rules = config["block_type_rules"]
        self.rule_exclusions = config["rule_exclusions"]

    # ------------------------------------------------------------------
    # Public analysis API
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        sentences: List[str],
        spacy_doc: Any = None,
        block_type: str = "paragraph",
        skip_rules: Optional[List[str]] = None,
        content_type: Optional[str] = None,
        inline_code_ranges: Optional[List[tuple]] = None,
        bold_code_ranges: Optional[List[tuple]] = None,
        acronym_context: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Run analysis using block-type-aware rule selection.

        Args:
            text: Full text to analyze.
            sentences: Pre-split list of sentences.
            spacy_doc: Pre-created SpaCy Doc object (optional).
            block_type: Content block type for rule selection.
            skip_rules: Rule types to exclude from this run.
            content_type: Modular documentation type (concept, procedure, etc.).
            inline_code_ranges: List of (start, end) tuples marking inline
                code positions in content coordinates.
            bold_code_ranges: List of (start, end, fmt, code_text) tuples
                marking bold/italic-wrapped code in content coordinates.
            acronym_context: Document-wide acronym definitions for the
                definitions rule.

        Returns:
            List of error dictionaries.
        """
        block_type = block_type.lower()
        if block_type in _SKIP_BLOCK_TYPES:
            return []

        applicable = self._get_applicable_rules(block_type)
        if skip_rules:
            applicable = [r for r in applicable if r not in skip_rules]

        context: Dict[str, Any] = {"block_type": block_type}
        if content_type:
            context["content_type"] = content_type
        if inline_code_ranges is not None:
            context["inline_code_ranges"] = inline_code_ranges
        if bold_code_ranges is not None:
            context["bold_code_ranges"] = bold_code_ranges
        if acronym_context is not None:
            context["acronym_context"] = acronym_context

        return self._run_rules(
            applicable, text, sentences, nlp=None,
            context=context, spacy_doc=spacy_doc,
        )

    def analyze_with_context_aware_rules(
        self,
        text: str,
        sentences: List[str],
        nlp: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run analysis with context-aware rule selection based on block type.

        This is the backward-compatible entry point used by the service layer.

        Args:
            text: Full text to analyze.
            sentences: Pre-split list of sentences.
            nlp: SpaCy language model (optional).
            context: Block-level context dict (optional).

        Returns:
            List of error dictionaries.
        """
        block_type = self._get_block_type(context)
        if block_type in _SKIP_BLOCK_TYPES:
            return []

        applicable = self._get_applicable_rules(block_type)
        skip_rules = context.get("skip_rules", []) if context else []
        if skip_rules:
            applicable = [r for r in applicable if r not in skip_rules]

        return self._run_rules(applicable, text, sentences, nlp, context)

    def analyze_with_all_rules(
        self,
        text: str,
        sentences: List[str],
        nlp: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Run analysis with every discovered rule (ignoring block type mapping).

        Args:
            text: Full text to analyze.
            sentences: Pre-split list of sentences.
            nlp: SpaCy language model (optional).
            context: Block-level context dict (optional).

        Returns:
            List of error dictionaries.
        """
        skip_rules = context.get("skip_rules", []) if context else []
        applicable = [rt for rt in self.rules if rt not in skip_rules]
        return self._run_rules(applicable, text, sentences, nlp, context)

    # ------------------------------------------------------------------
    # Rule execution
    # ------------------------------------------------------------------

    def _run_rules(
        self,
        rule_types: List[str],
        text: str,
        sentences: List[str],
        nlp: Any,
        context: Optional[Dict[str, Any]],
        spacy_doc: Any = None,
    ) -> List[Dict[str, Any]]:
        """Execute the given rules and return collected errors."""
        if spacy_doc is None and nlp and text and text.strip():
            spacy_doc = nlp(text)

        all_errors: List[Dict[str, Any]] = []

        for rule_type in rule_types:
            rule = self.rules.get(rule_type)
            if rule is not None:
                self._execute_rule(
                    rule, text, sentences, nlp, context, spacy_doc, all_errors
                )

        if self.confidence_threshold is not None:
            all_errors = self._apply_confidence_filter(all_errors)

        return all_errors

    def _execute_rule(
        self,
        rule: BaseRule,
        text: str,
        sentences: List[str],
        nlp: Any,
        context: Optional[Dict[str, Any]],
        spacy_doc: Any,
        all_errors: List[Dict[str, Any]],
    ) -> None:
        """Run a single rule and append results to *all_errors*."""
        try:
            results = rule.analyze(
                text, sentences, nlp, context, spacy_doc=spacy_doc
            )
            for error in results:
                if error is not None:
                    all_errors.append(rule._make_serializable(error))
        except (TypeError, ValueError, AttributeError, KeyError,
                IndexError) as exc:
            logger.warning(
                "Rule %s raised %s: %s",
                rule.__class__.__name__,
                type(exc).__name__,
                exc,
            )
            all_errors.append({
                "type": "system_error",
                "message": (
                    f"Rule {rule.__class__.__name__} failed: {exc}"
                ),
                "suggestions": ["Check rule implementation"],
                "sentence": "",
                "sentence_index": -1,
                "severity": "low",
            })

    def _apply_confidence_filter(
        self, errors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Remove errors whose confidence score falls below the threshold."""
        return [
            e for e in errors
            if e.get("confidence_score") is None
            or e["confidence_score"] >= self.confidence_threshold
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_block_type(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract and normalize the block type from a context dict."""
        if not context:
            return "paragraph"
        raw = (
            context.get("block_type")
            or context.get("type")
            or context.get("blockType")
            or "paragraph"
        )
        return str(raw).lower()

    def _get_applicable_rules(self, block_type: str) -> List[str]:
        """Return the list of rule types applicable to *block_type*."""
        applicable = self.block_type_rules.get(block_type, [])
        if not applicable and block_type not in self.block_type_rules:
            applicable = self.block_type_rules.get("paragraph", [])

        exclusions = self.rule_exclusions.get(block_type, [])
        return [
            r for r in applicable
            if r not in exclusions and r in self.rules
        ]

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_rule(self, rule_type: str) -> Optional[BaseRule]:
        """Return the rule instance for *rule_type*, or ``None``."""
        return self.rules.get(rule_type)

    def get_all_rules(self) -> Dict[str, BaseRule]:
        """Return the full ``{ rule_type: instance }`` mapping."""
        return self.rules

    def list_discovered_rules(self) -> Dict[str, Any]:
        """Return a summary of all discovered rules grouped by location."""
        rules_by_location: Dict[str, list] = {}
        for rule_type, location in self.rule_locations.items():
            rules_by_location.setdefault(location, []).append(rule_type)
        return {
            "total_rules": len(self.rules),
            "rules_by_location": rules_by_location,
            "all_rule_types": list(self.rules.keys()),
        }


# ---------------------------------------------------------------------------
# Backward-compatible singleton accessor
# ---------------------------------------------------------------------------

_registry: Optional[RulesRegistry] = None


def get_registry(
    confidence_threshold: Optional[float] = None, **kwargs: Any
) -> RulesRegistry:
    """Return the global registry singleton, creating it on first call.

    Args:
        confidence_threshold: Passed to ``RulesRegistry`` on first creation.
        **kwargs: Reserved for future use.

    Returns:
        The shared ``RulesRegistry`` instance.
    """
    global _registry
    if _registry is None:
        _registry = RulesRegistry(
            confidence_threshold=confidence_threshold, **kwargs
        )
    return _registry
