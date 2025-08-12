"""
Production-Grade Entity Detection Service
Provides robust entity detection with multiple strategies and fallback mechanisms.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class DetectedEntity:
    """Standardized entity representation"""
    text: str
    start_char: int
    end_char: int
    label: str
    confidence: float
    source: str  # Which detector found this entity
    
    @property
    def span(self) -> Tuple[int, int]:
        return (self.start_char, self.end_char)

class EntityDetector(ABC):
    """Abstract base class for entity detectors"""
    
    @abstractmethod
    def detect_entities(self, text: str, target_labels: Optional[Set[str]] = None) -> List[DetectedEntity]:
        """Detect entities in text"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Detector name for identification"""
        pass

class SpacyEntityDetector(EntityDetector):
    """SpaCy-based entity detector with confidence scoring"""
    
    def __init__(self, nlp=None):
        self.nlp = nlp
        self._name = "spacy"
    
    @property
    def name(self) -> str:
        return self._name
    
    def detect_entities(self, text: str, target_labels: Optional[Set[str]] = None) -> List[DetectedEntity]:
        """Detect entities using SpaCy NLP"""
        if not self.nlp or not text:
            return []
        
        entities = []
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # Filter by target labels if specified
                if target_labels and ent.label_ not in target_labels:
                    continue
                
                # Calculate confidence (SpaCy doesn't provide direct confidence)
                confidence = self._estimate_confidence(ent)
                
                entities.append(DetectedEntity(
                    text=ent.text,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    label=ent.label_,
                    confidence=confidence,
                    source=self.name
                ))
                
        except Exception as e:
            logger.warning(f"SpaCy entity detection failed: {e}")
        
        return entities
    
    def _estimate_confidence(self, ent) -> float:
        """Estimate confidence for SpaCy entities"""
        # Simple heuristic: longer entities and common patterns get higher confidence
        base_confidence = 0.7
        
        # Boost confidence for longer entities
        if len(ent.text) > 3:
            base_confidence += 0.1
        
        # Boost confidence for entities with capital letters (proper nouns)
        if ent.text[0].isupper():
            base_confidence += 0.1
        
        # Boost confidence for ORG entities (companies)
        if ent.label_ == 'ORG':
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

class RegexEntityDetector(EntityDetector):
    """Regex-based entity detector for known patterns"""
    
    def __init__(self, patterns: Dict[str, List[str]]):
        self.patterns = patterns  # label -> list of regex patterns
        self._name = "regex"
    
    @property
    def name(self) -> str:
        return self._name
    
    def detect_entities(self, text: str, target_labels: Optional[Set[str]] = None) -> List[DetectedEntity]:
        """Detect entities using regex patterns"""
        if not text:
            return []
        
        entities = []
        
        for label, patterns in self.patterns.items():
            # Filter by target labels if specified
            if target_labels and label not in target_labels:
                continue
            
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        entities.append(DetectedEntity(
                            text=match.group(),
                            start_char=match.start(),
                            end_char=match.end(),
                            label=label,
                            confidence=0.9,  # High confidence for exact pattern matches
                            source=self.name
                        ))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return entities

class CompanyEntityDetector(EntityDetector):
    """Specialized detector for company names using company registry"""
    
    def __init__(self, company_registry):
        self.company_registry = company_registry
        self._name = "company_registry"
    
    @property
    def name(self) -> str:
        return self._name
    
    def detect_entities(self, text: str, target_labels: Optional[Set[str]] = None) -> List[DetectedEntity]:
        """Detect company entities using the company registry"""
        if not text:
            return []
        
        # Only process if we're looking for ORG entities or no filter specified
        if target_labels and 'ORG' not in target_labels:
            return []
        
        entities = []
        detections = self.company_registry.detect_companies_in_text(text)
        
        for matched_text, start_pos, end_pos, company in detections:
            confidence = 0.95  # High confidence for known companies
            
            # Adjust confidence based on company priority
            if company.priority == 'high':
                confidence = 0.98
            elif company.priority == 'low':
                confidence = 0.85
            
            entities.append(DetectedEntity(
                text=matched_text,
                start_char=start_pos,
                end_char=end_pos,
                label='ORG',
                confidence=confidence,
                source=self.name
            ))
        
        return entities

class EnsembleEntityDetector:
    """
    Production-grade ensemble entity detector that combines multiple detection strategies.
    
    Features:
    - Multiple detection strategies (SpaCy, Regex, Company Registry)
    - Conflict resolution and deduplication
    - Confidence-based ranking
    - Fallback mechanisms
    """
    
    def __init__(self, detectors: List[EntityDetector], confidence_threshold: float = 0.5):
        self.detectors = detectors
        self.confidence_threshold = confidence_threshold
        logger.info(f"Initialized ensemble detector with {len(detectors)} detectors")
    
    def detect_entities(self, text: str, target_labels: Optional[Set[str]] = None) -> List[DetectedEntity]:
        """Detect entities using ensemble of detectors"""
        if not text:
            return []
        
        all_entities = []
        
        # Run all detectors
        for detector in self.detectors:
            try:
                entities = detector.detect_entities(text, target_labels)
                all_entities.extend(entities)
                logger.debug(f"{detector.name} found {len(entities)} entities")
            except Exception as e:
                logger.warning(f"Detector {detector.name} failed: {e}")
        
        # Deduplicate and resolve conflicts
        final_entities = self._resolve_conflicts(all_entities)
        
        # Filter by confidence threshold
        final_entities = [e for e in final_entities if e.confidence >= self.confidence_threshold]
        
        # Sort by position in text
        final_entities.sort(key=lambda e: e.start_char)
        
        return final_entities
    
    def _resolve_conflicts(self, entities: List[DetectedEntity]) -> List[DetectedEntity]:
        """Resolve overlapping entities by keeping highest confidence"""
        if not entities:
            return []
        
        # Sort by confidence descending
        entities.sort(key=lambda e: e.confidence, reverse=True)
        
        final_entities = []
        used_spans = []
        
        for entity in entities:
            # Check if this entity overlaps with any already selected entity
            overlaps = any(
                self._spans_overlap((entity.start_char, entity.end_char), span)
                for span in used_spans
            )
            
            if not overlaps:
                final_entities.append(entity)
                used_spans.append((entity.start_char, entity.end_char))
        
        return final_entities
    
    def _spans_overlap(self, span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
        """Check if two character spans overlap"""
        return not (span1[1] <= span2[0] or span2[1] <= span1[0])

def create_production_entity_detector(nlp=None, company_registry=None) -> EnsembleEntityDetector:
    """Create a production-ready entity detector with all strategies"""
    detectors = []
    
    # Add SpaCy detector if available
    if nlp:
        detectors.append(SpacyEntityDetector(nlp))
    
    # Add company registry detector if available
    if company_registry:
        detectors.append(CompanyEntityDetector(company_registry))
    
    # Add regex detector for common patterns
    regex_patterns = {
        'ORG': [
            r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc|Corp|LLC|Ltd)\.?\b',
            r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+Corporation\b',
            r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+Company\b'
        ]
    }
    detectors.append(RegexEntityDetector(regex_patterns))
    
    return EnsembleEntityDetector(detectors, confidence_threshold=0.6)
