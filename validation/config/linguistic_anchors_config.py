"""
Linguistic Anchors Configuration Class
Manages loading and validation of linguistic anchor configurations.
"""

import re
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path

from .base_config import BaseConfig, SchemaValidator, ConfigurationValidationError


class LinguisticAnchorsConfig(BaseConfig):
    """
    Configuration manager for linguistic anchors.
    Handles loading, validation, and access to linguistic anchor patterns that
    boost or reduce confidence in error detection.
    """
    
    def __init__(self, config_file: Optional[Path] = None, cache_ttl: int = 300):
        """
        Initialize linguistic anchors configuration.
        
        Args:
            config_file: Path to linguistic anchors YAML file
            cache_ttl: Cache time-to-live in seconds
        """
        if config_file is None:
            # Default to linguistic_anchors.yaml in the same directory
            config_file = Path(__file__).parent / 'linguistic_anchors.yaml'
        
        super().__init__(config_file, cache_ttl)
        self._compiled_patterns_cache = {}
    
    def _is_optional(self) -> bool:
        """
        Linguistic anchors configuration is optional.
        Will use defaults if file doesn't exist.
        
        Returns:
            True - configuration file is optional
        """
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default linguistic anchors configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'confidence_boosting_anchors': {
                'generic_patterns': {
                    'determiners': {
                        'patterns': [r'\bthe\b', r'\ba\b', r'\ban\b'],
                        'confidence_boost': 0.10,
                        'context_window': 3,
                        'description': 'Basic determiners'
                    }
                },
                'technical_patterns': {
                    'programming_terms': {
                        'patterns': [r'\bAPI\b', r'\bHTTP\b', r'\bJSON\b'],
                        'confidence_boost': 0.12,
                        'context_window': 5,
                        'description': 'Programming terminology'
                    }
                }
            },
            'confidence_reducing_anchors': {
                'proper_nouns': {
                    'person_names': {
                        'patterns': [r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'],
                        'confidence_reduction': 0.15,
                        'context_window': 2,
                        'description': 'Person names'
                    }
                },
                'quoted_content': {
                    'direct_quotes': {
                        'patterns': [r'"[^"]*"', r"'[^']*'"],
                        'confidence_reduction': 0.20,
                        'context_window': 0,
                        'description': 'Quoted text'
                    }
                }
            },
            'anchor_combination_rules': {
                'max_total_boost': 0.30,
                'max_total_reduction': 0.35,
                'combination_method': 'diminishing_returns'
            },
            'pattern_matching': {
                'case_sensitive': False,
                'enforce_word_boundaries': True,
                'max_context_window': 15
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate linguistic anchors configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ConfigurationValidationError: If configuration is invalid
        """
        # Validate required top-level keys
        required_keys = ['confidence_boosting_anchors', 'confidence_reducing_anchors']
        SchemaValidator.validate_required_keys(config, required_keys)
        
        # Validate boosting anchors
        self._validate_anchor_section(
            config['confidence_boosting_anchors'], 
            'confidence_boosting_anchors',
            'confidence_boost'
        )
        
        # Validate reducing anchors
        self._validate_anchor_section(
            config['confidence_reducing_anchors'],
            'confidence_reducing_anchors', 
            'confidence_reduction'
        )
        
        # Validate combination rules
        if 'anchor_combination_rules' in config:
            self._validate_combination_rules(config['anchor_combination_rules'])
        
        # Validate pattern matching settings
        if 'pattern_matching' in config:
            self._validate_pattern_matching(config['pattern_matching'])
        
        # Validate rule-specific weights
        if 'rule_specific_weights' in config:
            self._validate_rule_specific_weights(config['rule_specific_weights'])
        
        return True
    
    def _validate_anchor_section(self, section: Dict[str, Any], section_name: str, 
                                effect_key: str) -> None:
        """
        Validate an anchor section (boosting or reducing).
        
        Args:
            section: Anchor section to validate
            section_name: Name of the section for error messages
            effect_key: Key for confidence effect ('confidence_boost' or 'confidence_reduction')
            
        Raises:
            ConfigurationValidationError: If section is invalid
        """
        if not isinstance(section, dict):
            raise ConfigurationValidationError(
                f"{section_name} must be a dictionary"
            )
        
        for category_name, category in section.items():
            if not isinstance(category, dict):
                raise ConfigurationValidationError(
                    f"{section_name}.{category_name} must be a dictionary"
                )
            
            for anchor_name, anchor_config in category.items():
                self._validate_anchor_config(
                    anchor_config, 
                    f"{section_name}.{category_name}.{anchor_name}",
                    effect_key
                )
    
    def _validate_anchor_config(self, config: Dict[str, Any], config_path: str,
                               effect_key: str) -> None:
        """
        Validate individual anchor configuration.
        
        Args:
            config: Anchor configuration
            config_path: Path for error messages
            effect_key: Expected effect key
            
        Raises:
            ConfigurationValidationError: If configuration is invalid
        """
        # Required fields
        required_fields = ['patterns', effect_key, 'context_window']
        
        try:
            SchemaValidator.validate_required_keys(config, required_fields)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid {config_path}: {e}")
        
        # Validate patterns
        patterns = config['patterns']
        if not isinstance(patterns, list) or not patterns:
            raise ConfigurationValidationError(
                f"Invalid {config_path}: patterns must be non-empty list"
            )
        
        # Validate each pattern as valid regex
        for i, pattern in enumerate(patterns):
            if not isinstance(pattern, str):
                raise ConfigurationValidationError(
                    f"Invalid {config_path}: pattern {i} must be string"
                )
            
            try:
                re.compile(pattern)
            except re.error as e:
                raise ConfigurationValidationError(
                    f"Invalid {config_path}: pattern '{pattern}' is invalid regex: {e}"
                )
        
        # Validate confidence effect
        effect_value = config[effect_key]
        if not isinstance(effect_value, (int, float)) or not (0.0 <= effect_value <= 1.0):
            raise ConfigurationValidationError(
                f"Invalid {config_path}: {effect_key} must be number between 0.0 and 1.0, "
                f"got {effect_value}"
            )
        
        # Validate context window
        context_window = config['context_window']
        if not isinstance(context_window, int) or context_window < 0:
            raise ConfigurationValidationError(
                f"Invalid {config_path}: context_window must be non-negative integer, "
                f"got {context_window}"
            )
        
        # Check context window limit (use default max if not yet loaded to avoid recursion)
        max_window = 15  # Default max context window
        if context_window > max_window:
            raise ConfigurationValidationError(
                f"Invalid {config_path}: context_window ({context_window}) exceeds "
                f"maximum allowed ({max_window})"
            )
        
        # Validate optional description
        if 'description' in config and not isinstance(config['description'], str):
            raise ConfigurationValidationError(
                f"Invalid {config_path}: description must be string"
            )
    
    def _validate_combination_rules(self, rules: Dict[str, Any]) -> None:
        """
        Validate anchor combination rules.
        
        Args:
            rules: Combination rules to validate
            
        Raises:
            ConfigurationValidationError: If rules are invalid
        """
        # Validate max boost/reduction
        for key in ['max_total_boost', 'max_total_reduction']:
            if key in rules:
                value = rules[key]
                if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                    raise ConfigurationValidationError(
                        f"anchor_combination_rules.{key} must be number between 0.0 and 1.0, "
                        f"got {value}"
                    )
        
        # Validate combination method
        if 'combination_method' in rules:
            valid_methods = ['additive', 'diminishing_returns', 'weighted_average']
            method = rules['combination_method']
            if method not in valid_methods:
                raise ConfigurationValidationError(
                    f"anchor_combination_rules.combination_method must be one of {valid_methods}, "
                    f"got '{method}'"
                )
        
        # Validate diminishing returns settings
        if 'diminishing_returns' in rules:
            dr_config = rules['diminishing_returns']
            
            for key in ['effectiveness_decay', 'min_effectiveness']:
                if key in dr_config:
                    value = dr_config[key]
                    if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
                        raise ConfigurationValidationError(
                            f"anchor_combination_rules.diminishing_returns.{key} "
                            f"must be number between 0.0 and 1.0, got {value}"
                        )
    
    def _validate_pattern_matching(self, settings: Dict[str, Any]) -> None:
        """
        Validate pattern matching settings.
        
        Args:
            settings: Pattern matching settings
            
        Raises:
            ConfigurationValidationError: If settings are invalid
        """
        # Validate boolean settings
        boolean_settings = ['case_sensitive', 'enforce_word_boundaries', 'precompile_patterns']
        for setting in boolean_settings:
            if setting in settings and not isinstance(settings[setting], bool):
                raise ConfigurationValidationError(
                    f"pattern_matching.{setting} must be boolean, "
                    f"got {type(settings[setting]).__name__}"
                )
        
        # Validate max_context_window
        if 'max_context_window' in settings:
            value = settings['max_context_window']
            if not isinstance(value, int) or value < 1 or value > 100:
                raise ConfigurationValidationError(
                    f"pattern_matching.max_context_window must be integer 1-100, "
                    f"got {value}"
                )
    
    def _validate_rule_specific_weights(self, weights: Dict[str, Dict[str, float]]) -> None:
        """
        Validate rule-specific anchor weights.
        
        Args:
            weights: Rule-specific weights to validate
            
        Raises:
            ConfigurationValidationError: If weights are invalid
        """
        for rule_name, rule_weights in weights.items():
            if not isinstance(rule_weights, dict):
                raise ConfigurationValidationError(
                    f"rule_specific_weights.{rule_name} must be dictionary"
                )
            
            for weight_name, weight_value in rule_weights.items():
                if not isinstance(weight_value, (int, float)) or weight_value < 0:
                    raise ConfigurationValidationError(
                        f"rule_specific_weights.{rule_name}.{weight_name} "
                        f"must be non-negative number, got {weight_value}"
                    )
    
    def get_boosting_anchors(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get confidence-boosting anchors.
        
        Returns:
            Dictionary of boosting anchor categories and configurations
        """
        config = self.load_config()
        import copy
        return copy.deepcopy(config.get('confidence_boosting_anchors', {}))
    
    def get_reducing_anchors(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Get confidence-reducing anchors.
        
        Returns:
            Dictionary of reducing anchor categories and configurations
        """
        config = self.load_config()
        import copy
        return copy.deepcopy(config.get('confidence_reducing_anchors', {}))
    
    def get_anchor_category(self, category_type: str, category_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get specific anchor category.
        
        Args:
            category_type: 'boosting' or 'reducing'
            category_name: Name of the category (e.g., 'generic_patterns')
            
        Returns:
            Dictionary of anchor configurations in the category
        """
        if category_type == 'boosting':
            anchors = self.get_boosting_anchors()
        elif category_type == 'reducing':
            anchors = self.get_reducing_anchors()
        else:
            raise ValueError(f"Invalid category_type: {category_type}")
        
        import copy
        return copy.deepcopy(anchors.get(category_name, {}))
    
    def get_compiled_patterns(self, category_type: str, category_name: str, 
                            anchor_name: str) -> List[re.Pattern]:
        """
        Get compiled regex patterns for an anchor.
        
        Args:
            category_type: 'boosting' or 'reducing'
            category_name: Name of the category
            anchor_name: Name of the specific anchor
            
        Returns:
            List of compiled regex patterns
        """
        cache_key = f"{category_type}:{category_name}:{anchor_name}"
        
        if cache_key in self._compiled_patterns_cache:
            return self._compiled_patterns_cache[cache_key]
        
        category = self.get_anchor_category(category_type, category_name)
        if anchor_name not in category:
            return []
        
        anchor_config = category[anchor_name]
        patterns = anchor_config.get('patterns', [])
        
        # Get pattern matching settings
        pattern_settings = self.get_pattern_matching_settings()
        case_sensitive = pattern_settings.get('case_sensitive', False)
        
        # Compile patterns
        flags = 0 if case_sensitive else re.IGNORECASE
        compiled_patterns = []
        
        for pattern in patterns:
            try:
                compiled_patterns.append(re.compile(pattern, flags))
            except re.error:
                # Skip invalid patterns (should have been caught in validation)
                continue
        
        # Cache compiled patterns
        self._compiled_patterns_cache[cache_key] = compiled_patterns
        return compiled_patterns
    
    def get_combination_rules(self) -> Dict[str, Any]:
        """
        Get anchor combination rules.
        
        Returns:
            Dictionary of combination rules
        """
        config = self.load_config()
        return config.get('anchor_combination_rules', {}).copy()
    
    def get_pattern_matching_settings(self) -> Dict[str, Any]:
        """
        Get pattern matching settings.
        
        Returns:
            Dictionary of pattern matching settings
        """
        config = self.load_config()
        return config.get('pattern_matching', {}).copy()
    
    def get_rule_specific_weights(self, rule_type: str) -> Dict[str, float]:
        """
        Get rule-specific anchor weights.
        
        Args:
            rule_type: Type of rule (e.g., 'grammar', 'pronouns')
            
        Returns:
            Dictionary of anchor category weights for the rule type
        """
        config = self.load_config()
        rule_weights = config.get('rule_specific_weights', {})
        return rule_weights.get(rule_type, {}).copy()
    
    def get_content_type_adjustments(self, content_type: str) -> Dict[str, float]:
        """
        Get content-type-specific anchor adjustments.
        
        Args:
            content_type: Type of content (e.g., 'technical', 'narrative')
            
        Returns:
            Dictionary of anchor multipliers for the content type
        """
        config = self.load_config()
        adjustments = config.get('content_type_adjustments', {})
        return adjustments.get(content_type, {}).copy()
    
    def calculate_anchor_effect(self, text: str, error_position: int, 
                               rule_type: str = None, content_type: str = None) -> Tuple[float, List[str]]:
        """
        Calculate the total anchor effect for text around an error.
        
        Args:
            text: Full text containing the error
            error_position: Character position of the error
            rule_type: Type of rule for rule-specific weighting
            content_type: Type of content for content-specific adjustments
            
        Returns:
            Tuple of (net_confidence_effect, list_of_triggered_anchors)
        """
        total_boost = 0.0
        total_reduction = 0.0
        triggered_anchors = []
        
        # Get combination rules
        combination_rules = self.get_combination_rules()
        max_boost = combination_rules.get('max_total_boost', 0.30)
        max_reduction = combination_rules.get('max_total_reduction', 0.35)
        
        # Process boosting anchors
        boosting_anchors = self.get_boosting_anchors()
        boost_effects = []
        
        for category_name, category in boosting_anchors.items():
            for anchor_name, anchor_config in category.items():
                effect = self._calculate_single_anchor_effect(
                    text, error_position, 'boosting', category_name, 
                    anchor_name, anchor_config, rule_type, content_type
                )
                if effect > 0:
                    boost_effects.append(effect)
                    triggered_anchors.append(f"boost:{category_name}:{anchor_name}")
        
        # Process reducing anchors
        reducing_anchors = self.get_reducing_anchors()
        reduction_effects = []
        
        for category_name, category in reducing_anchors.items():
            for anchor_name, anchor_config in category.items():
                effect = self._calculate_single_anchor_effect(
                    text, error_position, 'reducing', category_name,
                    anchor_name, anchor_config, rule_type, content_type
                )
                if effect > 0:
                    reduction_effects.append(effect)
                    triggered_anchors.append(f"reduce:{category_name}:{anchor_name}")
        
        # Combine effects using specified method
        total_boost = self._combine_effects(boost_effects, combination_rules)
        total_reduction = self._combine_effects(reduction_effects, combination_rules)
        
        # Apply limits
        total_boost = min(total_boost, max_boost)
        total_reduction = min(total_reduction, max_reduction)
        
        # Net effect (positive = boost, negative = reduction)
        net_effect = total_boost - total_reduction
        
        return net_effect, triggered_anchors
    
    def _calculate_single_anchor_effect(self, text: str, error_position: int,
                                      category_type: str, category_name: str,
                                      anchor_name: str, anchor_config: Dict[str, Any],
                                      rule_type: str = None, content_type: str = None) -> float:
        """
        Calculate effect of a single anchor.
        
        Args:
            text: Full text
            error_position: Error position
            category_type: 'boosting' or 'reducing'
            category_name: Category name
            anchor_name: Anchor name
            anchor_config: Anchor configuration
            rule_type: Rule type for weighting
            content_type: Content type for adjustments
            
        Returns:
            Confidence effect value
        """
        # Get patterns
        compiled_patterns = self.get_compiled_patterns(category_type, category_name, anchor_name)
        if not compiled_patterns:
            return 0.0
        
        # Get context window
        context_window = anchor_config.get('context_window', 3)
        
        # Extract context around error
        words = text.split()
        error_word_index = self._find_word_index(text, error_position)
        
        if error_word_index == -1:
            return 0.0
        
        # Define context bounds
        start_index = max(0, error_word_index - context_window)
        end_index = min(len(words), error_word_index + context_window + 1)
        context_text = ' '.join(words[start_index:end_index])
        
        # Check for pattern matches
        for pattern in compiled_patterns:
            if pattern.search(context_text):
                # Get base effect
                if category_type == 'boosting':
                    base_effect = anchor_config.get('confidence_boost', 0.0)
                else:
                    base_effect = anchor_config.get('confidence_reduction', 0.0)
                
                # Apply rule-specific weighting
                if rule_type:
                    rule_weights = self.get_rule_specific_weights(rule_type)
                    weight_key = f"{category_name}_weight"
                    weight = rule_weights.get(weight_key, 1.0)
                    base_effect *= weight
                
                # Apply content-type adjustments
                if content_type:
                    adjustments = self.get_content_type_adjustments(content_type)
                    adjustment_key = f"{category_name}_multiplier"
                    multiplier = adjustments.get(adjustment_key, 1.0)
                    base_effect *= multiplier
                
                return base_effect
        
        return 0.0
    
    def _combine_effects(self, effects: List[float], combination_rules: Dict[str, Any]) -> float:
        """
        Combine multiple anchor effects using the specified method.
        
        Args:
            effects: List of individual anchor effects
            combination_rules: Rules for combining effects
            
        Returns:
            Combined effect value
        """
        if not effects:
            return 0.0
        
        method = combination_rules.get('combination_method', 'diminishing_returns')
        
        if method == 'additive':
            return sum(effects)
        
        elif method == 'weighted_average':
            return sum(effects) / len(effects)
        
        elif method == 'diminishing_returns':
            # Sort effects in descending order
            effects = sorted(effects, reverse=True)
            
            # Get diminishing returns settings
            dr_config = combination_rules.get('diminishing_returns', {})
            decay = dr_config.get('effectiveness_decay', 0.8)
            min_effectiveness = dr_config.get('min_effectiveness', 0.2)
            
            total_effect = 0.0
            current_multiplier = 1.0
            
            for effect in effects:
                total_effect += effect * current_multiplier
                current_multiplier = max(current_multiplier * decay, min_effectiveness)
            
            return total_effect
        
        else:
            # Default to additive
            return sum(effects)
    
    def _find_word_index(self, text: str, char_position: int) -> int:
        """
        Find the word index for a character position.
        
        Args:
            text: Full text
            char_position: Character position
            
        Returns:
            Word index, or -1 if not found
        """
        words = text.split()
        current_position = 0
        
        for i, word in enumerate(words):
            word_start = current_position
            word_end = current_position + len(word)
            
            if word_start <= char_position <= word_end:
                return i
            
            current_position = word_end + 1  # +1 for space
        
        return -1
    
    def get_all_anchor_categories(self, category_type: str) -> List[str]:
        """
        Get list of all anchor categories for a type.
        
        Args:
            category_type: 'boosting' or 'reducing'
            
        Returns:
            List of category names
        """
        if category_type == 'boosting':
            anchors = self.get_boosting_anchors()
        elif category_type == 'reducing':
            anchors = self.get_reducing_anchors()
        else:
            return []
        
        return list(anchors.keys())
    
    def get_all_anchors_in_category(self, category_type: str, category_name: str) -> List[str]:
        """
        Get list of all anchors in a specific category.
        
        Args:
            category_type: 'boosting' or 'reducing'
            category_name: Name of the category
            
        Returns:
            List of anchor names
        """
        category = self.get_anchor_category(category_type, category_name)
        return list(category.keys())