"""
Word Usage Rule for words starting with 'C'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class CWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'C'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_c'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "cancelation": {"suggestion": "Use 'cancellation'.", "severity": "low"},
            "can not": {"suggestion": "Use 'cannot'.", "severity": "high"},
            "canned": {"suggestion": "Avoid jargon. Use 'predefined' or 'preconfigured'.", "severity": "medium"},
            "catalogue": {"suggestion": "Use 'catalog'.", "severity": "low"},
            "checkbox": {"suggestion": "Use 'check box'.", "severity": "low"},
            "check out": {"suggestion": "Use 'check out' (verb) and 'checkout' (noun/adjective).", "severity": "low"},
            "choose": {"suggestion": "For UI elements, use a more specific verb like 'select' or 'click'.", "severity": "medium"},
            "class path": {"suggestion": "Use 'classpath' only as a variable, otherwise 'class path'.", "severity": "low"},
            "clean up": {"suggestion": "Use 'clean up' (verb) and 'cleanup' (noun).", "severity": "low"},
            "click on": {"suggestion": "Omit 'on'. Write 'click the button', not 'click on the button'.", "severity": "high"},
            "client-server": {"suggestion": "Use 'client/server'.", "severity": "low"},
            "combo box": {"suggestion": "Do not use. In instructions, use the name of the field.", "severity": "medium"},
            "comprise": {"suggestion": "The whole comprises the parts. The parts compose the whole. Avoid 'is comprised of'.", "severity": "medium"},
            "congratulations": {"suggestion": "Avoid in technical information. State the accomplishment directly.", "severity": "medium"},
            "counterclockwise": {"suggestion": "Use 'counterclockwise', not 'anticlockwise'.", "severity": "low"},
            "crash": {"suggestion": "Use a more specific term like 'fail' or 'stop unexpectedly'.", "severity": "medium"},
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
