"""
Ambiguity Rule - Main integration point with the existing rules system.

This rule provides the entry point for ambiguity detection and integrates
seamlessly with the existing IBM Style Guide rules system.
"""

from .base_ambiguity_rule import BaseAmbiguityRule


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