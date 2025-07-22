"""
Word Usage Rule for words starting with 'A'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class AWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'A'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_a'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
            
        doc = nlp(text)

        # Context-aware check for 'action' as a verb
        for token in doc:
            if token.lemma_.lower() == "action" and token.pos_ == "VERB":
                sent = token.sent
                errors.append(self._create_error(
                    sentence=sent.text,
                    message="Do not use 'action' as a verb.",
                    suggestions=["Use a more specific verb like 'run' or 'perform'."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))

        # General word map for other 'A' words
        word_map = {
            "abort": {"suggestion": "Use 'cancel' or 'stop'.", "severity": "high"},
            "above": {"suggestion": "Avoid relative locations. Use 'previous' or 'preceding'.", "severity": "medium"},
            "ad hoc": {"suggestion": "Write as two words: 'ad hoc'.", "severity": "low"},
            "adviser": {"suggestion": "Use 'advisor'.", "severity": "low"},
            "afterwards": {"suggestion": "Use 'afterward'.", "severity": "low"},
            "allow": {"suggestion": "Focus on the user. Instead of 'the product allows you to...', use 'you can use the product to...'.", "severity": "medium"},
            "amongst": {"suggestion": "Use 'among'.", "severity": "low"},
            "and/or": {"suggestion": "Avoid 'and/or'. Use 'a or b', or 'a, b, or both'.", "severity": "medium"},
            "appear": {"suggestion": "Do not use for UI elements. Use 'open' or 'is displayed'.", "severity": "medium"},
            "architect": {"suggestion": "Do not use as a verb. Use 'design', 'plan', or 'structure'.", "severity": "high"},
            "asap": {"suggestion": "Avoid informal abbreviations. Use 'as soon as possible'.", "severity": "medium"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Consider an alternative for the word '{match.group()}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors
