"""
Punctuation and Symbols Rule
Based on IBM Style Guide topic: "Punctuation and symbols"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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
            return errors
        
        doc = nlp(text)
        # Linguistic Anchor: Symbols that should be spelled out in general text.
        discouraged_symbols = {'&', '+'}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text in discouraged_symbols:
                    # Context-Aware Check: Avoid false positives in proper names or code.
                    is_part_of_proper_name_or_code = any(
                        ancestor.pos_ in ("PROPN", "X", "SYM") for ancestor in token.ancestors
                    )
                    
                    if not is_part_of_proper_name_or_code:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Avoid using the symbol '{token.text}' in general text.",
                            suggestions=[f"Replace '{token.text}' with 'and'."] if token.text in '&+' else [],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors
