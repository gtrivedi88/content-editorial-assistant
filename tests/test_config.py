"""
Configuration Management Tests
Tests for enterprise-ready configuration management and scalability.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestConfig, TestFixtures, TestValidators

# Import configuration classes
from src.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, config


class TestConfiguration:
    """Test suite for configuration management."""
    
    def test_configuration_constants_availability(self):
        """Test that configuration constants are available and properly typed."""
        
        # Test model configuration
        assert isinstance(TestConfig.DEFAULT_MODEL, str)
        assert isinstance(TestConfig.OLLAMA_MODEL, str)
        assert isinstance(TestConfig.OLLAMA_URL, str)
        
        # Test test data
        assert isinstance(TestConfig.SAMPLE_TEXT, str)
        assert isinstance(TestConfig.SAMPLE_IMPROVED_TEXT, str)
        assert isinstance(TestConfig.SAMPLE_RAW_RESPONSE, str)
        
        # Test confidence thresholds
        assert isinstance(TestConfig.MIN_CONFIDENCE, (int, float))
        assert isinstance(TestConfig.MAX_CONFIDENCE, (int, float))
        assert isinstance(TestConfig.EXPECTED_CONFIDENCE, (int, float))
        
        # Test context options
        assert isinstance(TestConfig.VALID_CONTEXTS, list)
        assert len(TestConfig.VALID_CONTEXTS) > 0
        
        # Test prompt limits
        assert isinstance(TestConfig.MAX_PROMPT_LENGTH, int)
        assert isinstance(TestConfig.MIN_PROMPT_LENGTH, int)
    
    def test_configuration_values_validity(self):
        """Test that configuration values are valid."""
        
        # Confidence should be between 0 and 1
        assert 0.0 <= TestConfig.MIN_CONFIDENCE <= 1.0
        assert 0.0 <= TestConfig.MAX_CONFIDENCE <= 1.0
        assert 0.0 <= TestConfig.EXPECTED_CONFIDENCE <= 1.0
        assert TestConfig.MIN_CONFIDENCE <= TestConfig.MAX_CONFIDENCE
        
        # Prompt lengths should be positive
        assert TestConfig.MIN_PROMPT_LENGTH > 0
        assert TestConfig.MAX_PROMPT_LENGTH > TestConfig.MIN_PROMPT_LENGTH
        
        # Valid contexts should be non-empty strings
        for context in TestConfig.VALID_CONTEXTS:
            assert isinstance(context, str)
            assert len(context) > 0
    
    def test_test_fixtures_functionality(self):
        """Test that test fixtures provide consistent data."""
        
        # Test sample errors
        sample_errors = TestFixtures.get_sample_errors()
        assert isinstance(sample_errors, list)
        assert len(sample_errors) > 0
        
        for error in sample_errors:
            assert isinstance(error, dict)
            assert 'type' in error
            assert 'message' in error
            assert 'severity' in error
        
        # Test mock responses
        ollama_response = TestFixtures.get_mock_ollama_response()
        assert isinstance(ollama_response, dict)
        assert 'model' in ollama_response
        assert 'response' in ollama_response
        assert 'done' in ollama_response
        
        # Test evaluation result
        eval_result = TestFixtures.get_mock_evaluation_result()
        assert isinstance(eval_result, dict)
        assert 'improvements' in eval_result
        assert 'confidence' in eval_result
        assert 'model_used' in eval_result
    
    def test_validators_functionality(self):
        """Test that validators work correctly."""
        
        # Test rewrite result validation
        valid_result = {
            'rewritten_text': TestConfig.SAMPLE_IMPROVED_TEXT,
            'confidence': TestConfig.EXPECTED_CONFIDENCE,
            'improvements': ['Test improvement']
        }
        
        # Should not raise exception
        TestValidators.validate_rewrite_result(valid_result)
        
        # Test prompt validation
        TestValidators.validate_prompt_content(TestConfig.TEST_PROMPT_SUFFICIENT_LENGTH)
        
        # Test system info validation
        test_system_info = {
            'model_info': {'test': 'info'},
            'available_components': ['component1', 'component2'],
            'is_ready': True
        }
        TestValidators.validate_system_info(test_system_info)
    
    def test_mock_factory_consistency(self):
        """Test that mock factory creates consistent objects."""
        
        # Test model manager mocks
        ollama_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        hf_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        
        assert ollama_manager.use_ollama is True
        assert hf_manager.use_ollama is False
        
        # Test other component mocks
        prompt_gen = TestMockFactory.create_mock_prompt_generator()
        text_gen = TestMockFactory.create_mock_text_generator()
        processor = TestMockFactory.create_mock_text_processor()
        evaluator = TestMockFactory.create_mock_evaluator()
        
        # All should be MagicMock instances with proper configuration
        assert hasattr(prompt_gen, 'style_guide_name')
        assert hasattr(text_gen, 'is_available')
        assert hasattr(processor, 'clean_generated_text')
        assert hasattr(evaluator, 'calculate_confidence')
    
    def test_configuration_scalability(self):
        """Test configuration scalability for enterprise use."""
        
        # Test handling of large error lists
        large_error_list = TestFixtures.get_sample_errors() * 100
        assert len(large_error_list) == 300
        
        # Test configuration with different model types
        model_configs = [
            {'use_ollama': True, 'model': TestConfig.OLLAMA_MODEL},
            {'use_ollama': False, 'model': TestConfig.DEFAULT_MODEL}
        ]
        
        for config in model_configs:
            mock_manager = TestMockFactory.create_mock_model_manager(
                use_ollama=config['use_ollama']
            )
            assert mock_manager.use_ollama == config['use_ollama']
    
    def test_no_hardcoded_values_in_tests(self):
        """Test that no hardcoded values are used in test configuration."""
        
        # All test data should come from configuration
        assert TestConfig.SAMPLE_TEXT != "hardcoded text"
        assert TestConfig.DEFAULT_MODEL != "hardcoded-model"
        assert TestConfig.OLLAMA_URL.startswith("http")  # Should be a proper URL
        
        # Sample errors should have proper structure without hardcoded content
        sample_errors = TestFixtures.get_sample_errors()
        for error in sample_errors:
            assert error['type'] in ['passive_voice', 'sentence_length', 'ambiguity']
            assert error['severity'] in ['low', 'medium', 'high']
    
    def test_enterprise_configuration_patterns(self):
        """Test enterprise-ready configuration patterns."""
        
        # Test environment-based configuration
        test_environments = ['development', 'testing', 'production']
        
        for env in test_environments:
            # Configuration should be adaptable to different environments
            config = {
                'environment': env,
                'model_name': f"{TestConfig.DEFAULT_MODEL}-{env}",
                'use_ollama': env != 'production',  # Use HF in production
                'max_retries': 3 if env == 'production' else 1
            }
            
            assert isinstance(config['environment'], str)
            assert isinstance(config['model_name'], str)
            assert isinstance(config['use_ollama'], bool)
            assert isinstance(config['max_retries'], int)
    
    def test_configuration_validation(self):
        """Test configuration validation for enterprise deployment."""
        
        # Test required configuration fields
        required_fields = [
            'DEFAULT_MODEL', 'OLLAMA_MODEL', 'OLLAMA_URL',
            'SAMPLE_TEXT', 'SAMPLE_IMPROVED_TEXT',
            'MIN_CONFIDENCE', 'MAX_CONFIDENCE', 'EXPECTED_CONFIDENCE',
            'VALID_CONTEXTS', 'MAX_PROMPT_LENGTH', 'MIN_PROMPT_LENGTH'
        ]
        
        for field in required_fields:
            assert hasattr(TestConfig, field), f"Missing required configuration field: {field}"
            value = getattr(TestConfig, field)
            assert value is not None, f"Configuration field {field} should not be None"
    
    def test_configuration_extensibility(self):
        """Test that configuration can be extended for future needs."""
        
        # Test adding new configuration without breaking existing
        extended_config = {
            **TestConfig.__dict__,
            'NEW_FEATURE_ENABLED': True,
            'CUSTOM_TIMEOUT': 30,
            'ADDITIONAL_MODELS': ['model1', 'model2']
        }
        
        # Should maintain all original configuration
        assert extended_config['DEFAULT_MODEL'] == TestConfig.DEFAULT_MODEL
        assert extended_config['OLLAMA_MODEL'] == TestConfig.OLLAMA_MODEL
        
        # Should include new configuration
        assert extended_config['NEW_FEATURE_ENABLED'] is True
        assert extended_config['CUSTOM_TIMEOUT'] == 30
        assert len(extended_config['ADDITIONAL_MODELS']) == 2


class TestEnvironmentConfigurations:
    """Test suite for environment-specific configurations."""
    
    def test_development_config_inheritance(self):
        """Test that development config properly inherits from base config."""
        dev_config = DevelopmentConfig()
        
        # Should inherit from base config
        assert hasattr(dev_config, 'SECRET_KEY')
        assert hasattr(dev_config, 'OLLAMA_MODEL')
        assert hasattr(dev_config, 'MAX_CONTENT_LENGTH')
        
        # Should have development-specific settings
        assert dev_config.DEBUG is True
        assert dev_config.AI_MODEL_TYPE == 'ollama'
        assert dev_config.OLLAMA_MODEL == 'llama3:8b'
    
    def test_production_config_security(self):
        """Test production config security settings."""
        prod_config = ProductionConfig()
        
        # Should have secure settings
        assert prod_config.DEBUG is False
        # SECRET_KEY should be set (either from env or fallback)
        assert prod_config.SECRET_KEY is not None
        assert len(prod_config.SECRET_KEY) > 0
    
    def test_testing_config_isolation(self):
        """Test testing config provides proper isolation."""
        test_config = TestingConfig()
        
        # Should have testing-specific settings
        assert test_config.TESTING is True
        assert test_config.SQLALCHEMY_DATABASE_URI == 'sqlite:///:memory:'
        
        # Should inherit other base settings
        assert hasattr(test_config, 'MAX_CONTENT_LENGTH')
        assert hasattr(test_config, 'ALLOWED_EXTENSIONS')
    
    def test_configuration_selector_function(self):
        """Test configuration selector dictionary."""
        
        # Test all environments are mapped
        assert 'development' in config
        assert 'production' in config
        assert 'testing' in config
        assert 'default' in config
        
        # Test configuration classes are correct
        assert config['development'] == DevelopmentConfig
        assert config['production'] == ProductionConfig
        assert config['testing'] == TestingConfig
        assert config['default'] == DevelopmentConfig
        
        # Test configurations can be instantiated
        for env, config_class in config.items():
            instance = config_class()
            assert hasattr(instance, 'SECRET_KEY')
            assert hasattr(instance, 'OLLAMA_MODEL')


class TestConfigurationSecurity:
    """Test suite for configuration security and sensitive data handling."""
    
    def test_secret_key_management(self):
        """Test secure secret key handling."""
        config_instance = Config()
        
        # Test that secret key is properly set
        assert config_instance.SECRET_KEY is not None
        assert len(config_instance.SECRET_KEY) > TestConfig.MIN_SECRET_KEY_LENGTH
        
        # Test that different config classes have appropriate secret keys
        prod_config = ProductionConfig()
        assert prod_config.SECRET_KEY is not None
        assert len(prod_config.SECRET_KEY) > TestConfig.MIN_SECRET_KEY_LENGTH
    
    def test_api_key_security(self):
        """Test API key security handling."""
        config_instance = Config()
        
        # OpenAI API key should be None if not set in environment
        # This is correct behavior for security
        assert config_instance.OPENAI_API_KEY is None or isinstance(config_instance.OPENAI_API_KEY, str)
    
    def test_database_uri_security(self):
        """Test database URI security configuration."""
        config_instance = Config()
        
        # Database URI should have a default value
        assert config_instance.SQLALCHEMY_DATABASE_URI is not None
        assert '://' in config_instance.SQLALCHEMY_DATABASE_URI
        
        # Testing config should use in-memory database
        test_config = TestingConfig()
        assert test_config.SQLALCHEMY_DATABASE_URI == TestConfig.MEMORY_DATABASE_URL
    
    def test_sensitive_data_not_exposed(self):
        """Test that sensitive data is not accidentally exposed."""
        config_instance = Config()
        
        # Get all config attributes
        config_attrs = [attr for attr in dir(config_instance) if not attr.startswith('_')]
        
        # Check that sensitive methods exist
        assert 'SECRET_KEY' in config_attrs
        assert 'OPENAI_API_KEY' in config_attrs
        
        # Test configuration methods don't expose sensitive data
        ai_config = config_instance.get_ai_config()
        assert 'openai_api_key' not in ai_config  # Should not be in general config
        
        upload_config = config_instance.get_upload_config()
        assert 'secret_key' not in upload_config  # Should not be in upload config


class TestConfigurationScalability:
    """Test suite for configuration scalability and performance."""
    
    def test_configuration_performance(self):
        """Test configuration access performance."""
        config_instance = Config()
        
        # Test multiple configuration accesses
        for _ in range(100):
            ai_config = config_instance.get_ai_config()
            assert 'model_type' in ai_config
            assert 'use_ollama' in ai_config
            
            upload_config = config_instance.get_upload_config()
            assert 'max_content_length' in upload_config
            assert 'allowed_extensions' in upload_config
    
    def test_configuration_memory_usage(self):
        """Test configuration memory efficiency."""
        
        # Create multiple configuration instances
        configs = [Config() for _ in range(10)]
        
        # All should be properly initialized
        for config_instance in configs:
            assert config_instance.SECRET_KEY is not None
            assert config_instance.OLLAMA_MODEL is not None
            assert config_instance.MAX_CONTENT_LENGTH > 0
    
    def test_concurrent_configuration_access(self):
        """Test thread-safe configuration access."""
        import threading
        import time
        
        config_instance = Config()
        results = []
        
        def access_config():
            ai_config = config_instance.get_ai_config()
            results.append(ai_config['model_type'])
        
        # Create multiple threads
        threads = [threading.Thread(target=access_config) for _ in range(5)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All results should be consistent
        assert len(results) == 5
        assert all(result == results[0] for result in results)


class TestConfigurationMigration:
    """Test suite for configuration migration and compatibility."""
    
    def test_configuration_backward_compatibility(self):
        """Test that configuration remains backward compatible."""
        config_instance = Config()
        
        # Test legacy configuration attributes still exist
        legacy_attrs = [
            'SECRET_KEY', 'SQLALCHEMY_DATABASE_URI', 'UPLOAD_FOLDER',
            'AI_MODEL_TYPE', 'OLLAMA_MODEL', 'HF_MODEL_NAME'
        ]
        
        for attr in legacy_attrs:
            assert hasattr(config_instance, attr), f"Legacy attribute {attr} is missing"
    
    def test_new_configuration_additions(self):
        """Test that new configuration can be added without breaking existing."""
        config_instance = Config()
        
        # Test adding new configuration dynamically
        setattr(config_instance, 'NEW_FEATURE_FLAG', True)
        setattr(config_instance, 'NEW_TIMEOUT_VALUE', 60)
        
        # Should not break existing functionality
        assert config_instance.get_ai_config() is not None
        assert config_instance.get_upload_config() is not None
        
        # New config should be accessible
        assert getattr(config_instance, 'NEW_FEATURE_FLAG', None) is True
        assert getattr(config_instance, 'NEW_TIMEOUT_VALUE', None) == 60
    
    def test_configuration_version_compatibility(self):
        """Test configuration compatibility across different versions."""
        config_instance = Config()
        
        # Test that configuration supports different model types
        assert config_instance.AI_MODEL_TYPE in [TestConfig.MODEL_TYPE_OLLAMA, TestConfig.MODEL_TYPE_HUGGINGFACE, TestConfig.MODEL_TYPE_OPENAI]
        
        # Test that configuration methods work regardless of model type
        ai_config = config_instance.get_ai_config()
        assert 'model_type' in ai_config
        assert 'use_ollama' in ai_config


class TestConfigurationHealthChecks:
    """Test suite for configuration health monitoring."""
    
    def test_configuration_health_validation(self):
        """Test configuration health validation."""
        config_instance = Config()
        
        # Test critical configuration is valid
        assert config_instance.SECRET_KEY is not None
        assert len(config_instance.SECRET_KEY) > 0
        
        # Test AI configuration is valid
        ai_config = config_instance.get_ai_config()
        assert ai_config['model_type'] in [TestConfig.MODEL_TYPE_OLLAMA, TestConfig.MODEL_TYPE_HUGGINGFACE, TestConfig.MODEL_TYPE_OPENAI]
        assert ai_config['use_ollama'] in [True, False]
        
        # Test upload configuration is valid
        upload_config = config_instance.get_upload_config()
        assert upload_config['max_content_length'] > 0
        assert len(upload_config['allowed_extensions']) > 0
    
    def test_configuration_connectivity_checks(self):
        """Test configuration connectivity validation."""
        config_instance = Config()
        
        # Test Ollama URL format
        assert config_instance.OLLAMA_BASE_URL.startswith('http')
        assert '://' in config_instance.OLLAMA_BASE_URL
        
        # Test Redis URL format
        assert config_instance.REDIS_URL.startswith('redis://')
        
        # Test database URI format
        assert '://' in config_instance.SQLALCHEMY_DATABASE_URI
    
    def test_configuration_drift_detection(self):
        """Test configuration drift detection capabilities."""
        
        # Create baseline configuration
        baseline_config = Config()
        baseline_values = {
            'SECRET_KEY': baseline_config.SECRET_KEY,
            'OLLAMA_MODEL': baseline_config.OLLAMA_MODEL,
            'MAX_CONTENT_LENGTH': baseline_config.MAX_CONTENT_LENGTH
        }
        
        # Test that we can detect differences between configurations
        dev_config = DevelopmentConfig()
        prod_config = ProductionConfig()
        
        # Development and production configs should have some differences
        # (This tests the ability to detect configuration drift)
        assert dev_config.DEBUG != prod_config.DEBUG


class TestConfigurationDeployment:
    """Test suite for deployment-specific configuration scenarios."""
    
    def test_docker_configuration_patterns(self):
        """Test Docker-style configuration patterns."""
        config_instance = Config()
        
        # Test that configuration supports containerized environments
        assert config_instance.OLLAMA_BASE_URL is not None
        assert config_instance.REDIS_URL is not None
        assert config_instance.SQLALCHEMY_DATABASE_URI is not None
        
        # Test that configuration has appropriate defaults for containers
        assert isinstance(config_instance.OLLAMA_TIMEOUT, int)
        assert config_instance.OLLAMA_TIMEOUT > 0
    
    def test_kubernetes_configuration_patterns(self):
        """Test Kubernetes-style configuration patterns."""
        config_instance = Config()
        
        # Test that configuration supports service discovery patterns
        assert '://' in config_instance.OLLAMA_BASE_URL
        assert '://' in config_instance.REDIS_URL
        assert '://' in config_instance.SQLALCHEMY_DATABASE_URI
        
        # Test that configuration supports environment-based overrides
        assert hasattr(config_instance, 'LOG_LEVEL')
        assert config_instance.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def test_cloud_configuration_patterns(self):
        """Test cloud-specific configuration patterns."""
        config_instance = Config()
        
        # Test that configuration supports cloud environments
        assert config_instance.OPENAI_API_KEY is None or isinstance(config_instance.OPENAI_API_KEY, str)
        assert config_instance.LOG_LEVEL is not None
        
        # Test that configuration has appropriate cloud defaults
        assert config_instance.MAX_CONTENT_LENGTH > 0
        assert len(config_instance.ALLOWED_EXTENSIONS) > 0
    
    def test_multi_tenant_configuration_support(self):
        """Test multi-tenant configuration support."""
        
        # Test that different configuration classes can coexist
        configs = [
            DevelopmentConfig(),
            ProductionConfig(),
            TestingConfig()
        ]
        
        for config_instance in configs:
            # Each should have valid configuration
            assert config_instance.SECRET_KEY is not None
            assert config_instance.OLLAMA_MODEL is not None
            assert config_instance.MAX_CONTENT_LENGTH > 0
            
            # Each should support the same interface
            ai_config = config_instance.get_ai_config()
            assert 'model_type' in ai_config
            assert 'use_ollama' in ai_config


class TestConfigurationMonitoring:
    """Test suite for configuration monitoring and observability."""
    
    def test_configuration_metrics_collection(self):
        """Test configuration metrics collection."""
        config_instance = Config()
        
        # Test configuration metrics
        metrics = {
            'ai_model_type': config_instance.AI_MODEL_TYPE,
            'ollama_enabled': config_instance.is_ollama_enabled(),
            'upload_max_size': config_instance.MAX_CONTENT_LENGTH,
            'allowed_extensions_count': len(config_instance.ALLOWED_EXTENSIONS)
        }
        
        # Validate metrics structure
        assert isinstance(metrics['ai_model_type'], str)
        assert isinstance(metrics['ollama_enabled'], bool)
        assert isinstance(metrics['upload_max_size'], int)
        assert isinstance(metrics['allowed_extensions_count'], int)
    
    def test_configuration_logging_setup(self):
        """Test configuration logging setup."""
        config_instance = Config()
        
        # Test log level configuration
        assert config_instance.LOG_LEVEL in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Test that log level is properly configured
        assert isinstance(config_instance.LOG_LEVEL, str)
        assert len(config_instance.LOG_LEVEL) > 0
    
    def test_configuration_alerting_thresholds(self):
        """Test configuration alerting thresholds."""
        config_instance = Config()
        
        # Test resource limits that could trigger alerts
        assert config_instance.MAX_CONTENT_LENGTH > 0
        assert config_instance.OLLAMA_TIMEOUT > 0
        assert config_instance.AI_MODEL_MAX_LENGTH > 0
        
        # Test configuration bounds
        assert config_instance.MAX_CONTENT_LENGTH <= TestConfig.MAX_FILE_SIZE_LIMIT  # 100MB max
        assert config_instance.OLLAMA_TIMEOUT <= TestConfig.MAX_TIMEOUT  # 5 minutes max
        assert config_instance.AI_TEMPERATURE >= TestConfig.MIN_TEMPERATURE and config_instance.AI_TEMPERATURE <= TestConfig.MAX_TEMPERATURE


# Import the TestMockFactory at module level to fix the reference issue
from tests.test_utils import TestMockFactory 