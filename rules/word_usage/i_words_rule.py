"""
Word Usage Rule for words starting with 'I'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class IWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'I'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_i'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with I-word patterns."""
        # Define word details for 'I' words
        word_details = {
            "i.e.": {"suggestion": "Use 'that is'.", "severity": "medium"},
            "IBMer": {"suggestion": "Use only in internal communications.", "severity": "high"},
            "inactivate": {"suggestion": "Use 'deactivate'.", "severity": "low"},
            "in as much as": {"suggestion": "Use 'because' or 'since'.", "severity": "medium"},
            "in-depth": {"suggestion": "Write as 'in depth' (two words).", "severity": "low"},
            "info": {"suggestion": "Avoid slang. Use 'information'.", "severity": "medium"},
            "in order to": {"suggestion": "Use the simpler term 'to'.", "severity": "low"},
            "input": {"suggestion": "Do not use as a verb. Use 'type' or 'enter'.", "severity": "medium"},
            "insure": {"suggestion": "Use 'ensure' to mean 'make sure'. 'Insure' relates to financial insurance.", "severity": "high"},
            "Internet": {"suggestion": "Use 'internet' (lowercase) unless part of a proper name like 'Internet of Things'.", "severity": "medium"},
            "invite": {"suggestion": "Do not use as a noun. Use 'invitation'.", "severity": "medium"},
            "issue": {"suggestion": "For commands, prefer 'run', 'type', or 'enter'.", "severity": "low"},
        }
        
        # Use base class method to setup patterns
        self._setup_word_patterns(nlp, word_details)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher functionality
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
