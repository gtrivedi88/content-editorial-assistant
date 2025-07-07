"""
Highlighting Rule (Placeholder)
Based on IBM Style Guide topic: "Highlighting"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class HighlightingRule(BaseStructureRule):
    """
    Placeholder for highlighting rules. This rule cannot be implemented
    reliably on plain text and requires access to the source markup
    (e.g., Markdown, AsciiDoc, HTML) to be effective.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'highlighting'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        This rule is a placeholder and does not perform analysis.

        Reasoning:
        Analyzing highlighting (bold, italics, monospace) requires parsing the
        source markup of the document, not just the raw text. A text-only
        analysis cannot reliably determine if a word was, for example,
        enclosed in asterisks for bolding (**word**) or just the word itself.
        Attempting to guess would lead to a high number of false positives.

        A robust implementation would require a pre-processing step where the
        source document (e.g., a Markdown file) is parsed into a structure
        that preserves both the text and its formatting tags.
        """
        return []
