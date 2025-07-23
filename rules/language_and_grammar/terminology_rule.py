"""
Terminology Rule
Based on IBM Style Guide topic: "Terminology" and "Word usage"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TerminologyRule(BaseLanguageRule):
    """
    Checks for the use of non-preferred or outdated terminology and suggests
    the correct IBM-approved terms.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'terminology'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for non-preferred terminology.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        term_map = {
            "info center": "IBM Documentation", "infocenter": "IBM Documentation",
            "knowledge center": "IBM Documentation", "dialog box": "dialog",
            "un-install": "uninstall", "de-install": "uninstall",
            "e-mail": "email", "end user": "user", "log on to": "log in to",
            "logon": "log in", "web site": "website", "work station": "workstation",
        }

        for i, sent in enumerate(doc.sents):
            for term, replacement in term_map.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Non-preferred term '{match.group()}' used.",
                        suggestions=[f"Use the preferred IBM term: '{replacement}'."],
                        severity='medium',
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
