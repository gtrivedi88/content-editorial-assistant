"""
Terminology Rule
Based on IBM Style Guide topic: "Terminology" and "Word usage"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

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
        
        # Linguistic Anchor: A dictionary mapping non-preferred terms to their
        # correct replacements based on the IBM Style Guide. This is the single
        # source of truth for this rule and is easily scalable.
        term_map = {
            "info center": "IBM Documentation",
            "infocenter": "IBM Documentation",
            "knowledge center": "IBM Documentation",
            "dialog box": "dialog",
            "un-install": "uninstall",
            "de-install": "uninstall",
            "e-mail": "email",
            "end user": "user",
            "log on to": "log in to",
            "logon": "log in",
            "web site": "website",
            "work station": "workstation",
        }

        for i, sentence in enumerate(sentences):
            # We check the lowercase version of the sentence for a broader match.
            sentence_lower = sentence.lower()
            for term, replacement in term_map.items():
                # Use regex with word boundaries (\b) to ensure we match whole words only.
                # This prevents false positives on words that might contain the term.
                pattern = r'\b' + re.escape(term) + r'\b'
                if re.search(pattern, sentence_lower):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Non-preferred term '{term}' used.",
                        suggestions=[f"Use the preferred IBM term: '{replacement}'."],
                        severity='medium'
                    ))
        return errors
