"""
Dashes Rule
Based on IBM Style Guide topic: "Dashes"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class DashesRule(BasePunctuationRule):
    """
    Checks for the use of em dashes, which are discouraged in technical info
    by the IBM Style Guide. The rule flags the character for replacement.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'dashes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of em dashes.
        """
        errors = []
        # The IBM Style Guide is direct: "Do not use em dashes in technical information."
        # Therefore, a simple and robust check for the character is sufficient and accurate.
        # No complex morphological analysis is needed because the character itself is the violation.
        for i, sentence in enumerate(sentences):
            if '—' in sentence: # Check for the em dash character (U+2014)
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid em dashes (—) in technical writing.",
                    suggestions=["Rewrite the sentence using commas, parentheses, or a colon instead."],
                    severity='medium'
                ))
        return errors