"""
Ambiguity Rule - Main integration point with the existing rules system.

This rule provides the entry point for ambiguity detection and integrates
seamlessly with the existing IBM Style Guide rules system.
"""

import os
import sys

# Add the parent directory to the path to import ambiguity package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ambiguity.base_ambiguity_rule import BaseAmbiguityRule


class AmbiguityRule(BaseAmbiguityRule):
    """
    Main ambiguity detection rule that integrates with the existing rules system.
    
    This rule will be discovered by the rules registry and applied alongside
    other IBM Style Guide rules to detect ambiguous content.
    """
    
    def __init__(self):
        super().__init__()
    
    def _get_rule_type(self) -> str:
        """Return the rule type identifier for the rules system."""
        return 'ambiguity' 