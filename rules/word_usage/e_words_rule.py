"""
Word Usage Rule for words starting with 'E'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class EWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'E'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_e'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with E-word patterns."""
        # Define word details for 'E' words
        word_details = {
            "e-business": {"suggestion": "Avoid. This term is outdated.", "severity": "high"},
            "e-mail": {"suggestion": "Use 'email' (one word).", "severity": "high"},
            "easy": {"suggestion": "Use with caution. This is a subjective claim.", "severity": "high"},
            "effortless": {"suggestion": "Use with caution. This is a subjective claim.", "severity": "high"},
            "e.g.": {"suggestion": "Use 'for example'.", "severity": "medium"},
            "enable": {"suggestion": "Focus on the user. Instead of 'this enables you to...', use 'you can...'.", "severity": "medium"},
            "end user": {"suggestion": "Use 'user' unless you need to differentiate types of users.", "severity": "low"},
            "engineer": {"suggestion": "Use only to refer to a person with an engineering degree. This is a legal requirement.", "severity": "high"},
            "ensure": {"suggestion": "Use 'ensure' to mean 'make sure'. Avoid suggesting a guarantee.", "severity": "medium"},
            "etc.": {"suggestion": "Avoid. Be specific or use 'and so on' for clear sequences.", "severity": "medium"},
            "evangelist": {"suggestion": "Avoid religious connotations. Use 'advocate' or 'influencer'.", "severity": "high"},
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
