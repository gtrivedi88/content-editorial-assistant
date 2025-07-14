"""
Base Ambiguity Rule - Integrates with existing rules system to detect ambiguity in technical writing.

This rule coordinates different types of ambiguity detection and provides specific
context to the AI rewriter about how to resolve ambiguities.
"""

import os
import sys
from typing import List, Dict, Any, Optional

# Handle imports for different contexts
try:
    from ..rules.base_rule import BaseRule
except ImportError:
    try:
        from rules.base_rule import BaseRule
    except ImportError:
        # Add parent directory to path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from rules.base_rule import BaseRule

# Local imports
from .types import (
    AmbiguityType, AmbiguityCategory, AmbiguitySeverity, 
    AmbiguityContext, AmbiguityEvidence, AmbiguityDetection,
    ResolutionStrategy, AmbiguityConfig
)


class BaseAmbiguityRule(BaseRule):
    """
    Base rule for ambiguity detection in technical writing.
    
    This rule integrates with the existing rules system and coordinates
    specific ambiguity detectors to identify unclear or ambiguous content.
    """
    
    def __init__(self):
        super().__init__()
        self.config = AmbiguityConfig()
        self.detectors = {}
        self._initialize_detectors()
    
    def _get_rule_type(self) -> str:
        """Return the rule type identifier."""
        return 'ambiguity'
    
    def _initialize_detectors(self):
        """Initialize available ambiguity detectors."""
        try:
            from .detectors.missing_actor_detector import MissingActorDetector
            self.add_detector('missing_actor', MissingActorDetector(self.config))
        except ImportError:
            pass
        
        try:
            from .detectors.pronoun_ambiguity_detector import PronounAmbiguityDetector
            self.add_detector('pronoun_ambiguity', PronounAmbiguityDetector(self.config))
        except ImportError:
            pass
        
        try:
            from .detectors.unsupported_claims_detector import UnsupportedClaimsDetector
            self.add_detector('unsupported_claims', UnsupportedClaimsDetector(self.config))
        except ImportError:
            pass
        
        try:
            from .detectors.fabrication_risk_detector import FabricationRiskDetector
            self.add_detector('fabrication_risk', FabricationRiskDetector(self.config))
        except ImportError:
            pass
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyze text for ambiguity and return list of errors found.
        
        Args:
            text: Full text to analyze
            sentences: List of sentences
            nlp: SpaCy nlp object (required for ambiguity detection)
            context: Optional context information about the block being analyzed
            
        Returns:
            List of error dictionaries compatible with existing rules system
        """
        if not nlp:
            # Ambiguity detection requires SpaCy for linguistic analysis
            return []
        
        errors = []
        
        try:
            # Analyze each sentence for ambiguity
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue
                
                # Create context for this sentence
                sentence_context = self._create_sentence_context(
                    sentence, i, sentences, text, context
                )
                
                # Run all enabled detectors
                for detector_type, detector in self.detectors.items():
                    if detector and self._is_detector_enabled(detector_type):
                        ambiguity_detections = detector.detect(sentence_context, nlp)
                        
                        # Convert detections to error format
                        for detection in ambiguity_detections:
                            error = detection.to_error_dict()
                            errors.append(error)
            
        except Exception as e:
            # Log error but don't fail the entire analysis
            print(f"Error in ambiguity analysis: {e}")
        
        return errors
    
    def _create_sentence_context(self, sentence: str, sentence_index: int, 
                                sentences: List[str], full_text: str, 
                                block_context: Optional[dict]) -> AmbiguityContext:
        """Create context information for a sentence."""
        # Get preceding and following sentences for context
        preceding = sentences[max(0, sentence_index - 2):sentence_index] if sentence_index > 0 else []
        following = sentences[sentence_index + 1:sentence_index + 3] if sentence_index < len(sentences) - 1 else []
        
        # Don't include paragraph context for now - it's causing issues with duplicate analysis
        # paragraph_context = self._extract_paragraph_context(full_text, sentence)
        
        return AmbiguityContext(
            sentence_index=sentence_index,
            sentence=sentence,
            paragraph_context=None,  # Keep it simple for now
            preceding_sentences=preceding,
            following_sentences=following,
            document_context=block_context
        )
    
    def _extract_paragraph_context(self, full_text: str, sentence: str) -> Optional[str]:
        """Extract paragraph context for a sentence."""
        try:
            # Simple approach: find the paragraph containing this sentence
            paragraphs = full_text.split('\n\n')
            for paragraph in paragraphs:
                if sentence in paragraph:
                    return paragraph.strip()
        except Exception:
            pass
        return None
    
    def _is_detector_enabled(self, detector_type: str) -> bool:
        """Check if a detector type is enabled."""
        enabled_detectors = {
            'missing_actor': True,
            'pronoun_ambiguity': True,
            'unsupported_claims': True,
            'fabrication_risk': True
        }
        return enabled_detectors.get(detector_type, False)
    
    def add_detector(self, detector_type: str, detector):
        """Add a new detector to the system."""
        self.detectors[detector_type] = detector
    
    def get_detector(self, detector_type: str):
        """Get a specific detector."""
        return self.detectors.get(detector_type)
    
    def configure_detector(self, detector_type: str, **kwargs):
        """Configure a specific detector."""
        detector = self.detectors.get(detector_type)
        if detector and hasattr(detector, 'configure'):
            detector.configure(**kwargs)
    
    def get_ambiguity_statistics(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about detected ambiguities."""
        ambiguity_errors = [e for e in errors if e.get('type') == 'ambiguity']
        
        if not ambiguity_errors:
            return {}
        
        # Count by type
        type_counts = {}
        severity_counts = {}
        category_counts = {}
        
        for error in ambiguity_errors:
            # Count by subtype
            subtype = error.get('subtype', 'unknown')
            type_counts[subtype] = type_counts.get(subtype, 0) + 1
            
            # Count by severity
            severity = error.get('severity', 'medium')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Count by category
            category = error.get('category', 'semantic')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            'total_ambiguities': len(ambiguity_errors),
            'types': type_counts,
            'severities': severity_counts,
            'categories': category_counts,
            'ambiguity_rate': len(ambiguity_errors) / len(errors) if errors else 0
        }


class AmbiguityDetector:
    """
    Base class for specific ambiguity detectors.
    
    Each detector focuses on a specific type of ambiguity and provides
    specialized detection logic.
    """
    
    def __init__(self, config: AmbiguityConfig):
        self.config = config
        self.enabled = True
    
    def detect(self, context: AmbiguityContext, nlp) -> List[AmbiguityDetection]:
        """
        Detect ambiguities in the given context.
        
        Args:
            context: Sentence context for analysis
            nlp: SpaCy nlp object
            
        Returns:
            List of ambiguity detections
        """
        raise NotImplementedError("Subclasses must implement detect method")
    
    def configure(self, **kwargs):
        """Configure the detector with custom parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def enable(self):
        """Enable this detector."""
        self.enabled = True
    
    def disable(self):
        """Disable this detector."""
        self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if this detector is enabled."""
        return self.enabled 