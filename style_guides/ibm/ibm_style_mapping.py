"""IBM Style Guide mapping utility.

Central system for managing IBM Style Guide rule citations.
Loads rule mappings from ibm_style_mapping.yaml and provides
lookup, citation formatting, confidence adjustment, and
verification status functions.

Usage:
    from style_guides.ibm.ibm_style_mapping import get_rule_mapping, format_citation

    mapping = get_rule_mapping('articles')
    citation = format_citation('articles')  # "IBM Style Guide (Page 91)"
    adjustment = get_confidence_adjustment('articles')  # 0.2 boost for verified
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Constants
IBM_STYLE_GUIDE_DEFAULT_CITATION = "IBM Style Guide"

# Categories searched when looking up rules
_CATEGORIES = (
    'language_and_grammar',
    'structure_and_format',
    'audience_and_medium',
    'legal_information',
    'punctuation',
    'numbers_and_measurement',
    'technical_elements',
    'references',
    'word_usage',
    'modular_compliance',
)


class IBMStyleMapping:
    """Singleton class for IBM Style Guide mapping management.

    Loads the ibm_style_mapping.yaml file once and provides methods
    to look up rule mappings, format citations, compute confidence
    adjustments, and check verification status.
    """

    _instance: Optional['IBMStyleMapping'] = None
    _mapping: Optional[Dict[str, Any]] = None
    _loaded: bool = False

    def __new__(cls) -> 'IBMStyleMapping':
        """Return the singleton instance, creating it if necessary."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize and load mapping if not already loaded."""
        if not self._loaded:
            self._load_mapping()

    def _load_mapping(self) -> None:
        """Load the IBM Style Guide mapping YAML file."""
        current_dir = Path(__file__).parent
        mapping_file = current_dir / 'ibm_style_mapping.yaml'

        if not mapping_file.exists():
            logger.warning(
                "IBM Style mapping file not found at %s, using defaults",
                mapping_file,
            )
            self._mapping = self._get_default_mapping()
            IBMStyleMapping._loaded = True
            return

        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self._mapping = yaml.safe_load(f)
            IBMStyleMapping._loaded = True
            logger.info("IBM Style Guide mapping loaded successfully")
        except yaml.YAMLError as exc:
            logger.error("YAML parse error loading IBM Style mapping: %s", exc)
            self._mapping = self._get_default_mapping()
            IBMStyleMapping._loaded = True
        except FileNotFoundError:
            logger.error("IBM Style mapping file disappeared during read")
            self._mapping = self._get_default_mapping()
            IBMStyleMapping._loaded = True

    @staticmethod
    def _get_default_mapping() -> Dict[str, Any]:
        """Return minimal default mapping when file cannot be loaded.

        Returns:
            Dictionary with empty category sections and default
            confidence adjustment values.
        """
        return {
            'version': '1.0',
            'language_and_grammar': {},
            'structure_and_format': {},
            'audience_and_medium': {},
            'legal_information': {},
            'confidence_adjustments': {
                'verified_rule_boost': 0.2,
                'unverified_rule_penalty': 0.1,
                'legal_rule_boost': 0.3,
            },
        }

    def get_rule_mapping(
        self, rule_id: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get mapping for a specific rule.

        Args:
            rule_id: Rule identifier (e.g., 'articles', 'wordiness').
            category: Optional category hint (e.g., 'language_and_grammar').

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
            Formatted citation string such as
            ``"IBM Style Guide (Page 91)"`` for verified rules.
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return IBM_STYLE_GUIDE_DEFAULT_CITATION

        ibm_style = mapping.get('ibm_style', {})
        return self._build_citation_string(mapping, ibm_style, include_verification)

    def _build_citation_string(
        self,
        mapping: Dict[str, Any],
        ibm_style: Dict[str, Any],
        include_verification: bool,
    ) -> str:
        """Build a formatted citation string from mapping data.

        Args:
            mapping: Full rule mapping dict.
            ibm_style: The ibm_style sub-dict from the mapping.
            include_verification: Whether to append verification indicator.

        Returns:
            Formatted citation string.
        """
        verification_status = ibm_style.get('verification_status', 'unverified')
        pages = ibm_style.get('pages', [])

        if verification_status == 'verified' and pages:
            return self._format_verified_citation(pages, include_verification)

        display_citation = mapping.get('display_citation')
        if display_citation:
            if include_verification:
                return f"{display_citation} [Citation Pending]"
            return str(display_citation)

        topic = ibm_style.get('topic', 'Style Guidelines')
        return f"{IBM_STYLE_GUIDE_DEFAULT_CITATION}: {topic}"

    @staticmethod
    def _format_verified_citation(pages: List[int], include_verification: bool) -> str:
        """Format a citation string for a verified rule with page numbers.

        Args:
            pages: List of verified page numbers.
            include_verification: Whether to append a check mark.

        Returns:
            Formatted citation string with page references.
        """
        if len(pages) == 1:
            citation = f"{IBM_STYLE_GUIDE_DEFAULT_CITATION} (Page {pages[0]})"
        else:
            page_list = ', '.join(str(p) for p in pages)
            citation = f"{IBM_STYLE_GUIDE_DEFAULT_CITATION} (Pages {page_list})"

        if include_verification:
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

        ibm_style = mapping.get('ibm_style', {})
        return {
            'guide_name': IBM_STYLE_GUIDE_DEFAULT_CITATION,
            'topic': ibm_style.get('topic', ''),
            'pages': ibm_style.get('pages', []),
            'excerpt': ibm_style.get('excerpt', ibm_style.get('guidance', '')),
            'verified': ibm_style.get('verification_status') == 'verified',
        }

    def get_confidence_adjustment(
        self, rule_id: str, category: Optional[str] = None
    ) -> float:
        """Get confidence score adjustment based on verification status.

        Verified rules receive a positive boost, unverified rules receive
        a small penalty, and legal rules receive an additional boost.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.

        Returns:
            Confidence adjustment value (positive or negative float).
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return 0.0

        if 'confidence_boost' in mapping:
            return float(mapping['confidence_boost'])
        if 'confidence_penalty' in mapping:
            return -abs(float(mapping['confidence_penalty']))

        return self._compute_adjustment_from_status(mapping, category)

    def _compute_adjustment_from_status(
        self, mapping: Dict[str, Any], category: Optional[str]
    ) -> float:
        """Compute confidence adjustment from verification status fields.

        Args:
            mapping: Full rule mapping dict.
            category: Optional category used to detect legal rules.

        Returns:
            Computed confidence adjustment.
        """
        adjustments = self._mapping.get('confidence_adjustments', {})
        ibm_style = mapping.get('ibm_style', {})
        verification_status = ibm_style.get('verification_status', 'unverified')

        if verification_status == 'verified':
            return self._verified_adjustment(ibm_style, adjustments, category)

        if verification_status == 'unverified':
            penalty = adjustments.get('unverified_rule_penalty', 0.1)
            return -abs(float(penalty))

        return 0.0

    def _verified_adjustment(
        self,
        ibm_style: Dict[str, Any],
        adjustments: Dict[str, Any],
        category: Optional[str],
    ) -> float:
        """Calculate adjustment for a verified rule.

        Args:
            ibm_style: The ibm_style sub-dict from the mapping.
            adjustments: Global confidence adjustment settings.
            category: Category string, checked for legal boost.

        Returns:
            Total confidence adjustment for the verified rule.
        """
        adjustment = float(adjustments.get('verified_rule_boost', 0.2))

        if category == 'legal_information':
            adjustment += float(adjustments.get('legal_rule_boost', 0.3))

        verified_date = ibm_style.get('verified_date')
        if verified_date:
            adjustment += self._get_verification_age_penalty(verified_date, adjustments)

        return adjustment

    @staticmethod
    def _get_verification_age_penalty(
        verified_date: str, adjustments: Dict[str, Any]
    ) -> float:
        """Calculate penalty based on how old the verification is.

        Args:
            verified_date: ISO date string of last verification.
            adjustments: Global confidence adjustment settings.

        Returns:
            Negative penalty if verification is stale, else 0.0.
        """
        try:
            verified = datetime.strptime(verified_date, '%Y-%m-%d')
            age = datetime.now() - verified

            if age > timedelta(days=365):
                return float(adjustments.get('verification_older_than_1_year', -0.1))
            if age > timedelta(days=180):
                return float(adjustments.get('verification_older_than_6_months', -0.05))

            return 0.0
        except (ValueError, TypeError) as exc:
            logger.debug("Could not parse verification date '%s': %s", verified_date, exc)
            return 0.0

    def get_verification_status(
        self, rule_id: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get detailed verification status for a rule.

        Args:
            rule_id: Rule identifier.
            category: Optional category hint.

        Returns:
            Dict with status, verified, verified_date, pages, topic,
            and note fields.
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return {'status': 'unknown', 'verified': False}

        ibm_style = mapping.get('ibm_style', {})
        return {
            'status': ibm_style.get('verification_status', 'unverified'),
            'verified': ibm_style.get('verification_status') == 'verified',
            'verified_date': ibm_style.get('verified_date'),
            'pages': ibm_style.get('pages', []),
            'topic': ibm_style.get('topic'),
            'note': ibm_style.get('note'),
        }

    def get_all_unverified_rules(self) -> List[Dict[str, Any]]:
        """Get list of all unverified rules for verification tracking.

        Returns:
            List of dicts with rule_id, category, display_name,
            status, topic, and note for each unverified rule.
        """
        unverified: List[Dict[str, Any]] = []

        for category in _CATEGORIES:
            cat_data = self._mapping.get(category)
            if not isinstance(cat_data, dict):
                continue
            self._collect_unverified_in_category(cat_data, category, unverified)

        return unverified

    @staticmethod
    def _collect_unverified_in_category(
        cat_data: Dict[str, Any],
        category: str,
        result: List[Dict[str, Any]],
    ) -> None:
        """Append unverified rules from one category to result list.

        Args:
            cat_data: Mapping data for a single category.
            category: Category name string.
            result: List to append unverified rule info dicts to.
        """
        for rule_id, rule_data in cat_data.items():
            if not isinstance(rule_data, dict):
                continue
            ibm_style = rule_data.get('ibm_style', {})
            if ibm_style.get('verification_status') != 'verified':
                result.append({
                    'rule_id': rule_id,
                    'category': category,
                    'display_name': rule_data.get('display_name', rule_id),
                    'status': ibm_style.get('verification_status', 'unverified'),
                    'topic': ibm_style.get('topic'),
                    'note': ibm_style.get('note'),
                })

    def get_verification_stats(self) -> Dict[str, Any]:
        """Get overall verification statistics.

        Returns:
            Dict with total_rules, verified_rules, unverified_rules,
            and verification_percentage.
        """
        if 'verification_stats' in self._mapping:
            return self._mapping['verification_stats']

        return self._calculate_verification_stats()

    def _calculate_verification_stats(self) -> Dict[str, Any]:
        """Calculate verification statistics across all categories.

        Returns:
            Dict with total and verified counts plus percentage.
        """
        total = 0
        verified = 0

        for category in _CATEGORIES:
            cat_data = self._mapping.get(category)
            if not isinstance(cat_data, dict):
                continue
            for rule_data in cat_data.values():
                if not isinstance(rule_data, dict):
                    continue
                total += 1
                ibm_style = rule_data.get('ibm_style', {})
                if ibm_style.get('verification_status') == 'verified':
                    verified += 1

        percentage = int((verified / total * 100) if total > 0 else 0)
        return {
            'total_rules': total,
            'verified_rules': verified,
            'unverified_rules': total - verified,
            'verification_percentage': percentage,
        }


# ============================================================================
# Convenience functions delegating to the singleton
# ============================================================================

_mapping_instance: Optional[IBMStyleMapping] = None


def get_mapping_instance() -> IBMStyleMapping:
    """Get the singleton instance of IBMStyleMapping.

    Returns:
        The shared IBMStyleMapping singleton.
    """
    global _mapping_instance  # noqa: PLW0603
    if _mapping_instance is None:
        _mapping_instance = IBMStyleMapping()
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
    return get_mapping_instance().get_rule_mapping(rule_id, category)


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
    return get_mapping_instance().format_citation(rule_id, category, include_verification)


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
    return get_mapping_instance().get_excerpt(rule_id, category)


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
    return get_mapping_instance().get_confidence_adjustment(rule_id, category)


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
    return get_mapping_instance().get_verification_status(rule_id, category)


def get_all_unverified_rules() -> List[Dict[str, Any]]:
    """Get list of all unverified rules.

    Returns:
        List of unverified rule info dicts.
    """
    return get_mapping_instance().get_all_unverified_rules()


def get_verification_stats() -> Dict[str, Any]:
    """Get overall verification statistics.

    Returns:
        Dict with verification stats.
    """
    return get_mapping_instance().get_verification_stats()
