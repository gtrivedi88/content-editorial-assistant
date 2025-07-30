"""
Word Usage Rule for words starting with 'G'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'G'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_g'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with G-word patterns."""
        # Define word details for 'G' words
        word_details = {
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
