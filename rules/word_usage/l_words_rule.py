"""
Word Usage Rule for words starting with 'L'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection combined with advanced morphological analysis.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    Enhanced with spaCy PhraseMatcher for efficient detection combined with advanced morphological analysis.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with L-word patterns."""
        # Define word details for 'L' words (complex morphological analysis handled separately)
        word_details = {
            "land and expand": {"suggestion": "Avoid this term due to colonial connotations. Use 'expansion strategy'.", "severity": "high"},
            "last name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "leverage": {"suggestion": "Avoid in technical content; it does not translate well. Use 'use'.", "severity": "medium"},
            "licence": {"suggestion": "Use the spelling 'license'.", "severity": "low"},
            "log on to": {"suggestion": "This is the correct form. Avoid 'log onto'.", "severity": "low"},
            "log off of": {"suggestion": "Use 'log off from'.", "severity": "medium"},
            "look and feel": {"suggestion": "Avoid this phrase. Be more specific about the UI characteristics.", "severity": "medium"},
            "lowercase": {"suggestion": "Write as 'lowercase' (one word).", "severity": "low"},
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

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Enterprise context intelligence
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        
        if not should_apply:
            return errors  # Skip for technical labels, navigation items, etc.

        # PRESERVE EXISTING ADVANCED FUNCTIONALITY: Special morphological analysis for compound words
        for i, sent in enumerate(doc.sents):
            # LINGUISTIC ANCHOR: Use SpaCy to detect "life cycle" (two words) that should be "lifecycle"
            for token in sent:
                if token.lemma_.lower() == "life" and token.i + 1 < len(doc):
                    next_token = doc[token.i + 1]
                    if next_token.lemma_.lower() == "cycle":
                        # Check if they form a compound that should be one word
                        if token.dep_ == "compound" or next_token.dep_ == "compound":
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Review usage of the term 'life cycle'.",
                                suggestions=["Write as 'lifecycle' (one word)."],
                                severity='low',
                                span=(token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=f"{token.text} {next_token.text}"
                            ))

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher for simple word patterns
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors
