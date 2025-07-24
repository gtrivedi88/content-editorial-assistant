"""
Quotation Marks Rule (Enhanced)
Based on IBM Style Guide topic: "Quotation marks"
"""
from typing import List, Dict, Any
import re
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class QuotationMarksRule(BasePunctuationRule):
    """
    Checks for multiple quotation mark issues, including incorrect placement
    of punctuation and inappropriate use for emphasis.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various quotation mark violations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            errors.extend(self._check_punctuation_placement(sent, i))
            errors.extend(self._check_inappropriate_use_for_emphasis(sent, i))

        return errors

    def _check_punctuation_placement(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """Checks for incorrect placement of punctuation relative to quotes."""
        errors = []
        for token in sent:
            # Rule: In US English, periods and commas are placed inside the closing quotation mark.
            if token.text == '"' and token.i < sent.end - 1:
                next_token = sent.doc[token.i + 1]
                if next_token.text in {'.', ','}:
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=sentence_index,
                        message="Punctuation placement with quotation mark may be incorrect for US English style.",
                        suggestions=[f"In US English, periods and commas are placed inside the closing quotation mark. Consider moving the '{next_token.text}' before the closing quote."],
                        severity='low',
                        span=(token.idx, next_token.idx + len(next_token.text)),
                        flagged_text=f'{token.text}{next_token.text}'
                    ))
        return errors

    def _check_inappropriate_use_for_emphasis(self, sent: Doc, sentence_index: int) -> List[Dict[str, Any]]:
        """Checks if quotes are used for emphasis instead of italics."""
        errors = []
        # Linguistic Anchor: Find single words inside double quotes.
        for match in re.finditer(r'"(\w+)"', sent.text):
            flagged_text = match.group(0)
            word_inside = match.group(1)
            errors.append(self._create_error(
                sentence=sent.text,
                sentence_index=sentence_index,
                message=f"Quotation marks should not be used for emphasis on the word '{word_inside}'.",
                suggestions=["Use italics for emphasis, not quotation marks."],
                severity='medium',
                span=(sent.start_char + match.start(), sent.start_char + match.end()),
                flagged_text=flagged_text
            ))
        return errors
