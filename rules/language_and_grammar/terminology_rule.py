"""
Terminology Rule
Based on IBM Style Guide topic: "Terminology"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class TerminologyRule(BaseLanguageRule):
    """
    Checks for use of non-preferred or incorrect terminology.
    """
    def _get_rule_type(self) -> str:
        return 'terminology'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: A dictionary of non-preferred terms and their replacements.
        # This can be greatly expanded.
        term_map = {
            "info center": "IBM Documentation",
            "infocenter": "IBM Documentation",
            "dialog box": "dialog",
            "un-install": "uninstall",
            "de-install": "uninstall",
        }

        for i, sentence in enumerate(sentences):
            for term, replacement in term_map.items():
                if f" {term} " in f" {sentence.lower()} ":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Non-preferred term '{term}' used.",
                        suggestions=[f"Use the preferred IBM term: '{replacement}'."],
                        severity='medium'
                    ))
        return errors
