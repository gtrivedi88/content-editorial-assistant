"""
Conversational Style Rule
Based on IBM Style Guide topic: "Conversational style"
"""
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ConversationalStyleRule(BaseAudienceRule):
    """
    Checks for language that is overly formal or complex, hindering a
    conversational style. It suggests simpler alternatives for common
    complex words.
    """
    def _get_rule_type(self) -> str:
        return 'audience_conversational'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)

        # Linguistic Anchor: A mapping of complex words to simpler, preferred alternatives.
        complex_word_map = {
            "utilize": "use",
            "facilitate": "help",
            "commence": "start",
            "terminate": "end",
            "demonstrate": "show",
            "implement": "do or set up"
        }

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_.lower() in complex_word_map:
                    complex_word = token.text
                    suggestion = complex_word_map[token.lemma_.lower()]
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"The word '{complex_word}' is too formal. Use a simpler alternative for a conversational tone.",
                        suggestions=[f"Replace '{complex_word}' with '{suggestion}'."],
                        severity='low',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors
