"""
Inclusive Language Rule
Based on IBM Style Guide topic: "Inclusive language"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class InclusiveLanguageRule(BaseLanguageRule):
    """
    Checks for non-inclusive terms and suggests alternatives.
    """
    def _get_rule_type(self) -> str:
        return 'inclusive_language'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: A dictionary of non-inclusive terms and their preferred replacements.
        non_inclusive_terms = {
            "whitelist": "allowlist",
            "blacklist": "blocklist",
            "master": "primary or controller",
            "slave": "secondary or replica",
            "man-hours": "person-hours or labor-hours",
            "man hours": "person-hours or labor-hours",
            "manned": "staffed or operated",
        }

        for i, sentence in enumerate(sentences):
            for term, replacement in non_inclusive_terms.items():
                if f" {term} " in f" {sentence.lower()} ":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Consider replacing the non-inclusive term '{term}'.",
                        suggestions=[f"Use a more inclusive alternative, such as '{replacement}'."],
                        severity='medium'
                    ))
        return errors
