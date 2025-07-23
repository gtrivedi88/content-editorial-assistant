"""
Capitalization Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for incorrect capitalization, specifically focusing on the
    over-capitalization of common nouns within a sentence.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for unnecessary capitalization of common nouns.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                is_common_noun = token.pos_ == 'NOUN' and token.tag_ == 'NN'
                is_capitalized = token.is_title
                is_not_first_word = token.i > sent.start

                if is_common_noun and is_capitalized and is_not_first_word:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Unnecessary capitalization of the common noun '{token.text}'.",
                        suggestions=["Common nouns should be lowercase unless they are part of a proper name or at the beginning of a sentence."],
                        severity='low',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors
