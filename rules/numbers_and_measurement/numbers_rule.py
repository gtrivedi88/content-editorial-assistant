"""
Numbers Rule
Based on IBM Style Guide topic: "Numbers"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumbersRule(BaseNumbersRule):
    """
    Checks for general number formatting issues, such as missing comma
    separators and incorrect decimal formatting.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'numbers_general'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for number formatting violations.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)

        # Linguistic Anchor: Regex to find numbers with 5 or more digits without commas.
        # This targets potential violations of the thousands separator rule.
        no_comma_pattern = re.compile(r'\b\d{5,}\b')
        
        # Linguistic Anchor: Regex to find decimals starting with a dot without a leading zero.
        leading_decimal_pattern = re.compile(r'(?<!\d)\.\d+')

        for i, sent in enumerate(doc.sents):
            # Guideline: Use a comma to separate groups of three numerals.
            for match in no_comma_pattern.finditer(sent.text):
                flagged_text = match.group(0)
                # Format the number with commas for the suggestion
                suggestion_number = f"{int(flagged_text):,}"
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Large numbers should use commas as thousands separators.",
                    suggestions=[f"Add commas to the number (e.g., '{suggestion_number}')."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=flagged_text
                ))

            # Guideline: Put a 0 in front of the decimal separator for values less than 1.
            for match in leading_decimal_pattern.finditer(sent.text):
                flagged_text = match.group(0)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Decimal values less than 1 should have a leading zero.",
                    suggestions=[f"Add a '0' before the decimal point (e.g., '0{flagged_text}')."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=flagged_text
                ))
        return errors
