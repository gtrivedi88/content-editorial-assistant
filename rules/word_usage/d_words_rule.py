"""
Word Usage Rule for words starting with 'D'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class DWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'D'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_d'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        # General word map
        word_map = {
            "data base": {"suggestion": "Use 'database' (one word).", "severity": "high"},
            "data center": {"suggestion": "Use 'datacenter' only for VMware contexts.", "severity": "low"},
            "data set": {"suggestion": "Use 'dataset' unless it is part of existing product terminology.", "severity": "medium"},
            "deactivate": {"suggestion": "Use 'deactivate', not 'inactivate'.", "severity": "low"},
            "deallocate": {"suggestion": "Use 'deallocate', not 'unallocate'.", "severity": "low"},
            "deinstall": {"suggestion": "Use 'uninstall'.", "severity": "high"},
            "demilitarized zone": {"suggestion": "Use 'DMZ'.", "severity": "medium"},
            "demo": {"suggestion": "Avoid in technical content. Use 'demonstration'.", "severity": "medium"},
            "depress": {"suggestion": "Do not use for keys or buttons. Use 'press' or 'type'.", "severity": "high"},
            "deselect": {"suggestion": "Use 'clear' for check boxes. 'Deselect' is acceptable otherwise.", "severity": "low"},
            "desire": {"suggestion": "Avoid. Use 'want' or 'need'.", "severity": "low"},
            "dialog box": {"suggestion": "Use 'dialog' or refer to the window by its title.", "severity": "medium"},
            "disabled": {"suggestion": "Do not use to refer to a person. For UI, 'disabled' is acceptable if an element is visible but not usable.", "severity": "high"},
            "disc": {"suggestion": "Use 'disc' for optical media (CD, DVD), 'disk' for magnetic media.", "severity": "medium"},
            "display": {"suggestion": "Use as a transitive verb only (e.g., 'the system displays a message').", "severity": "low"},
            "double click": {"suggestion": "Use 'double-click' (hyphenated verb).", "severity": "high"},
            "downgrade": {"suggestion": "Avoid. Use 'revert to an earlier version' or 'roll back'.", "severity": "medium"},
            "drop-down": {"suggestion": "Use only as an adjective before 'menu' or 'list'.", "severity": "low"},
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
