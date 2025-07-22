"""
Word Usage Rule for words starting with 'F'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class FWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'F'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_f'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # General word map
        word_map = {
            "failback": {"suggestion": "Use 'failback' (one word) as a noun/adjective, and 'fail back' (two words) as a verb.", "severity": "low"},
            "failover": {"suggestion": "Use 'failover' (one word) as a noun/adjective, and 'fail over' (two words) as a verb.", "severity": "low"},
            "fallback": {"suggestion": "Use 'fallback' (one word) as a noun/adjective, and 'fall back' (two words) as a verb.", "severity": "low"},
            "farther": {"suggestion": "Use 'farther' for physical distance and 'further' for degree or quantity.", "severity": "medium"},
            "Fibre Channel": {"suggestion": "Use 'Fibre Channel', not 'Fiber Channel'.", "severity": "high"},
            "file name": {"suggestion": "Use 'filename' only as a variable. Otherwise, use 'file name' (two words).", "severity": "low"},
            "fill out": {"suggestion": "Use a more precise verb like 'complete', 'specify', or 'enter'.", "severity": "medium"},
            "fine tune": {"suggestion": "Use 'fine-tune' as an adjective (e.g., 'fine-tuned model') and 'fine tune' as a verb.", "severity": "low"},
            "fire up": {"suggestion": "Avoid jargon. Use 'start'.", "severity": "medium"},
            "first name": {"suggestion": "Use the globally recognized term 'given name'.", "severity": "medium"},
            "fix pack": {"suggestion": "Write as 'fix pack' (two words).", "severity": "low"},
            "following": {"suggestion": "Use as an adjective before a noun (e.g., 'the following steps'). Do not use as a standalone noun.", "severity": "medium"},
            "foo": {"suggestion": "Do not use. This is technical jargon.", "severity": "high"},
            "forename": {"suggestion": "Use 'given name'.", "severity": "medium"},
            "foundation model": {"suggestion": "Use 'foundation model', not 'foundational model'.", "severity": "medium"},
            "free": {"suggestion": "Avoid using 'free' to refer to price unless approved by legal. Use 'at no cost' or 'without charge'.", "severity": "high"},
            "functionality": {"suggestion": "Consider using the simpler term 'functions'.", "severity": "low"},
            "future-proof": {"suggestion": "Use with caution. This is an unsupported claim.", "severity": "high"},
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
