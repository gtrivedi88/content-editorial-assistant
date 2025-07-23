"""
Web, IP, and Email Addresses Rule
Based on IBM Style Guide topic: "Web, IP, and email addresses"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WebAddressesRule(BaseTechnicalRule):
    """
    Checks for common formatting errors in web addresses, such as trailing slashes.
    """
    def _get_rule_type(self) -> str:
        return 'technical_web_addresses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for web address formatting violations.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Regex to find URLs ending with a slash that are not just the base domain
        trailing_slash_pattern = re.compile(r'https?://[^\s/]+/[^\s]*?/')

        for i, sent in enumerate(doc.sents):
            for match in trailing_slash_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=f"Web address '{match.group()}' should not end with a forward slash.",
                    suggestions=["Remove the trailing slash from the URL."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors
