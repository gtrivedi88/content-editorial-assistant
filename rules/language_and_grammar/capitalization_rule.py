"""
Capitalization Rule
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for capitalization issues, such as using headline-style instead
    of the preferred sentence-style capitalization.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        # This is a simplified check. A full capitalization rule is very complex.
        # We check for titles/headings with too many capitalized words.
        for i, sentence in enumerate(sentences):
            # Heuristic: If a short sentence (likely a heading) has many title-cased words, flag it.
            words = sentence.split()
            if 3 < len(words) < 10:
                title_cased_words = [word for word in words if word.istitle()]
                # If more than half the words are title-cased, it might be incorrect headline style.
                if len(title_cased_words) > len(words) / 2:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Potential incorrect headline-style capitalization.",
                        suggestions=["Use sentence-style capitalization for headings and titles (capitalize only the first word and proper nouns)."],
                        severity='low'
                    ))
        return errors
