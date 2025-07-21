"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
import re

class ContractionsRule(BaseLanguageRule):
    """
    Checks for the use of contractions, which are generally discouraged
    in formal technical documentation for a more professional tone.
    """
    def _get_rule_type(self) -> str:
        return 'contractions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        # A regex pattern to find common English contractions.
        contraction_pattern = re.compile(r"\b(n't|'re|'s|'ll|'d|'ve)\b", re.IGNORECASE)
        
        for i, sentence in enumerate(sentences):
            for match in contraction_pattern.finditer(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=f"Contraction found: '{match.group()}'.",
                    suggestions=["Expand contractions for a more formal tone (e.g., 'isn't' becomes 'is not')."],
                    severity='low',
                    span=match.span(),
                    flagged_text=match.group(0)
                ))
        return errors
