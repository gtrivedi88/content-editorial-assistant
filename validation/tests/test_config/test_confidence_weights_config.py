"""
Comprehensive test suite for confidence weights configuration.
Tests weight loading, validation, rule-specific weights, and content type weights.
"""

import unittest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from validation.config.confidence_weights_config import ConfidenceWeightsConfig
from validation.config.base_config import (
    ConfigurationValidationError,
    ConfigurationLoadError
)


class TestConfidenceWeightsConfigLoading(unittest.TestCase):
    """Test confidence weights configuration loading functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_config_file = Path(self.temp_dir) / 'valid_weights.yaml'
        self.invalid_config_file = Path(self.temp_dir) / 'invalid_weights.yaml'
        
        # Create valid configuration
        self.valid_config = {
            'default_weights': {
                'morphological': 0.35,
                'contextual': 0.30,
                'domain': 0.20,
                'discourse': 0.15
            },
            'rule_specific_weights': {
                'pronouns': {
                    'morphological': 0.25,
                    'contextual': 0.45,
                    'domain': 0.20,
                    'discourse': 0.10
                }
            },
            'content_type_weights': {
                'technical': {
                    'morphological': 0.30,
                    'contextual': 0.25,
                    'domain': 0.30,
                    'discourse': 0.15
                }
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.35,
                    'contextual': 0.30,
                    'domain': 0.20,
                    'discourse': 0.15
                }
            }
        }
        
        with open(self.valid_config_file, 'w') as f:
            yaml.dump(self.valid_config, f)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_valid_config_file(self):
        """Test loading a valid confidence weights configuration."""
        config_manager = ConfidenceWeightsConfig(self.valid_config_file)
        config = config_manager.load_config()
        
        # Verify default weights are loaded correctly
        self.assertEqual(config['default_weights']['morphological'], 0.35)
        self.assertEqual(config['default_weights']['contextual'], 0.30)
        self.assertEqual(config['default_weights']['domain'], 0.20)
        self.assertEqual(config['default_weights']['discourse'], 0.15)
        
        # Verify rule-specific weights are loaded
        self.assertIn('pronouns', config['rule_specific_weights'])
        pronouns_weights = config['rule_specific_weights']['pronouns']
        self.assertEqual(pronouns_weights['contextual'], 0.45)
    
    def test_load_with_defaults_when_missing_file(self):
        """Test loading defaults when configuration file is missing."""
        missing_file = Path(self.temp_dir) / 'missing.yaml'
        config_manager = ConfidenceWeightsConfig(missing_file)
        config = config_manager.load_config()
        
        # Should load defaults
        self.assertIn('default_weights', config)
        self.assertEqual(config['default_weights']['morphological'], 0.35)
        self.assertEqual(config['default_weights']['contextual'], 0.30)
    
    def test_default_config_file_path(self):
        """Test that default config file path is set correctly."""
        config_manager = ConfidenceWeightsConfig()
        expected_path = Path(__file__).parent.parent.parent / 'config' / 'confidence_weights.yaml'
        self.assertEqual(config_manager.get_config_file_path(), expected_path)
    
    def test_get_default_config_structure(self):
        """Test that default configuration has correct structure."""
        config_manager = ConfidenceWeightsConfig(self.valid_config_file)
        defaults = config_manager.get_default_config()
        
        # Check required sections
        self.assertIn('default_weights', defaults)
        self.assertIn('fallback_weights', defaults)
        self.assertIn('adjustment_factors', defaults)
        self.assertIn('calculation_settings', defaults)
        
        # Check default weights sum to 1.0
        weights = defaults['default_weights']
        weight_sum = sum(weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=6)


class TestConfidenceWeightsValidation(unittest.TestCase):
    """Test confidence weights validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_weights.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_weight_configuration(self):
        """Test validation of valid weight configuration."""
        valid_config = {
            'default_weights': {
                'morphological': 0.35,
                'contextual': 0.30,
                'domain': 0.20,
                'discourse': 0.15
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        # Should not raise an exception
        config = config_manager.load_config()
        self.assertIsNotNone(config)
    
    def test_merged_config_weight_sum_validation(self):
        """Test that weight sum validation works on merged configuration.
        
        Note: Missing keys are filled with defaults, then sum is validated.
        This tests that the merged configuration (user values + defaults) must sum to 1.0.
        """
        invalid_config = {
            'default_weights': {
                'morphological': 0.6,  # User overrides
                'contextual': 0.4      # User overrides
                # 'domain' and 'discourse' will be filled from defaults (0.2 + 0.15 = 0.35)
                # Total: 0.6 + 0.4 + 0.2 + 0.15 = 1.35 (invalid)
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('default_weights', error_message)
        self.assertIn('weights must sum to 1.0', error_message)
        self.assertIn('1.350000', error_message)  # Expected sum after merging with defaults
    
    def test_weights_not_summing_to_one(self):
        """Test validation error when weights don't sum to 1.0."""
        invalid_config = {
            'default_weights': {
                'morphological': 0.5,
                'contextual': 0.3,
                'domain': 0.2,
                'discourse': 0.1  # Sum = 1.1, not 1.0
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('weights must sum to 1.0', error_message)
    
    def test_weight_values_out_of_range(self):
        """Test validation error for weight values outside 0.0-1.0 range."""
        invalid_config = {
            'default_weights': {
                'morphological': 1.5,  # Invalid: > 1.0
                'contextual': -0.1,    # Invalid: < 0.0
                'domain': 0.3,
                'discourse': 0.3
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('Configuration range validation errors', error_message)
    
    def test_invalid_weight_types(self):
        """Test validation error for non-numeric weight values."""
        invalid_config = {
            'default_weights': {
                'morphological': 'not_a_number',  # Invalid type
                'contextual': 0.30,
                'domain': 0.35,
                'discourse': 0.35
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('must be a number', error_message)


class TestAdjustmentFactorsValidation(unittest.TestCase):
    """Test adjustment factors validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_weights.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_adjustment_factors(self):
        """Test validation of valid adjustment factors."""
        valid_config = {
            'default_weights': {
                'morphological': 0.25,
                'contextual': 0.25,
                'domain': 0.25,
                'discourse': 0.25
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            },
            'adjustment_factors': {
                'high_certainty_boost': 1.2,
                'ambiguity_penalty': 0.8,
                'adjustment_threshold': 0.6,
                'max_confidence': 0.95,
                'min_confidence': 0.05
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        config = config_manager.load_config()
        self.assertIsNotNone(config)
    
    def test_invalid_adjustment_factor_ranges(self):
        """Test validation error for adjustment factors out of valid ranges."""
        invalid_config = {
            'default_weights': {
                'morphological': 0.25,
                'contextual': 0.25,
                'domain': 0.25,
                'discourse': 0.25
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            },
            'adjustment_factors': {
                'max_confidence': 1.5,  # Invalid: > 1.0
                'min_confidence': -0.1  # Invalid: < 0.0
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('must be between 0.0 and 1.0', error_message)
    
    def test_min_max_confidence_logical_constraint(self):
        """Test validation error when min_confidence >= max_confidence."""
        invalid_config = {
            'default_weights': {
                'morphological': 0.25,
                'contextual': 0.25,
                'domain': 0.25,
                'discourse': 0.25
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            },
            'adjustment_factors': {
                'max_confidence': 0.3,
                'min_confidence': 0.8  # Invalid: min > max
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('must be less than max_confidence', error_message)


class TestCalculationSettingsValidation(unittest.TestCase):
    """Test calculation settings validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_weights.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_calculation_settings(self):
        """Test validation of valid calculation settings."""
        valid_config = {
            'default_weights': {
                'morphological': 0.25,
                'contextual': 0.25,
                'domain': 0.25,
                'discourse': 0.25
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            },
            'calculation_settings': {
                'combination_method': 'geometric_mean',
                'normalize_weights': False,
                'precision': 4,
                'enable_caching': True,
                'cache_ttl': 600
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        config = config_manager.load_config()
        self.assertIsNotNone(config)
    
    def test_invalid_combination_method(self):
        """Test validation error for invalid combination method."""
        invalid_config = {
            'default_weights': {
                'morphological': 0.25,
                'contextual': 0.25,
                'domain': 0.25,
                'discourse': 0.25
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.25,
                    'contextual': 0.25,
                    'domain': 0.25,
                    'discourse': 0.25
                }
            },
            'calculation_settings': {
                'combination_method': 'invalid_method'
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ConfidenceWeightsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('combination_method must be one of', error_message)


class TestConfidenceWeightsAccess(unittest.TestCase):
    """Test confidence weights access methods."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_weights.yaml'
        
        # Create configuration with rule-specific and content-type weights
        self.test_config = {
            'default_weights': {
                'morphological': 0.35,
                'contextual': 0.30,
                'domain': 0.20,
                'discourse': 0.15
            },
            'rule_specific_weights': {
                'pronouns': {
                    'morphological': 0.25,
                    'contextual': 0.45,
                    'domain': 0.20,
                    'discourse': 0.10
                },
                'grammar': {
                    'morphological': 0.50,
                    'contextual': 0.20,
                    'domain': 0.15,
                    'discourse': 0.15
                }
            },
            'content_type_weights': {
                'technical': {
                    'morphological': 0.30,
                    'contextual': 0.25,
                    'domain': 0.30,
                    'discourse': 0.15
                },
                'narrative': {
                    'morphological': 0.25,
                    'contextual': 0.35,
                    'domain': 0.15,
                    'discourse': 0.25
                }
            },
            'fallback_weights': {
                'unknown_rule': {
                    'morphological': 0.40,
                    'contextual': 0.25,
                    'domain': 0.20,
                    'discourse': 0.15
                },
                'unknown_content': {
                    'morphological': 0.30,
                    'contextual': 0.30,
                    'domain': 0.25,
                    'discourse': 0.15
                }
            },
            'adjustment_factors': {
                'high_certainty_boost': 1.1,
                'ambiguity_penalty': 0.9
            },
            'calculation_settings': {
                'combination_method': 'weighted_average',
                'normalize_weights': True
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config, f)
        
        self.config_manager = ConfidenceWeightsConfig(self.config_file)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_weights_for_rule_specific(self):
        """Test getting weights for specific rule types."""
        # Test rule-specific weights
        pronouns_weights = self.config_manager.get_weights_for_rule('pronouns')
        self.assertEqual(pronouns_weights['contextual'], 0.45)
        self.assertEqual(pronouns_weights['morphological'], 0.25)
        
        grammar_weights = self.config_manager.get_weights_for_rule('grammar')
        self.assertEqual(grammar_weights['morphological'], 0.50)
        self.assertEqual(grammar_weights['contextual'], 0.20)
    
    def test_get_weights_for_rule_fallback_to_default(self):
        """Test fallback to default weights for unknown rule types."""
        unknown_weights = self.config_manager.get_weights_for_rule('unknown_rule_type')
        
        # Should fallback to default weights
        self.assertEqual(unknown_weights['morphological'], 0.35)
        self.assertEqual(unknown_weights['contextual'], 0.30)
        self.assertEqual(unknown_weights['domain'], 0.20)
        self.assertEqual(unknown_weights['discourse'], 0.15)
    
    def test_get_weights_for_content_type_specific(self):
        """Test getting weights for specific content types."""
        technical_weights = self.config_manager.get_weights_for_content_type('technical')
        self.assertEqual(technical_weights['domain'], 0.30)
        self.assertEqual(technical_weights['morphological'], 0.30)
        
        narrative_weights = self.config_manager.get_weights_for_content_type('narrative')
        self.assertEqual(narrative_weights['contextual'], 0.35)
        self.assertEqual(narrative_weights['discourse'], 0.25)
    
    def test_get_weights_for_content_type_fallback_to_default(self):
        """Test fallback to default weights for unknown content types."""
        unknown_weights = self.config_manager.get_weights_for_content_type('unknown_content_type')
        
        # Should fallback to default weights
        self.assertEqual(unknown_weights['morphological'], 0.35)
        self.assertEqual(unknown_weights['contextual'], 0.30)
    
    def test_get_fallback_weights(self):
        """Test getting fallback weights."""
        unknown_rule_weights = self.config_manager.get_fallback_weights('unknown_rule')
        self.assertEqual(unknown_rule_weights['morphological'], 0.40)
        
        unknown_content_weights = self.config_manager.get_fallback_weights('unknown_content')
        self.assertEqual(unknown_content_weights['morphological'], 0.30)
        
        # Test default fallback
        default_fallback = self.config_manager.get_fallback_weights('nonexistent_fallback')
        self.assertEqual(default_fallback['morphological'], 0.35)  # Should use default weights
    
    def test_get_adjustment_factors(self):
        """Test getting adjustment factors."""
        factors = self.config_manager.get_adjustment_factors()
        
        self.assertEqual(factors['high_certainty_boost'], 1.1)
        self.assertEqual(factors['ambiguity_penalty'], 0.9)
    
    def test_get_calculation_settings(self):
        """Test getting calculation settings."""
        settings = self.config_manager.get_calculation_settings()
        
        self.assertEqual(settings['combination_method'], 'weighted_average')
        self.assertEqual(settings['normalize_weights'], True)
    
    def test_get_all_rule_types(self):
        """Test getting all defined rule types."""
        rule_types = self.config_manager.get_all_rule_types()
        
        self.assertIn('pronouns', rule_types)
        self.assertIn('grammar', rule_types)
        self.assertEqual(len(rule_types), 2)
    
    def test_get_all_content_types(self):
        """Test getting all defined content types."""
        content_types = self.config_manager.get_all_content_types()
        
        self.assertIn('technical', content_types)
        self.assertIn('narrative', content_types)
        self.assertEqual(len(content_types), 2)
    
    def test_weights_are_copied_not_referenced(self):
        """Test that returned weights are copies, not references."""
        weights1 = self.config_manager.get_weights_for_rule('pronouns')
        weights2 = self.config_manager.get_weights_for_rule('pronouns')
        
        # Modify one copy
        weights1['morphological'] = 0.99
        
        # Other copy should be unchanged
        self.assertEqual(weights2['morphological'], 0.25)


class TestConfidenceWeightsDefaultFile(unittest.TestCase):
    """Test using the default confidence weights file."""
    
    def test_default_file_loading(self):
        """Test that the default confidence_weights.yaml file can be loaded."""
        # This tests the actual shipped configuration file
        config_manager = ConfidenceWeightsConfig()
        
        # Should be able to load without errors
        config = config_manager.load_config()
        
        # Verify essential structure
        self.assertIn('default_weights', config)
        self.assertIn('rule_specific_weights', config)
        self.assertIn('content_type_weights', config)
        self.assertIn('fallback_weights', config)
        
        # Verify default weights sum to 1.0
        default_weights = config['default_weights']
        weight_sum = sum(default_weights.values())
        self.assertAlmostEqual(weight_sum, 1.0, places=6)
        
        # Verify some expected rule types exist
        rule_types = config['rule_specific_weights']
        self.assertIn('pronouns', rule_types)
        self.assertIn('grammar', rule_types)
        self.assertIn('terminology', rule_types)
        
        # Verify some expected content types exist
        content_types = config['content_type_weights']
        self.assertIn('technical', content_types)
        self.assertIn('narrative', content_types)


if __name__ == '__main__':
    unittest.main(verbosity=2)