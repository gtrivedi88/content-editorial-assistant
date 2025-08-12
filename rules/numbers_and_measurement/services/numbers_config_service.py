"""
Numbers Configuration Service

Manages YAML-based configurations for numbers and measurement rules
with caching, evidence calculation, and context-aware adjustments.
"""

import os
import yaml
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class ConfigEntry:
    """Represents a configuration entry with evidence scoring and context."""
    pattern: str
    evidence_base: float
    category: str
    alternatives: List[str] = field(default_factory=list)
    context_adjustments: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class NumbersContext:
    """Context information for numbers and measurement rules."""
    content_type: str = ""
    audience: str = ""
    domain: str = ""
    block_type: str = ""

class NumbersConfigService:
    """
    Configuration management service for numbers and measurement rules.
    
    Features:
    - YAML-based configuration management
    - Context-aware evidence calculation
    - Runtime configuration updates
    - Caching for performance
    - Pattern compilation and optimization
    """
    
    _instances: Dict[str, 'NumbersConfigService'] = {}
    
    def __new__(cls, config_name: str):
        """Singleton pattern for each configuration type."""
        if config_name not in cls._instances:
            cls._instances[config_name] = super().__new__(cls)
            cls._instances[config_name]._initialized = False
        return cls._instances[config_name]
    
    def __init__(self, config_name: str):
        """Initialize the configuration service."""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.config_name = config_name
        self._config_cache: Dict[str, Any] = {}
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._last_modified: Optional[float] = None
        self._config_path = self._get_config_path()
        
        # Load initial configuration
        self._load_config()
        self._initialized = True
    
    def _get_config_path(self) -> str:
        """Get the full path to the configuration file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(os.path.dirname(current_dir), 'config')
        return os.path.join(config_dir, f'{self.config_name}.yaml')
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(self._config_path):
                logger.warning(f"Configuration file not found: {self._config_path}")
                self._config_cache = {}
                return
            
            # Check if file has been modified
            current_modified = os.path.getmtime(self._config_path)
            if self._last_modified and current_modified <= self._last_modified:
                return  # No need to reload
            
            with open(self._config_path, 'r', encoding='utf-8') as file:
                self._config_cache = yaml.safe_load(file) or {}
            
            self._last_modified = current_modified
            self._compile_patterns()
            
            logger.info(f"Loaded configuration: {self.config_name}")
            
        except Exception as e:
            logger.error(f"Error loading configuration {self.config_name}: {e}")
            self._config_cache = {}
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._compiled_patterns.clear()
        
        # Compile detection patterns
        detection_patterns = self._config_cache.get('detection_patterns', {})
        for pattern_name, pattern_config in detection_patterns.items():
            if isinstance(pattern_config, dict) and 'pattern' in pattern_config:
                try:
                    flags = 0
                    if pattern_config.get('flags'):
                        flag_list = pattern_config['flags']
                        if isinstance(flag_list, str):
                            flag_list = [flag_list]
                        for flag in flag_list:
                            if flag.upper() == 'IGNORECASE':
                                flags |= re.IGNORECASE
                            elif flag.upper() == 'MULTILINE':
                                flags |= re.MULTILINE
                    
                    compiled_pattern = re.compile(pattern_config['pattern'], flags)
                    self._compiled_patterns[pattern_name] = compiled_pattern
                except re.error as e:
                    logger.error(f"Error compiling pattern {pattern_name}: {e}")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        self._load_config()  # Check for updates
        return self._config_cache.get(key, default)
    
    def get_pattern(self, pattern_name: str) -> Optional[re.Pattern]:
        """Get compiled regex pattern by name."""
        self._load_config()  # Check for updates
        return self._compiled_patterns.get(pattern_name)
    
    def get_evidence_base(self, category: str, item_key: str) -> float:
        """Get base evidence score for a category item."""
        category_data = self.get_config(category, {})
        if isinstance(category_data, dict):
            for item in category_data.values():
                if isinstance(item, list):
                    for entry in item:
                        if isinstance(entry, dict) and entry.get('pattern') == item_key:
                            return entry.get('evidence_base', 0.5)
                elif isinstance(item, dict) and item.get('pattern') == item_key:
                    return item.get('evidence_base', 0.5)
        return 0.5
    
    def calculate_context_evidence(self, base_evidence: float, context: NumbersContext, 
                                 category: str = "") -> float:
        """Calculate evidence score with context adjustments."""
        evidence = base_evidence
        
        # Get context adjustments from config
        context_adjustments = self.get_config('context_adjustments', {})
        
        # Apply audience modifiers
        audience_modifiers = context_adjustments.get('audience_modifiers', {})
        if context.audience in audience_modifiers:
            modifier = audience_modifiers[context.audience]
            if 'evidence_increase' in modifier:
                evidence += modifier['evidence_increase']
            elif 'evidence_decrease' in modifier:
                evidence += modifier['evidence_decrease']  # Note: decrease values should be negative
        
        # Apply content type modifiers
        content_type_modifiers = context_adjustments.get('content_type_modifiers', {})
        if context.content_type in content_type_modifiers:
            modifier = content_type_modifiers[context.content_type]
            if 'evidence_increase' in modifier:
                evidence += modifier['evidence_increase']
            elif 'evidence_decrease' in modifier:
                evidence += modifier['evidence_decrease']
        
        # Apply domain-specific modifiers
        domain_modifiers = context_adjustments.get('domain_specific', {})
        for domain_name, domain_config in domain_modifiers.items():
            if context.domain == domain_name or context.content_type in domain_config.get('categories', []):
                if 'evidence_increase' in domain_config:
                    evidence += domain_config['evidence_increase']
        
        return max(0.0, min(1.0, evidence))
    
    def get_surgical_guards(self) -> List[str]:
        """Get surgical guard patterns to exclude from detection."""
        guards = self.get_config('surgical_guards', {})
        all_patterns = []
        
        for guard_category, patterns in guards.items():
            if isinstance(patterns, list):
                all_patterns.extend(patterns)
            elif isinstance(patterns, str):
                all_patterns.append(patterns)
        
        return all_patterns
    
    def get_message_template(self, evidence_level: str, message_type: str) -> str:
        """Get evidence-aware message template."""
        messages = self.get_config('messages', {})
        
        # Determine evidence level category
        if evidence_level not in messages:
            if float(evidence_level) > 0.7:
                evidence_level = 'high_evidence'
            elif float(evidence_level) > 0.5:
                evidence_level = 'medium_evidence'
            else:
                evidence_level = 'low_evidence'
        
        level_messages = messages.get(evidence_level, {})
        return level_messages.get(message_type, "Formatting could be improved.")
    
    def get_suggestions(self, evidence_level: str, suggestion_type: str) -> List[str]:
        """Get evidence-aware suggestions."""
        suggestions = self.get_config('suggestions', {})
        
        # Determine evidence level category if numeric value provided
        if evidence_level not in suggestions:
            try:
                level_float = float(evidence_level)
                if level_float > 0.7:
                    evidence_level = 'high_evidence'
                elif level_float > 0.5:
                    evidence_level = 'medium_evidence'
                else:
                    evidence_level = 'low_evidence'
            except ValueError:
                # Already a string level, use as-is
                pass
        
        type_suggestions = suggestions.get(suggestion_type, {})
        level_suggestions = type_suggestions.get(evidence_level, [])
        
        return level_suggestions[:3] if isinstance(level_suggestions, list) else []
    
    def check_surgical_guard(self, text: str, context: NumbersContext) -> bool:
        """Check if text should be excluded by surgical guards."""
        guard_patterns = self.get_surgical_guards()
        text_lower = text.lower()
        
        for pattern in guard_patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            except re.error:
                # If pattern is not regex, do simple string match
                if pattern.lower() in text_lower:
                    return True
        
        return False
    
    def get_unit_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all unit categories and their units."""
        return self.get_config('unit_categories', {})
    
    def get_currency_patterns(self) -> Dict[str, Any]:
        """Get currency patterns and symbols."""
        return {
            'symbols': self.get_config('currency_symbols', {}),
            'multipliers': self.get_config('currency_multipliers', {}),
            'iso_codes': self.get_config('iso_currency_codes', {})
        }
    
    def get_date_time_patterns(self) -> Dict[str, Any]:
        """Get date and time formatting patterns."""
        return {
            'date_formats': self.get_config('date_formats', {}),
            'time_formats': self.get_config('time_formats', {}),
            'regional_preferences': self.get_config('regional_preferences', {})
        }
    
    def get_number_formatting_rules(self) -> Dict[str, Any]:
        """Get number formatting rules and patterns."""
        return {
            'thousands_separators': self.get_config('thousands_separators', {}),
            'decimal_formatting': self.get_config('decimal_formatting', {}),
            'size_based_rules': self.get_config('size_based_rules', {})
        }
    
    def get_numerals_words_rules(self) -> Dict[str, Any]:
        """Get numerals vs words consistency rules."""
        return {
            'number_words': self.get_config('number_words', {}),
            'consistency_rules': self.get_config('consistency_rules', {}),
            'special_cases': self.get_config('special_cases', {})
        }
    
    def refresh_config(self) -> None:
        """Force reload configuration from file."""
        self._last_modified = None
        self._load_config()
        logger.info(f"Refreshed configuration: {self.config_name}")

# Pre-configured service instances
class ConfigServices:
    """Convenience class for accessing configuration services."""
    
    @staticmethod
    def currency() -> NumbersConfigService:
        """Get currency patterns configuration service."""
        return NumbersConfigService('currency_patterns')
    
    @staticmethod
    def units() -> NumbersConfigService:
        """Get measurement units configuration service."""
        return NumbersConfigService('measurement_units')
    
    @staticmethod
    def dates() -> NumbersConfigService:
        """Get date time formats configuration service."""
        return NumbersConfigService('date_time_formats')
    
    @staticmethod
    def numbers() -> NumbersConfigService:
        """Get number formatting configuration service."""
        return NumbersConfigService('number_formatting')
    
    @staticmethod
    def numerals_words() -> NumbersConfigService:
        """Get numerals vs words configuration service."""
        return NumbersConfigService('numerals_vs_words')
