"""
Word Usage Rule for words starting with 'G'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class GWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'G'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_g'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "gage": {"suggestion": "Use 'gauge'.", "severity": "low"},
            "GenAI": {"suggestion": "Use 'gen AI' (lowercase g, uppercase AI).", "severity": "medium"},
            "geo": {"suggestion": "Do not use as an abbreviation for 'geographical area' in customer-facing content.", "severity": "medium"},
            "given name": {"suggestion": "This is the preferred term over 'first name' or 'Christian name'.", "severity": "low"},
            "globalization": {"suggestion": "This is the preferred term. Do not use 'G11N'.", "severity": "medium"},
            "go-live": {"suggestion": "Write as 'go live' (two words).", "severity": "low"},
            "gray": {"suggestion": "Use 'gray', not 'grey'.", "severity": "low"},
            "grayed out": {"suggestion": "Use 'disabled' or 'unavailable' for UI elements.", "severity": "medium"},
            "green": {"suggestion": "Do not use to describe environmental benefits unless the claim is substantiated and approved.", "severity": "high"},
            "GUI": {"suggestion": "Avoid generic use. Refer to the specific part of the interface (e.g., 'the User Management window').", "severity": "low"},
            "gzip": {"suggestion": "Due to legal implications, use 'compress' instead of 'gzip' as a verb.", "severity": "high"},
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
