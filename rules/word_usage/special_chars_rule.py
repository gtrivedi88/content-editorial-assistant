"""
Word Usage Rule for special characters and numbers.
Enhanced with spaCy Matcher and PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
    from spacy.matcher import Matcher
except ImportError:
    Doc = None
    Matcher = None

class SpecialCharsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific special characters and numbers.
    Enhanced with spaCy Matcher and PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_special'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy Matcher and PhraseMatcher with special character patterns."""
        # 1. Setup PhraseMatcher for specific phrases and fiscal periods
        # Note: Base class converts to lowercase, so use lowercase keys
        phrase_word_details = {
            "24/7": {"suggestion": "Avoid. Use '24x7' or descriptive wording like '24 hours a day, every day'.", "severity": "medium"},
            # Fiscal periods - enumerate all possibilities (lowercase keys for base class compatibility)
            "h1": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "h2": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "h3": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "h4": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "q1": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "q2": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "q3": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
            "q4": {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
        }
        
        # Use base class method to setup PhraseMatcher patterns  
        self._setup_word_patterns(nlp, phrase_word_details)
        
        # 2. Setup Matcher for hash character patterns
        if Matcher is not None and not hasattr(self, '_hash_matcher'):
            self._hash_matcher = Matcher(nlp.vocab)
            # Pattern for standalone hash character: {"TEXT": "#"}
            hash_pattern = [{"TEXT": "#"}]
            self._hash_matcher.add("HASH_CHAR", [hash_pattern])

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # 1. NEW ENHANCED APPROACH: Use base class PhraseMatcher for phrases and fiscal periods
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        # 2. NEW ENHANCED APPROACH: Use spaCy Matcher for hash character detection
        if hasattr(self, '_hash_matcher') and self._hash_matcher:
            hash_matches = self._hash_matcher(doc)
            for match_id, start, end in hash_matches:
                span = doc[start:end]
                sent = span.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message=f"Review usage of the term '{span.text}'.",
                    suggestions=["Use 'number sign' to refer to the # character, or 'hash sign' for hashtags."],
                    severity='low',
                    span=(span.start_char, span.end_char),
                    flagged_text=span.text
                ))
        
        return errors
