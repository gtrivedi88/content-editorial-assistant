"""
Structure Vocabulary Service for Structure & Format Rules

Manages YAML-based vocabularies with caching, evidence calculation,
and context-aware adjustments for structure-specific rule patterns.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class StructureVocabularyEntry:
    """Represents a structure vocabulary entry with evidence scoring and context."""
    phrase: str
    evidence: float
    category: str
    alternatives: List[str] = field(default_factory=list)
    context_adjustments: Dict[str, float] = field(default_factory=dict)
    description: Optional[str] = None
    severity: Optional[str] = None

class StructureVocabularyService:
    """
    YAML-based vocabulary management service for structure & format rules.
    
    Features:
    - YAML-based configuration management
    - Context-aware evidence calculation
    - Runtime vocabulary updates
    - Caching for performance
    - Structure-specific pattern management
    """
    
    _instance: Optional['StructureVocabularyService'] = None
    
    def __new__(cls):
        """Singleton pattern for vocabulary service."""
        if cls._instance is None:
            cls._instance = super(StructureVocabularyService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize vocabulary service."""
        if hasattr(self, '_initialized'):
            return
            
        self.config_path = self._get_config_path()
        self._vocabularies: Dict[str, Dict[str, Any]] = {}
        self._load_vocabularies()
        self._initialized = True
    
    def _get_config_path(self) -> str:
        """Get path to structure vocabularies YAML file."""
        current_dir = Path(__file__).parent
        return str(current_dir / ".." / "config" / "structure_vocabularies.yaml")
    
    def _load_vocabularies(self):
        """Load all structure vocabularies from YAML configuration."""
        logger.info(f"Loading structure vocabularies from {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Store the full configuration for easy access
            self._vocabularies = config
            
            # Log vocabulary counts
            vocab_counts = {}
            if 'exaggerated_language' in config:
                vocab_counts['exaggerated_words'] = len(config['exaggerated_language'].get('high_severity', [])) + len(config['exaggerated_language'].get('medium_severity', []))
            if 'note_labels' in config:
                vocab_counts['note_labels'] = len(config['note_labels'].get('approved_labels', []))
            if 'admonition_labels' in config:
                vocab_counts['admonition_labels'] = len(config['admonition_labels'].get('approved_labels', []))
            
            logger.info(f"Loaded structure vocabularies: {vocab_counts}")
            
        except FileNotFoundError:
            logger.error(f"Structure vocabulary file not found: {self.config_path}")
            self._vocabularies = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing structure vocabulary YAML: {e}")
            self._vocabularies = {}
        except Exception as e:
            logger.error(f"Unexpected error loading structure vocabularies: {e}")
            self._vocabularies = {}
    
    def get_exaggerated_words(self) -> Dict[str, StructureVocabularyEntry]:
        """Get exaggerated language vocabulary for MessagesRule."""
        exaggerated_words = {}
        
        exaggerated_config = self._vocabularies.get('exaggerated_language', {})
        
        # Process high severity words
        for item in exaggerated_config.get('high_severity', []):
            entry = StructureVocabularyEntry(
                phrase=item['phrase'],
                evidence=item['evidence'],
                category=item['category'],
                alternatives=item.get('alternatives', []),
                context_adjustments=item.get('context_adjustments', {})
            )
            exaggerated_words[item['phrase']] = entry
        
        # Process medium severity words
        for item in exaggerated_config.get('medium_severity', []):
            entry = StructureVocabularyEntry(
                phrase=item['phrase'],
                evidence=item['evidence'],
                category=item['category'],
                alternatives=item.get('alternatives', [])
            )
            exaggerated_words[item['phrase']] = entry
        
        return exaggerated_words
    
    def get_note_labels(self) -> Dict[str, StructureVocabularyEntry]:
        """Get note labels vocabulary for NotesRule."""
        note_labels = {}
        
        note_config = self._vocabularies.get('note_labels', {})
        
        for item in note_config.get('approved_labels', []):
            entry = StructureVocabularyEntry(
                phrase=item['label'],
                evidence=item['evidence'],
                category=item['category'],
                description=item.get('description')
            )
            note_labels[item['label']] = entry
        
        return note_labels
    
    def get_admonition_labels(self) -> Dict[str, StructureVocabularyEntry]:
        """Get admonition labels vocabulary for AdmonitionsRule."""
        admonition_labels = {}
        
        admonition_config = self._vocabularies.get('admonition_labels', {})
        
        for item in admonition_config.get('approved_labels', []):
            entry = StructureVocabularyEntry(
                phrase=item['label'],
                evidence=item['evidence'],
                category=item['category'],
                description=item.get('description'),
                severity=item.get('severity')
            )
            admonition_labels[item['label']] = entry
        
        return admonition_labels
    
    def get_procedural_indicators(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get procedural indicators for ProceduresRule."""
        return self._vocabularies.get('procedural_indicators', {})
    
    def get_ui_elements(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get UI elements vocabulary for HighlightingRule."""
        return self._vocabularies.get('ui_elements', {})
    
    def get_formatting_context(self) -> Dict[str, List[str]]:
        """Get formatting context indicators for ParagraphsRule."""
        return self._vocabularies.get('formatting_context', {})
    
    def get_heading_patterns(self) -> Dict[str, List[str]]:
        """Get heading patterns for HeadingsRule."""
        return self._vocabularies.get('heading_patterns', {})
    
    def get_technical_context_indicators(self) -> Dict[str, List[str]]:
        """Get technical context indicators for context-aware evidence calculation."""
        return self._vocabularies.get('technical_context_indicators', {})
    
    def get_list_indicators(self) -> Dict[str, List[str]]:
        """Get list formatting indicators."""
        return self._vocabularies.get('list_indicators', {})
    
    def get_content_type_modifiers(self) -> Dict[str, List[str]]:
        """Get content type groupings for evidence adjustments."""
        return self._vocabularies.get('content_type_modifiers', {})
    
    def get_base_evidence_scores(self) -> Dict[str, float]:
        """Get base evidence scores for different violation types."""
        return self._vocabularies.get('base_evidence_scores', {})
    
    def calculate_context_adjusted_evidence(self, base_evidence: float, word: str, 
                                         context: Dict[str, Any]) -> float:
        """
        Calculate context-adjusted evidence score using vocabulary adjustments.
        
        Args:
            base_evidence: Base evidence score
            word: The word/phrase being evaluated
            context: Document context
            
        Returns:
            Adjusted evidence score
        """
        adjusted_evidence = base_evidence
        
        # Get exaggerated words with context adjustments
        exaggerated_words = self.get_exaggerated_words()
        
        if word.lower() in exaggerated_words:
            entry = exaggerated_words[word.lower()]
            content_type = context.get('content_type', '')
            
            # Apply context adjustments from vocabulary
            for context_key, adjustment in entry.context_adjustments.items():
                if context_key in content_type:
                    adjusted_evidence += adjustment
                    break
        
        return max(0.0, min(1.0, adjusted_evidence))
    
    def is_technical_context(self, sentence: str, context: Dict[str, Any]) -> bool:
        """Check if we're in a technical context based on vocabulary indicators."""
        technical_indicators = self.get_technical_context_indicators()
        sentence_lower = sentence.lower()
        content_type = context.get('content_type', '').lower()
        
        # Check for technical content type
        if content_type in ['technical', 'programming', 'api', 'reference']:
            return True
        
        # Check for technical indicators in sentence
        for category, indicators in technical_indicators.items():
            if any(indicator in sentence_lower for indicator in indicators):
                return True
        
        return False
    
    def get_invalid_label_suggestions(self, invalid_label: str) -> List[str]:
        """Get suggestions for invalid admonition labels."""
        invalid_suggestions = self._vocabularies.get('admonition_labels', {}).get('invalid_suggestions', {})
        return invalid_suggestions.get(invalid_label.upper(), ['IMPORTANT', 'NOTE'])
    
    def reload_vocabularies(self):
        """Reload vocabularies from YAML file (for runtime updates)."""
        logger.info("Reloading structure vocabularies")
        self._load_vocabularies()

# Singleton instance getter functions
def get_structure_vocabulary_service() -> StructureVocabularyService:
    """Get the singleton structure vocabulary service instance."""
    return StructureVocabularyService()

def get_exaggerated_words() -> Dict[str, StructureVocabularyEntry]:
    """Get exaggerated language vocabulary."""
    return get_structure_vocabulary_service().get_exaggerated_words()

def get_note_labels() -> Dict[str, StructureVocabularyEntry]:
    """Get note labels vocabulary.""" 
    return get_structure_vocabulary_service().get_note_labels()

def get_admonition_labels() -> Dict[str, StructureVocabularyEntry]:
    """Get admonition labels vocabulary."""
    return get_structure_vocabulary_service().get_admonition_labels()

def get_procedural_indicators() -> Dict[str, List[Dict[str, Any]]]:
    """Get procedural indicators."""
    return get_structure_vocabulary_service().get_procedural_indicators()

def get_ui_elements() -> Dict[str, List[Dict[str, Any]]]:
    """Get UI elements vocabulary."""
    return get_structure_vocabulary_service().get_ui_elements()

def get_formatting_context() -> Dict[str, List[str]]:
    """Get formatting context indicators."""
    return get_structure_vocabulary_service().get_formatting_context()

def get_heading_patterns() -> Dict[str, List[str]]:
    """Get heading patterns."""
    return get_structure_vocabulary_service().get_heading_patterns()

def get_technical_context_indicators() -> Dict[str, List[str]]:
    """Get technical context indicators."""
    return get_structure_vocabulary_service().get_technical_context_indicators()

def is_technical_context(sentence: str, context: Dict[str, Any]) -> bool:
    """Check if we're in a technical context."""
    return get_structure_vocabulary_service().is_technical_context(sentence, context)
