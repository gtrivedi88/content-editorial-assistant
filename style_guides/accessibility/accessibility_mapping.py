"""Accessibility guidelines mapping utility.

Central system for managing accessibility rule citations.
Loads rule mappings from accessibility_mapping.yaml and provides
lookup, citation formatting, confidence adjustment, and
verification status functions.

Usage:
    from style_guides.accessibility.accessibility_mapping import get_rule_mapping

    mapping = get_rule_mapping('alt_text')
    citation = format_citation('headings')
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Constants
ACCESSIBILITY_DEFAULT_CITATION = "Getting Started with Accessibility for Writers"

# Categories searched when looking up rules
_CATEGORIES = (
    'inclusive_language',
    'content_structure',
    'images_and_media',
    'links_and_navigation',
)


class AccessibilityMapping:
    """Singleton class for accessibility guidelines mapping management.

    Loads the accessibility_mapping.yaml file once and provides
    methods to look up rule mappings, format citations, compute
    confidence adjustments, and check verification status.
    """

    _instance: Optional['AccessibilityMapping'] = None
    _mapping: Optional[Dict[str, Any]] = None
    _loaded: bool = False

    def __new__(cls) -> 'AccessibilityMapping':
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize and load mapping if not already loaded."""
        if not self._loaded:
            self._load_mapping()

    def _load_mapping(self) -> None:
        """Load the accessibility mapping YAML file."""
        current_dir = Path(__file__).parent
        mapping_file = current_dir / 'accessibility_mapping.yaml'

        if not mapping_file.exists():
            logger.warning(
                "Accessibility mapping file not found at %s, using defaults",
                mapping_file,
            )
            self._mapping = self._get_default_mapping()
            AccessibilityMapping._loaded = True
            return

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self._mapping = yaml.safe_load(f)
            AccessibilityMapping._loaded = True
            logger.info("Accessibility mapping loaded successfully")
        except yaml.YAMLError as exc:
            logger.error("YAML parse error loading accessibility mapping: %s", exc)
            self._mapping = self._get_default_mapping()
            AccessibilityMapping._loaded = True
        except FileNotFoundError:
            logger.error("Accessibility mapping file disappeared during read")
            self._mapping = self._get_default_mapping()
            AccessibilityMapping._loaded = True

    @staticmethod
    def _get_default_mapping() -> Dict[str, Any]:
        """Return minimal default mapping when file cannot be loaded.

        Returns:
            Dictionary with empty category sections and default
            confidence adjustment values.
        """
        return {
            'version': '1.0',
            'inclusive_language': {},
            'content_structure': {},
            'images_and_media': {},
            'links_and_navigation': {},
            'confidence_adjustments': {
                'verified_rule_boost': 0.2,
                'unverified_rule_penalty': 0.1,
                'accessibility_critical_boost': 0.25,
            },
        }

    def get_rule_mapping(
        self, rule_id: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get mapping for a specific rule.

        Args:
            rule_id: Rule identifier (e.g., 'alt_text', 'headings').
            category: Optional category hint (e.g., 'content_structure').

        Returns:
            Rule mapping dict or None if not found.
        """
        if not self._mapping:
            return None

        if category and category in self._mapping:
            cat_data = self._mapping[category]
            if isinstance(cat_data, dict) and rule_id in cat_data:
                return cat_data[rule_id]

        return self._search_all_categories(rule_id)

    def _search_all_categories(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Search all known categories for a rule_id.

        Args:
            rule_id: Rule identifier to search for.

        Returns:
            Rule mapping dict or None if not found.
        """
        for cat in _CATEGORIES:
            cat_data = self._mapping.get(cat)
            if isinstance(cat_data, dict) and rule_id in cat_data:
                return cat_data[rule_id]
        return None

    def format_citation(
        self,
        rule_id: str,
        category: Optional[str] = None,
        include_verification: bool = True,
    ) -> str:
        """Format citation string for display in error messages.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.
            include_verification: Whether to include verification indicator.

        Returns:
            Formatted citation string.
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return ACCESSIBILITY_DEFAULT_CITATION

        accessibility = mapping.get('accessibility', {})
        return self._build_citation_string(accessibility, include_verification)

    def _build_citation_string(
        self,
        accessibility: Dict[str, Any],
        include_verification: bool,
    ) -> str:
        """Build a formatted citation string from mapping data.

        Args:
            accessibility: The accessibility sub-dict from the mapping.
            include_verification: Whether to append verification indicator.

        Returns:
            Formatted citation string.
        """
        verification_status = accessibility.get('verification_status', 'unverified')
        section = accessibility.get('section', '')
        topic = accessibility.get('topic', 'Accessibility Guidelines')

        if section:
            citation = f"{ACCESSIBILITY_DEFAULT_CITATION} (Section: {section})"
        else:
            citation = f"{ACCESSIBILITY_DEFAULT_CITATION}: {topic}"

        if include_verification and verification_status == 'verified':
            citation += " [Verified]"

        return citation

    def get_excerpt(
        self, rule_id: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get excerpt data for a rule.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.

        Returns:
            Dict with guide_name, topic, pages, excerpt, and verified
            fields, or empty dict if not found.
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return {}

        accessibility = mapping.get('accessibility', {})
        return {
            'guide_name': ACCESSIBILITY_DEFAULT_CITATION,
            'topic': accessibility.get('topic', ''),
            'pages': [],
            'excerpt': accessibility.get('excerpt', accessibility.get('guidance', '')),
            'verified': accessibility.get('verification_status') == 'verified',
        }

    def get_confidence_adjustment(
        self, rule_id: str, category: Optional[str] = None
    ) -> float:
        """Get confidence score adjustment based on verification status.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.

        Returns:
            Confidence adjustment value (positive or negative float).
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return 0.0

        adjustments = self._mapping.get('confidence_adjustments', {})
        accessibility = mapping.get('accessibility', {})
        verification_status = accessibility.get('verification_status', 'unverified')

        if verification_status == 'verified':
            return float(adjustments.get('verified_rule_boost', 0.2))

        if verification_status == 'unverified':
            penalty = adjustments.get('unverified_rule_penalty', 0.1)
            return -abs(float(penalty))

        return 0.0

    def get_verification_status(
        self, rule_id: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed verification status for a rule.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.

        Returns:
            Dict with status, verified, section, and topic fields.
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return {'status': 'unknown', 'verified': False}

        accessibility = mapping.get('accessibility', {})
        return {
            'status': accessibility.get('verification_status', 'unverified'),
            'verified': accessibility.get('verification_status') == 'verified',
            'section': accessibility.get('section'),
            'topic': accessibility.get('topic'),
        }

    def get_all_unverified_rules(self) -> List[Dict[str, Any]]:
        """Get list of all unverified rules for verification tracking.

        Returns:
            List of dicts with rule_id, category, display_name,
            status, and topic for each unverified rule.
        """
        unverified: List[Dict[str, Any]] = []

        for category in _CATEGORIES:
            cat_data = self._mapping.get(category)
            if not isinstance(cat_data, dict):
                continue
            for rule_id, rule_data in cat_data.items():
                if not isinstance(rule_data, dict):
                    continue
                accessibility = rule_data.get('accessibility', {})
                if accessibility.get('verification_status') != 'verified':
                    unverified.append({
                        'rule_id': rule_id,
                        'category': category,
                        'display_name': rule_data.get('display_name', rule_id),
                        'status': accessibility.get('verification_status', 'unverified'),
                        'topic': accessibility.get('topic'),
                    })

        return unverified


# ============================================================================
# Convenience functions delegating to the singleton
# ============================================================================

_mapping_instance: Optional[AccessibilityMapping] = None


def _get_mapping_instance() -> AccessibilityMapping:
    """Get the singleton instance of AccessibilityMapping.

    Returns:
        The shared AccessibilityMapping singleton.
    """
    global _mapping_instance  # noqa: PLW0603
    if _mapping_instance is None:
        _mapping_instance = AccessibilityMapping()
    return _mapping_instance


def get_rule_mapping(
    rule_id: str, category: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Get mapping for a specific rule.

    Args:
        rule_id: Rule identifier.
        category: Optional category hint.

    Returns:
        Rule mapping dict or None if not found.
    """
    return _get_mapping_instance().get_rule_mapping(rule_id, category)


def format_citation(
    rule_id: str,
    category: Optional[str] = None,
    include_verification: bool = True,
) -> str:
    """Format citation string for display.

    Args:
        rule_id: Rule identifier.
        category: Optional category hint.
        include_verification: Whether to include verification indicator.

    Returns:
        Formatted citation string.
    """
    return _get_mapping_instance().format_citation(rule_id, category, include_verification)


def get_excerpt(
    rule_id: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Get excerpt data for a rule.

    Args:
        rule_id: Rule identifier.
        category: Optional category hint.

    Returns:
        Dict with excerpt fields or empty dict if not found.
    """
    return _get_mapping_instance().get_excerpt(rule_id, category)


def get_confidence_adjustment(
    rule_id: str, category: Optional[str] = None
) -> float:
    """Get confidence adjustment for a rule.

    Args:
        rule_id: Rule identifier.
        category: Optional category hint.

    Returns:
        Confidence adjustment value.
    """
    return _get_mapping_instance().get_confidence_adjustment(rule_id, category)


def get_verification_status(
    rule_id: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Get verification status for a rule.

    Args:
        rule_id: Rule identifier.
        category: Optional category hint.

    Returns:
        Dict with verification status details.
    """
    return _get_mapping_instance().get_verification_status(rule_id, category)
