"""
Word Usage Rule for words starting with 'S'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class SWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'S'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_s'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "sanity check": {"suggestion": "Avoid this term. Use 'validation', 'check', or 'review'.", "severity": "high"},
            "screen shot": {"suggestion": "Use 'screenshot' (one word).", "severity": "low"},
            "second name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "secure": {"suggestion": "Avoid making absolute claims. Use 'security-enhanced' or describe the specific feature.", "severity": "high"},
            "segregate": {"suggestion": "Use 'separate'.", "severity": "high"},
            "server-side": {"suggestion": "Write as 'serverside' (one word).", "severity": "low"},
            "set up": {"suggestion": "Use 'set up' (verb) and 'setup' (noun/adjective).", "severity": "low"},
            "shall": {"suggestion": "Avoid. Use 'must' for requirements or 'will' for future tense.", "severity": "medium"},
            "ship": {"suggestion": "Avoid. Use 'release' or 'make available'.", "severity": "medium"},
            "should": {"suggestion": "Avoid for mandatory actions. Use 'must' or the imperative.", "severity": "medium"},
            "shut down": {"suggestion": "Use 'shut down' (verb) and 'shutdown' (noun/adjective).", "severity": "low"},
            "slave": {"suggestion": "Use inclusive language. Use 'secondary', 'replica', 'agent', or 'worker'.", "severity": "high"},
            "stand-alone": {"suggestion": "Write as 'standalone' (one word).", "severity": "low"},
            "suite": {"suggestion": "Avoid for groups of unrelated products. Use 'family' or 'set'.", "severity": "medium"},
            "sunset": {"suggestion": "Avoid jargon. Use 'discontinue' or 'withdraw from service'.", "severity": "medium"},
        }

        for i, sentence in enumerate(sentences):
            for word, details in word_map.items():
                if re.search(r'\b' + re.escape(word) + r'\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Review usage of the term '{word}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity']
                    ))
        return errors
