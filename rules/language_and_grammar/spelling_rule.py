"""
Spelling Rule
Based on IBM Style Guide topic: "Spelling"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

class SpellingRule(BaseLanguageRule):
    """
    Checks for common non-US spellings and suggests the preferred US spelling,
    as required by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for common non-US English spellings.
        """
        errors = []
        
        # Linguistic Anchor: A dictionary mapping common non-US spellings
        # to their preferred US English equivalents.
        spelling_map = {
            "centre": "center",
            "colour": "color",
            "flavour": "flavor",
            "licence": "license",
            "organise": "organize",
            "analyse": "analyze",
            "catalogue": "catalog",
            "dialogue": "dialog",
            "grey": "gray",
            "behaviour": "behavior",
            "programme": "program",
        }

        for i, sentence in enumerate(sentences):
            # We check the lowercase version of the sentence for a broader match.
            sentence_lower = sentence.lower()
            for non_us, us_spelling in spelling_map.items():
                # Use regex with word boundaries (\b) to ensure we match whole words only.
                # This prevents flagging "analysed" within "paralysed", for example.
                pattern = r'\b' + re.escape(non_us) + r'\b'
                if re.search(pattern, sentence_lower):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Non-US spelling used for '{non_us}'.",
                        suggestions=[f"IBM Style prefers US spelling. Use '{us_spelling}' instead."],
                        severity='medium'
                    ))
        return errors
