"""Unified style guide citation registry.

Provides a single entry point for looking up citations, excerpts,
and confidence adjustments across all supported style guides.

Checks guides in priority order: Red Hat -> IBM -> Accessibility ->
Modular Docs, returning the first match found.  Red Hat SSG overrides
IBM when both guides cover the same topic.

Usage:
    from style_guides.registry import get_citation, format_citation

    citation = get_citation('articles')
    formatted = format_citation('inclusive_language')
    adjustment = get_confidence_adjustment('procedures')
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default citation when no guide has a mapping
DEFAULT_CITATION = "IBM Style Guide"

# Guide registry: (name, module_path, guide_key_for_excerpts)
# Each entry is loaded lazily with ImportError protection
_GUIDE_MODULES: List[Tuple[str, str]] = [
    ('Red Hat Supplementary Style Guide', 'style_guides.red_hat.red_hat_style_mapping'),
    ('IBM Style Guide', 'style_guides.ibm.ibm_style_mapping'),
    ('Getting Started with Accessibility for Writers', 'style_guides.accessibility.accessibility_mapping'),
    ('Modular Documentation Reference Guide', 'style_guides.modular_docs.modular_docs_mapping'),
]

# Cached module references after first import attempt
_loaded_modules: Dict[str, Optional[object]] = {}


def _get_guide_module(module_path: str) -> Optional[object]:
    """Lazily import and cache a guide module.

    Args:
        module_path: Dotted Python module path to import.

    Returns:
        The imported module object, or None if import failed.
    """
    if module_path in _loaded_modules:
        return _loaded_modules[module_path]

    try:
        import importlib
        module = importlib.import_module(module_path)
        _loaded_modules[module_path] = module
        return module
    except ImportError as exc:
        logger.debug("Could not import guide module %s: %s", module_path, exc)
        _loaded_modules[module_path] = None
        return None


def _find_in_guides(
    func_name: str,
    rule_type: str,
    category: Optional[str],
    empty_result: Any,
) -> Tuple[Optional[str], Any]:
    """Search all guides in priority order for a rule using the named function.

    Args:
        func_name: Name of the function to call on each guide module.
        rule_type: Rule identifier to look up.
        category: Optional category hint.
        empty_result: Value that indicates "not found" (None or {} or similar).

    Returns:
        Tuple of (guide_name, result) or (None, empty_result) if not found.
    """
    for guide_name, module_path in _GUIDE_MODULES:
        module = _get_guide_module(module_path)
        if module is None:
            continue

        func: Optional[Callable] = getattr(module, func_name, None)
        if func is None:
            continue

        result = func(rule_type, category)
        if _is_valid_result(result, empty_result):
            return guide_name, result

    return None, empty_result


def _is_valid_result(result: Any, empty_result: Any) -> bool:
    """Check whether a lookup result is non-empty.

    Args:
        result: The value returned by a guide lookup function.
        empty_result: The sentinel empty value to compare against.

    Returns:
        True if result is present and non-empty.
    """
    if result is None:
        return False
    if isinstance(result, dict) and not result:
        return False
    return result != empty_result


def get_citation(
    rule_type: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Look up citation data for a rule across all style guides.

    Checks IBM, Red Hat, Accessibility, and Modular Docs in priority
    order. Returns the first match found.

    Args:
        rule_type: Rule identifier (e.g., 'articles', 'inclusive_language').
        category: Optional category hint to speed up lookup.

    Returns:
        Dict with guide_name, topic, pages, verified, and
        citation_text fields, or empty dict if not found in any guide.
    """
    guide_name, mapping = _find_in_guides('get_rule_mapping', rule_type, category, None)

    if mapping is None or guide_name is None:
        return {}

    return _build_citation_dict(guide_name, mapping)


def _build_citation_dict(guide_name: str, mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Build a standardized citation dict from a guide-specific mapping.

    Args:
        guide_name: Name of the style guide that provided the mapping.
        mapping: The raw rule mapping dict from the guide module.

    Returns:
        Standardized citation dict with guide_name, topic, pages,
        verified, and citation_text fields.
    """
    guide_data = _extract_guide_data(mapping)
    topic = guide_data.get('topic', '')
    pages = guide_data.get('pages', [])
    verified = guide_data.get('verification_status') == 'verified'
    guidance = guide_data.get('guidance', '')

    return {
        'guide_name': guide_name,
        'topic': topic,
        'pages': pages,
        'verified': verified,
        'citation_text': guidance,
    }


def _extract_guide_data(mapping: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the guide-specific sub-dict from a rule mapping.

    Checks for ibm_style, red_hat_ssg, accessibility, or modular_docs
    keys in order.

    Args:
        mapping: The raw rule mapping dict.

    Returns:
        The guide-specific sub-dict, or empty dict if none found.
    """
    for key in ('ibm_style', 'red_hat_ssg', 'accessibility', 'modular_docs'):
        if key in mapping:
            return mapping[key]
    return {}


def get_excerpt(
    rule_type: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Look up excerpt data for a rule across all style guides.

    Args:
        rule_type: Rule identifier.
        category: Optional category hint.

    Returns:
        Dict with guide_name, topic, pages, excerpt, and verified
        fields, or empty dict if not found.
    """
    guide_name, excerpt = _find_in_guides('get_excerpt', rule_type, category, {})

    if not excerpt:
        return {}

    return excerpt


def format_citation(
    rule_type: str, category: Optional[str] = None
) -> str:
    """Format a human-readable citation string for a rule.

    Checks all guides in priority order and returns the formatted
    citation from the first guide that has a mapping.

    Args:
        rule_type: Rule identifier.
        category: Optional category hint.

    Returns:
        Formatted citation string like ``"IBM Style Guide (Page 312)"``
        or the default citation if not found.
    """
    for _guide_name, module_path in _GUIDE_MODULES:
        module = _get_guide_module(module_path)
        if module is None:
            continue

        format_func: Optional[Callable] = getattr(module, 'format_citation', None)
        get_rule_func: Optional[Callable] = getattr(module, 'get_rule_mapping', None)

        if format_func is None or get_rule_func is None:
            continue

        if get_rule_func(rule_type, category) is not None:
            return format_func(rule_type, category)

    return DEFAULT_CITATION


def get_confidence_adjustment(
    rule_type: str, category: Optional[str] = None
) -> float:
    """Get confidence score adjustment for a rule.

    Verified rules get +0.2 boost, unverified -0.1, legal +0.3.
    Returns the adjustment from the first guide that has a mapping.

    Args:
        rule_type: Rule identifier.
        category: Optional category hint.

    Returns:
        Confidence adjustment value, or 0.0 if not found.
    """
    _guide_name, adjustment = _find_in_guides(
        'get_confidence_adjustment', rule_type, category, 0.0
    )

    return adjustment


def get_verification_status(
    rule_type: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Get verification status for a rule across all guides.

    Args:
        rule_type: Rule identifier.
        category: Optional category hint.

    Returns:
        Dict with status and verified fields, or default unknown
        status if not found.
    """
    for _guide_name, module_path in _GUIDE_MODULES:
        module = _get_guide_module(module_path)
        if module is None:
            continue

        func: Optional[Callable] = getattr(module, 'get_verification_status', None)
        if func is None:
            continue

        result = func(rule_type, category)
        if result and result.get('status') != 'unknown':
            return result

    return {'status': 'unknown', 'verified': False}
