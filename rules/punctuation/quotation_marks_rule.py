"""
Quotation Marks Rule
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for incorrect placement of punctuation with quotation marks.
    """
    def _get_rule_type(self) -> str:
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Rule: In US English, periods and commas go inside the closing quote.
                # This check looks for the opposite, which is a common error.
                if token.text == '"' and token.i < len(doc) - 1:
                    next_token = doc[token.i + 1]
                    if next_token.text in {'.', ','}:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Punctuation placement with quotation mark may be incorrect for US English style.",
                            suggestions=[f"Consider moving the '{next_token.text}' inside the closing quotation mark."],
                            severity='low'
                        ))
        return errors
