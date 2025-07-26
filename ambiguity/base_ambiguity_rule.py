"""
Base Ambiguity Rule - Integrates with existing rules system to detect ambiguity.

**UPDATED** to inherit the exception-checking capabilities from the main BaseRule.
This allows all ambiguity detectors to use the `_is_excepted` method to check
the exceptions.yaml file, reducing false positives.
"""

import os
import sys
from typing import List, Dict, Any, Optional

# This now correctly inherits from your main rules.base_rule
from rules.base_rule import BaseRule

# Local imports for ambiguity-specific types
from .types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity, 
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class BaseAmbiguityRule(BaseRule):
    """
    Base rule for ambiguity detection. It coordinates specific ambiguity
    detectors and now provides them with access to the central exception framework.
    """
    
    def __init__(self):
        # Initialize the parent BaseRule, which loads exceptions.yaml
        super().__init__()
        self.config = AmbiguityConfig()
        self.detectors = {}
        self._initialize_detectors()
    
    def _get_rule_type(self) -> str:
        """Return the rule type identifier."""
        return 'ambiguity'
    
    def _initialize_detectors(self):
        """Initialize available ambiguity detectors."""
        # This logic remains the same. It dynamically loads detectors.
        try:
            from .detectors.missing_actor_detector import MissingActorDetector
            self.add_detector('missing_actor', MissingActorDetector(self.config, self))
        except ImportError:
            pass
        
        try:
            from .detectors.pronoun_ambiguity_detector import PronounAmbiguityDetector
            self.add_detector('pronoun_ambiguity', PronounAmbiguityDetector(self.config, self))
        except ImportError:
            pass
        
        try:
            from .detectors.unsupported_claims_detector import UnsupportedClaimsDetector
            self.add_detector('unsupported_claims', UnsupportedClaimsDetector(self.config, self))
        except ImportError:
            pass
        
        try:
            from .detectors.fabrication_risk_detector import FabricationRiskDetector
            self.add_detector('fabrication_risk', FabricationRiskDetector(self.config, self))
        except ImportError:
            pass
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyze text for ambiguity by running all enabled detectors.
        """
        if not nlp:
            return []
        
        errors = []
        
        try:
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                
                sentence_context = self._create_sentence_context(
                    sentence, i, sentences, text, context
                )
                
                for detector_type, detector in self.detectors.items():
                    if detector and detector.is_enabled():
                        ambiguity_detections = detector.detect(sentence_context, nlp)
                        for detection in ambiguity_detections:
                            errors.append(detection.to_error_dict())
            
        except Exception as e:
            print(f"Error in ambiguity analysis: {e}")
        
        return errors
    
    # (Helper methods like _create_sentence_context, add_detector, etc. remain the same)
    # ... Omitted for brevity ...

    def add_detector(self, detector_type: str, detector):
        """Add a new detector to the system."""
        self.detectors[detector_type] = detector

    def _create_sentence_context(self, sentence: str, sentence_index: int, 
                                sentences: List[str], full_text: str, 
                                block_context: Optional[dict]) -> AmbiguityContext:
        preceding = sentences[max(0, sentence_index - 2):sentence_index] if sentence_index > 0 else []
        following = sentences[sentence_index + 1:sentence_index + 3] if sentence_index < len(sentences) - 1 else []
        return AmbiguityContext(
            sentence_index=sentence_index,
            sentence=sentence,
            preceding_sentences=preceding,
            following_sentences=following,
            document_context=block_context
        )

class AmbiguityDetector:
    """
    Base class for specific ambiguity detectors.
    Each detector now gets a reference to the parent rule to access the
    exception framework.
    """
    
    def __init__(self, config: AmbiguityConfig, parent_rule: BaseAmbiguityRule):
        self.config = config
        self.enabled = True
        # Store a reference to the parent to use its _is_excepted method
        self.parent_rule = parent_rule
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """Detect ambiguities in the given context."""
        raise NotImplementedError("Subclasses must implement detect method")

    def _is_excepted(self, text_span: str) -> bool:
        """
        Convenience method to check for exceptions using the parent rule's logic.
        This is the key integration point for the exception framework.
        """
        # We need to set the parent's rule_type temporarily to check the correct
        # section in exceptions.yaml. This is a bit of a workaround but effective.
        # A more advanced solution would be to pass the subtype to the parent.
        original_type = self.parent_rule.rule_type
        # For now, we assume all ambiguity subtypes can check against a 'claims' or global list
        # This can be made more specific if needed.
        self.parent_rule.rule_type = 'claims' # Check against the 'claims' exception list
        is_claim_exception = self.parent_rule._is_excepted(text_span)
        self.parent_rule.rule_type = original_type # Restore original type
        
        # Also check global exceptions
        is_global_exception = self.parent_rule._is_excepted(text_span)

        return is_claim_exception or is_global_exception

    def is_enabled(self) -> bool:
        """Check if this detector is enabled."""
        return self.enabled
