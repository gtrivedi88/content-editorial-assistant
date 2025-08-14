"""
Punctuation Configuration Service
Manages YAML-based configuration for punctuation rules with caching and performance optimization.
"""

import os
import yaml
from typing import Dict, List, Set, Any, Optional, Tuple
from functools import lru_cache
import threading

class PunctuationConfigService:
    """
    Service for managing punctuation rule configurations from YAML files.
    Provides cached access to patterns, abbreviations, compounds, and context guards.
    """
    
    _instance = None
    _lock = threading.Lock()
    _config_cache = {}
    _config_dir = None
    
    def __new__(cls):
        """Singleton pattern for configuration service."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PunctuationConfigService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration service if not already initialized."""
        if not getattr(self, '_initialized', False):
            self._config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
            self._config_cache = {}
            self._initialized = True
    
    @lru_cache(maxsize=128)
    def _load_yaml_config(self, config_name: str) -> Dict[str, Any]:
        """
        Load and cache YAML configuration file.
        
        Args:
            config_name: Name of the configuration file (without .yaml extension)
            
        Returns:
            Dict containing the configuration data
        """
        config_path = os.path.join(self._config_dir, f"{config_name}.yaml")
        
        if not os.path.exists(config_path):
            # Return empty config if file doesn't exist
            return {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except (yaml.YAMLError, IOError) as e:
            # Log error and return empty config
            print(f"Warning: Could not load {config_name}.yaml: {e}")
            return {}
    
    # === PUNCTUATION PATTERNS ===
    
    def get_warning_indicators(self) -> Dict[str, List[str]]:
        """Get warning and alert indicators for exclamation points and other rules."""
        config = self._load_yaml_config('punctuation_patterns')
        return config.get('warning_indicators', {
            'primary_warnings': ['warning', 'caution', 'danger', 'important', 'note'],
            'command_words': ['must', 'should', 'required', 'ensure', 'verify']
        })
    
    def get_academic_notation(self) -> Dict[str, List[str]]:
        """Get academic and reference notation terms."""
        config = self._load_yaml_config('punctuation_patterns')
        return config.get('academic_notation', {
            'reference_terms': ['vol', 'volume', 'issue', 'page', 'line'],
            'abbreviations': ['p', 'pp', 'ch', 'sec', 'ed']
        })
    
    def get_list_indicators(self) -> Dict[str, List[str]]:
        """Get list and hierarchical indicators for complex list detection."""
        config = self._load_yaml_config('punctuation_patterns')
        return config.get('list_indicators', {
            'professional_titles': ['ceo', 'cto', 'cfo', 'director'],
            'formal_titles': ['dr', 'prof', 'mr', 'mrs', 'ms']
        })
    
    def get_measurement_units(self) -> Dict[str, List[str]]:
        """Get measurement units for slash and other rules."""
        config = self._load_yaml_config('punctuation_patterns')
        return config.get('measurement_units', {
            'distance': ['km', 'mile', 'meter', 'yard'],
            'time': ['hour', 'minute', 'second', 'day'],
            'speed': ['mph', 'kph', 'rpm', 'bpm', 'fps']
        })
    
    def get_file_path_indicators(self) -> Dict[str, List[str]]:
        """Get file and path indicators for slash rules."""
        config = self._load_yaml_config('punctuation_patterns')
        return config.get('file_path_indicators', {
            'system_directories': ['usr', 'bin', 'etc', 'var', 'home'],
            'filesystem_terms': ['directory', 'folder', 'path', 'file']
        })
    
    # === LEGITIMATE ABBREVIATIONS ===
    
    def get_time_abbreviations(self) -> Dict[str, Any]:
        """Get time-related abbreviations that should not be flagged."""
        config = self._load_yaml_config('legitimate_abbreviations')
        return config.get('time_abbreviations', {
            'am_pm': [
                {'phrase': 'A.M.', 'variants': ['A.M', 'AM'], 'evidence_reduction': 1.0},
                {'phrase': 'P.M.', 'variants': ['P.M', 'PM'], 'evidence_reduction': 1.0}
            ]
        })
    
    def get_geographical_abbreviations(self) -> Dict[str, Any]:
        """Get geographical and postal abbreviations."""
        config = self._load_yaml_config('legitimate_abbreviations')
        return config.get('geographical_abbreviations', {})
    
    def get_title_abbreviations(self) -> Dict[str, Any]:
        """Get personal and professional title abbreviations."""
        config = self._load_yaml_config('legitimate_abbreviations')
        return config.get('title_abbreviations', {})
    
    def get_technical_abbreviations(self) -> Dict[str, Any]:
        """Get technical abbreviations with slashes (I/O, TCP/IP, etc.)."""
        config = self._load_yaml_config('legitimate_abbreviations')
        return config.get('technical_abbreviations', {})
    
    def get_academic_abbreviations(self) -> Dict[str, Any]:
        """Get academic and reference abbreviations."""
        config = self._load_yaml_config('legitimate_abbreviations')
        return config.get('academic_abbreviations', {})
    
    @lru_cache(maxsize=256)
    def is_legitimate_abbreviation(self, text: str, context: str = 'general') -> Tuple[bool, float]:
        """
        Check if text is a legitimate abbreviation and get evidence reduction.
        
        Args:
            text: The text to check
            context: The context type (time, geographical, technical, etc.)
            
        Returns:
            Tuple of (is_legitimate, evidence_reduction)
        """
        text_lower = text.lower()
        
        # Check all abbreviation categories
        categories = [
            self.get_time_abbreviations(),
            self.get_geographical_abbreviations(),
            self.get_title_abbreviations(),
            self.get_technical_abbreviations(),
            self.get_academic_abbreviations()
        ]
        
        for category in categories:
            for abbrev_type, abbrevs in category.items():
                if isinstance(abbrevs, list):
                    for abbrev_data in abbrevs:
                        if isinstance(abbrev_data, dict):
                            # Check main phrase
                            if abbrev_data.get('phrase', '').lower() == text_lower:
                                return True, abbrev_data.get('evidence_reduction', 0.0)
                            
                            # Check variants
                            variants = abbrev_data.get('variants', [])
                            if any(variant.lower() == text_lower for variant in variants):
                                return True, abbrev_data.get('evidence_reduction', 0.0)
        
        return False, 0.0
    
    # === AMBIGUOUS PATTERNS ===
    
    def get_ambiguous_slash_patterns(self) -> Dict[str, Any]:
        """Get ambiguous slash patterns that should be flagged."""
        config = self._load_yaml_config('ambiguous_patterns')
        return config.get('ambiguous_slash_patterns', {})
    
    def get_mathematical_expressions(self) -> Dict[str, Any]:
        """Get mathematical expression patterns that should NOT be flagged."""
        config = self._load_yaml_config('ambiguous_patterns')
        return config.get('mathematical_expressions', {})
    
    def get_company_patterns(self) -> Dict[str, Any]:
        """Get company name patterns that should NOT be flagged."""
        config = self._load_yaml_config('ambiguous_patterns')
        return config.get('company_patterns', {})
    
    def get_symbol_ambiguity(self) -> Dict[str, Any]:
        """Get symbol ambiguity patterns for punctuation and symbols rule."""
        config = self._load_yaml_config('ambiguous_patterns')
        return config.get('symbol_ambiguity', {})
    
    @lru_cache(maxsize=256)
    def is_ambiguous_pattern(self, prev_word: str, next_word: str, rule_type: str = 'slash') -> Tuple[bool, float, str]:
        """
        Check if a word pair creates an ambiguous pattern.
        
        Args:
            prev_word: Word before the punctuation
            next_word: Word after the punctuation
            rule_type: Type of rule checking (slash, symbol, etc.)
            
        Returns:
            Tuple of (is_ambiguous, evidence_score, category)
        """
        if rule_type == 'slash':
            patterns = self.get_ambiguous_slash_patterns()
            
            for category_name, category_data in patterns.items():
                if isinstance(category_data, list):
                    for pattern_data in category_data:
                        pattern = pattern_data.get('pattern', [])
                        if len(pattern) == 2:
                            if (pattern[0].lower() == prev_word.lower() and 
                                pattern[1].lower() == next_word.lower()):
                                return (True, 
                                       pattern_data.get('evidence', 0.8), 
                                       pattern_data.get('category', category_name))
        
        return False, 0.0, 'none'
    
    # === TECHNICAL COMPOUNDS ===
    
    def get_technical_compounds(self) -> Dict[str, Any]:
        """Get technical compound words and hyphenation patterns."""
        config = self._load_yaml_config('technical_compounds')
        return config.get('technical_compounds', {})
    
    def get_domain_specific_compounds(self) -> Dict[str, Any]:
        """Get domain-specific compound patterns."""
        config = self._load_yaml_config('technical_compounds')
        return config.get('domain_specific_compounds', {})
    
    def get_hyphenation_rules(self) -> Dict[str, Any]:
        """Get hyphenation rules by context."""
        config = self._load_yaml_config('technical_compounds')
        return config.get('hyphenation_rules', {})
    
    @lru_cache(maxsize=256)
    def is_technical_compound(self, prefix: str, word: str, domain: str = 'general') -> Tuple[bool, float]:
        """
        Check if a prefix-word combination is a legitimate technical compound.
        
        Args:
            prefix: The prefix (multi, sub, pre, etc.)
            word: The base word
            domain: The domain context
            
        Returns:
            Tuple of (is_compound, evidence_reduction)
        """
        compounds = self.get_technical_compounds()
        
        # Check prefix-based compounds
        prefix_compounds = compounds.get(f'{prefix}_compounds', {})
        if word.lower() in prefix_compounds:
            compound_data = prefix_compounds[word.lower()]
            if isinstance(compound_data, dict):
                return True, compound_data.get('evidence_reduction', 0.5)
            else:
                return True, 0.5
        
        # Check domain-specific compounds
        domain_compounds = self.get_domain_specific_compounds()
        domain_data = domain_compounds.get(domain, {})
        legitimate_hyphens = domain_data.get('legitimate_hyphens', [])
        compound_term = f"{prefix}-{word}"
        
        if compound_term in legitimate_hyphens:
            return True, domain_data.get('evidence_reduction', 0.6)
        
        return False, 0.0
    
    # === CONTEXT GUARDS ===
    
    def get_content_type_guards(self) -> Dict[str, Any]:
        """Get content type specific guards and adjustments."""
        config = self._load_yaml_config('context_guards')
        return config.get('content_type_guards', {})
    
    def get_domain_guards(self) -> Dict[str, Any]:
        """Get domain-specific guards and adjustments."""
        config = self._load_yaml_config('context_guards')
        return config.get('domain_guards', {})
    
    def get_block_type_guards(self) -> Dict[str, Any]:
        """Get block type specific guards."""
        config = self._load_yaml_config('context_guards')
        return config.get('block_type_guards', {})
    
    def get_audience_guards(self) -> Dict[str, Any]:
        """Get audience-specific adjustments."""
        config = self._load_yaml_config('context_guards')
        return config.get('audience_guards', {})
    
    @lru_cache(maxsize=512)
    def get_context_evidence_adjustment(self, rule_name: str, content_type: str = None, 
                                      domain: str = None, block_type: str = None, 
                                      audience: str = None) -> float:
        """
        Get evidence adjustment for a rule based on context.
        
        Args:
            rule_name: Name of the rule (e.g., 'slashes_rule', 'periods_rule')
            content_type: Content type (creative, technical, legal, etc.)
            domain: Domain (software, engineering, finance, etc.)
            block_type: Block type (code_block, quote, heading, etc.)
            audience: Audience type (expert, general, beginner, etc.)
            
        Returns:
            Evidence adjustment value (negative reduces evidence, positive increases)
        """
        total_adjustment = 0.0
        
        # Content type adjustments
        if content_type:
            content_guards = self.get_content_type_guards()
            content_data = content_guards.get(content_type, {})
            adjustments = content_data.get('evidence_adjustments', {})
            total_adjustment += adjustments.get(rule_name, 0.0)
        
        # Domain adjustments
        if domain:
            domain_guards = self.get_domain_guards()
            domain_data = domain_guards.get(domain, {})
            adjustments = domain_data.get('evidence_adjustments', {})
            total_adjustment += adjustments.get(rule_name, 0.0)
        
        # Block type adjustments
        if block_type:
            block_guards = self.get_block_type_guards()
            block_data = block_guards.get(block_type, {})
            adjustments = block_data.get('evidence_adjustments', {})
            
            # Check for rule-specific adjustment
            rule_adjustment = adjustments.get(rule_name, 0.0)
            if rule_adjustment == 0.0:
                # Check for all_punctuation_rules adjustment
                rule_adjustment = adjustments.get('all_punctuation_rules', 0.0)
            
            total_adjustment += rule_adjustment
        
        # Audience adjustments
        if audience:
            audience_guards = self.get_audience_guards()
            audience_data = audience_guards.get(audience, {})
            adjustments = audience_data.get('evidence_adjustments', {})
            
            # Check for rule-specific adjustment
            rule_adjustment = adjustments.get(rule_name, 0.0)
            if rule_adjustment == 0.0:
                # Check for all_rules adjustment
                rule_adjustment = adjustments.get('all_rules', 0.0)
            
            total_adjustment += rule_adjustment
        
        return total_adjustment
    
    @lru_cache(maxsize=256)
    def should_apply_guard(self, guard_type: str, content_type: str = None, 
                          domain: str = None, block_type: str = None) -> bool:
        """
        Check if a specific guard should be applied based on context.
        
        Args:
            guard_type: Type of guard to check
            content_type: Content type
            domain: Domain
            block_type: Block type
            
        Returns:
            True if guard should be applied (return 0.0 evidence)
        """
        # Block type guards (highest priority)
        if block_type in ['code_block', 'literal_block', 'inline_code']:
            return True
        
        # Content type specific permissions
        if content_type and guard_type in ['ellipses', 'exclamation_points', 'em_dashes']:
            content_guards = self.get_content_type_guards()
            content_data = content_guards.get(content_type, {})
            permissions = content_data.get('punctuation_permissions', {})
            
            if guard_type == 'ellipses' and permissions.get('ellipses', False):
                return True
            elif guard_type == 'exclamation_points' and permissions.get('exclamation_points', False):
                return True
            elif guard_type == 'em_dashes' and permissions.get('em_dashes', False):
                return True
        
        # Domain specific protections
        if domain and guard_type in ['file_paths', 'technical_compounds', 'financial_symbols']:
            domain_guards = self.get_domain_guards()
            domain_data = domain_guards.get(domain, {})
            patterns = domain_data.get('allowed_patterns', {})
            
            if guard_type == 'file_paths' and patterns.get('file_paths', False):
                return True
            elif guard_type == 'technical_compounds' and patterns.get('compound_technical_terms', False):
                return True
            elif guard_type == 'financial_symbols' and patterns.get('currency_symbols', False):
                return True
        
        return False
    
    # === UTILITY METHODS ===
    
    def clear_cache(self):
        """Clear all cached configuration data."""
        self._load_yaml_config.cache_clear()
        self.is_legitimate_abbreviation.cache_clear()
        self.is_ambiguous_pattern.cache_clear()
        self.is_technical_compound.cache_clear()
        self.get_context_evidence_adjustment.cache_clear()
        self.should_apply_guard.cache_clear()
    
    def reload_config(self, config_name: str = None):
        """
        Reload specific configuration or all configurations.
        
        Args:
            config_name: Specific config to reload, or None for all
        """
        if config_name:
            # Clear specific config from cache
            if config_name in self._config_cache:
                del self._config_cache[config_name]
        else:
            # Clear all caches
            self.clear_cache()
    
    def get_all_patterns_for_rule(self, rule_name: str) -> Dict[str, Any]:
        """
        Get all relevant patterns for a specific rule.
        
        Args:
            rule_name: Name of the rule (slashes_rule, periods_rule, etc.)
            
        Returns:
            Dict containing all relevant patterns for the rule
        """
        patterns = {}
        
        if rule_name == 'slashes_rule':
            patterns.update({
                'ambiguous_patterns': self.get_ambiguous_slash_patterns(),
                'technical_abbreviations': self.get_technical_abbreviations(),
                'measurement_units': self.get_measurement_units(),
                'file_path_indicators': self.get_file_path_indicators(),
                'academic_notation': self.get_academic_notation()
            })
        
        elif rule_name == 'periods_rule':
            patterns.update({
                'time_abbreviations': self.get_time_abbreviations(),
                'geographical_abbreviations': self.get_geographical_abbreviations(),
                'title_abbreviations': self.get_title_abbreviations(),
                'academic_abbreviations': self.get_academic_abbreviations()
            })
        
        elif rule_name == 'hyphens_rule':
            patterns.update({
                'technical_compounds': self.get_technical_compounds(),
                'domain_specific_compounds': self.get_domain_specific_compounds(),
                'hyphenation_rules': self.get_hyphenation_rules()
            })
        
        elif rule_name == 'exclamation_points_rule':
            patterns.update({
                'warning_indicators': self.get_warning_indicators()
            })
        
        elif rule_name == 'semicolons_rule':
            patterns.update({
                'list_indicators': self.get_list_indicators(),
                'academic_notation': self.get_academic_notation()
            })
        
        elif rule_name == 'punctuation_and_symbols_rule':
            patterns.update({
                'symbol_ambiguity': self.get_symbol_ambiguity(),
                'mathematical_expressions': self.get_mathematical_expressions(),
                'company_patterns': self.get_company_patterns()
            })
        
        # Add context guards for all rules
        patterns.update({
            'content_type_guards': self.get_content_type_guards(),
            'domain_guards': self.get_domain_guards(),
            'block_type_guards': self.get_block_type_guards(),
            'audience_guards': self.get_audience_guards()
        })
        
        return patterns

# Global instance
_config_service = None

def get_punctuation_config() -> PunctuationConfigService:
    """Get the global punctuation configuration service instance."""
    global _config_service
    if _config_service is None:
        _config_service = PunctuationConfigService()
    return _config_service
