"""
IBM Style Guide Mapping Utility

Central system for managing IBM Style Guide and Red Hat SSG rule citations.

PURPOSE:
1. Single source of truth for all style guide references
2. Prevent hallucinated page numbers
3. Enable verification tracking
4. Support UI display of rule sources
5. Link confidence scoring to verification status

USAGE:
    from style_guides.ibm.ibm_style_mapping import get_rule_mapping, format_citation

    # Get mapping for a rule
    mapping = get_rule_mapping('articles')

    # Format citation for display
    citation = format_citation('articles')  # "IBM Style Guide (Pages 91-92)"

    # Get confidence adjustment
    adjustment = get_confidence_adjustment('articles')  # 0.2 boost for verified
"""

import yaml
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta

# Constants
IBM_STYLE_GUIDE_DEFAULT_CITATION = "IBM Style Guide"


class IBMStyleMapping:
    """
    Singleton class for IBM Style Guide mapping management.
    """

    _instance = None
    _mapping = None
    _loaded = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize and load mapping if not already loaded."""
        if not self._loaded:
            self._load_mapping()

    def _load_mapping(self):
        """Load the IBM Style Guide mapping YAML file."""
        try:
            # Get path to YAML file
            current_dir = Path(__file__).parent
            mapping_file = current_dir / 'ibm_style_mapping.yaml'

            if not mapping_file.exists():
                print(f"⚠️ Warning: IBM Style mapping file not found at {mapping_file}")
                self._mapping = self._get_default_mapping()
                self._loaded = True
                return

            with open(mapping_file, 'r', encoding='utf-8') as f:
                self._mapping = yaml.safe_load(f)

            self._loaded = True
            print("✅ IBM Style Guide mapping loaded successfully")

        except Exception as e:
            print(f"❌ Error loading IBM Style mapping: {e}")
            self._mapping = self._get_default_mapping()
            self._loaded = True

    def _get_default_mapping(self) -> Dict[str, Any]:
        """Return minimal default mapping if file can't be loaded."""
        return {
            'version': '1.0',
            'language_and_grammar': {},
            'structure_and_format': {},
            'audience_and_medium': {},
            'legal_information': {},
            'confidence_adjustments': {
                'verified_rule_boost': 0.2,
                'unverified_rule_penalty': 0.1,
                'legal_rule_boost': 0.3
            }
        }

    def get_rule_mapping(self, rule_id: str, category: str = None) -> Optional[Dict[str, Any]]:
        """
        Get mapping for a specific rule.

        Args:
            rule_id: Rule identifier (e.g., 'articles', 'wordiness')
            category: Optional category hint (e.g., 'language_and_grammar')

        Returns:
            Rule mapping dict or None if not found
        """
        if not self._mapping:
            return None

        # Try with category if provided
        if category and category in self._mapping:
            if rule_id in self._mapping[category]:
                return self._mapping[category][rule_id]

        # Search all categories
        for cat in ['language_and_grammar', 'structure_and_format',
                    'audience_and_medium', 'legal_information', 'punctuation',
                    'numbers_and_measurement', 'technical_elements', 'references',
                    'word_usage', 'modular_compliance']:
            if cat in self._mapping and rule_id in self._mapping[cat]:
                return self._mapping[cat][rule_id]

        return None

    def format_citation(self, rule_id: str, category: str = None,
                       include_verification: bool = True) -> str:
        """
        Format citation string for display in error messages.

        Args:
            rule_id: Rule identifier
            category: Optional category hint
            include_verification: Include verification status indicator

        Returns:
            Formatted citation string
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return IBM_STYLE_GUIDE_DEFAULT_CITATION

        ibm_style = mapping.get('ibm_style', {})
        verification_status = ibm_style.get('verification_status', 'unverified')

        # For verified rules with pages
        if verification_status == 'verified' and ibm_style.get('pages'):
            pages = ibm_style['pages']
            if len(pages) == 1:
                citation = f"{IBM_STYLE_GUIDE_DEFAULT_CITATION} (Page {pages[0]})"
            else:
                page_list = ', '.join(map(str, pages))
                citation = f"{IBM_STYLE_GUIDE_DEFAULT_CITATION} (Pages {page_list})"

            if include_verification:
                citation += " ✓"
            return citation

        # For unverified rules
        display_citation = mapping.get('display_citation')
        if display_citation:
            if include_verification:
                display_citation += " [Citation Pending]"
            return display_citation

        # Fallback
        topic = ibm_style.get('topic', 'Style Guidelines')
        return f"{IBM_STYLE_GUIDE_DEFAULT_CITATION}: {topic}"

    def get_confidence_adjustment(self, rule_id: str, category: str = None) -> float:
        """
        Get confidence score adjustment for a rule based on verification status.

        Args:
            rule_id: Rule identifier
            category: Optional category hint

        Returns:
            Confidence adjustment value (can be positive or negative)
        """
        mapping = self.get_rule_mapping(rule_id, category)
        if not mapping:
            return 0.0

        # Check for explicit adjustment in rule mapping
        if 'confidence_boost' in mapping:
            return mapping['confidence_boost']
        if 'confidence_penalty' in mapping:
            return -abs(mapping['confidence_penalty'])

        # Use default adjustments based on verification status
        adjustments = self._mapping.get('confidence_adjustments', {})
        ibm_style = mapping.get('ibm_style', {})
        verification_status = ibm_style.get('verification_status', 'unverified')

        if verification_status == 'verified':
            adjustment = adjustments.get('verified_rule_boost', 0.2)

            # Additional boost for legal rules
            if category == 'legal_information':
                adjustment += adjustments.get('legal_rule_boost', 0.3)

            # Check verification age
            verified_date = ibm_style.get('verified_date')
            if verified_date:
                age_penalty = self._get_verification_age_penalty(verified_date, adjustments)
                adjustment += age_penalty

            return adjustment

        elif verification_status == 'unverified':
            return -abs(adjustments.get('unverified_rule_penalty', 0.1))

        else:  # needs_review or other
            return 0.0

    def _get_verification_age_penalty(self, verified_date: str,
                                      adjustments: Dict[str, Any]) -> float:
        """Calculate penalty based on how old the verification is."""
        try:
            verified = datetime.strptime(verified_date, '%Y-%m-%d')
            age = datetime.now() - verified

            if age > timedelta(days=365):
                return adjustments.get('verification_older_than_1_year', -0.1)
            elif age > timedelta(days=180):
                return adjustments.get('verification_older_than_6_months', -0.05)

            return 0.0

        except Exception:
            return 0.0

    def get_verification_status(self, rule_id: str, category: str = None) -> Dict[str, Any]:
        """
        Get detailed verification status for a rule.

        Returns:
            Dict with verification details
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
            'note': ibm_style.get('note')
        }

    def get_all_unverified_rules(self) -> List[Dict[str, Any]]:
        """
        Get list of all unverified rules for verification tracking.

        Returns:
            List of unverified rule info dicts
        """
        unverified = []

        for category in ['language_and_grammar', 'structure_and_format',
                        'audience_and_medium', 'legal_information', 'punctuation',
                        'numbers_and_measurement', 'technical_elements', 'references',
                        'word_usage', 'modular_compliance']:
            if category not in self._mapping:
                continue

            for rule_id, rule_data in self._mapping[category].items():
                ibm_style = rule_data.get('ibm_style', {})
                if ibm_style.get('verification_status') != 'verified':
                    unverified.append({
                        'rule_id': rule_id,
                        'category': category,
                        'display_name': rule_data.get('display_name', rule_id),
                        'status': ibm_style.get('verification_status', 'unverified'),
                        'topic': ibm_style.get('topic'),
                        'note': ibm_style.get('note')
                    })

        return unverified

    def get_verification_stats(self) -> Dict[str, Any]:
        """
        Get overall verification statistics.

        Returns:
            Dict with verification stats
        """
        if 'verification_stats' in self._mapping:
            return self._mapping['verification_stats']

        # Calculate on the fly
        total = 0
        verified = 0

        for category in ['language_and_grammar', 'structure_and_format',
                        'audience_and_medium', 'legal_information', 'punctuation',
                        'numbers_and_measurement', 'technical_elements', 'references',
                        'word_usage', 'modular_compliance']:
            if category not in self._mapping:
                continue

            for rule_id, rule_data in self._mapping[category].items():
                total += 1
                ibm_style = rule_data.get('ibm_style', {})
                if ibm_style.get('verification_status') == 'verified':
                    verified += 1

        return {
            'total_rules': total,
            'verified_rules': verified,
            'unverified_rules': total - verified,
            'verification_percentage': int((verified / total * 100) if total > 0 else 0)
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Singleton instance
_mapping_instance = None


def get_mapping_instance() -> IBMStyleMapping:
    """Get singleton instance of IBMStyleMapping."""
    global _mapping_instance
    if _mapping_instance is None:
        _mapping_instance = IBMStyleMapping()
    return _mapping_instance


def get_rule_mapping(rule_id: str, category: str = None) -> Optional[Dict[str, Any]]:
    """Get mapping for a specific rule."""
    return get_mapping_instance().get_rule_mapping(rule_id, category)


def format_citation(rule_id: str, category: str = None,
                   include_verification: bool = True) -> str:
    """Format citation string for display."""
    return get_mapping_instance().format_citation(rule_id, category, include_verification)


def get_confidence_adjustment(rule_id: str, category: str = None) -> float:
    """Get confidence adjustment for a rule."""
    return get_mapping_instance().get_confidence_adjustment(rule_id, category)


def get_verification_status(rule_id: str, category: str = None) -> Dict[str, Any]:
    """Get verification status for a rule."""
    return get_mapping_instance().get_verification_status(rule_id, category)


def get_all_unverified_rules() -> List[Dict[str, Any]]:
    """Get list of all unverified rules."""
    return get_mapping_instance().get_all_unverified_rules()


def get_verification_stats() -> Dict[str, Any]:
    """Get overall verification statistics."""
    return get_mapping_instance().get_verification_stats()


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_citation(rule_id: str, proposed_pages: List[int],
                     category: str = None) -> Dict[str, Any]:
    """
    Validate a proposed citation before adding to mapping.

    Args:
        rule_id: Rule identifier
        proposed_pages: List of proposed page numbers
        category: Rule category

    Returns:
        Validation result dict
    """
    mapping = get_rule_mapping(rule_id, category)

    if not mapping:
        return {
            'valid': False,
            'reason': f"Rule '{rule_id}' not found in mapping"
        }

    ibm_style = mapping.get('ibm_style', {})
    current_pages = ibm_style.get('pages', [])
    current_status = ibm_style.get('verification_status', 'unverified')

    # If already verified with different pages, warn
    if current_status == 'verified' and current_pages and current_pages != proposed_pages:
        return {
            'valid': False,
            'reason': f"Rule already verified with different pages: {current_pages}",
            'action': 'needs_review'
        }

    return {
        'valid': True,
        'current_pages': current_pages,
        'proposed_pages': proposed_pages,
        'current_status': current_status,
        'action': 'can_update'
    }


def check_for_hallucinations(error_messages: List[str]) -> List[Dict[str, Any]]:
    """
    Check error messages for hallucinated page numbers.

    Args:
        error_messages: List of error message strings

    Returns:
        List of potential hallucinations
    """
    import re

    hallucinations = []
    page_pattern = re.compile(r'Pages?\s+(\d+(?:[-,]\s*\d+)*)', re.IGNORECASE)

    for message in error_messages:
        matches = page_pattern.findall(message)
        for match in matches:
            # Extract page numbers
            pages = [int(p.strip()) for p in re.findall(r'\d+', match)]

            # Check if these pages are verified
            # (This is a simplified check - would need rule context in practice)
            hallucinations.append({
                'message': message,
                'cited_pages': pages,
                'warning': 'Verify these page numbers in IBM Style Guide PDF'
            })

    return hallucinations
