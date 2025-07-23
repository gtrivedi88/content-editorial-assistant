"""
Claims and Recommendations Rule
Based on IBM Style Guide topic: "Claims and recommendations"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ClaimsRule(BaseLegalRule):
    """
    Checks for unsupported claims and subjective words that could have
    legal implications, such as "secure," "easy," or "best practice."
    """
    def _get_rule_type(self) -> str:
        return 'legal_claims'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for legally problematic claims.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Linguistic Anchor: A list of words that make subjective or absolute claims.
        claim_words = {
            "secure", "easy", "effortless", "best practice", "future-proof"
        }

        for i, sent in enumerate(doc.sents):
            for word in claim_words:
                # Use re.finditer to get match objects for every occurrence
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"The term '{match.group()}' makes a subjective or unsupported claim that should be avoided.",
                        suggestions=["Replace with a more descriptive and objective statement. For example, instead of 'secure', use 'security-enhanced'."],
                        severity='high',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
