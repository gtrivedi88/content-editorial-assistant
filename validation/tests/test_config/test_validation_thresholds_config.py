"""
Comprehensive test suite for validation thresholds configuration.
Tests threshold loading, validation, severity-based thresholds, and multi-pass settings.
"""

import unittest
import tempfile
import yaml
import os
from pathlib import Path
from unittest.mock import patch

from validation.config.validation_thresholds_config import ValidationThresholdsConfig
from validation.config.base_config import (
    ConfigurationValidationError,
    ConfigurationLoadError
)


class TestValidationThresholdsConfigLoading(unittest.TestCase):
    """Test validation thresholds configuration loading functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_config_file = Path(self.temp_dir) / 'valid_thresholds.yaml'
        
        # Create valid configuration
        self.valid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                },
                'major': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.55,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            },
            'multi_pass_validation': {
                'enabled': True,
                'max_passes': 4,
                'default_agreement_threshold': 2
            }
        }
        
        with open(self.valid_config_file, 'w') as f:
            yaml.dump(self.valid_config, f)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_valid_config_file(self):
        """Test loading a valid validation thresholds configuration."""
        config_manager = ValidationThresholdsConfig(self.valid_config_file)
        config = config_manager.load_config()
        
        # Verify minimum confidence thresholds are loaded correctly
        thresholds = config['minimum_confidence_thresholds']
        self.assertEqual(thresholds['high_confidence'], 0.80)
        self.assertEqual(thresholds['medium_confidence'], 0.60)
        self.assertEqual(thresholds['low_confidence'], 0.40)
        self.assertEqual(thresholds['rejection_threshold'], 0.25)
        
        # Verify severity thresholds are loaded
        severities = config['severity_thresholds']
        self.assertIn('critical', severities)
        self.assertEqual(severities['critical']['minimum_confidence'], 0.85)
        self.assertEqual(severities['critical']['minimum_passes_agreement'], 3)
    
    def test_load_with_defaults_when_missing_file(self):
        """Test loading defaults when configuration file is missing."""
        missing_file = Path(self.temp_dir) / 'missing.yaml'
        config_manager = ValidationThresholdsConfig(missing_file)
        config = config_manager.load_config()
        
        # Should load defaults
        self.assertIn('minimum_confidence_thresholds', config)
        thresholds = config['minimum_confidence_thresholds']
        self.assertEqual(thresholds['high_confidence'], 0.80)
        self.assertEqual(thresholds['medium_confidence'], 0.60)
    
    def test_default_config_file_path(self):
        """Test that default config file path is set correctly."""
        config_manager = ValidationThresholdsConfig()
        expected_path = Path(__file__).parent.parent.parent / 'config' / 'validation_thresholds.yaml'
        self.assertEqual(config_manager.get_config_file_path(), expected_path)
    
    def test_get_default_config_structure(self):
        """Test that default configuration has correct structure."""
        config_manager = ValidationThresholdsConfig(self.valid_config_file)
        defaults = config_manager.get_default_config()
        
        # Check required sections
        self.assertIn('minimum_confidence_thresholds', defaults)
        self.assertIn('severity_thresholds', defaults)
        self.assertIn('multi_pass_validation', defaults)
        
        # Check threshold ordering
        thresholds = defaults['minimum_confidence_thresholds']
        self.assertLess(thresholds['rejection_threshold'], thresholds['low_confidence'])
        self.assertLess(thresholds['low_confidence'], thresholds['medium_confidence'])
        self.assertLess(thresholds['medium_confidence'], thresholds['high_confidence'])


class TestValidationThresholdsValidation(unittest.TestCase):
    """Test validation thresholds validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_thresholds.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_threshold_configuration(self):
        """Test validation of valid threshold configuration."""
        valid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.85,
                'medium_confidence': 0.65,
                'low_confidence': 0.45,
                'rejection_threshold': 0.20
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.80,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'major': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.50,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        # Should not raise an exception
        config = config_manager.load_config()
        self.assertIsNotNone(config)
    
    def test_threshold_ordering_after_merge_validation(self):
        """Test validation error when user overrides create invalid threshold ordering.
        
        Note: Missing keys are filled with defaults, then ordering is validated.
        This tests that the merged configuration must have proper threshold ordering.
        """
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.50,  # User sets this too low
                'medium_confidence': 0.60,  # User sets this higher than high (invalid)
                # 'low_confidence' and 'rejection_threshold' will be filled from defaults
                # This creates invalid ordering after merging
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('must be in ascending order', error_message)
    
    def test_threshold_ordering_validation(self):
        """Test validation error when thresholds are not in ascending order."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.60,  # Should be highest
                'medium_confidence': 0.80,  # Incorrectly higher than high
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('must be in ascending order', error_message)
    
    def test_threshold_values_out_of_range(self):
        """Test validation error for threshold values outside 0.0-1.0 range."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 1.5,  # Invalid: > 1.0
                'medium_confidence': 0.60,
                'low_confidence': -0.1,  # Invalid: < 0.0
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('Configuration range validation errors', error_message)
    
    def test_invalid_severity_config_after_merge(self):
        """Test validation error when user overrides create invalid severity configuration.
        
        Note: Missing severity levels are filled with defaults, then validated.
        This tests that user-provided severity configurations must be valid.
        """
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                },
                'major': {
                    'minimum_confidence': 'invalid_value',  # Invalid: should be number
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                }
                # 'minor' and 'suggestion' will be filled from defaults
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('minimum_confidence must be between 0.0 and 1.0', error_message)


class TestSeverityConfigValidation(unittest.TestCase):
    """Test severity configuration validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_thresholds.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_invalid_severity_minimum_confidence(self):
        """Test validation error for invalid severity minimum confidence."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 1.5,  # Invalid: > 1.0
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                },
                'major': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.55,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('minimum_confidence must be between 0.0 and 1.0', error_message)
    
    def test_invalid_severity_passes_agreement(self):
        """Test validation error for invalid minimum passes agreement."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 15  # Invalid: > 10
                },
                'major': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.55,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('minimum_passes_agreement must be integer 1-10', error_message)
    
    def test_invalid_severity_require_multi_pass_type(self):
        """Test validation error for non-boolean require_multi_pass."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': 'yes',  # Invalid: should be boolean
                    'minimum_passes_agreement': 3
                },
                'major': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.55,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('require_multi_pass must be boolean', error_message)


class TestMultiPassValidation(unittest.TestCase):
    """Test multi-pass validation settings."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_thresholds.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_multi_pass_settings(self):
        """Test validation of valid multi-pass settings."""
        valid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                }
            },
            'multi_pass_validation': {
                'enabled': True,
                'max_passes': 3,
                'default_agreement_threshold': 2,
                'agreement_confidence_boost': 0.1,
                'disagreement_confidence_penalty': 0.15
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        config = config_manager.load_config()
        self.assertIsNotNone(config)
    
    def test_invalid_multi_pass_max_passes(self):
        """Test validation error for invalid max_passes."""
        invalid_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.80,
                'medium_confidence': 0.60,
                'low_confidence': 0.40,
                'rejection_threshold': 0.25
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.85,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                }
            },
            'multi_pass_validation': {
                'enabled': True,
                'max_passes': 15,  # Invalid: > 10
                'default_agreement_threshold': 2
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config_manager = ValidationThresholdsConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('max_passes must be integer 1-10', error_message)


class TestValidationThresholdsAccess(unittest.TestCase):
    """Test validation thresholds access methods."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_thresholds.yaml'
        
        # Create configuration with various thresholds
        self.test_config = {
            'minimum_confidence_thresholds': {
                'high_confidence': 0.85,
                'medium_confidence': 0.65,
                'low_confidence': 0.45,
                'rejection_threshold': 0.20
            },
            'severity_thresholds': {
                'critical': {
                    'minimum_confidence': 0.90,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 3
                },
                'major': {
                    'minimum_confidence': 0.75,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'minor': {
                    'minimum_confidence': 0.55,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                },
                'suggestion': {
                    'minimum_confidence': 0.40,
                    'require_multi_pass': False,
                    'minimum_passes_agreement': 1
                }
            },
            'rule_specific_thresholds': {
                'pronouns': {
                    'minimum_confidence': 0.70,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                },
                'grammar': {
                    'minimum_confidence': 0.65,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                }
            },
            'content_type_thresholds': {
                'technical': {
                    'confidence_modifier': 1.1,
                    'minimum_confidence_override': 0.70
                },
                'narrative': {
                    'confidence_modifier': 0.9,
                    'minimum_confidence_override': 0.50
                }
            },
            'multi_pass_validation': {
                'enabled': True,
                'max_passes': 4,
                'default_agreement_threshold': 2
            },
            'error_acceptance_criteria': {
                'auto_accept': {
                    'single_pass_threshold': 0.90,
                    'multi_pass_threshold': 0.70,
                    'min_agreeing_passes': 2
                },
                'auto_reject': {
                    'low_confidence_threshold': 0.20,
                    'max_disagreement_ratio': 0.7
                }
            },
            'fallback_thresholds': {
                'unknown_rule': {
                    'minimum_confidence': 0.65,
                    'require_multi_pass': True,
                    'minimum_passes_agreement': 2
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(self.test_config, f)
        
        self.config_manager = ValidationThresholdsConfig(self.config_file)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_minimum_confidence_thresholds(self):
        """Test getting minimum confidence thresholds."""
        thresholds = self.config_manager.get_minimum_confidence_thresholds()
        
        self.assertEqual(thresholds['high_confidence'], 0.85)
        self.assertEqual(thresholds['medium_confidence'], 0.65)
        self.assertEqual(thresholds['low_confidence'], 0.45)
        self.assertEqual(thresholds['rejection_threshold'], 0.20)
    
    def test_get_severity_threshold_specific(self):
        """Test getting thresholds for specific severity levels."""
        critical_threshold = self.config_manager.get_severity_threshold('critical')
        self.assertEqual(critical_threshold['minimum_confidence'], 0.90)
        self.assertTrue(critical_threshold['require_multi_pass'])
        self.assertEqual(critical_threshold['minimum_passes_agreement'], 3)
        
        minor_threshold = self.config_manager.get_severity_threshold('minor')
        self.assertEqual(minor_threshold['minimum_confidence'], 0.55)
        self.assertFalse(minor_threshold['require_multi_pass'])
        self.assertEqual(minor_threshold['minimum_passes_agreement'], 1)
    
    def test_get_severity_threshold_fallback(self):
        """Test fallback to default for unknown severity levels."""
        unknown_threshold = self.config_manager.get_severity_threshold('unknown_severity')
        
        # Should use fallback values
        self.assertEqual(unknown_threshold['minimum_confidence'], 0.65)
        self.assertTrue(unknown_threshold['require_multi_pass'])
        self.assertEqual(unknown_threshold['minimum_passes_agreement'], 2)
    
    def test_get_rule_threshold_specific(self):
        """Test getting thresholds for specific rule types."""
        pronoun_threshold = self.config_manager.get_rule_threshold('pronouns')
        self.assertEqual(pronoun_threshold['minimum_confidence'], 0.70)
        self.assertTrue(pronoun_threshold['require_multi_pass'])
        
        grammar_threshold = self.config_manager.get_rule_threshold('grammar')
        self.assertEqual(grammar_threshold['minimum_confidence'], 0.65)
    
    def test_get_rule_threshold_fallback(self):
        """Test fallback to default for unknown rule types."""
        unknown_threshold = self.config_manager.get_rule_threshold('unknown_rule_type')
        
        # Should use fallback values
        self.assertEqual(unknown_threshold['minimum_confidence'], 0.65)
        self.assertTrue(unknown_threshold['require_multi_pass'])
    
    def test_get_content_type_threshold_specific(self):
        """Test getting thresholds for specific content types."""
        technical_threshold = self.config_manager.get_content_type_threshold('technical')
        self.assertEqual(technical_threshold['confidence_modifier'], 1.1)
        self.assertEqual(technical_threshold['minimum_confidence_override'], 0.70)
        
        narrative_threshold = self.config_manager.get_content_type_threshold('narrative')
        self.assertEqual(narrative_threshold['confidence_modifier'], 0.9)
    
    def test_get_content_type_threshold_fallback(self):
        """Test fallback to default for unknown content types."""
        unknown_threshold = self.config_manager.get_content_type_threshold('unknown_content')
        
        # Should use fallback values
        self.assertEqual(unknown_threshold['confidence_modifier'], 1.0)
        self.assertEqual(unknown_threshold['minimum_confidence_override'], 0.60)
    
    def test_get_multi_pass_settings(self):
        """Test getting multi-pass validation settings."""
        settings = self.config_manager.get_multi_pass_settings()
        
        self.assertTrue(settings['enabled'])
        self.assertEqual(settings['max_passes'], 4)
        self.assertEqual(settings['default_agreement_threshold'], 2)
    
    def test_get_error_acceptance_criteria(self):
        """Test getting error acceptance criteria."""
        criteria = self.config_manager.get_error_acceptance_criteria()
        
        auto_accept = criteria['auto_accept']
        self.assertEqual(auto_accept['single_pass_threshold'], 0.90)
        self.assertEqual(auto_accept['multi_pass_threshold'], 0.70)
        
        auto_reject = criteria['auto_reject']
        self.assertEqual(auto_reject['low_confidence_threshold'], 0.20)
    
    def test_should_auto_accept(self):
        """Test auto-acceptance logic."""
        # High confidence single pass
        self.assertTrue(self.config_manager.should_auto_accept(0.95, 1))
        
        # Medium confidence with multiple passes
        self.assertTrue(self.config_manager.should_auto_accept(0.75, 2))
        
        # Low confidence should not auto-accept
        self.assertFalse(self.config_manager.should_auto_accept(0.50, 1))
        
        # Medium confidence with insufficient passes
        self.assertFalse(self.config_manager.should_auto_accept(0.75, 1))
    
    def test_should_auto_reject(self):
        """Test auto-rejection logic."""
        # Very low confidence
        self.assertTrue(self.config_manager.should_auto_reject(0.15, 0.0))
        
        # High disagreement ratio
        self.assertTrue(self.config_manager.should_auto_reject(0.60, 0.8))
        
        # Acceptable confidence and disagreement
        self.assertFalse(self.config_manager.should_auto_reject(0.70, 0.3))
    
    def test_get_all_rule_types(self):
        """Test getting all configured rule types."""
        rule_types = self.config_manager.get_all_rule_types()
        
        self.assertIn('pronouns', rule_types)
        self.assertIn('grammar', rule_types)
        self.assertEqual(len(rule_types), 2)
    
    def test_get_all_content_types(self):
        """Test getting all configured content types."""
        content_types = self.config_manager.get_all_content_types()
        
        self.assertIn('technical', content_types)
        self.assertIn('narrative', content_types)
        self.assertEqual(len(content_types), 2)
    
    def test_get_all_severity_levels(self):
        """Test getting all configured severity levels."""
        severity_levels = self.config_manager.get_all_severity_levels()
        
        self.assertIn('critical', severity_levels)
        self.assertIn('major', severity_levels)
        self.assertIn('minor', severity_levels)
        self.assertIn('suggestion', severity_levels)
        self.assertEqual(len(severity_levels), 4)
    
    def test_thresholds_are_copied_not_referenced(self):
        """Test that returned thresholds are copies, not references."""
        thresholds1 = self.config_manager.get_severity_threshold('critical')
        thresholds2 = self.config_manager.get_severity_threshold('critical')
        
        # Modify one copy
        thresholds1['minimum_confidence'] = 0.99
        
        # Other copy should be unchanged
        self.assertEqual(thresholds2['minimum_confidence'], 0.90)


class TestValidationThresholdsDefaultFile(unittest.TestCase):
    """Test using the default validation thresholds file."""
    
    def test_default_file_loading(self):
        """Test that the default validation_thresholds.yaml file can be loaded."""
        # This tests the actual shipped configuration file
        config_manager = ValidationThresholdsConfig()
        
        # Should be able to load without errors
        config = config_manager.load_config()
        
        # Verify essential structure
        self.assertIn('minimum_confidence_thresholds', config)
        self.assertIn('severity_thresholds', config)
        self.assertIn('multi_pass_validation', config)
        
        # Verify threshold ordering
        thresholds = config['minimum_confidence_thresholds']
        self.assertLess(thresholds['rejection_threshold'], thresholds['low_confidence'])
        self.assertLess(thresholds['low_confidence'], thresholds['medium_confidence'])
        self.assertLess(thresholds['medium_confidence'], thresholds['high_confidence'])
        
        # Verify some expected severity levels exist
        severities = config['severity_thresholds']
        self.assertIn('critical', severities)
        self.assertIn('major', severities)
        self.assertIn('minor', severities)
        self.assertIn('suggestion', severities)
        
        # Verify rule-specific thresholds exist
        if 'rule_specific_thresholds' in config:
            rule_thresholds = config['rule_specific_thresholds']
            self.assertIn('pronouns', rule_thresholds)
            self.assertIn('grammar', rule_thresholds)


if __name__ == '__main__':
    unittest.main(verbosity=2)