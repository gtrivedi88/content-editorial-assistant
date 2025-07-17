"""
References package - Enhanced with pure SpaCy morphological analysis
All rules now use advanced linguistic anchors and context-aware detection.
"""

from .base_references_rule import BaseReferencesRule
from .product_versions_rule import ProductVersionsRule
from .product_names_rule import ProductNamesRule
from .names_and_titles_rule import NamesAndTitlesRule
from .geographic_locations_rule import GeographicLocationsRule
from .citations_rule import CitationsRule

__all__ = [
    'BaseReferencesRule',
    'ProductVersionsRule',
    'ProductNamesRule', 
    'NamesAndTitlesRule',
    'GeographicLocationsRule',
    'CitationsRule'
]
