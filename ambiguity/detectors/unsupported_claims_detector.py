"""
Unsupported Claims Detector

**REFACTORED** to consolidate logic from the separate `claims_rule`, be less 
aggressive, and use the new exception framework with more intelligent, 
context-aware linguistic checks.
"""

from typing import List, Dict, Any, Optional
from ..base_ambiguity_rule import AmbiguityDetector
from ..types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity,
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)

class UnsupportedClaimsDetector(AmbiguityDetector):
    """
    Detects unsupported claims and promises by analyzing words in their
    linguistic context, using the central exception framework to avoid false positives.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule):
        super().__init__(config, parent_rule)
        
        # A focused list of words that are almost always problematic claims
        self.strong_claim_words = {
            'guarantee', 'always', 'never', 'impossible', 'perfect', 
            'flawless', 'foolproof'
        }
        
        # Words that are only problematic in certain contexts
        self.contextual_claim_words = {
            'ensure', 'will', 'must', 'easy', 'secure', 'full', 'every', 
            'best practice', 'effortless', 'future-proof'
        }

    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        detections = []
        if not context.sentence.strip():
            return detections
        
        try:
            doc = nlp(context.sentence)
            for token in doc:
                word_lemma = token.lemma_.lower()
                
                # First, check if the word or a phrase it's part of is explicitly allowed
                if self._is_excepted(token.text) or self._is_part_of_excepted_phrase(token):
                    continue

                # Check for strong, almost always problematic claims
                if word_lemma in self.strong_claim_words:
                    detections.append(self._create_detection(token, 0.9, context))

                # Check for contextual claims that need more analysis
                elif word_lemma in self.contextual_claim_words:
                    if self._is_problematic_claim_context(token, doc):
                        detections.append(self._create_detection(token, 0.7, context))

        except Exception as e:
            print(f"Error in unsupported claims detection: {e}")
        
        return detections

    def _is_part_of_excepted_phrase(self, token) -> bool:
        """Checks for two-word exceptions like 'easy management'."""
        if token.i + 1 < len(token.doc):
            phrase = f"{token.text.lower()} {token.doc[token.i + 1].text.lower()}"
            if self._is_excepted(phrase):
                return True
        return False

    def _is_problematic_claim_context(self, token, doc) -> bool:
        """
        Determines if a contextual claim word is being used in a way that
        makes an unsupported promise. More intelligent than a simple keyword match.
        """
        word_lemma = token.lemma_.lower()

        if word_lemma in ['easy', 'secure', 'effortless']:
            if token.dep_ == 'amod' and token.head.pos_ == 'NOUN':
                if token.head.lemma_ in ['solution', 'process', 'system', 'method', 'installation']:
                    return True
            return False

        if word_lemma == 'ensure':
            if token.head.lemma_ == 'to' and token.head.dep_ == 'aux':
                return True
            return False

        if word_lemma == 'will':
            if token.head.pos_ == 'VERB' and token.head.lemma_ in ['work', 'succeed', 'fail', 'perform', 'validate']:
                return True
            return False

        if word_lemma == 'every':
            if token.head.lemma_ in ['administrator', 'user', 'person', 'customer']:
                return True
            return False
            
        if word_lemma == 'best practice':
            return True # This is generally discouraged outside of specific contexts

        return False # Default to not flagging contextual words

    def _create_detection(self, token, confidence: float, context: AmbiguityContext) -> AmbiguityDetection:
        """Creates a standardized detection object with contextual suggestions."""
        suggestions = self._generate_contextual_suggestions(token, token.sent)
        
        evidence = AmbiguityEvidence(
            tokens=[token.text],
            linguistic_pattern=f"unsupported_claim_{token.lemma_}",
            confidence=confidence
        )
        
        return AmbiguityDetection(
            ambiguity_type=AmbiguityType.UNSUPPORTED_CLAIMS,
            category=AmbiguityCategory.SEMANTIC,
            severity=self.config.get_severity(AmbiguityType.UNSUPPORTED_CLAIMS),
            context=context,
            evidence=evidence,
            resolution_strategies=[ResolutionStrategy.SPECIFY_REFERENCE],
            ai_instructions=suggestions # Use the generated suggestions for AI
        )

    def _generate_contextual_suggestions(self, token, sentence) -> List[str]:
        """
        Generate context-aware suggestions, inspired by your original claims_rule.py.
        """
        word = token.lemma_.lower()
        suggestions = []

        if word == "easy":
            if any(t.lemma_ in ["process", "step"] for t in sentence):
                suggestions.append("Replace with 'straightforward' or 'simple'.")
            else:
                suggestions.append("Replace with 'accessible' or describe *why* it is easy (e.g., 'uses a guided setup').")
        elif word == "secure":
            suggestions.append("Replace with 'security-enhanced' or specify the security feature (e.g., 'uses end-to-end encryption').")
        elif word == "best practice":
            suggestions.append("Replace with 'recommended approach' or 'standard method'.")
        elif word == "effortless":
            suggestions.append("Replace with 'automated' or 'streamlined'.")
        elif word == "ensure":
            suggestions.append("Use 'ensure' to mean 'make sure'. Avoid suggesting a guarantee. Consider 'helps to ensure' or 'is designed to'.")
        
        if not suggestions:
            suggestions.append(f"Replace '{token.text}' with a more specific, objective description.")
            
        return suggestions
