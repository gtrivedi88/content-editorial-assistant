"""
Word Usage Rule for words starting with 'W'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced morphological analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class WWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'W'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced morphological analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with W-word patterns."""
        # Define word details for 'W' words (advanced analysis and skipped words handled separately)
        word_details = {
            "w/": {"suggestion": "Spell out 'with'.", "severity": "medium"},
            "war room": {"suggestion": "Avoid military metaphors. Use 'command center' or 'operations center'.", "severity": "high"},
            # Skip "we" - handled by second_person_rule to avoid duplicates
            "web site": {"suggestion": "Use 'website' (one word).", "severity": "low"},
            "whitelist": {"suggestion": "Use inclusive language. Use 'allowlist'.", "severity": "high"},
            "Wi-Fi": {"suggestion": "Use 'Wi-Fi' for the certified technology and 'wifi' for a generic wireless connection.", "severity": "low"},
            "work station": {"suggestion": "Use 'workstation' (one word).", "severity": "low"},
            "world-wide": {"suggestion": "Use 'worldwide' (one word).", "severity": "low"},
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

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Context-aware morphological analysis for 'while'
        # This sophisticated linguistic analysis uses dependency parsing and morphology to determine semantic usage
        for token in doc:
            if token.lemma_.lower() == "while" and token.dep_ == "mark":
                sent = token.sent
                # Get the sentence index by finding the sentence in the doc.sents
                sentence_index = 0
                for i, s in enumerate(doc.sents):
                    if s == sent:
                        sentence_index = i
                        break
                
                # Heuristic: if the clause is not clearly about time, flag for review.
                is_time_related = any(t.pos_ == "VERB" and "ing" in t.morph for t in token.head.children)
                if not is_time_related:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sentence_index,
                        message="Use 'while' only to refer to time. For contrast, use 'although' or 'whereas'.",
                        suggestions=["Replace 'while' with 'although' when indicating contrast."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher for simple word patterns
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
