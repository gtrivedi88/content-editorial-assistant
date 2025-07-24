"""
Dashes Rule
Based on IBM Style Guide topic: "Dashes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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
        if not nlp:
            return errors
            
        doc = nlp(text)
        # The IBM Style Guide is direct: "Do not use em dashes in technical information."
        # No complex morphological analysis is needed because the character itself is the violation.
        for i, sent in enumerate(doc.sents):
            # Check for the em dash character (U+2014)
            for match in re.finditer(r'—', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid em dashes (—) in technical writing.",
                    suggestions=["Rewrite the sentence using commas, parentheses, or a colon instead."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors
