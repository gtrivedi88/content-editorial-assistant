"""
Vocabulary Service for Audience & Medium Rules

Manages YAML-based vocabularies with caching, morphological processing,
and context-aware evidence calculation for zero false positives.
"""

import os
import yaml
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)

@dataclass
class VocabularyEntry:
    """Represents a vocabulary entry with evidence scoring and context."""
    phrase: str
    evidence: float
    category: str
    variants: List[str] = field(default_factory=list)
    context_adjustments: Dict[str, float] = field(default_factory=dict)

@dataclass
class DomainContext:
    """Context information for domain-specific appropriateness."""
    content_type: str = ""
    domain: str = ""
    audience: str = ""
    block_type: str = ""

class VocabularyService:
    """
    vocabulary management service.
    
    Features:
    - YAML-based configuration management
    - Automatic morphological variant generation
    - Context-aware evidence calculation
    - Runtime vocabulary updates
    - Caching for performance
    """
    
    _instances: Dict[str, 'VocabularyService'] = {}
    
    def __new__(cls, config_name: str):
        """Singleton pattern for each vocabulary type."""
        if config_name not in cls._instances:
            cls._instances[config_name] = super(VocabularyService, cls).__new__(cls)
        return cls._instances[config_name]
    
    def __init__(self, config_name: str):
        """Initialize vocabulary service for a specific config."""
        if hasattr(self, '_initialized'):
            return
            
        self.config_name = config_name
        self.config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', f'{config_name}.yaml'
        )
        self._vocabulary: Dict[str, VocabularyEntry] = {}
        self._domain_appropriateness: Dict[str, List[str]] = {}
        self._content_adjustments: Dict[str, Dict[str, float]] = {}
        self._feedback_patterns: Dict[str, Any] = {}
        self._morphological_cache: Dict[str, List[str]] = {}
        
        self._load_vocabulary()
        self._initialized = True
    
    def _load_vocabulary(self):
        """Load vocabulary from YAML configuration."""
        logger.info(f"Loading vocabulary from {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load based on config type
            if self.config_name == 'tone_vocabularies':
                self._load_tone_vocabulary(config)
            elif self.config_name == 'conversational_vocabularies':
                self._load_conversational_vocabulary(config)
            elif self.config_name == 'global_patterns':
                self._load_global_patterns(config)
            elif self.config_name == 'llm_patterns':
                self._load_llm_patterns(config)
            
            logger.info(f"Loaded {len(self._vocabulary)} vocabulary entries")
            
        except FileNotFoundError:
            logger.error(f"Vocabulary file not found: {self.config_path}")
            self._vocabulary = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing vocabulary YAML: {e}")
            self._vocabulary = {}
        except Exception as e:
            logger.error(f"Unexpected error loading vocabulary: {e}")
            self._vocabulary = {}
    
    def _load_tone_vocabulary(self, config: Dict[str, Any]):
        """Load tone-specific vocabulary patterns."""
        business_jargon = config.get('business_jargon', {})
        
        # Load all categories of business jargon
        for category_name, entries in business_jargon.items():
            if isinstance(entries, list):
                for entry in entries:
                    phrase = entry['phrase']
                    evidence = entry['evidence']
                    category = entry.get('category', 'unknown')
                    variants = entry.get('variants', [])
                    
                    # Create main entry
                    vocab_entry = VocabularyEntry(
                        phrase=phrase,
                        evidence=evidence,
                        category=category,
                        variants=variants
                    )
                    self._vocabulary[phrase] = vocab_entry
                    
                    # Add variants
                    for variant in variants:
                        self._vocabulary[variant] = VocabularyEntry(
                            phrase=variant,
                            evidence=evidence,
                            category=category,
                            variants=[phrase]  # Link back to main phrase
                        )
        
        # Load domain appropriateness
        self._domain_appropriateness = config.get('domain_appropriateness', {})
        
        # Load content type appropriateness
        self._content_adjustments = config.get('content_type_appropriateness', {})
        
        # Load feedback patterns
        self._feedback_patterns = config.get('feedback_patterns', {})
    
    def _load_conversational_vocabulary(self, config: Dict[str, Any]):
        """Load conversational style vocabulary patterns."""
        formal_to_conv = config.get('formal_to_conversational', {})
        
        # Load all categories of formal words
        for category_name, entries in formal_to_conv.items():
            if isinstance(entries, list):
                for entry in entries:
                    formal = entry['formal']
                    conversational = entry['conversational']
                    evidence_base = entry['evidence_base']
                    category = entry.get('category', 'unknown')
                    
                    # Create vocabulary entry
                    vocab_entry = VocabularyEntry(
                        phrase=formal,
                        evidence=evidence_base,
                        category=category,
                        variants=self._generate_morphological_variants(formal)
                    )
                    vocab_entry.context_adjustments['conversational_alternative'] = conversational
                    self._vocabulary[formal] = vocab_entry
                    
                    # Add morphological variants
                    for variant in vocab_entry.variants:
                        self._vocabulary[variant] = VocabularyEntry(
                            phrase=variant,
                            evidence=evidence_base,
                            category=category,
                            variants=[formal]
                        )
        
        # Load context adjustments
        self._content_adjustments = config.get('context_adjustments', {})
        
        # Load feedback patterns
        self._feedback_patterns = config.get('feedback_patterns', {})
    
    def _load_global_patterns(self, config: Dict[str, Any]):
        """Load global audience patterns."""
        negative_constructions = config.get('negative_constructions', {})
        
        # Load problematic patterns
        patterns = negative_constructions.get('problematic_patterns', [])
        for pattern_entry in patterns:
            pattern = pattern_entry['pattern']
            evidence_base = pattern_entry['evidence_base']
            severity = pattern_entry.get('severity', 'medium')
            alternatives = pattern_entry.get('alternatives', [])
            
            vocab_entry = VocabularyEntry(
                phrase=pattern,
                evidence=evidence_base,
                category=f'negative_{severity}',
                variants=alternatives
            )
            self._vocabulary[pattern] = vocab_entry
        
        # Load context appropriateness
        self._content_adjustments = config.get('context_appropriateness', {})
        
        # Load sentence length patterns
        self._sentence_length_config = config.get('sentence_length', {})
        
        # Load feedback patterns
        self._feedback_patterns = config.get('feedback_patterns', {})
    
    def _load_llm_patterns(self, config: Dict[str, Any]):
        """Load LLM consumability patterns."""
        # Load content length thresholds
        self._length_thresholds = config.get('content_length', {})
        
        # Load completeness indicators
        completeness = config.get('completeness_indicators', {})
        patterns = completeness.get('incomplete_patterns', [])
        for pattern_entry in patterns:
            pattern = pattern_entry['pattern']
            evidence_base = pattern_entry['evidence_base']
            category = pattern_entry.get('category', 'unknown')
            
            vocab_entry = VocabularyEntry(
                phrase=pattern,
                evidence=evidence_base,
                category=category
            )
            self._vocabulary[pattern] = vocab_entry
        
        # Load other patterns
        self._exemptions = config.get('exemptions', {})
        self._ui_complexity = config.get('ui_complexity', {})
        self._feedback_patterns = config.get('feedback_patterns', {})
    
    def _generate_morphological_variants(self, word: str) -> List[str]:
        """Generate morphological variants for a word."""
        if word in self._morphological_cache:
            return self._morphological_cache[word]
        
        variants = []
        
        # Basic verb inflections
        if word.endswith('e'):
            variants.extend([
                word + 's',      # utilizes
                word + 'd',      # utilized
                word[:-1] + 'ing'  # utilizing
            ])
        else:
            variants.extend([
                word + 's',      # demonstrates
                word + 'd',      # demonstrated  
                word + 'ing'     # demonstrating
            ])
        
        # Past participle forms
        if word.endswith('e'):
            variants.append(word + 'd')
        elif word.endswith('y'):
            variants.append(word[:-1] + 'ied')
        else:
            variants.append(word + 'ed')
        
        # Adverb forms for adjectives
        if word.endswith('al'):
            variants.append(word + 'ly')  # optimal -> optimally
        elif not word.endswith('ly'):
            variants.append(word + 'ly')
        
        # Remove duplicates and cache
        variants = list(set(variants))
        self._morphological_cache[word] = variants
        return variants
    
    def get_vocabulary_entry(self, phrase: str) -> Optional[VocabularyEntry]:
        """Get vocabulary entry for a phrase."""
        return self._vocabulary.get(phrase.lower())
    
    def is_domain_appropriate(self, phrase: str, context: DomainContext) -> bool:
        """Check if phrase is appropriate for the given domain/context."""
        phrase_lower = phrase.lower()
        
        # Check domain appropriateness
        if context.domain in self._domain_appropriateness:
            domain_phrases = [p.lower() for p in self._domain_appropriateness[context.domain]]
            if phrase_lower in domain_phrases:
                # For tone rules, only technical content allows domain-appropriate phrases
                if self.config_name == 'tone_vocabularies':
                    return context.content_type == 'technical'
                return True
        
        # Check content type appropriateness
        if context.content_type in self._content_adjustments:
            content_phrases = self._content_adjustments[context.content_type]
            if isinstance(content_phrases, list):
                content_phrases_lower = [p.lower() for p in content_phrases]
                return phrase_lower in content_phrases_lower
        
        return False
    
    def calculate_context_adjusted_evidence(self, phrase: str, base_evidence: float, context: DomainContext) -> float:
        """Calculate evidence score adjusted for context."""
        evidence = base_evidence
        
        # Apply content type adjustments
        if self.config_name == 'conversational_vocabularies':
            formal_contexts = self._content_adjustments.get('formal_appropriate_contexts', {})
            if context.content_type in formal_contexts:
                reduction = formal_contexts[context.content_type].get('evidence_reduction', 0)
                evidence -= reduction
            
            # Apply audience adjustments
            formal_audiences = self._content_adjustments.get('formal_appropriate_audiences', {})
            if context.audience in formal_audiences:
                reduction = formal_audiences[context.audience].get('evidence_reduction', 0)
                evidence -= reduction
        
        elif self.config_name == 'global_patterns':
            # Technical warning adjustments
            technical_warnings = self._content_adjustments.get('technical_warnings', {})
            if context.content_type == 'technical':
                warning_patterns = technical_warnings.get('patterns', [])
                if any(pattern in phrase.lower() for pattern in warning_patterns):
                    evidence -= technical_warnings.get('evidence_reduction', 0)
        
        return max(0.0, min(1.0, evidence))
    
    def get_feedback_patterns(self) -> Dict[str, Any]:
        """Get feedback patterns for learning."""
        return self._feedback_patterns
    
    def add_feedback_pattern(self, phrase: str, accepted: bool, context: DomainContext):
        """Add user feedback to improve future detection."""
        if accepted:
            self._feedback_patterns.setdefault('accepted_phrases', []).append(phrase)
        else:
            self._feedback_patterns.setdefault('flagged_phrases', []).append(phrase)
        
        # Save feedback (in production, this would update the YAML file)
        logger.info(f"Added feedback: {phrase} -> {'accepted' if accepted else 'flagged'}")
    
    def get_length_thresholds(self, content_type: str = 'general') -> Dict[str, float]:
        """Get length-based evidence thresholds for LLM consumability."""
        if self.config_name == 'llm_patterns':
            thresholds = self._length_thresholds.get('thresholds', {})
            return thresholds.get(content_type, thresholds.get('general', {}))
        return {}
    
    def is_exempt_content(self, text: str, context: DomainContext) -> bool:
        """Check if content should be exempt from analysis."""
        if self.config_name == 'llm_patterns':
            exemptions = self._exemptions
            
            # Check content type exemptions
            exempt_types = exemptions.get('exempt_content_types', [])
            if context.content_type in exempt_types:
                return True
            
            # Check block type exemptions  
            exempt_blocks = exemptions.get('exempt_block_types', [])
            if context.block_type in exempt_blocks:
                return True
            
            # Check intentionally short patterns
            intentionally_short = exemptions.get('intentionally_short', [])
            text_upper = text.upper()
            if any(pattern in text_upper for pattern in intentionally_short):
                return True
        
        return False
    
    def reload_vocabulary(self):
        """Reload vocabulary from YAML file (for runtime updates)."""
        logger.info(f"Reloading vocabulary: {self.config_name}")
        self._vocabulary.clear()
        self._morphological_cache.clear()
        self._load_vocabulary()
    
    @classmethod
    def reload_all_vocabularies(cls):
        """Reload all vocabulary instances."""
        for instance in cls._instances.values():
            instance.reload_vocabulary()

# Factory functions for easy access
def get_tone_vocabulary() -> VocabularyService:
    """Get tone vocabulary service."""
    return VocabularyService('tone_vocabularies')

def get_conversational_vocabulary() -> VocabularyService:
    """Get conversational vocabulary service."""
    return VocabularyService('conversational_vocabularies')

def get_global_patterns() -> VocabularyService:
    """Get global patterns service."""
    return VocabularyService('global_patterns')

def get_llm_patterns() -> VocabularyService:
    """Get LLM patterns service."""
    return VocabularyService('llm_patterns')
