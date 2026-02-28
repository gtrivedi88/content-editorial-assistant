"""
Rules Registry — Automatically discovers and loads all writing rules.
Supports automatic discovery of rules in subdirectories up to 4 levels deep.
"""

import importlib
import importlib.util
import logging
import os
import yaml
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import base rule
try:
    from .base_rule import BaseRule
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from base_rule import BaseRule

# Base class names to skip during rule discovery
_BASE_CLASS_NAMES = frozenset([
    'BaseRule', 'BaseLanguageRule', 'BasePunctuationRule',
    'BaseStructureRule', 'BaseTechnicalRule', 'BaseWordUsageRule',
    'BaseAudienceRule', 'BaseNumbersRule', 'BaseReferencesRule',
    'BaseLegalRule',
])


class RulesRegistry:
    """Registry that discovers and manages all writing rules."""

    def __init__(self, confidence_threshold: float = None, **kwargs):
        self.rules: Dict[str, BaseRule] = {}
        self.rule_locations: Dict[str, str] = {}
        self.block_type_rules: Dict[str, List[str]] = {}
        self.rule_exclusions: Dict[str, List[str]] = {}

        self.confidence_threshold = confidence_threshold

        # Auto-discover and load all rules + mappings
        self._load_rule_mappings()
        self._load_all_rules()

    # ── Rule Discovery ────────────────────────────────────────────────

    def _load_all_rules(self):
        """Discover and load all rule modules from subdirectories (up to 4 levels)."""
        rules_dir = os.path.dirname(os.path.abspath(__file__))

        for root, _dirs, files in os.walk(rules_dir):
            if '__pycache__' in root:
                continue
            rel_path = os.path.relpath(root, rules_dir)
            depth = 0 if rel_path == '.' else len(rel_path.split(os.sep))
            if depth > 4:
                continue
            self._scan_directory(root, rel_path, files)

        print(f"Rules discovery complete. Loaded {len(self.rules)} rules.")

    def _scan_directory(self, root, rel_path, files):
        """Scan a single directory for rule files."""
        for filename in files:
            if not filename.endswith('_rule.py') or filename.startswith('base_'):
                continue
            if rel_path == '.':
                import_path = filename[:-3]
                location = "main"
            else:
                import_path = f"{rel_path.replace(os.sep, '.')}.{filename[:-3]}"
                location = rel_path.replace(os.sep, ' > ')
            self._try_load_rule(import_path, root, filename, location)

    def _try_load_rule(self, import_path, file_dir, filename, location):
        """Attempt to load a single rule module."""
        try:
            module = self._import_module(import_path, file_dir, filename)
            if not module:
                return
            instance = self._find_rule_class(module)
            if instance and instance.rule_type not in self.rules:
                self.rules[instance.rule_type] = instance
                self.rule_locations[instance.rule_type] = location
        except Exception as e:
            print(f"Error loading rule {import_path}: {e}")

    def _import_module(self, import_path, file_dir, filename):
        """Import a rule module."""
        # Absolute import
        try:
            return importlib.import_module(f"rules.{import_path}")
        except ImportError:
            pass
        # Relative import
        try:
            if '.' in import_path:
                return importlib.import_module(f".{import_path}", package="rules")
        except ImportError:
            pass
        # Direct file fallback
        try:
            file_path = os.path.join(file_dir, filename)
            spec = importlib.util.spec_from_file_location(
                f"rule_module_{import_path.replace('.', '_')}", file_path,
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception:
            pass
        return None

    def _find_rule_class(self, module):
        """Find and instantiate the concrete rule class in a module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if self._is_concrete_rule(attr, module):
                instance = self._try_instantiate(attr)
                if instance:
                    return instance
        return None

    @staticmethod
    def _is_concrete_rule(attr, module) -> bool:
        if not isinstance(attr, type) or attr.__name__ in _BASE_CLASS_NAMES:
            return False
        if not attr.__name__.endswith('Rule') or attr.__module__ != module.__name__:
            return False
        if not all(hasattr(attr, m) for m in ('analyze', '_get_rule_type')):
            return False
        return not (hasattr(attr, '__abstractmethods__') and attr.__abstractmethods__)

    @staticmethod
    def _try_instantiate(cls):
        try:
            instance = cls()
            if instance.rule_type and instance.rule_type != 'base':
                return instance
        except Exception:
            pass
        return None

    # ── Rule Mappings ─────────────────────────────────────────────────

    def _load_rule_mappings(self):
        """Load rule-to-block type mappings from YAML configuration."""
        rules_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(rules_dir, 'rule_mappings.yaml')

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Rule mappings not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")
        for key in ('block_type_rules', 'rule_exclusions'):
            if key not in config or not isinstance(config[key], dict):
                raise ValueError(f"Missing or invalid key: {key}")

        self.block_type_rules = config['block_type_rules']
        self.rule_exclusions = config['rule_exclusions']

    # ── Analysis ──────────────────────────────────────────────────────

    def analyze_with_context_aware_rules(self, text: str, sentences: List[str],
                                          nlp=None, context=None) -> List[Dict[str, Any]]:
        """Run analysis with context-aware rule selection based on block type."""
        block_type = self._get_block_type(context)
        if self._should_skip(block_type):
            return []

        applicable = self._get_applicable_rules(block_type)
        skip_rules = context.get('skip_rules', []) if context else []
        if skip_rules:
            applicable = [r for r in applicable if r not in skip_rules]

        return self._run_rules(applicable, text, sentences, nlp, context)

    def analyze_with_all_rules(self, text: str, sentences: List[str],
                                nlp=None, context=None) -> List[Dict[str, Any]]:
        """Run analysis with all discovered rules."""
        skip_rules = context.get('skip_rules', []) if context else []
        applicable = [rt for rt in self.rules if rt not in skip_rules]
        return self._run_rules(applicable, text, sentences, nlp, context)

    def _run_rules(self, rule_types, text, sentences, nlp, context):
        """Execute rules and return collected errors."""
        spacy_doc = nlp(text) if (nlp and text and text.strip()) else None
        all_errors: List[Dict[str, Any]] = []

        for rule_type in rule_types:
            rule = self.rules.get(rule_type)
            if rule:
                self._execute_rule(rule, text, sentences, nlp, context,
                                   spacy_doc, all_errors)

        # Confidence filtering
        if self.confidence_threshold is not None:
            all_errors = [
                e for e in all_errors
                if e.get('confidence_score') is None
                or e['confidence_score'] >= self.confidence_threshold
            ]

        return all_errors

    def _execute_rule(self, rule, text, sentences, nlp, context,
                      spacy_doc, all_errors):
        """Run a single rule and append results."""
        try:
            for error in rule.analyze(text, sentences, nlp, context,
                                       spacy_doc=spacy_doc):
                if error is not None:
                    all_errors.append(rule._make_serializable(error))
        except Exception as e:
            all_errors.append({
                'type': 'system_error',
                'message': f'Rule {rule.__class__.__name__} failed: {str(e)}',
                'suggestions': ['Check rule implementation'],
                'sentence': '', 'sentence_index': -1, 'severity': 'low',
            })

    # ── Helpers ────────────────────────────────────────────────────────

    def _get_block_type(self, context: Optional[dict]) -> str:
        if not context:
            return 'paragraph'
        return str(
            context.get('block_type') or context.get('type')
            or context.get('blockType') or 'paragraph'
        ).lower()

    def _should_skip(self, block_type: str) -> bool:
        return block_type in {
            'listing', 'literal', 'code_block', 'inline_code', 'pass',
            'attribute_entry', 'html_block', 'html_inline',
            'horizontal_rule', 'softbreak', 'hardbreak',
        }

    def _get_applicable_rules(self, block_type: str) -> List[str]:
        applicable = self.block_type_rules.get(block_type, [])
        if not applicable and block_type not in self.block_type_rules:
            applicable = self.block_type_rules.get('paragraph', [])
        exclusions = self.rule_exclusions.get(block_type, [])
        return [r for r in applicable if r not in exclusions and r in self.rules]

    def get_rule(self, rule_type: str) -> Optional[BaseRule]:
        return self.rules.get(rule_type)

    def get_all_rules(self) -> Dict[str, BaseRule]:
        return self.rules

    def list_discovered_rules(self) -> Dict[str, Any]:
        rules_by_location: Dict[str, list] = {}
        for rule_type, location in self.rule_locations.items():
            rules_by_location.setdefault(location, []).append(rule_type)
        return {
            'total_rules': len(self.rules),
            'rules_by_location': rules_by_location,
            'all_rule_types': list(self.rules.keys()),
        }


# ── Global Singleton ──────────────────────────────────────────────────

_registry = None


def get_registry(confidence_threshold=None, **kwargs):
    """Get the global registry instance, initializing if needed."""
    global _registry
    if _registry is None:
        _registry = RulesRegistry(
            confidence_threshold=confidence_threshold,
        )
    return _registry


class _RegistryProxy:
    """Proxy that initializes the registry on first access."""
    def __getattr__(self, name):
        return getattr(get_registry(), name)


registry = _RegistryProxy()
