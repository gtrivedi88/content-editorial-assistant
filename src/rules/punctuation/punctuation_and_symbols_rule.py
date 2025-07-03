"""
Punctuation and Symbols Rule
Based on IBM Style Guide topic: "Punctuation and symbols"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class PunctuationAndSymbolsRule(BasePunctuationRule):
    """
    Checks for the use of symbols instead of words in general text.
    """
    def _get_rule_type(self) -> str:
        return 'punctuation_and_symbols'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        # Linguistic Anchor: Symbols that should be words in general text.
        discouraged_symbols = {'&', '+'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text in discouraged_symbols:
                    # Avoid flagging symbols in code or technical names
                    if token.head.pos_ not in ("PROPN", "X"):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid using the symbol '{token.text}' in general text.",
                            suggestions=[f"Replace '{token.text}' with the word 'and'."] if token.text in '&+' else [],
                            severity='medium'
                        ))
        return errors
