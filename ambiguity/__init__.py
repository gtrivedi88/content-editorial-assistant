"""
Ambiguity Detection Package

This package provides comprehensive ambiguity detection for technical writing,
integrating with the existing rules system to identify unclear or ambiguous content.
"""

from .types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity, 
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig, AmbiguityPattern
)

from .base_ambiguity_rule import BaseAmbiguityRule, AmbiguityDetector

# Main rule class for integration with rules system
AmbiguityRule = BaseAmbiguityRule

__all__ = [
    'AmbiguityType', 'AmbiguityCategory', 'AmbiguitySeverity',
    'AmbiguityContext', 'AmbiguityEvidence', 'AmbiguityDetection',
    'ResolutionStrategy', 'AmbiguityConfig', 'AmbiguityPattern',
    'BaseAmbiguityRule', 'AmbiguityDetector', 'AmbiguityRule'
] 