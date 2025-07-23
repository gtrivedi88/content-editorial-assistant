"""
Inclusive Language Rule
Based on IBM Style Guide topic: "Inclusive language"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class InclusiveLanguageRule(BaseLanguageRule):
    """
    Checks for non-inclusive terms and suggests modern, neutral alternatives
    as specified by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        return 'inclusive_language'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for specific non-inclusive terms.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        non_inclusive_terms = {
            "whitelist": "allowlist",
            "blacklist": "blocklist",
            "master": "primary, main, or controller",
            "slave": "secondary, replica, or agent",
            "man-hours": "person-hours or work-hours",
            "man hours": "person-hours or work-hours",
            "manned": "staffed, operated, or crewed",
            "sanity check": "coherence check, confirmation, or validation",
        }

        for i, sent in enumerate(doc.sents):
            for term, replacement in non_inclusive_terms.items():
                for match in re.finditer(r'\b' + re.escape(term) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Consider replacing the non-inclusive term '{match.group()}'.",
                        suggestions=[f"Use a more inclusive alternative, such as '{replacement}'."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
