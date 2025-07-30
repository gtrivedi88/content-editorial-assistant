"""
Word Usage Rule for words starting with 'X'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection (case-sensitive).
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
    from spacy.matcher import PhraseMatcher
except ImportError:
    Doc = None
    PhraseMatcher = None

class XWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'X'.
    Enhanced with spaCy PhraseMatcher for efficient detection (case-sensitive).
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_x'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with X-word patterns (case-sensitive)."""
        if PhraseMatcher is None:
            return
        
        # Define word details for 'X' words (note: case-sensitive for technical terms)
        word_details = {
            "XSA": {"suggestion": "Do not use. Use 'extended subarea addressing'.", "severity": "medium"},
            "xterm": {"suggestion": "Write as 'xterm' (lowercase).", "severity": "low"},
        }
        
        self.word_details = word_details
        
        # Setup case-sensitive PhraseMatcher (using TEXT attribute instead of LOWER)
        if not hasattr(self, '_phrase_matcher') or self._phrase_matcher is None:
            self._phrase_matcher = PhraseMatcher(nlp.vocab, attr="TEXT")  # Case-sensitive
            patterns = [nlp(word) for word in word_details.keys()]
            self._phrase_matcher.add("WORD_USAGE_X", patterns)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # NEW ENHANCED APPROACH: Use case-sensitive PhraseMatcher functionality
        if hasattr(self, '_phrase_matcher') and self._phrase_matcher:
            matches = self._phrase_matcher(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                matched_text = span.text  # Keep original case
                sent = span.sent
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                if matched_text in self.word_details:
                    details = self.word_details[matched_text]
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message=f"Review usage of the term '{span.text}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=(span.start_char, span.end_char),
                        flagged_text=span.text
                    ))
        
        return errors
