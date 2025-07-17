"""
Personal Information Rule
Based on IBM Style Guide topic: "Personal information"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule
import re

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
        # Linguistic Anchor: A mapping of discouraged terms to preferred terms.
        name_terms = {
            "first name": "given name",
            "christian name": "given name",
            "last name": "surname"
        }

        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            for bad_term, good_term in name_terms.items():
                if bad_term in sentence_lower:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid using the term '{bad_term}'. Use a more globally understood term.",
                        suggestions=[f"Replace '{bad_term}' with '{good_term}'."],
                        severity='medium'
                    ))
        return errors
