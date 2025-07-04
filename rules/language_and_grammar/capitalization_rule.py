"""
Capitalization Rule (Context-Aware)
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for capitalization issues in general text, but is now context-aware
    and will ignore blocks that are identified as headings to prevent
    redundant errors with the more specific headings_rule.py.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for capitalization issues, skipping heading blocks.
        """
        errors = []
        
        # --- Context-Aware Check ---
        # If the context indicates this block is a heading, we skip this rule
        # entirely to let the more specific headings_rule.py handle it.
        if context and context.get('block_type') == 'heading':
            return errors

        # If it's not a heading, proceed with general capitalization checks.
        for i, sentence in enumerate(sentences):
            # This is a placeholder for any general capitalization logic you might add
            # for paragraphs or other text blocks in the future.
            pass
            
        return errors
