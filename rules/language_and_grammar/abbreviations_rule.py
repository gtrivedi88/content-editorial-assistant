"""
Abbreviations Rule (Enhanced)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule

class AbbreviationsRule(BaseLanguageRule):
    """
    Checks for multiple abbreviation-related style issues, including:
    - Use of discouraged Latin abbreviations.
    - Ensuring abbreviations are defined on first use.
    - Preventing the use of abbreviations as verbs.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'abbreviations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the full text for abbreviation violations. This rule needs to
        process the entire text at once to track the first use of an abbreviation.
        """
        errors = []
        if not nlp:
            return errors

        # --- State Tracking for First Use ---
        # This set will store abbreviations that have already been defined.
        defined_abbreviations: Set[str] = set()

        # --- Full Text Analysis ---
        # We process the entire document text at once to find abbreviations.
        doc = nlp(text)

        # Find all potential abbreviations (e.g., all-caps words of 2-5 letters)
        # This regex is a linguistic anchor for common initialisms and acronyms.
        potential_abbreviations = re.findall(r'\b[A-Z]{2,5}\b', text)

        for i, token in enumerate(doc):
            # --- Rule 1: Check for Latin Abbreviations ---
            errors.extend(self._check_latin_abbreviations(doc, token, i, sentences))

            # --- Rule 2: Check for Undefined First Use ---
            if token.text in potential_abbreviations and token.text not in defined_abbreviations:
                # Check if this first use is followed by a definition in parentheses.
                if not self._is_defined(doc, i):
                    errors.append(self._create_error(
                        sentence=token.sent.text,
                        sentence_index=self._get_sentence_index(sentences, token.sent.text),
                        message=f"Abbreviation '{token.text}' may not be defined on first use.",
                        suggestions=[f"If '{token.text}' is not a commonly known abbreviation, spell it out on its first use, followed by the abbreviation in parentheses. For example: 'Application Programming Interface (API)'."],
                        severity='medium'
                    ))
                # Once an abbreviation is seen (whether defined or not), add it to the set.
                defined_abbreviations.add(token.text)
            
            # --- Rule 3: Check for Abbreviations Used as Verbs ---
            if token.is_upper and len(token.text) > 1 and token.pos_ == 'VERB':
                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=self._get_sentence_index(sentences, token.sent.text),
                    message=f"Avoid using abbreviations like '{token.text}' as verbs.",
                    suggestions=[f"Rewrite the sentence to use a proper verb. For example, instead of 'FTP the file', write 'Use FTP to send the file'."],
                    severity='medium'
                ))

        return errors

    def _check_latin_abbreviations(self, doc, token, token_index, sentences) -> List[Dict[str, Any]]:
        """Checks for discouraged Latin abbreviations like e.g. and i.e."""
        errors = []
        # Linguistic Anchor for Latin abbreviations
        latin_abbreviations = {'e.g.', 'i.e.', 'etc.'}
        replacements = {'e.g.': 'for example', 'i.e.': 'that is', 'etc.': 'and so on'}

        if token.text.lower() in latin_abbreviations:
            errors.append(self._create_error(
                sentence=token.sent.text,
                sentence_index=self._get_sentence_index(sentences, token.sent.text),
                message=f"Avoid using the Latin abbreviation '{token.text}'.",
                suggestions=[f"Use its English equivalent, such as '{replacements.get(token.text.lower())}'."],
                severity='medium'
            ))
        return errors

    def _is_defined(self, doc, token_index: int) -> bool:
        """
        Checks if an abbreviation at a given index is immediately followed
        by its spelled-out form in parentheses.
        """
        # Look ahead in the document for a pattern like: (Spelled Out Form)
        if token_index + 1 < len(doc) and doc[token_index + 1].text == '(':
            return True
        # A more complex check could look for the spelled-out form *before* the abbreviation.
        # Example: Application Programming Interface (API)
        if token_index > 0 and doc[token_index - 1].text == ')' and doc[token_index - 2].is_alpha:
            return True
            
        return False

    def _get_sentence_index(self, sentences: List[str], sentence_text: str) -> int:
        """Helper to find the index of a sentence within the list."""
        try:
            return sentences.index(sentence_text)
        except ValueError:
            return -1 # Should not happen in practice
