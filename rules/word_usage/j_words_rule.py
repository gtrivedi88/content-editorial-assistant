"""
Word Usage Rule for words starting with 'J'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class JWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'J'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_j'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with J-word patterns."""
        # Define word details for 'J' words
        word_details = {
            "jar": {"suggestion": "Do not use as a verb. Use 'compress' or 'archive'.", "severity": "medium"},
            "JavaBeans": {"suggestion": "Write as 'JavaBeans' (correct capitalization).", "severity": "low"},
            "JavaDoc": {"suggestion": "Use 'Javadoc'.", "severity": "low"},
            "job log": {"suggestion": "Use 'joblog' (one word).", "severity": "low"},
            "job stream": {"suggestion": "Use 'jobstream' (one word).", "severity": "low"},
            "judgement": {"suggestion": "Use the spelling 'judgment'.", "severity": "low"},
            "just": {"suggestion": "Omit if superfluous. Do not use to mean 'only'.", "severity": "low"},
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
