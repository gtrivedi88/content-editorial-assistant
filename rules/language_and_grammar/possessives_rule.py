"""
Possessives Rule
Based on IBM Style Guide topic: "Possessives"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PossessivesRule(BaseLanguageRule):
    """
    Checks for incorrect use of possessives, specifically flagging the use
    of apostrophe-s with uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        return 'possessives'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect possessive constructions with abbreviations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == "'s":
                    if token.i > 0:
                        prev_token = doc[token.i - 1]
                        is_abbreviation = prev_token.is_upper and len(prev_token.text) > 1

                        if is_abbreviation:
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=f"Avoid using the possessive ''s' with the abbreviation '{prev_token.text}'.",
                                suggestions=[f"Rewrite the phrase to use a preposition. For example, instead of '{prev_token.text}'s properties', write 'the properties of {prev_token.text}'."],
                                severity='medium',
                                text=text,  # Enhanced: Pass full text for better confidence analysis
                                context=context,  # Enhanced: Pass context for domain-specific validation
                                span=(prev_token.idx, token.idx + len(token.text)),
                                flagged_text=f"{prev_token.text}{token.text}"
                            ))
        return errors
