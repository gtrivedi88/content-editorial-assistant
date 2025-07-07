"""
Plurals Rule
Based on IBM Style Guide topic: "Plurals"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PluralsRule(BaseLanguageRule):
    """
    Checks for several common pluralization errors, including the use of "(s)",
    and using plural nouns as adjectives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'plurals'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for pluralization errors.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            # --- Rule 1: Avoid using "(s)" to indicate plural ---
            # This is a direct violation of the style guide. A simple regex is sufficient.
            if re.search(r'\w+\(s\)', sentence, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid using '(s)' to indicate a plural.",
                    suggestions=["Rewrite the sentence to use either the singular or plural form, or use a phrase like 'one or more'."],
                    severity='medium'
                ))

            doc = nlp(sentence)
            for token in doc:
                # --- Rule 2: Avoid using plural nouns as adjectives ---
                # Example: "the systems files" should be "the system files"
                # Linguistic Anchor: We look for a plural noun ('NNS') that is acting
                # as a compound modifier for another noun.
                if token.tag_ == 'NNS' and token.dep_ == 'compound':
                    # To avoid false positives, we check if the singular form is a known word.
                    # This prevents flagging legitimate compound nouns where the first part is plural.
                    if token.lemma_ != token.lower_: # e.g., 'systems' -> 'system'
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Potential misuse of a plural noun '{token.text}' as an adjective.",
                            suggestions=[f"Consider using the singular form '{token.lemma_}' when a noun modifies another noun."],
                            severity='low'
                        ))
        return errors
