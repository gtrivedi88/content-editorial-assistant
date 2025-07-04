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

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        # This rule assumes that each "sentence" passed to it is a potential heading.
        # A more advanced system would need metadata to know if a line is a heading.
        for i, sentence in enumerate(sentences):
            # Rule: Headings should not end with a period.
            if sentence.strip().endswith('.'):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Headings should not end with a period.",
                    suggestions=["Remove the period from the end of the heading."],
                    severity='medium'
                ))

            # Rule: Use sentence-style capitalization, not headline-style.
            words = sentence.split()
            if len(words) > 2: # Ignore very short headings
                title_cased_words = [word for word in words[1:] if word.istitle()]
                # Heuristic: If more than a third of words (excluding the first) are capitalized,
                # it might be incorrect headline style.
                if len(title_cased_words) > len(words) / 3:
                     errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Headings should use sentence-style capitalization.",
                        suggestions=["Capitalize only the first word and proper nouns in the heading."],
                        severity='low'
                    ))
        return errors
