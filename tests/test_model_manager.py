"""
Model Manager Tests
Tests for the ModelManager class that handles AI model initialization and connectivity.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ModelManager
from tests.test_utils import TestConfig, TestFixtures, TestValidators


class TestModelManager:
    """Test suite for the ModelManager class."""
    
    def test_model_manager_initialization_ollama(self):
        """Test ModelManager initialization with Ollama."""
        
        with patch('rewriter.models.requests.post') as mock_post:
            # Mock successful Ollama connection
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            manager = ModelManager(
                TestConfig.DEFAULT_MODEL, 
                use_ollama=True, 
                ollama_model=TestConfig.OLLAMA_MODEL
            )
            
            assert manager.use_ollama is True
            assert manager.ollama_model == TestConfig.OLLAMA_MODEL
            assert manager.model_name == TestConfig.DEFAULT_MODEL
            assert manager.ollama_url == TestConfig.OLLAMA_URL
    
    def test_model_manager_initialization_huggingface(self):
        """Test ModelManager initialization with Hugging Face."""
        
        with patch('rewriter.models.HF_AVAILABLE', True):
            with patch('rewriter.models.AutoTokenizer') as mock_tokenizer_class:
                with patch('rewriter.models.pipeline') as mock_pipeline:
                    
                    # Mock tokenizer
                    mock_tokenizer = MagicMock()
                    mock_tokenizer.pad_token = None
                    mock_tokenizer.eos_token = '[EOS]'
                    mock_tokenizer.eos_token_id = 1
                    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                    
                    # Mock pipeline
                    mock_generator = MagicMock()
                    mock_pipeline.return_value = mock_generator
                    
                    manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
                    
                    assert manager.use_ollama is False
                    assert manager.model_name == TestConfig.DEFAULT_MODEL
                    assert manager.generator == mock_generator
                    assert manager.tokenizer == mock_tokenizer
                    
                    # Verify tokenizer setup
                    mock_tokenizer_class.from_pretrained.assert_called_once_with(TestConfig.DEFAULT_MODEL)
                    mock_pipeline.assert_called_once()
    
    def test_model_manager_ollama_connection_test(self):
        """Test Ollama connection testing."""
        
        with patch('rewriter.models.requests.get') as mock_get:
            # Test successful connection
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'models': [{'name': TestConfig.OLLAMA_MODEL}]
            }
            mock_get.return_value = mock_response
            
            manager = ModelManager(
                TestConfig.DEFAULT_MODEL, 
                use_ollama=True, 
                ollama_model=TestConfig.OLLAMA_MODEL
            )
            
            # Connection test should have been called during initialization
            mock_get.assert_called_once()
            
            # Verify request parameters
            call_args = mock_get.call_args
            assert call_args[0][0] == "http://localhost:11434/api/tags"
            # Check that timeout was set
            assert 'timeout' in call_args[1]
            assert call_args[1]['timeout'] == 5
    
    def test_model_manager_ollama_connection_failure(self):
        """Test Ollama connection failure handling."""
        
        with patch('rewriter.models.requests.post') as mock_post:
            # Mock connection failure
            mock_post.side_effect = Exception("Connection failed")
            
            manager = ModelManager(
                TestConfig.DEFAULT_MODEL, 
                use_ollama=True, 
                ollama_model=TestConfig.OLLAMA_MODEL
            )
            
            # Should handle connection failure gracefully
            assert manager.use_ollama is True
            assert manager.ollama_model == TestConfig.OLLAMA_MODEL
    
    def test_model_manager_huggingface_initialization_failure(self):
        """Test Hugging Face model initialization failure."""
        
        with patch('rewriter.models.HF_AVAILABLE', True):
            with patch('rewriter.models.AutoTokenizer') as mock_tokenizer_class:
                # Mock tokenizer failure
                mock_tokenizer_class.from_pretrained.side_effect = Exception("Model not found")
                
                manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
                
                # Should handle failure gracefully
                assert manager.use_ollama is False
                assert manager.model_name == TestConfig.DEFAULT_MODEL
                assert manager.generator is None
    
    def test_model_manager_huggingface_unavailable(self):
        """Test behavior when Hugging Face transformers is not available."""
        
        with patch('rewriter.models.HF_AVAILABLE', False):
            manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
            
            assert manager.use_ollama is False
            assert manager.model_name == TestConfig.DEFAULT_MODEL
            assert manager.generator is None
    
    def test_model_manager_is_available_ollama(self):
        """Test availability check for Ollama."""
        
        with patch('rewriter.models.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            manager = ModelManager(
                TestConfig.DEFAULT_MODEL, 
                use_ollama=True, 
                ollama_model=TestConfig.OLLAMA_MODEL
            )
            
            # Ollama should be available if connection test passed
            assert manager.is_available() is True
    
    def test_model_manager_is_available_huggingface(self):
        """Test availability check for Hugging Face."""
        
        with patch('rewriter.models.HF_AVAILABLE', True):
            with patch('rewriter.models.AutoTokenizer') as mock_tokenizer_class:
                with patch('rewriter.models.pipeline') as mock_pipeline:
                    
                    # Mock successful initialization
                    mock_tokenizer = MagicMock()
                    mock_tokenizer.pad_token = None
                    mock_tokenizer.eos_token = '[EOS]'
                    mock_tokenizer.eos_token_id = 1
                    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                    
                    mock_generator = MagicMock()
                    mock_pipeline.return_value = mock_generator
                    
                    manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
                    
                    # Should be available if generator is initialized
                    assert manager.is_available() is True
    
    def test_model_manager_is_available_huggingface_failed(self):
        """Test availability check for failed Hugging Face initialization."""
        
        with patch('rewriter.models.HF_AVAILABLE', True):
            with patch('rewriter.models.AutoTokenizer') as mock_tokenizer_class:
                # Mock initialization failure
                mock_tokenizer_class.from_pretrained.side_effect = Exception("Model not found")
                
                manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
                
                # Should not be available if generator failed to initialize
                assert manager.is_available() is False
    
    def test_model_manager_get_model_info_ollama(self):
        """Test getting model information for Ollama."""
        
        with patch('rewriter.models.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            manager = ModelManager(
                TestConfig.DEFAULT_MODEL, 
                use_ollama=True, 
                ollama_model=TestConfig.OLLAMA_MODEL
            )
            
            info = manager.get_model_info()
            
            # Verify model information structure
            assert isinstance(info, dict)
            assert info['use_ollama'] is True
            assert info['ollama_model'] == TestConfig.OLLAMA_MODEL
            assert info['hf_model'] is None
            assert info['hf_available'] is not None
            assert info['is_available'] is True
    
    def test_model_manager_get_model_info_huggingface(self):
        """Test getting model information for Hugging Face."""
        
        with patch('rewriter.models.HF_AVAILABLE', True):
            with patch('rewriter.models.AutoTokenizer') as mock_tokenizer_class:
                with patch('rewriter.models.pipeline') as mock_pipeline:
                    
                    # Mock successful initialization
                    mock_tokenizer = MagicMock()
                    mock_tokenizer.pad_token = None
                    mock_tokenizer.eos_token = '[EOS]'
                    mock_tokenizer.eos_token_id = 1
                    mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
                    
                    mock_generator = MagicMock()
                    mock_pipeline.return_value = mock_generator
                    
                    manager = ModelManager(TestConfig.DEFAULT_MODEL, use_ollama=False)
                    
                    info = manager.get_model_info()
                    
                    # Verify model information structure
                    assert isinstance(info, dict)
                    assert info['use_ollama'] is False
                    assert info['ollama_model'] is None
                    assert info['hf_model'] == TestConfig.DEFAULT_MODEL
                    assert info['hf_available'] is True
                    assert info['is_available'] is True
    
    def test_model_manager_configuration_flexibility(self):
        """Test that ModelManager accepts different configuration options."""
        
        test_cases = [
            {
                'model_name': 'custom-model',
                'use_ollama': True,
                'ollama_model': 'custom-ollama-model'
            },
            {
                'model_name': 'another-model',
                'use_ollama': False,
                'ollama_model': 'not-used'
            }
        ]
        
        for config in test_cases:
            if config['use_ollama']:
                with patch('rewriter.models.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        'models': [{'name': config['ollama_model']}]
                    }
                    mock_get.return_value = mock_response

                    manager = ModelManager(**config)

                    assert manager.model_name == config['model_name']
                    assert manager.use_ollama == config['use_ollama']
                    assert manager.ollama_model == config['ollama_model']
            else:
                with patch('rewriter.models.HF_AVAILABLE', False):
                    manager = ModelManager(**config)
                    
                    assert manager.model_name == config['model_name']
                    assert manager.use_ollama == config['use_ollama']
    
    def test_model_manager_default_parameters(self):
        """Test ModelManager with default parameters."""
        
        with patch('rewriter.models.HF_AVAILABLE', False):
            manager = ModelManager()
            
            # Should use default values from configuration
            assert manager.model_name == "microsoft/DialoGPT-medium"
            assert manager.use_ollama is False
            assert manager.ollama_model == "llama3:8b"
            assert manager.ollama_url == TestConfig.OLLAMA_URL 