"""
References Rules Package

Deterministic rules based on the IBM Style Guide (p. 217-234).
Covers citations, geographic locations, names/titles, product names,
and product versions.
"""

from .base_references_rule import BaseReferencesRule
from .citations_rule import CitationsRule
from .geographic_locations_rule import GeographicLocationsRule
from .names_and_titles_rule import NamesAndTitlesRule
from .product_names_rule import ProductNamesRule
from .product_versions_rule import ProductVersionsRule

__all__ = [
    'BaseReferencesRule',
    'CitationsRule',
    'GeographicLocationsRule',
    'NamesAndTitlesRule',
    'ProductNamesRule',
    'ProductVersionsRule',
]
