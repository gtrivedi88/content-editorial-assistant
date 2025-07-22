"""
Word Usage Rule for words starting with 'J'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class JWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'J'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_j'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        word_map = {
            "jar": {"suggestion": "Do not use as a verb. Use 'compress' or 'archive'.", "severity": "medium"},
            "JavaBeans": {"suggestion": "Write as 'JavaBeans' (correct capitalization).", "severity": "low"},
            "JavaDoc": {"suggestion": "Use 'Javadoc'.", "severity": "low"},
            "job log": {"suggestion": "Use 'joblog' (one word).", "severity": "low"},
            "job stream": {"suggestion": "Use 'jobstream' (one word).", "severity": "low"},
            "judgement": {"suggestion": "Use the spelling 'judgment'.", "severity": "low"},
            "just": {"suggestion": "Omit if superfluous. Do not use to mean 'only'.", "severity": "low"},
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
