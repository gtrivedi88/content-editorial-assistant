"""
Rule Loader -- Discovers and instantiates all concrete rule modules.

Walks the ``rules/`` directory tree (up to 4 levels deep), imports every
``*_rule.py`` file (skipping ``base_*.py``), finds concrete ``BaseRule``
subclasses, and returns a mapping of ``{ rule_type: instance }``.
"""

import importlib
import importlib.util
import logging
import os
from typing import Any, Dict, Optional, Tuple

from rules.base_rule import BaseRule

logger = logging.getLogger(__name__)

# Base class names that must never be instantiated as concrete rules.
_BASE_CLASS_NAMES = frozenset([
    "BaseRule",
    "BaseLanguageRule",
    "BasePunctuationRule",
    "BaseStructureRule",
    "BaseTechnicalRule",
    "BaseWordUsageRule",
    "BaseAudienceRule",
    "BaseNumbersRule",
    "BaseReferencesRule",
    "BaseLegalRule",
])

_MAX_DEPTH = 4


def discover_rules(
    rules_dir: Optional[str] = None,
) -> Tuple[Dict[str, BaseRule], Dict[str, str]]:
    """Discover and instantiate all concrete rule classes under *rules_dir*.

    Args:
        rules_dir: Root directory to scan.  Defaults to the directory
            containing this module (``rules/``).

    Returns:
        A 2-tuple of:
        - ``rules``: ``{ rule_type: rule_instance }``
        - ``rule_locations``: ``{ rule_type: human-readable directory label }``
    """
    if rules_dir is None:
        rules_dir = os.path.dirname(os.path.abspath(__file__))

    rules: Dict[str, BaseRule] = {}
    rule_locations: Dict[str, str] = {}

    for root, _dirs, files in os.walk(rules_dir):
        if "__pycache__" in root:
            continue

        rel_path = os.path.relpath(root, rules_dir)
        depth = 0 if rel_path == "." else len(rel_path.split(os.sep))
        if depth > _MAX_DEPTH:
            continue

        _scan_directory(root, rel_path, files, rules, rule_locations)

    logger.info("Rule discovery complete: loaded %d rules", len(rules))
    return rules, rule_locations


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _scan_directory(
    root: str,
    rel_path: str,
    files: list,
    rules: Dict[str, BaseRule],
    rule_locations: Dict[str, str],
) -> None:
    """Scan a single directory for rule files and load them."""
    for filename in files:
        if not filename.endswith("_rule.py") or filename.startswith("base_"):
            continue

        if rel_path == ".":
            import_path = filename[:-3]
            location = "main"
        else:
            import_path = f"{rel_path.replace(os.sep, '.')}.{filename[:-3]}"
            location = rel_path.replace(os.sep, " > ")

        _try_load_rule(import_path, root, filename, location, rules, rule_locations)


def _try_load_rule(
    import_path: str,
    file_dir: str,
    filename: str,
    location: str,
    rules: Dict[str, BaseRule],
    rule_locations: Dict[str, str],
) -> None:
    """Attempt to import a module, find a concrete rule class, and register it."""
    try:
        module = _import_module(import_path, file_dir, filename)
        if module is None:
            return
        instance = _find_rule_class(module)
        if instance is not None and instance.rule_type not in rules:
            rules[instance.rule_type] = instance
            rule_locations[instance.rule_type] = location
    except (ImportError, AttributeError, TypeError, ValueError) as exc:
        logger.warning("Failed to load rule %s: %s", import_path, exc)


def _import_module(
    import_path: str, file_dir: str, filename: str
) -> Optional[Any]:
    """Import a rule module using multiple strategies."""
    # Strategy 1: absolute import via the rules package
    try:
        return importlib.import_module(f"rules.{import_path}")
    except ImportError:
        pass

    # Strategy 2: relative import within the rules package
    if "." in import_path:
        try:
            return importlib.import_module(
                f".{import_path}", package="rules"
            )
        except ImportError:
            pass

    # Strategy 3: direct file-based import as last resort
    try:
        file_path = os.path.join(file_dir, filename)
        spec = importlib.util.spec_from_file_location(
            f"rule_module_{import_path.replace('.', '_')}", file_path
        )
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    except (ImportError, AttributeError, FileNotFoundError) as exc:
        logger.debug("Direct import failed for %s: %s", import_path, exc)

    return None


def _find_rule_class(module: Any) -> Optional[BaseRule]:
    """Find and instantiate the first concrete BaseRule subclass in *module*."""
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if not _is_concrete_rule(attr, module):
            continue
        instance = _try_instantiate(attr)
        if instance is not None:
            return instance
    return None


def _is_concrete_rule(attr: Any, module: Any) -> bool:
    """Return ``True`` if *attr* is a concrete (non-abstract) rule class defined in *module*."""
    if not isinstance(attr, type):
        return False
    if attr.__name__ in _BASE_CLASS_NAMES:
        return False
    if not attr.__name__.endswith("Rule"):
        return False
    if attr.__module__ != module.__name__:
        return False
    if not all(hasattr(attr, m) for m in ("analyze", "_get_rule_type")):
        return False
    if hasattr(attr, "__abstractmethods__") and attr.__abstractmethods__:
        return False
    return True


def _try_instantiate(cls: type) -> Optional[BaseRule]:
    """Instantiate *cls* and return the instance if it has a valid rule_type."""
    try:
        instance = cls()
        if (
            hasattr(instance, "rule_type")
            and instance.rule_type
            and instance.rule_type != "base"
            and hasattr(instance, "analyze")
        ):
            return instance
    except (TypeError, ValueError, AttributeError, KeyError,
            IndexError, FileNotFoundError) as exc:
        logger.warning(
            "Could not instantiate %s: %s", cls.__name__, exc
        )
    return None
