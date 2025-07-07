"""
Punctuation and Symbols Rule
Based on IBM Style Guide topic: "Punctuation and symbols"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class PunctuationAndSymbolsRule(BasePunctuationRule):
    """
    Checks for the use of symbols instead of words in general text, using
    dependency parsing to avoid flagging symbols in proper names or code.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_and_symbols'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for discouraged symbols in general text.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing for context.
            return errors
        
        # Linguistic Anchor: Symbols that should be spelled out in general text.
        discouraged_symbols = {'&', '+'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text in discouraged_symbols:
                    
                    # --- Context-Aware Check ---
                    # To avoid false positives, we check if the symbol is part of a
                    # larger entity that is likely a proper name or code. We do this
                    # by checking the part-of-speech of the symbol's ancestors in
                    # the dependency tree.
                    is_part_of_proper_name_or_code = any(
                        ancestor.pos_ in ("PROPN", "X", "SYM") for ancestor in token.ancestors
                    )
                    
                    if not is_part_of_proper_name_or_code:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid using the symbol '{token.text}' in general text.",
                            suggestions=[f"Replace '{token.text}' with 'and'."] if token.text in '&+' else [],
                            severity='medium'
                        ))
        return errors
