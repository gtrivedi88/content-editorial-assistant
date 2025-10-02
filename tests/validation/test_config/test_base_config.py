"""
Comprehensive test suite for base configuration system.
Tests YAML loading, validation, caching, and error handling.
"""

import unittest
import tempfile
import os
import yaml
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

from validation.config.base_config import (
    BaseConfig,
    SchemaValidator,
    ConfigurationError,
    ConfigurationValidationError,
    ConfigurationLoadError
)


class TestBaseConfig(BaseConfig):
    """Test implementation of BaseConfig for testing purposes."""
    
    def get_default_config(self):
        """Return test default configuration."""
        return {
            'test_string': 'default_value',
            'test_number': 42,
            'test_float': 3.14,
            'test_boolean': True,
            'test_dict': {
                'nested_key': 'nested_value',
                'nested_number': 100
            },
            'test_list': ['item1', 'item2']
        }
    
    def validate_config(self, config):
        """Validate test configuration."""
        # Required keys
        required_keys = ['test_string', 'test_number']
        SchemaValidator.validate_required_keys(config, required_keys)
        
        # Type validation
        key_types = {
            'test_string': str,
            'test_number': int,
            'test_float': float,
            'test_boolean': bool,
            'test_dict': dict,
            'test_list': list
        }
        SchemaValidator.validate_key_types(config, key_types)
        
        # Range validation
        value_ranges = {
            'test_number': {'min': 0, 'max': 1000},
            'test_float': {'min': 0.0, 'max': 10.0}
        }
        SchemaValidator.validate_value_ranges(config, value_ranges)
        
        return True


class TestOptionalConfig(BaseConfig):
    """Test implementation with optional configuration file."""
    
    def _is_optional(self):
        return True
    
    def get_default_config(self):
        return {'optional_key': 'default_value'}
    
    def validate_config(self, config):
        return True


class TestBaseConfigLoading(unittest.TestCase):
    """Test configuration loading functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.valid_config_file = Path(self.temp_dir) / 'valid_config.yaml'
        self.invalid_config_file = Path(self.temp_dir) / 'invalid_config.yaml'
        self.missing_config_file = Path(self.temp_dir) / 'missing_config.yaml'
        self.empty_config_file = Path(self.temp_dir) / 'empty_config.yaml'
        
        # Create valid configuration file
        valid_config = {
            'test_string': 'custom_value',
            'test_number': 123,
            'test_float': 2.71,
            'test_dict': {
                'nested_key': 'custom_nested_value'
            }
        }
        with open(self.valid_config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        # Create invalid YAML file
        with open(self.invalid_config_file, 'w') as f:
            f.write('invalid: yaml: content: [unclosed')
        
        # Create empty file
        with open(self.empty_config_file, 'w') as f:
            f.write('')
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_valid_config_file(self):
        """Test loading a valid configuration file."""
        config_manager = TestBaseConfig(self.valid_config_file)
        config = config_manager.load_config()
        
        # Should merge with defaults
        self.assertEqual(config['test_string'], 'custom_value')  # Overridden
        self.assertEqual(config['test_number'], 123)  # Overridden
        self.assertEqual(config['test_boolean'], True)  # From defaults
        self.assertEqual(config['test_dict']['nested_key'], 'custom_nested_value')  # Merged
        self.assertEqual(config['test_dict']['nested_number'], 100)  # From defaults
    
    def test_load_missing_required_config_file(self):
        """Test error handling for missing required configuration file."""
        with self.assertRaises(ConfigurationLoadError) as context:
            TestBaseConfig(self.missing_config_file)
        
        self.assertIn('Required configuration file not found', str(context.exception))
    
    def test_load_missing_optional_config_file(self):
        """Test handling of missing optional configuration file."""
        config_manager = TestOptionalConfig(self.missing_config_file)
        config = config_manager.load_config()
        
        # Should return defaults only
        self.assertEqual(config, {'optional_key': 'default_value'})
    
    def test_load_invalid_yaml_file(self):
        """Test error handling for invalid YAML syntax."""
        config_manager = TestBaseConfig(self.invalid_config_file)
        
        with self.assertRaises(ConfigurationLoadError) as context:
            config_manager.load_config()
        
        self.assertIn('Failed to parse YAML', str(context.exception))
    
    def test_load_empty_config_file(self):
        """Test handling of empty configuration file."""
        config_manager = TestBaseConfig(self.empty_config_file)
        config = config_manager.load_config()
        
        # Should return defaults only
        expected_defaults = config_manager.get_default_config()
        self.assertEqual(config, expected_defaults)
    
    def test_non_dict_yaml_content(self):
        """Test error handling for non-dictionary YAML content."""
        non_dict_file = Path(self.temp_dir) / 'non_dict.yaml'
        with open(non_dict_file, 'w') as f:
            f.write('- item1\n- item2\n')  # YAML list, not dict
        
        config_manager = TestBaseConfig(non_dict_file)
        
        with self.assertRaises(ConfigurationLoadError) as context:
            config_manager.load_config()
        
        self.assertIn('must contain a YAML mapping/dictionary', str(context.exception))
    
    def test_unicode_decode_error(self):
        """Test handling of Unicode decode errors."""
        binary_file = Path(self.temp_dir) / 'binary.yaml'
        with open(binary_file, 'wb') as f:
            f.write(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        config_manager = TestBaseConfig(binary_file)
        
        with self.assertRaises(ConfigurationLoadError) as context:
            config_manager.load_config()
        
        self.assertIn('Failed to decode configuration file', str(context.exception))


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'test_config.yaml'
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_missing_required_keys(self):
        """Test validation error for missing required keys."""
        # Create a config missing a required key that's not in defaults
        config = {'test_string': 'valid_string'}  # Missing 'test_number' which has no default
        
        # Create a custom test config that requires a key not in defaults
        class TestConfigMissingKey(TestBaseConfig):
            def get_default_config(self):
                # Don't include test_number in defaults
                return {
                    'test_string': 'default_value',
                    'test_float': 3.14,
                    'test_boolean': True,
                    'test_dict': {
                        'nested_key': 'nested_value',
                        'nested_number': 100
                    },
                    'test_list': ['item1', 'item2']
                }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
        
        config_manager = TestConfigMissingKey(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        self.assertIn('Missing required configuration keys', str(context.exception))
        self.assertIn('test_number', str(context.exception))
    
    def test_incorrect_key_types(self):
        """Test validation error for incorrect key types."""
        config = {
            'test_string': 123,  # Should be string
            'test_number': 'not_a_number'  # Should be int
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
        
        config_manager = TestBaseConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('Configuration type validation errors', error_message)
        self.assertIn('test_string', error_message)
        self.assertIn('expected str', error_message)
    
    def test_value_out_of_range(self):
        """Test validation error for values out of range."""
        config = {
            'test_string': 'valid_string',
            'test_number': 2000,  # Out of range (max: 1000)
            'test_float': 15.0    # Out of range (max: 10.0)
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
        
        config_manager = TestBaseConfig(self.config_file)
        
        with self.assertRaises(ConfigurationValidationError) as context:
            config_manager.load_config()
        
        error_message = str(context.exception)
        self.assertIn('Configuration range validation errors', error_message)
        self.assertIn('test_number', error_message)
        self.assertIn('greater than maximum', error_message)


class TestConfigCaching(unittest.TestCase):
    """Test configuration caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'cached_config.yaml'
        
        # Create initial config
        config = {
            'test_string': 'initial_value',
            'test_number': 100
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_configuration_caching(self):
        """Test that configuration is cached after first load."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=60)  # 1 minute TTL
        
        # First load
        config1 = config_manager.load_config()
        self.assertTrue(config_manager.is_cached())
        self.assertIsNotNone(config_manager.get_cache_age())
        
        # Second load should use cache
        config2 = config_manager.load_config()
        self.assertEqual(config1, config2)
    
    def test_cache_invalidation_on_file_change(self):
        """Test that cache is invalidated when file changes."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=60)
        
        # First load
        config1 = config_manager.load_config()
        original_value = config1['test_string']
        
        # Modify file
        time.sleep(0.1)  # Ensure different modification time
        new_config = {
            'test_string': 'modified_value',
            'test_number': 200
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # Second load should detect change and reload
        config2 = config_manager.load_config()
        self.assertNotEqual(config1['test_string'], config2['test_string'])
        self.assertEqual(config2['test_string'], 'modified_value')
    
    def test_cache_ttl_expiration(self):
        """Test that cache expires after TTL."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=1)  # 1 second TTL
        
        # First load
        config_manager.load_config()
        self.assertTrue(config_manager.is_cached())
        
        # Wait for cache to expire
        time.sleep(1.5)
        
        # Cache should be considered invalid due to TTL
        self.assertFalse(config_manager._is_cache_valid())
    
    def test_force_reload(self):
        """Test forced reload bypasses cache."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=60)
        
        # First load
        config1 = config_manager.load_config()
        
        # Modify file without waiting
        new_config = {
            'test_string': 'force_reload_value',
            'test_number': 300
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # Force reload should get new values
        config2 = config_manager.load_config(force_reload=True)
        self.assertEqual(config2['test_string'], 'force_reload_value')
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=60)
        
        # Load and verify cache
        config_manager.load_config()
        self.assertTrue(config_manager.is_cached())
        
        # Clear cache
        config_manager.clear_cache()
        self.assertFalse(config_manager.is_cached())
        self.assertIsNone(config_manager.get_cache_age())
    
    def test_reload_config(self):
        """Test reload_config method."""
        config_manager = TestBaseConfig(self.config_file, cache_ttl=60)
        
        # First load
        config_manager.load_config()
        self.assertTrue(config_manager.is_cached())
        
        # Reload should clear cache and reload
        config = config_manager.reload_config()
        self.assertIsNotNone(config)
        self.assertTrue(config_manager.is_cached())


class TestSchemaValidator(unittest.TestCase):
    """Test schema validation helper functionality."""
    
    def test_validate_required_keys_success(self):
        """Test successful required keys validation."""
        config = {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}
        required_keys = ['key1', 'key2']
        
        result = SchemaValidator.validate_required_keys(config, required_keys)
        self.assertTrue(result)
    
    def test_validate_required_keys_failure(self):
        """Test required keys validation failure."""
        config = {'key1': 'value1'}
        required_keys = ['key1', 'key2', 'key3']
        
        with self.assertRaises(ConfigurationValidationError) as context:
            SchemaValidator.validate_required_keys(config, required_keys)
        
        error_message = str(context.exception)
        self.assertIn('Missing required configuration keys', error_message)
        self.assertIn('key2', error_message)
        self.assertIn('key3', error_message)
    
    def test_validate_key_types_success(self):
        """Test successful key types validation."""
        config = {
            'str_key': 'string_value',
            'int_key': 42,
            'float_key': 3.14,
            'bool_key': True,
            'list_key': [1, 2, 3],
            'dict_key': {'nested': 'value'}
        }
        key_types = {
            'str_key': str,
            'int_key': int,
            'float_key': float,
            'bool_key': bool,
            'list_key': list,
            'dict_key': dict
        }
        
        result = SchemaValidator.validate_key_types(config, key_types)
        self.assertTrue(result)
    
    def test_validate_key_types_failure(self):
        """Test key types validation failure."""
        config = {
            'str_key': 123,  # Should be string
            'int_key': 'not_an_int'  # Should be int
        }
        key_types = {
            'str_key': str,
            'int_key': int
        }
        
        with self.assertRaises(ConfigurationValidationError) as context:
            SchemaValidator.validate_key_types(config, key_types)
        
        error_message = str(context.exception)
        self.assertIn('Configuration type validation errors', error_message)
        self.assertIn('expected str', error_message)
        self.assertIn('expected int', error_message)
    
    def test_validate_value_ranges_success(self):
        """Test successful value ranges validation."""
        config = {
            'percentage': 75,
            'temperature': 23.5,
            'count': 50
        }
        value_ranges = {
            'percentage': {'min': 0, 'max': 100},
            'temperature': {'min': -10.0, 'max': 50.0},
            'count': {'min': 1}  # Only minimum
        }
        
        result = SchemaValidator.validate_value_ranges(config, value_ranges)
        self.assertTrue(result)
    
    def test_validate_value_ranges_failure(self):
        """Test value ranges validation failure."""
        config = {
            'percentage': 150,  # Too high
            'temperature': -20.0,  # Too low
            'negative_count': -5  # Below minimum
        }
        value_ranges = {
            'percentage': {'min': 0, 'max': 100},
            'temperature': {'min': -10.0, 'max': 50.0},
            'negative_count': {'min': 0}
        }
        
        with self.assertRaises(ConfigurationValidationError) as context:
            SchemaValidator.validate_value_ranges(config, value_ranges)
        
        error_message = str(context.exception)
        self.assertIn('Configuration range validation errors', error_message)
        self.assertIn('greater than maximum', error_message)
        self.assertIn('less than minimum', error_message)


class TestConfigUtilities(unittest.TestCase):
    """Test configuration utility methods."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / 'utility_config.yaml'
        
        config = {'test_key': 'test_value'}
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_get_config_file_path(self):
        """Test getting configuration file path."""
        config_manager = TestBaseConfig(self.config_file)
        
        path = config_manager.get_config_file_path()
        self.assertEqual(path, self.config_file)
        self.assertIsInstance(path, Path)
    
    def test_config_file_exists(self):
        """Test checking if configuration file exists."""
        config_manager = TestBaseConfig(self.config_file)
        self.assertTrue(config_manager.config_file_exists())
        
        missing_file = Path(self.temp_dir) / 'missing.yaml'
        config_manager_missing = TestOptionalConfig(missing_file)
        self.assertFalse(config_manager_missing.config_file_exists())
    
    def test_get_config_file_mtime(self):
        """Test getting configuration file modification time."""
        config_manager = TestBaseConfig(self.config_file)
        
        mtime = config_manager.get_config_file_mtime()
        self.assertIsInstance(mtime, datetime)
        
        # Test with missing file
        missing_file = Path(self.temp_dir) / 'missing.yaml'
        config_manager_missing = TestOptionalConfig(missing_file)
        mtime_missing = config_manager_missing.get_config_file_mtime()
        self.assertIsNone(mtime_missing)
    
    def test_deep_merge(self):
        """Test deep merge functionality."""
        config_manager = TestBaseConfig(self.config_file)
        
        base = {
            'level1': {
                'level2a': {
                    'value1': 'base_value1',
                    'value2': 'base_value2'
                },
                'level2b': 'base_level2b'
            },
            'top_level': 'base_top'
        }
        
        override = {
            'level1': {
                'level2a': {
                    'value1': 'override_value1',  # Should override
                    'value3': 'new_value3'        # Should add
                },
                'level2c': 'new_level2c'          # Should add
            },
            'new_top': 'new_top_value'            # Should add
        }
        
        result = config_manager._deep_merge(base, override)
        
        # Check merged values
        self.assertEqual(result['level1']['level2a']['value1'], 'override_value1')
        self.assertEqual(result['level1']['level2a']['value2'], 'base_value2')
        self.assertEqual(result['level1']['level2a']['value3'], 'new_value3')
        self.assertEqual(result['level1']['level2b'], 'base_level2b')
        self.assertEqual(result['level1']['level2c'], 'new_level2c')
        self.assertEqual(result['top_level'], 'base_top')
        self.assertEqual(result['new_top'], 'new_top_value')


class TestErrorHandling(unittest.TestCase):
    """Test error handling and error message quality."""
    
    def test_configuration_error_hierarchy(self):
        """Test that error classes have correct inheritance."""
        self.assertTrue(issubclass(ConfigurationValidationError, ConfigurationError))
        self.assertTrue(issubclass(ConfigurationLoadError, ConfigurationError))
        
        # Test instantiation
        load_error = ConfigurationLoadError("Load error message")
        self.assertIsInstance(load_error, ConfigurationError)
        self.assertEqual(str(load_error), "Load error message")
        
        validation_error = ConfigurationValidationError("Validation error message")
        self.assertIsInstance(validation_error, ConfigurationError)
        self.assertEqual(str(validation_error), "Validation error message")
    
    def test_clear_error_messages(self):
        """Test that error messages are clear and actionable."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Test missing file error
            missing_file = Path(temp_dir) / 'missing.yaml'
            with self.assertRaises(ConfigurationLoadError) as context:
                TestBaseConfig(missing_file)
            
            error_message = str(context.exception)
            self.assertIn('Required configuration file not found', error_message)
            self.assertIn(str(missing_file), error_message)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main(verbosity=2)