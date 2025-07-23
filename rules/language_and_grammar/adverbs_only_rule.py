"""
Adverbs - only Rule
Based on IBM Style Guide topic: "Adverbs - only"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class AdverbsOnlyRule(BaseLanguageRule):
    """
    Checks for the word "only" and advises the user to review its placement
    to ensure the meaning of the sentence is clear and unambiguous.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'adverbs_only'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of the word "only".
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_ == 'only':
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message="The word 'only' can be ambiguous depending on its placement.",
                        suggestions=["To ensure clarity, review the sentence and place 'only' immediately before the word or phrase it is intended to modify."],
                        severity='low',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors
