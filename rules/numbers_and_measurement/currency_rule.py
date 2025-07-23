"""
Currency Rule
Based on IBM Style Guide topic: "Currency"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CurrencyRule(BaseNumbersRule):
    """
    Checks for correct currency formatting, including the use of ISO codes
    and the avoidance of letter abbreviations for multipliers like 'M' for million.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_currency'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for currency formatting errors.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Pattern to find currency symbols or multipliers.
        # Group 1: Catches symbols like $100
        # Group 2: Catches multipliers like 4M or $4M
        currency_pattern = re.compile(r'([\$€£]\s?\d[\d,.]*)|(\d[\d,.]*\s?[MK])\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in currency_pattern.finditer(sent.text):
                flagged_text = match.group(0)
                
                # Check for symbol usage
                if any(c in flagged_text for c in "$€£"):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message="For international audiences, use the three-letter ISO currency code before the amount.",
                        suggestions=["Replace currency symbols like '$' with ISO codes like 'USD '."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=flagged_text
                    ))
                
                # Check for multiplier usage
                if any(c in flagged_text.upper() for c in "MK"):
                     errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Do not use letter abbreviations like '{flagged_text}' for currency multipliers.",
                        suggestions=["Spell out the full number (e.g., 'USD 4 million' or 'USD 4,000,000')."],
                        severity='high',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=flagged_text
                    ))
        return errors
