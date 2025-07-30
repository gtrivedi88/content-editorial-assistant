"""
Word Usage Rule for words starting with 'M'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with context-aware analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'M'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with context-aware analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_m'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with M-word patterns."""
        # Define word details for 'M' words (context-aware logic handled separately)
        word_details = {
            "man-hour": {"suggestion": "Use inclusive language. Use 'person hour' or 'labor hour'.", "severity": "high"},
            "man day": {"suggestion": "Use inclusive language. Use 'person day'.", "severity": "high"},
            "master": {"suggestion": "Avoid when paired with 'slave'. Use 'primary', 'main', 'controller', or 'leader'.", "severity": "high"},
            "may": {"suggestion": "Use 'can' to indicate ability and 'might' to indicate possibility.", "severity": "medium"},
            "menu bar": {"suggestion": "Write as 'menubar' (one word).", "severity": "low"},
            "meta data": {"suggestion": "Write as 'metadata' (one word).", "severity": "low"},
            "methodology": {"suggestion": "Use only to refer to a group of methods. Often, 'method' is sufficient.", "severity": "low"},
            "migrate": {"suggestion": "Use correctly. 'Migrate' (move between systems) is not the same as 'upgrade' (new version) or 'port' (different OS).", "severity": "medium"},
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
        
        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware filtering for 'master'
        # Apply sophisticated contextual logic - only flag 'master' when 'slave' is present
        for error in word_usage_errors:
            if error['flagged_text'].lower() == 'master':
                # Find the sentence containing this error to check for context
                error_sentence = error['sentence'].lower()
                if 'slave' in error_sentence:
                    errors.append(error)
                # Skip 'master' if 'slave' is not in the same sentence (avoid false positives)
            else:
                errors.append(error)
        
        return errors
