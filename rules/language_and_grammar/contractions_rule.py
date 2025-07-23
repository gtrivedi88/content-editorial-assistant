"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ContractionsRule(BaseLanguageRule):
    """
    Checks for the use of contractions, which are generally discouraged
    in formal technical documentation for a more professional tone.
    """
    def _get_rule_type(self) -> str:
        return 'contractions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        contraction_pattern = re.compile(r"\b(n't|'re|'s|'ll|'d|'ve)\b", re.IGNORECASE)
        
        for i, sent in enumerate(doc.sents):
            for match in contraction_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=f"Contraction found: '{match.group()}'.",
                    suggestions=["Expand contractions for a more formal tone (e.g., 'isn't' becomes 'is not')."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors
