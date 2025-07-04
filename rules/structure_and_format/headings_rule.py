"""
Headings Rule
Based on IBM Style Guide topic: "Headings"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class HeadingsRule(BaseStructureRule):
    """
    Checks for common style issues in headings, such as incorrect
    capitalization and ending punctuation.
    """
    def _get_rule_type(self) -> str:
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Context-aware analysis: Only analyze if we know this is a heading
        if not context or context.get('block_type') != 'heading':
            return errors  # Skip analysis if not a heading block
            
        # Now we know this is definitely a heading, so we can apply heading rules with confidence
        heading_text = text.strip()
        
        # Rule: Headings should not end with a period.
        if heading_text.endswith('.'):
            errors.append(self._create_error(
                sentence=heading_text,
                sentence_index=0,
                message="Headings should not end with a period.",
                suggestions=["Remove the period from the end of the heading."],
                severity='medium'
            ))

        # Rule: Use sentence-style capitalization, not headline-style.
        words = heading_text.split()
        if len(words) > 2: # Ignore very short headings
            title_cased_words = [word for word in words[1:] if word.istitle()]
            # Check if more than a third of words (excluding the first) are capitalized
            if len(title_cased_words) > len(words) / 3:
                 errors.append(self._create_error(
                    sentence=heading_text,
                    sentence_index=0,
                    message="Headings should use sentence-style capitalization.",
                    suggestions=["Capitalize only the first word and proper nouns in the heading."],
                    severity='low'
                ))
        return errors
