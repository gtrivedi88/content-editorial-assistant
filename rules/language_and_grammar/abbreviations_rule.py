"""
Abbreviations Rule
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AbbreviationsRule(BaseLanguageRule):
    """
    Checks for the use of Latin abbreviations and ensures that abbreviations
    are defined on first use.
    """
    def _get_rule_type(self) -> str:
        return 'abbreviations'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: Discouraged Latin abbreviations and their replacements.
        latin_abbreviations = {
            r'\be\.g\.': 'for example',
            r'\bi\.e\.': 'that is',
            r'\betc\.': 'and so on',
        }

        for i, sentence in enumerate(sentences):
            for pattern, replacement in latin_abbreviations.items():
                if re.search(pattern, sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid using the Latin abbreviation '{pattern.replace(r'\\b', '')}'.",
                        suggestions=[f"Use its English equivalent, such as '{replacement}'."],
                        severity='medium'
                    ))
        return errors
