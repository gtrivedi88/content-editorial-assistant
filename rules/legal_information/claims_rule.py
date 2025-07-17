"""
Claims and Recommendations Rule
Based on IBM Style Guide topic: "Claims and recommendations"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

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
        # Linguistic Anchor: A list of words that make subjective or absolute claims.
        claim_words = {
            "secure", "easy", "effortless", "best practice", "future-proof"
        }

        for i, sentence in enumerate(sentences):
            # Using regex to find whole words, case-insensitive
            for word in claim_words:
                if re.search(r'\b' + word + r'\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"The term '{word}' makes a subjective or unsupported claim that should be avoided.",
                        suggestions=["Replace with a more descriptive and objective statement. For example, instead of 'secure', use 'security-enhanced'."],
                        severity='high'
                    ))
        return errors
