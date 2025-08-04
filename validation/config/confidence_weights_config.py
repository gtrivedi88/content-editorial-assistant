"""
Confidence Weights Configuration Class
Manages loading and validation of confidence weight configurations.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .base_config import BaseConfig, SchemaValidator, ConfigurationValidationError


class ConfidenceWeightsConfig(BaseConfig):
    """
    Configuration manager for confidence weights.
    Handles loading, validation, and access to confidence weight settings.
    """
    
    def __init__(self, config_file: Optional[Path] = None, cache_ttl: int = 300):
        """
        Initialize confidence weights configuration.
        
        Args:
            config_file: Path to confidence weights YAML file
            cache_ttl: Cache time-to-live in seconds
        """
        if config_file is None:
            # Default to confidence_weights.yaml in the same directory
            config_file = Path(__file__).parent / 'confidence_weights.yaml'
        
        super().__init__(config_file, cache_ttl)
    
    def _is_optional(self) -> bool:
        """
        Confidence weights configuration is optional.
        Will use defaults if file doesn't exist.
        
        Returns:
            True - configuration file is optional
        """
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return default confidence weights configuration.
        
        Returns:
            Default configuration dictionary
        """
        return {
            'default_weights': {
                'morphological': 0.35,
                'contextual': 0.30,
                'domain': 0.20,
                'discourse': 0.15
            },
            'rule_specific_weights': {},
            'content_type_weights': {},
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.35,
                    'contextual': 0.30,
                    'domain': 0.20,
                    'discourse': 0.15
                },
                'unknown_content': {
                    'morphological': 0.35,
                    'contextual': 0.30,
                    'domain': 0.20,
                    'discourse': 0.15
                }
            },
            'adjustment_factors': {
                'high_certainty_boost': 1.1,
                'ambiguity_penalty': 0.9,
                'adjustment_threshold': 0.5,
                'max_confidence': 0.95,
                'min_confidence': 0.05
            },
            'calculation_settings': {
                'combination_method': 'weighted_average',
                'normalize_weights': True,
                'precision': 3,
                'enable_caching': True,
                'cache_ttl': 300
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate confidence weights configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ConfigurationValidationError: If configuration is invalid
        """
        # Validate required top-level keys
        required_keys = ['default_weights', 'fallback_weights']
        SchemaValidator.validate_required_keys(config, required_keys)
        
        # Validate weight sections
        self._validate_weight_section(config['default_weights'], 'default_weights')
        
        if 'rule_specific_weights' in config:
            for rule_name, weights in config['rule_specific_weights'].items():
                self._validate_weight_section(weights, f'rule_specific_weights.{rule_name}')
        
        if 'content_type_weights' in config:
            for content_type, weights in config['content_type_weights'].items():
                self._validate_weight_section(weights, f'content_type_weights.{content_type}')
        
        if 'fallback_weights' in config:
            for fallback_name, weights in config['fallback_weights'].items():
                self._validate_weight_section(weights, f'fallback_weights.{fallback_name}')
        
        # Validate adjustment factors
        if 'adjustment_factors' in config:
            self._validate_adjustment_factors(config['adjustment_factors'])
        
        # Validate calculation settings
        if 'calculation_settings' in config:
            self._validate_calculation_settings(config['calculation_settings'])
        
        return True
    
    def _validate_weight_section(self, weights: Dict[str, float], section_name: str) -> None:
        """
        Validate a weight section (default, rule-specific, etc.).
        
        Args:
            weights: Weight dictionary to validate
            section_name: Name of the section for error messages
            
        Raises:
            ConfigurationValidationError: If weights are invalid
        """
        # Required weight keys
        required_weight_keys = ['morphological', 'contextual', 'domain', 'discourse']
        
        # First validate required keys
        try:
            SchemaValidator.validate_required_keys(weights, required_weight_keys)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid {section_name}: {e}")
        
        # Validate weight types
        weight_types = {key: (int, float) for key in required_weight_keys}
        for key, value in weights.items():
            if key in weight_types and not isinstance(value, weight_types[key]):
                raise ConfigurationValidationError(
                    f"Invalid {section_name}: {key} must be a number, got {type(value).__name__}"
                )
        
        # Validate weight ranges (0.0 to 1.0)
        weight_ranges = {key: {'min': 0.0, 'max': 1.0} for key in required_weight_keys}
        try:
            SchemaValidator.validate_value_ranges(weights, weight_ranges)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid {section_name}: {e}")
        
        # Validate weight sum (should be approximately 1.0) - do this last
        # Only check sum if all required keys are present (already validated above)
        try:
            weight_sum = sum(weights[key] for key in required_weight_keys)
            tolerance = 0.001  # Allow small floating-point errors
            
            if abs(weight_sum - 1.0) > tolerance:
                raise ConfigurationValidationError(
                    f"Invalid {section_name}: weights must sum to 1.0, got {weight_sum:.6f}"
                )
        except KeyError as e:
            # This shouldn't happen if required keys validation passed, but just in case
            raise ConfigurationValidationError(
                f"Invalid {section_name}: missing weight key {e}"
            )
    
    def _validate_adjustment_factors(self, factors: Dict[str, Any]) -> None:
        """
        Validate adjustment factors configuration.
        
        Args:
            factors: Adjustment factors to validate
            
        Raises:
            ConfigurationValidationError: If factors are invalid
        """
        expected_factors = {
            'high_certainty_boost': (float, int),
            'ambiguity_penalty': (float, int),
            'adjustment_threshold': (float, int),
            'max_confidence': (float, int),
            'min_confidence': (float, int)
        }
        
        for factor_name, expected_type in expected_factors.items():
            if factor_name in factors:
                value = factors[factor_name]
                if not isinstance(value, expected_type):
                    raise ConfigurationValidationError(
                        f"adjustment_factors.{factor_name} must be a number, "
                        f"got {type(value).__name__}"
                    )
                
                # Validate ranges
                if factor_name in ['max_confidence', 'min_confidence', 'adjustment_threshold']:
                    if not (0.0 <= value <= 1.0):
                        raise ConfigurationValidationError(
                            f"adjustment_factors.{factor_name} must be between 0.0 and 1.0, "
                            f"got {value}"
                        )
                
                elif factor_name in ['high_certainty_boost', 'ambiguity_penalty']:
                    if value <= 0.0:
                        raise ConfigurationValidationError(
                            f"adjustment_factors.{factor_name} must be positive, got {value}"
                        )
        
        # Validate logical constraints
        if 'min_confidence' in factors and 'max_confidence' in factors:
            if factors['min_confidence'] >= factors['max_confidence']:
                raise ConfigurationValidationError(
                    f"adjustment_factors.min_confidence ({factors['min_confidence']}) "
                    f"must be less than max_confidence ({factors['max_confidence']})"
                )
    
    def _validate_calculation_settings(self, settings: Dict[str, Any]) -> None:
        """
        Validate calculation settings configuration.
        
        Args:
            settings: Calculation settings to validate
            
        Raises:
            ConfigurationValidationError: If settings are invalid
        """
        # Validate combination method
        if 'combination_method' in settings:
            valid_methods = ['weighted_average', 'geometric_mean', 'harmonic_mean']
            if settings['combination_method'] not in valid_methods:
                raise ConfigurationValidationError(
                    f"calculation_settings.combination_method must be one of {valid_methods}, "
                    f"got '{settings['combination_method']}'"
                )
        
        # Validate boolean settings
        boolean_settings = ['normalize_weights', 'enable_caching']
        for setting in boolean_settings:
            if setting in settings and not isinstance(settings[setting], bool):
                raise ConfigurationValidationError(
                    f"calculation_settings.{setting} must be boolean, "
                    f"got {type(settings[setting]).__name__}"
                )
        
        # Validate numeric settings
        numeric_settings = {
            'precision': (int, range(0, 10)),
            'cache_ttl': (int, range(1, 86400))  # 1 second to 1 day
        }
        
        for setting, (expected_type, valid_range) in numeric_settings.items():
            if setting in settings:
                value = settings[setting]
                if not isinstance(value, expected_type):
                    raise ConfigurationValidationError(
                        f"calculation_settings.{setting} must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
                
                if isinstance(valid_range, range) and value not in valid_range:
                    raise ConfigurationValidationError(
                        f"calculation_settings.{setting} must be between "
                        f"{valid_range.start} and {valid_range.stop-1}, got {value}"
                    )
    
    def get_weights_for_rule(self, rule_type: str) -> Dict[str, float]:
        """
        Get confidence weights for a specific rule type.
        
        Args:
            rule_type: Type of rule (e.g., 'pronouns', 'grammar')
            
        Returns:
            Dictionary of confidence weights
        """
        config = self.load_config()
        
        # Check for rule-specific weights first
        if rule_type in config.get('rule_specific_weights', {}):
            return config['rule_specific_weights'][rule_type].copy()
        
        # Fall back to default weights
        return config['default_weights'].copy()
    
    def get_weights_for_content_type(self, content_type: str) -> Dict[str, float]:
        """
        Get confidence weights for a specific content type.
        
        Args:
            content_type: Type of content (e.g., 'technical', 'narrative')
            
        Returns:
            Dictionary of confidence weights
        """
        config = self.load_config()
        
        # Check for content-type-specific weights first
        if content_type in config.get('content_type_weights', {}):
            return config['content_type_weights'][content_type].copy()
        
        # Fall back to default weights
        return config['default_weights'].copy()
    
    def get_fallback_weights(self, fallback_type: str = 'unknown_rule') -> Dict[str, float]:
        """
        Get fallback weights for unknown rule or content types.
        
        Args:
            fallback_type: Type of fallback ('unknown_rule', 'unknown_content')
            
        Returns:
            Dictionary of fallback confidence weights
        """
        config = self.load_config()
        
        fallback_weights = config.get('fallback_weights', {})
        if fallback_type in fallback_weights:
            return fallback_weights[fallback_type].copy()
        
        # Ultimate fallback to default weights
        return config['default_weights'].copy()
    
    def get_adjustment_factors(self) -> Dict[str, float]:
        """
        Get confidence adjustment factors.
        
        Returns:
            Dictionary of adjustment factors
        """
        config = self.load_config()
        return config.get('adjustment_factors', {}).copy()
    
    def get_calculation_settings(self) -> Dict[str, Any]:
        """
        Get confidence calculation settings.
        
        Returns:
            Dictionary of calculation settings
        """
        config = self.load_config()
        return config.get('calculation_settings', {}).copy()
    
    def get_all_rule_types(self) -> list:
        """
        Get list of all defined rule types.
        
        Returns:
            List of rule type names
        """
        config = self.load_config()
        return list(config.get('rule_specific_weights', {}).keys())
    
    def get_all_content_types(self) -> list:
        """
        Get list of all defined content types.
        
        Returns:
            List of content type names
        """
        config = self.load_config()
        return list(config.get('content_type_weights', {}).keys())