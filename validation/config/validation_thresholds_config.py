"""
Validation Thresholds Configuration Class
Manages loading and validation of validation threshold configurations.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from .base_config import BaseConfig, SchemaValidator, ConfigurationValidationError


class ValidationThresholdsConfig(BaseConfig):
    """
    Configuration manager for validation thresholds.
    Handles loading, validation, and access to threshold settings for multi-pass validation.
    """
    
    def __init__(self, config_file: Optional[Path] = None, cache_ttl: int = 300):
        """
        Initialize validation thresholds configuration.
        
        Args:
            config_file: Path to validation thresholds YAML file
            cache_ttl: Cache time-to-live in seconds
        """
        if config_file is None:
            # Default to validation_thresholds.yaml in the same directory
            config_file = Path(__file__).parent / 'validation_thresholds.yaml'
        
        super().__init__(config_file, cache_ttl)
    
    def _is_optional(self) -> bool:
        """
        Validation thresholds configuration is optional.
        Will use defaults if file doesn't exist.
        
        Returns:
            True - configuration file is optional
        """
        return True
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return simplified universal threshold configuration.
        
        NOTE: This has been simplified to support the universal threshold system.
        All thresholds now use the universal value of 0.35.
        
        Returns:
            Simplified universal threshold configuration
        """
        return {
            'minimum_confidence_thresholds': {
                'universal': 0.35,  # Universal threshold for all rule and content types
                'default': 0.35,   # Legacy compatibility
                'high_confidence': 0.35,
                'medium_confidence': 0.35,
                'low_confidence': 0.35,
                'rejection_threshold': 0.35
            },
            'multi_pass_validation': {
                'enabled': True,
                'passes': {
                    'morphological': {'enabled': True, 'weight': 0.35},
                    'contextual': {'enabled': True, 'weight': 0.30},
                    'domain': {'enabled': True, 'weight': 0.20},
                    'cross_rule': {'enabled': True, 'weight': 0.15}
                }
            },
            'performance_settings': {
                'result_caching': {
                    'enabled': True,
                    'cache_ttl': 600,
                    'max_cache_size': 1000
                },
                'timeouts': {
                    'individual_pass_timeout': 30,
                    'total_validation_timeout': 120
                }
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate validation thresholds configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
            
        Raises:
            ConfigurationValidationError: If configuration is invalid
        """
        # Validate required top-level keys (simplified for universal threshold)
        required_keys = ['minimum_confidence_thresholds']
        SchemaValidator.validate_required_keys(config, required_keys)
        
        # Validate minimum confidence thresholds (simplified)
        self._validate_minimum_confidence_thresholds(
            config['minimum_confidence_thresholds']
        )
        
        # Validate optional multi-pass validation settings
        if 'multi_pass_validation' in config:
            self._validate_multi_pass_settings(config['multi_pass_validation'])
        
        # Validate optional performance settings
        if 'performance_settings' in config:
            self._validate_performance_settings(config['performance_settings'])
        
        return True
    
    def _validate_minimum_confidence_thresholds(self, thresholds: Dict[str, float]) -> None:
        """
        Validate simplified universal threshold configuration.
        
        Args:
            thresholds: Threshold dictionary to validate
            
        Raises:
            ConfigurationValidationError: If thresholds are invalid
        """
        # For universal threshold system, we just need the universal threshold
        required_thresholds = ['universal']
        
        try:
            SchemaValidator.validate_required_keys(thresholds, required_thresholds)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid minimum_confidence_thresholds: {e}")
        
        # Validate threshold types and ranges
        threshold_ranges = {'universal': {'min': 0.0, 'max': 1.0}}
        # Also validate legacy keys if present
        for key in ['default', 'high_confidence', 'medium_confidence', 'low_confidence', 'rejection_threshold']:
            if key in thresholds:
                threshold_ranges[key] = {'min': 0.0, 'max': 1.0}
        
        try:
            SchemaValidator.validate_value_ranges(thresholds, threshold_ranges)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid minimum_confidence_thresholds: {e}")
    
    def _validate_severity_thresholds(self, severities: Dict[str, Dict[str, Any]]) -> None:
        """
        Validate severity-based thresholds.
        
        Args:
            severities: Severity thresholds to validate
            
        Raises:
            ConfigurationValidationError: If severities are invalid
        """
        required_severities = ['critical', 'major', 'minor', 'suggestion']
        
        # Check that required severities exist
        missing_severities = [s for s in required_severities if s not in severities]
        if missing_severities:
            raise ConfigurationValidationError(
                f"Missing severity thresholds: {missing_severities}"
            )
        
        # Validate each severity configuration
        for severity, config in severities.items():
            self._validate_severity_config(config, f"severity_thresholds.{severity}")
    
    def _validate_severity_config(self, config: Dict[str, Any], section_name: str) -> None:
        """
        Validate individual severity configuration.
        
        Args:
            config: Severity configuration
            section_name: Name for error messages
            
        Raises:
            ConfigurationValidationError: If configuration is invalid
        """
        # Required fields
        required_fields = ['minimum_confidence', 'require_multi_pass', 'minimum_passes_agreement']
        
        try:
            SchemaValidator.validate_required_keys(config, required_fields)
        except ConfigurationValidationError as e:
            raise ConfigurationValidationError(f"Invalid {section_name}: {e}")
        
        # Validate minimum_confidence range
        confidence = config['minimum_confidence']
        if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            raise ConfigurationValidationError(
                f"Invalid {section_name}: minimum_confidence must be between 0.0 and 1.0, "
                f"got {confidence}"
            )
        
        # Validate require_multi_pass type
        if not isinstance(config['require_multi_pass'], bool):
            raise ConfigurationValidationError(
                f"Invalid {section_name}: require_multi_pass must be boolean, "
                f"got {type(config['require_multi_pass']).__name__}"
            )
        
        # Validate minimum_passes_agreement
        agreement = config['minimum_passes_agreement']
        if not isinstance(agreement, int) or agreement < 1 or agreement > 10:
            raise ConfigurationValidationError(
                f"Invalid {section_name}: minimum_passes_agreement must be integer 1-10, "
                f"got {agreement}"
            )
    
    def _validate_multi_pass_settings(self, settings: Dict[str, Any]) -> None:
        """
        Validate multi-pass validation settings.
        
        Args:
            settings: Multi-pass settings to validate
            
        Raises:
            ConfigurationValidationError: If settings are invalid
        """
        # Validate enabled flag
        if 'enabled' in settings and not isinstance(settings['enabled'], bool):
            raise ConfigurationValidationError(
                "multi_pass_validation.enabled must be boolean"
            )
        
        # Validate max_passes
        if 'max_passes' in settings:
            max_passes = settings['max_passes']
            if not isinstance(max_passes, int) or max_passes < 1 or max_passes > 10:
                raise ConfigurationValidationError(
                    f"multi_pass_validation.max_passes must be integer 1-10, got {max_passes}"
                )
        
        # Validate agreement threshold
        if 'default_agreement_threshold' in settings:
            threshold = settings['default_agreement_threshold']
            if not isinstance(threshold, int) or threshold < 1:
                raise ConfigurationValidationError(
                    f"multi_pass_validation.default_agreement_threshold must be positive integer, "
                    f"got {threshold}"
                )
        
        # Validate confidence modifiers
        confidence_fields = ['agreement_confidence_boost', 'disagreement_confidence_penalty']
        for field in confidence_fields:
            if field in settings:
                value = settings[field]
                if not isinstance(value, (int, float)) or value < 0:
                    raise ConfigurationValidationError(
                        f"multi_pass_validation.{field} must be non-negative number, "
                        f"got {value}"
                    )
    
    def _validate_error_acceptance_criteria(self, criteria: Dict[str, Any]) -> None:
        """
        Validate error acceptance criteria.
        
        Args:
            criteria: Error acceptance criteria to validate
            
        Raises:
            ConfigurationValidationError: If criteria are invalid
        """
        # Validate auto_accept criteria
        if 'auto_accept' in criteria:
            auto_accept = criteria['auto_accept']
            
            # Check thresholds
            for threshold_name in ['single_pass_threshold', 'multi_pass_threshold']:
                if threshold_name in auto_accept:
                    threshold = auto_accept[threshold_name]
                    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                        raise ConfigurationValidationError(
                            f"error_acceptance_criteria.auto_accept.{threshold_name} "
                            f"must be between 0.0 and 1.0, got {threshold}"
                        )
            
            # Check min_agreeing_passes
            if 'min_agreeing_passes' in auto_accept:
                passes = auto_accept['min_agreeing_passes']
                if not isinstance(passes, int) or passes < 1:
                    raise ConfigurationValidationError(
                        f"error_acceptance_criteria.auto_accept.min_agreeing_passes "
                        f"must be positive integer, got {passes}"
                    )
        
        # Validate auto_reject criteria
        if 'auto_reject' in criteria:
            auto_reject = criteria['auto_reject']
            
            if 'low_confidence_threshold' in auto_reject:
                threshold = auto_reject['low_confidence_threshold']
                if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
                    raise ConfigurationValidationError(
                        f"error_acceptance_criteria.auto_reject.low_confidence_threshold "
                        f"must be between 0.0 and 1.0, got {threshold}"
                    )
            
            if 'max_disagreement_ratio' in auto_reject:
                ratio = auto_reject['max_disagreement_ratio']
                if not isinstance(ratio, (int, float)) or not (0.0 <= ratio <= 1.0):
                    raise ConfigurationValidationError(
                        f"error_acceptance_criteria.auto_reject.max_disagreement_ratio "
                        f"must be between 0.0 and 1.0, got {ratio}"
                    )
    
    def _validate_rule_specific_thresholds(self, rules: Dict[str, Dict[str, Any]]) -> None:
        """
        Validate rule-specific thresholds.
        
        Args:
            rules: Rule-specific thresholds to validate
            
        Raises:
            ConfigurationValidationError: If thresholds are invalid
        """
        for rule_name, config in rules.items():
            self._validate_severity_config(config, f"rule_specific_thresholds.{rule_name}")
    
    def _validate_content_type_thresholds(self, content_types: Dict[str, Dict[str, Any]]) -> None:
        """
        Validate content-type-specific thresholds.
        
        Args:
            content_types: Content-type thresholds to validate
            
        Raises:
            ConfigurationValidationError: If thresholds are invalid
        """
        for content_type, config in content_types.items():
            # Validate confidence_modifier
            if 'confidence_modifier' in config:
                modifier = config['confidence_modifier']
                if not isinstance(modifier, (int, float)) or modifier <= 0:
                    raise ConfigurationValidationError(
                        f"content_type_thresholds.{content_type}.confidence_modifier "
                        f"must be positive number, got {modifier}"
                    )
            
            # Validate minimum_confidence_override
            if 'minimum_confidence_override' in config:
                override = config['minimum_confidence_override']
                if not isinstance(override, (int, float)) or not (0.0 <= override <= 1.0):
                    raise ConfigurationValidationError(
                        f"content_type_thresholds.{content_type}.minimum_confidence_override "
                        f"must be between 0.0 and 1.0, got {override}"
                    )
    
    def get_minimum_confidence_thresholds(self) -> Dict[str, float]:
        """
        Get minimum confidence thresholds.
        
        Returns:
            Dictionary of minimum confidence thresholds
        """
        config = self.load_config()
        return config['minimum_confidence_thresholds'].copy()
    
    def get_severity_threshold(self, severity: str) -> Dict[str, Any]:
        """
        Get threshold configuration for a specific severity level.
        
        Args:
            severity: Severity level (e.g., 'critical', 'major', 'minor')
            
        Returns:
            Dictionary of threshold configuration for the severity
        """
        config = self.load_config()
        
        # Check specific severity first
        severities = config.get('severity_thresholds', {})
        if severity in severities:
            return severities[severity].copy()
        
        # Fall back to default based on fallback thresholds
        fallback = config.get('fallback_thresholds', {}).get('unknown_rule', {})
        return {
            'minimum_confidence': fallback.get('minimum_confidence', 0.60),
            'require_multi_pass': fallback.get('require_multi_pass', True),
            'minimum_passes_agreement': fallback.get('minimum_passes_agreement', 2)
        }
    
    def get_rule_threshold(self, rule_type: str) -> Dict[str, Any]:
        """
        Get threshold configuration for a specific rule type.
        
        Args:
            rule_type: Type of rule (e.g., 'pronouns', 'grammar')
            
        Returns:
            Dictionary of threshold configuration for the rule type
        """
        config = self.load_config()
        
        # Check rule-specific thresholds first
        rule_thresholds = config.get('rule_specific_thresholds', {})
        if rule_type in rule_thresholds:
            return rule_thresholds[rule_type].copy()
        
        # Fall back to default thresholds
        fallback = config.get('fallback_thresholds', {}).get('unknown_rule', {})
        return {
            'minimum_confidence': fallback.get('minimum_confidence', 0.60),
            'require_multi_pass': fallback.get('require_multi_pass', True),
            'minimum_passes_agreement': fallback.get('minimum_passes_agreement', 2)
        }
    
    def get_content_type_threshold(self, content_type: str) -> Dict[str, Any]:
        """
        Get threshold configuration for a specific content type.
        
        Args:
            content_type: Type of content (e.g., 'technical', 'narrative')
            
        Returns:
            Dictionary of threshold configuration for the content type
        """
        config = self.load_config()
        
        # Check content-type-specific thresholds
        content_thresholds = config.get('content_type_thresholds', {})
        if content_type in content_thresholds:
            return content_thresholds[content_type].copy()
        
        # Fall back to default
        fallback = config.get('fallback_thresholds', {}).get('unknown_content', {})
        return {
            'confidence_modifier': fallback.get('confidence_modifier', 1.0),
            'minimum_confidence_override': fallback.get('minimum_confidence_override', 0.60)
        }
    
    def get_multi_pass_settings(self) -> Dict[str, Any]:
        """
        Get multi-pass validation settings.
        
        Returns:
            Dictionary of multi-pass validation settings
        """
        config = self.load_config()
        return config.get('multi_pass_validation', {}).copy()
    
    def get_error_acceptance_criteria(self) -> Dict[str, Any]:
        """
        Get error acceptance criteria.
        
        Returns:
            Dictionary of error acceptance criteria
        """
        config = self.load_config()
        return config.get('error_acceptance_criteria', {}).copy()
    
    def should_auto_accept(self, confidence: float, agreeing_passes: int = 1) -> bool:
        """
        Determine if an error should be automatically accepted.
        
        Args:
            confidence: Confidence score of the error
            agreeing_passes: Number of validation passes that agree
            
        Returns:
            True if error should be auto-accepted
        """
        criteria = self.get_error_acceptance_criteria()
        auto_accept = criteria.get('auto_accept', {})
        
        # Check single pass threshold
        single_threshold = auto_accept.get('single_pass_threshold', 0.85)
        if confidence >= single_threshold:
            return True
        
        # Check multi-pass threshold
        multi_threshold = auto_accept.get('multi_pass_threshold', 0.65)
        min_passes = auto_accept.get('min_agreeing_passes', 2)
        
        if confidence >= multi_threshold and agreeing_passes >= min_passes:
            return True
        
        return False
    
    def should_auto_reject(self, confidence: float, disagreement_ratio: float = 0.0) -> bool:
        """
        Determine if an error should be automatically rejected.
        
        Args:
            confidence: Confidence score of the error
            disagreement_ratio: Ratio of passes that disagree (0.0 to 1.0)
            
        Returns:
            True if error should be auto-rejected
        """
        criteria = self.get_error_acceptance_criteria()
        auto_reject = criteria.get('auto_reject', {})
        
        # Check low confidence threshold
        low_threshold = auto_reject.get('low_confidence_threshold', 0.25)
        if confidence < low_threshold:
            return True
        
        # Check disagreement ratio
        max_disagreement = auto_reject.get('max_disagreement_ratio', 0.6)
        if disagreement_ratio > max_disagreement:
            return True
        
        return False
    
    def get_all_rule_types(self) -> List[str]:
        """
        Get list of all configured rule types.
        
        Returns:
            List of rule type names
        """
        config = self.load_config()
        return list(config.get('rule_specific_thresholds', {}).keys())
    
    def get_all_content_types(self) -> List[str]:
        """
        Get list of all configured content types.
        
        Returns:
            List of content type names
        """
        config = self.load_config()
        return list(config.get('content_type_thresholds', {}).keys())
    
    def get_all_severity_levels(self) -> List[str]:
        """
        Get list of all configured severity levels.
        
        Returns:
            List of severity level names
        """
        config = self.load_config()
        return list(config.get('severity_thresholds', {}).keys())
    
    def _validate_performance_settings(self, settings: Dict[str, Any]) -> None:
        """
        Validate performance settings for the universal threshold system.
        
        Args:
            settings: Performance settings to validate
            
        Raises:
            ConfigurationValidationError: If settings are invalid
        """
        # Validate result_caching if present
        if 'result_caching' in settings:
            caching = settings['result_caching']
            
            if 'enabled' in caching and not isinstance(caching['enabled'], bool):
                raise ConfigurationValidationError(
                    "performance_settings.result_caching.enabled must be boolean"
                )
            
            if 'cache_ttl' in caching:
                ttl = caching['cache_ttl']
                if not isinstance(ttl, int) or ttl < 0:
                    raise ConfigurationValidationError(
                        f"performance_settings.result_caching.cache_ttl must be non-negative integer, got {ttl}"
                    )
            
            if 'max_cache_size' in caching:
                size = caching['max_cache_size']
                if not isinstance(size, int) or size < 0:
                    raise ConfigurationValidationError(
                        f"performance_settings.result_caching.max_cache_size must be non-negative integer, got {size}"
                    )
        
        # Validate timeouts if present
        if 'timeouts' in settings:
            timeouts = settings['timeouts']
            
            for timeout_name in ['individual_pass_timeout', 'total_validation_timeout']:
                if timeout_name in timeouts:
                    timeout = timeouts[timeout_name]
                    if not isinstance(timeout, int) or timeout <= 0:
                        raise ConfigurationValidationError(
                            f"performance_settings.timeouts.{timeout_name} must be positive integer, got {timeout}"
                        )
    
    def create_confidence_breakdown(self, confidence: float, rule_type: str, content_type: str = 'general') -> Dict[str, Any]:
        """
        Create human-readable confidence explanation for the universal threshold system.
        
        Args:
            confidence: Final confidence score
            rule_type: Type of rule (e.g., 'grammar', 'commands')
            content_type: Type of content (e.g., 'technical', 'narrative')
            
        Returns:
            Dictionary with confidence breakdown explanation
        """
        # Get universal threshold
        thresholds = self.get_minimum_confidence_thresholds()
        universal_threshold = thresholds.get('universal', 0.35)
        
        # Create explanation
        explanation = {
            'final_confidence': confidence,
            'universal_threshold': universal_threshold,
            'meets_threshold': confidence >= universal_threshold,
            'rule_type': rule_type,
            'content_type': content_type,
            'explanation': self._generate_confidence_explanation(confidence, rule_type, content_type, universal_threshold)
        }
        
        return explanation
    
    def _generate_confidence_explanation(self, confidence: float, rule_type: str, content_type: str, threshold: float) -> str:
        """
        Generate human-readable explanation of confidence calculation.
        
        Args:
            confidence: Final confidence score
            rule_type: Type of rule
            content_type: Type of content
            threshold: Universal threshold
            
        Returns:
            Human-readable explanation string
        """
        status = "meets" if confidence >= threshold else "below"
        
        explanation_parts = [
            f"Confidence score: {confidence:.3f}",
            f"Universal threshold: {threshold:.3f}",
            f"Status: {status} threshold",
            f"Rule type: {rule_type}",
            f"Content type: {content_type}"
        ]
        
        if confidence >= threshold:
            explanation_parts.append("✅ Error will be accepted")
        else:
            explanation_parts.append("❌ Error will be rejected")
        
        return " | ".join(explanation_parts)