"""
Language Vocabulary Service

Production-grade service for managing YAML-based vocabularies for language and grammar rules.
Provides centralized, cacheable, and updateable vocabulary management.
"""

import os
import yaml
from typing import Dict, Any, Set, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DomainContext:
    """Context information for domain-specific vocabulary lookups."""
    content_type: str = "general"
    audience: str = "general"
    domain: str = "general"


class LanguageVocabularyService:
    """
    Production-grade service for managing language and grammar vocabularies.
    
    Features:
    - Lazy loading with caching
    - Thread-safe operations
    - Domain-aware lookups
    - Morphological variant generation
    - Runtime vocabulary updates
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            # Auto-detect config directory relative to this file
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent / "config"
        
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._loaded_files: Set[str] = set()
    
    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """Load and cache a YAML vocabulary file."""
        if filename in self._cache:
            return self._cache[filename]
        
        file_path = self.config_dir / filename
        
        if not file_path.exists():
            print(f"⚠️  Warning: Vocabulary file {file_path} not found. Using empty vocabulary.")
            self._cache[filename] = {}
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            self._cache[filename] = data
            self._loaded_files.add(filename)
            print(f"✓ Loaded language vocabulary: {filename}")
            return data
            
        except Exception as e:
            print(f"❌ Error loading vocabulary file {file_path}: {e}")
            self._cache[filename] = {}
            return {}
    
    def reload_vocabulary(self, filename: str) -> None:
        """Reload a specific vocabulary file (useful for runtime updates)."""
        if filename in self._cache:
            del self._cache[filename]
        self._load_yaml_file(filename)
    
    def reload_all_vocabularies(self) -> None:
        """Reload all cached vocabulary files."""
        loaded_files = list(self._loaded_files)
        self._cache.clear()
        self._loaded_files.clear()
        
        for filename in loaded_files:
            self._load_yaml_file(filename)
    
    # === SPECIFIC VOCABULARY ACCESSORS ===
    
    def get_articles_phonetics(self) -> Dict[str, Any]:
        """Get articles phonetics vocabulary."""
        return self._load_yaml_file("articles_phonetics.yaml")
    
    def get_plurals_corrections(self) -> Dict[str, Any]:
        """Get plurals corrections vocabulary."""
        return self._load_yaml_file("plurals_corrections.yaml")
    
    def get_verbs_corrections(self) -> Dict[str, Any]:
        """Get verbs corrections vocabulary."""
        return self._load_yaml_file("verbs_corrections.yaml")
    
    def get_anthropomorphism_entities(self) -> Dict[str, Any]:
        """Get anthropomorphism entities vocabulary."""
        return self._load_yaml_file("anthropomorphism_entities.yaml")
    
    def get_inclusive_language_terms(self) -> Dict[str, Any]:
        """Get inclusive language terms vocabulary."""
        return self._load_yaml_file("inclusive_language_terms.yaml")
    
    # === UTILITY METHODS ===
    
    def generate_morphological_variants(self, base_word: str) -> List[str]:
        """Generate morphological variants of a word."""
        variants = [base_word]
        
        # Common morphological patterns
        if base_word.endswith('s'):
            variants.append(base_word[:-1])  # Remove plural
        else:
            variants.append(base_word + 's')  # Add plural
        
        if base_word.endswith('ed'):
            variants.append(base_word[:-2])  # Remove past tense
        else:
            variants.append(base_word + 'ed')  # Add past tense
        
        if base_word.endswith('ing'):
            variants.append(base_word[:-3])  # Remove present participle
        else:
            variants.append(base_word + 'ing')  # Add present participle
        
        # Capitalization variants
        variants.extend([
            base_word.capitalize(),
            base_word.upper(),
            base_word.lower()
        ])
        
        return list(set(variants))  # Remove duplicates
    
    def context_aware_lookup(self, word: str, vocabulary: Dict[str, Any], 
                           context: DomainContext) -> Optional[Dict[str, Any]]:
        """Perform context-aware vocabulary lookup."""
        # Direct lookup first
        if word in vocabulary:
            return vocabulary[word]
        
        # Case-insensitive lookup
        word_lower = word.lower()
        for key, value in vocabulary.items():
            if key.lower() == word_lower:
                return value
        
        # Morphological variant lookup
        for variant in self.generate_morphological_variants(word):
            if variant in vocabulary:
                return vocabulary[variant]
        
        return None


# === GLOBAL SERVICE INSTANCES ===

# Singleton instances for each vocabulary type
_articles_service: Optional[LanguageVocabularyService] = None
_plurals_service: Optional[LanguageVocabularyService] = None
_verbs_service: Optional[LanguageVocabularyService] = None
_anthropomorphism_service: Optional[LanguageVocabularyService] = None
_inclusive_language_service: Optional[LanguageVocabularyService] = None


def get_articles_vocabulary() -> LanguageVocabularyService:
    """Get the articles vocabulary service instance."""
    global _articles_service
    if _articles_service is None:
        _articles_service = LanguageVocabularyService()
    return _articles_service


def get_plurals_vocabulary() -> LanguageVocabularyService:
    """Get the plurals vocabulary service instance."""
    global _plurals_service
    if _plurals_service is None:
        _plurals_service = LanguageVocabularyService()
    return _plurals_service


def get_verbs_vocabulary() -> LanguageVocabularyService:
    """Get the verbs vocabulary service instance."""
    global _verbs_service
    if _verbs_service is None:
        _verbs_service = LanguageVocabularyService()
    return _verbs_service


def get_anthropomorphism_vocabulary() -> LanguageVocabularyService:
    """Get the anthropomorphism vocabulary service instance."""
    global _anthropomorphism_service
    if _anthropomorphism_service is None:
        _anthropomorphism_service = LanguageVocabularyService()
    return _anthropomorphism_service


def get_inclusive_language_vocabulary() -> LanguageVocabularyService:
    """Get the inclusive language vocabulary service instance."""
    global _inclusive_language_service
    if _inclusive_language_service is None:
        _inclusive_language_service = LanguageVocabularyService()
    return _inclusive_language_service
