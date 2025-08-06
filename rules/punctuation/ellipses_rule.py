"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class EllipsesRule(BasePunctuationRule):
    """
    Checks for the use of ellipses, which should be avoided in general text
    according to the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of ellipses.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        # The IBM Style Guide is direct: "Avoid using ellipses in text in most cases."
        # Check for both three consecutive dots and Unicode ellipsis character
        for i, sent in enumerate(doc.sents):
            # LINGUISTIC ANCHOR 1: Three consecutive dots pattern
            for match in re.finditer(r'\.\.\.', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using ellipses (...) in technical writing.",
                    suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
                    severity='low',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
            
            # LINGUISTIC ANCHOR 2: Unicode ellipsis character (U+2026)
            for match in re.finditer(r'…', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using ellipses (…) in technical writing.",
                    suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
                    severity='low',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors
