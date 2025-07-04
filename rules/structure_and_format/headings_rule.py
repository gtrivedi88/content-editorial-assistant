"""
Headings Rule (Consolidated)
Based on IBM Style Guide topic: "Headings"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class HeadingsRule(BaseStructureRule):
    """
    Checks for all common style issues in headings. This consolidated
    version combines checks to prevent redundant error messages.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a heading for multiple style violations.
        """
        errors = []
        for i, sentence in enumerate(sentences):
            
            # Rule 1: Headings should not end with a period.
            if sentence.strip().endswith('.'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Headings should not end with a period.",
                    suggestions=["Remove the period from the end of the heading."],
                    severity='medium'
                ))

            # Rule 2: Use sentence-style capitalization (consolidated check).
            words = sentence.split()
            if len(words) > 2:
                # Heuristic: If more than a third of words (excluding the first) are capitalized,
                # it might be incorrect headline style.
                title_cased_words = [word for word in words[1:] if word.istitle() and not word.isupper()]
                if len(title_cased_words) > len(words) / 3:
                     errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Headings should use sentence-style capitalization, not headline-style.",
                        suggestions=["Capitalize only the first word and proper nouns in the heading."],
                        severity='low'
                    ))
        return errors