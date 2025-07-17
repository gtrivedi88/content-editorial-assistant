"""
Currency Rule
Based on IBM Style Guide topic: "Currency"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

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
        # Regex to find a number followed by a currency multiplier like M, K, B
        # and not followed by a standard unit like MHz, KB, etc.
        multiplier_pattern = re.compile(r'\b\d+\s?[MK]\b(?!\w)')

        for i, sentence in enumerate(sentences):
            # Check for incorrect multiplier abbreviations (e.g., "$4M")
            matches = multiplier_pattern.finditer(sentence)
            for match in matches:
                # Linguistic Anchor: Avoid flagging valid technical units like "4 MB".
                # This simple regex looks for multipliers standing alone.
                if "USD" in sentence or "CAD" in sentence or "EUR" in sentence or "£" in sentence or "$" in sentence:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Do not use letter abbreviations like '{match.group()}' for currency multipliers.",
                        suggestions=["Spell out the full number (e.g., 'USD 4 million' or 'USD 4,000,000')."],
                        severity='high'
                    ))

            # Check for currency symbol before the number instead of ISO code
            if re.search(r'[\$€£]\s?\d', sentence):
                 errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="For international audiences, use the three-letter ISO currency code before the amount.",
                    suggestions=["Replace currency symbols like '$' with ISO codes like 'USD '."],
                    severity='medium'
                ))
        return errors
