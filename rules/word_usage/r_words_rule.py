"""
Word Usage Rule for words starting with 'R'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class RWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'R'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_r'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Context-aware checks for compound words
        for token in doc:
            # Linguistic Anchor: Check for 'real time' used as an adjective.
            if token.lemma_ == "real" and token.i + 1 < len(doc) and doc[token.i + 1].lemma_ == "time":
                if doc[token.i + 1].dep_ == "amod" or token.dep_ == "amod":
                     sent = token.sent
                     next_token = doc[token.i + 1]
                     errors.append(self._create_error(
                        sentence=sent.text,
                        message="Incorrect adjective form: 'real time' should be 'real-time'.",
                        suggestions=["Use 'real-time' (hyphenated) as an adjective before a noun."],
                        severity='medium',
                        span=(token.idx, next_token.idx + len(next_token.text)),
                        flagged_text=f"{token.text} {next_token.text}"
                     ))

        # General word map
        word_map = {
            "read-only": {"suggestion": "Write as 'read-only' (hyphenated).", "severity": "low"},
            "re-": {"suggestion": "Most words with the 're-' prefix are not hyphenated (e.g., 'reenter', 'reorder').", "severity": "low"},
            "Redbook": {"suggestion": "The correct term is 'IBM Redbooks publication'.", "severity": "high"},
            "refer to": {"suggestion": "For cross-references, prefer 'see'.", "severity": "low"},
            "respective": {"suggestion": "Avoid. Rewrite the sentence to be more direct.", "severity": "medium"},
            "roadmap": {"suggestion": "Write as 'roadmap' (one word).", "severity": "low"},
            "roll back": {"suggestion": "Use 'roll back' (verb) and 'rollback' (noun/adjective).", "severity": "low"},
            "run time": {"suggestion": "Use 'runtime' (one word) as an adjective, and 'run time' (two words) as a noun.", "severity": "low"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Review usage of the term '{match.group()}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
