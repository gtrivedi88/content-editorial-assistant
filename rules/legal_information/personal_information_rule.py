"""
Personal Information Rule
Based on IBM Style Guide topic: "Personal information"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PersonalInformationRule(BaseLegalRule):
    """
    Checks for the use of culturally specific terms like "first name" or
    "last name" and suggests more global alternatives.
    """
    def _get_rule_type(self) -> str:
        return 'legal_personal_information'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for incorrect terminology for personal names.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Linguistic Anchor: A mapping of discouraged terms to preferred terms.
        name_terms = {
            "first name": "given name",
            "christian name": "given name",
            "last name": "surname"
        }

        for i, sent in enumerate(doc.sents):
            for bad_term, good_term in name_terms.items():
                for match in re.finditer(r'\b' + re.escape(bad_term) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Avoid using the term '{match.group()}'. Use a more globally understood term.",
                        suggestions=[f"Replace '{match.group()}' with '{good_term}'."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
