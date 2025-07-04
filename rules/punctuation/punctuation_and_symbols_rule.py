"""
Quotation Marks Rule
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for incorrect placement of punctuation with quotation marks,
    specifically for periods and commas placed outside the closing quote,
    which is contrary to standard US English style.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect punctuation placement after a
        closing quotation mark.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization to identify punctuation order.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The rule triggers when a closing quotation mark is found.
                # The IBM Style Guide follows US English conventions.
                if token.text == '"' and token.i < len(doc) - 1:
                    
                    # --- Context-Aware Check ---
                    # The context is the token immediately following the quote.
                    next_token = doc[token.i + 1]
                    
                    # Linguistic Anchor: The error pattern is a closing quote
                    # followed immediately by a period or comma.
                    if next_token.text in {'.', ','}:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Punctuation placement with quotation mark may be incorrect for US English style.",
                            suggestions=[f"Consider moving the '{next_token.text}' to be inside the closing quotation mark."],
                            severity='low'
                        ))
        return errors