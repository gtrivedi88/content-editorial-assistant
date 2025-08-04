"""
Word Usage Rule for words starting with 'A'.
Enhanced with spaCy Matcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
    from spacy.matcher import PhraseMatcher
except ImportError:
    Doc = None
    PhraseMatcher = None

class AWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'A'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_a'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with A-word patterns."""
        # Define word details for 'A' words
        word_details = {
            "abort": {"suggestion": "Use 'cancel' or 'stop'.", "severity": "high"},
            "above": {"suggestion": "Avoid relative locations. Use 'previous' or 'preceding'.", "severity": "medium"},
            "ad hoc": {"suggestion": "Write as two words: 'ad hoc'.", "severity": "low"},
            "adviser": {"suggestion": "Use 'advisor'.", "severity": "low"},
            "afterwards": {"suggestion": "Use 'afterward'.", "severity": "low"},
            "allow": {"suggestion": "Focus on the user. Instead of 'the product allows you to...', use 'you can use the product to...'.", "severity": "medium"},
            "amongst": {"suggestion": "Use 'among'.", "severity": "low"},
            "and/or": {"suggestion": "Avoid 'and/or'. Use 'a or b', or 'a, b, or both'.", "severity": "medium"},
            "appear": {"suggestion": "Do not use for UI elements. Use 'open' or 'is displayed'.", "severity": "medium"},
            "architect": {"suggestion": "Do not use as a verb. Use 'design', 'plan', or 'structure'.", "severity": "high"},
            "asap": {"suggestion": "Avoid informal abbreviations. Use 'as soon as possible'.", "severity": "medium"},
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

        # PRESERVE EXISTING FUNCTIONALITY: Context-aware check for 'action' as a verb
        # This specialized grammar check is kept for enhanced accuracy
        for token in doc:
            if token.lemma_.lower() == "action" and token.pos_ == "VERB":
                sent = token.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                        
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_index,
                    message="Do not use 'action' as a verb.",
                    suggestions=["Use a more specific verb like 'run' or 'perform'."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher functionality
        word_usage_errors = self._find_word_usage_errors(doc, "Consider an alternative for the word", text, context)
        
        # Filter out 'action' since it's handled above with grammar awareness
        for error in word_usage_errors:
            if error['flagged_text'].lower() != "action":
                errors.append(error)
        
        return errors
