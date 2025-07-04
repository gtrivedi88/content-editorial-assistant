"""
Spelling Rule
Based on IBM Style Guide topic: "Spelling"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class SpellingRule(BaseLanguageRule):
    """
    Checks for common non-US spellings and suggests the preferred US spelling.
    """
    def _get_rule_type(self) -> str:
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: A dictionary of UK/International vs. US spellings.
        spelling_map = {
            "centre": "center",
            "colour": "color",
            "flavour": "flavor",
            "licence": "license",
            "organise": "organize",
            "analyse": "analyze",
            "catalogue": "catalog",
        }

        for i, sentence in enumerate(sentences):
            for non_us, us_spelling in spelling_map.items():
                if f" {non_us} " in f" {sentence.lower()} ":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Non-US spelling '{non_us}' used.",
                        suggestions=[f"IBM Style prefers US spelling. Use '{us_spelling}' instead."],
                        severity='medium'
                    ))
        return errors
