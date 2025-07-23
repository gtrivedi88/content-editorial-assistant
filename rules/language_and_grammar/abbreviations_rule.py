"""
Abbreviations Rule (Enhanced)
Based on IBM Style Guide topic: "Abbreviations"
"""
import re
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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

        doc = nlp(text)
        defined_abbreviations: Set[str] = set()
        
        # --- Rule 1: Check for Latin Abbreviations ---
        latin_map = {'e.g.': 'for example', 'i.e.': 'that is', 'etc.': 'and so on'}
        for i, sent in enumerate(doc.sents):
            for term, replacement in latin_map.items():
                for match in re.finditer(r'\b' + re.escape(term) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Avoid using the Latin abbreviation '{match.group()}'.",
                        suggestions=[f"Use its English equivalent, such as '{replacement}'."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))

        # --- Rules 2 & 3: First Use Definition and Verb Usage ---
        potential_abbreviations = re.findall(r'\b[A-Z]{2,5}\b', text)
        for token in doc:
            # Check for undefined first use
            if token.text in potential_abbreviations and token.text not in defined_abbreviations:
                if not self._is_defined(doc, token.i):
                    sent = token.sent
                    sent_index = list(doc.sents).index(sent)
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sent_index,
                        message=f"Abbreviation '{token.text}' may not be defined on first use.",
                        suggestions=[f"If '{token.text}' is not a commonly known abbreviation, spell it out on its first use, followed by the abbreviation in parentheses. For example: 'Application Programming Interface (API)'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
                defined_abbreviations.add(token.text)
            
            # Check for abbreviations used as verbs
            if token.is_upper and len(token.text) > 1 and token.pos_ == 'VERB':
                sent = token.sent
                sent_index = list(doc.sents).index(sent)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sent_index,
                    message=f"Avoid using abbreviations like '{token.text}' as verbs.",
                    suggestions=[f"Rewrite the sentence to use a proper verb. For example, instead of 'FTP the file', write 'Use FTP to send the file'."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
        return errors

    def _is_defined(self, doc: Doc, token_index: int) -> bool:
        """
        Checks if an abbreviation at a given index is immediately followed
        by its spelled-out form in parentheses.
        """
        if token_index + 1 < len(doc) and doc[token_index + 1].text == '(':
            return True
        if token_index > 0 and doc[token_index - 1].text == ')' and doc[token_index - 2].is_alpha:
            return True
        return False
