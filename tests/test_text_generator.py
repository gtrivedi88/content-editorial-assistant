"""
Text Generator Tests
Tests for the TextGenerator class that handles AI text generation.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
import requests

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.generators import TextGenerator
from tests.test_utils import TestConfig, TestFixtures, TestValidators, TestMockFactory


class TestTextGenerator:
    """Test suite for the TextGenerator class."""
    
    def test_text_generator_initialization(self):
        """Test TextGenerator initialization."""
        
        mock_model_manager = TestMockFactory.create_mock_model_manager()
        generator = TextGenerator(mock_model_manager)
        
        assert generator.model_manager == mock_model_manager
    
    @patch('requests.post')
    def test_text_generator_ollama_success(self, mock_post):
        """Test successful text generation with Ollama."""
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": TestConfig.SAMPLE_IMPROVED_TEXT,
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Create mock model manager
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_IMPROVED_TEXT
        mock_post.assert_called_once()
        
        # Verify request parameters
        call_args = mock_post.call_args
        assert call_args[0][0] == TestConfig.OLLAMA_URL
        assert 'json' in call_args[1]
        assert call_args[1]['json']['model'] == TestConfig.OLLAMA_MODEL
        assert call_args[1]['json']['prompt'] == "Test prompt"
    
    @patch('requests.post')
    def test_text_generator_ollama_failure(self, mock_post):
        """Test text generation with Ollama failure."""
        
        # Mock Ollama failure
        mock_post.side_effect = Exception("Connection failed")
        
        # Create mock model manager
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original on failure
    
    @patch('requests.post')
    def test_text_generator_ollama_http_error(self, mock_post):
        """Test text generation with Ollama HTTP error."""
        
        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
        mock_post.return_value = mock_response
        
        # Create mock model manager
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original on error
    
    @patch('requests.post')
    def test_text_generator_ollama_timeout(self, mock_post):
        """Test text generation with Ollama timeout."""
        
        # Mock timeout
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Create mock model manager
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original on timeout
    
    def test_text_generator_huggingface_success(self):
        """Test successful text generation with Hugging Face."""
        
        # Create mock model manager with HF generator
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        mock_model_manager.generator = MagicMock()
        mock_model_manager.generator.return_value = [{
            'generated_text': f"Test prompt {TestConfig.SAMPLE_IMPROVED_TEXT}"
        }]
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_hf_model("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_IMPROVED_TEXT
        mock_model_manager.generator.assert_called_once()
    
    def test_text_generator_huggingface_failure(self):
        """Test text generation with Hugging Face failure."""
        
        # Create mock model manager with failing HF generator
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        mock_model_manager.generator = MagicMock()
        mock_model_manager.generator.side_effect = Exception("Generation failed")
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_hf_model("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original on failure
    
    def test_text_generator_huggingface_no_generator(self):
        """Test text generation when HF generator is not available."""
        
        # Create mock model manager without generator
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        mock_model_manager.generator = None
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_hf_model("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original when no generator
    
    def test_text_generator_generate_text_ollama(self):
        """Test the main generate_text method with Ollama."""
        
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        
        generator = TextGenerator(mock_model_manager)
        
        with patch.object(generator, 'generate_with_ollama') as mock_ollama:
            mock_ollama.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
            
            result = generator.generate_text("Test prompt", TestConfig.SAMPLE_TEXT)
            
            assert result == TestConfig.SAMPLE_IMPROVED_TEXT
            mock_ollama.assert_called_once_with("Test prompt", TestConfig.SAMPLE_TEXT)
    
    def test_text_generator_generate_text_huggingface(self):
        """Test the main generate_text method with Hugging Face."""
        
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        
        generator = TextGenerator(mock_model_manager)
        
        with patch.object(generator, 'generate_with_hf_model') as mock_hf:
            mock_hf.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
            
            result = generator.generate_text("Test prompt", TestConfig.SAMPLE_TEXT)
            
            assert result == TestConfig.SAMPLE_IMPROVED_TEXT
            mock_hf.assert_called_once_with("Test prompt", TestConfig.SAMPLE_TEXT)
    
    def test_text_generator_is_available(self):
        """Test availability check."""
        
        # Test with available model
        mock_model_manager = TestMockFactory.create_mock_model_manager()
        mock_model_manager.is_available.return_value = True
        
        generator = TextGenerator(mock_model_manager)
        assert generator.is_available() is True
        
        # Test with unavailable model
        mock_model_manager.is_available.return_value = False
        assert generator.is_available() is False
    
    def test_text_generator_get_model_info(self):
        """Test getting model information."""
        
        mock_model_manager = TestMockFactory.create_mock_model_manager()
        mock_model_info = {
            'use_ollama': True,
            'model': TestConfig.OLLAMA_MODEL,
            'is_available': True
        }
        mock_model_manager.get_model_info.return_value = mock_model_info
        
        generator = TextGenerator(mock_model_manager)
        
        info = generator.get_model_info()
        
        assert isinstance(info, dict)
        assert 'generation_available' in info
        assert info['generation_available'] is True
        
        # Should include model manager info
        for key, value in mock_model_info.items():
            assert info[key] == value
    
    @patch('requests.post')
    def test_text_generator_ollama_empty_response(self, mock_post):
        """Test handling of empty Ollama response."""
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "",
            "done": True
        }
        mock_post.return_value = mock_response
        
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original for empty response
    
    @patch('requests.post')
    def test_text_generator_ollama_malformed_response(self, mock_post):
        """Test handling of malformed Ollama response."""
        
        # Mock malformed response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "invalid": "response"
        }
        mock_post.return_value = mock_response
        
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original for malformed response
    
    def test_text_generator_huggingface_empty_generated_text(self):
        """Test handling of empty Hugging Face generated text."""
        
        mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=False)
        mock_model_manager.generator = MagicMock()
        mock_model_manager.generator.return_value = [{
            'generated_text': "Test prompt"  # Only the original prompt
        }]
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_hf_model("Test prompt", TestConfig.SAMPLE_TEXT)
        
        assert result == TestConfig.SAMPLE_TEXT  # Should return original when no new text generated
    
    def test_text_generator_model_configuration_flexibility(self):
        """Test that TextGenerator works with different model configurations."""
        
        configurations = [
            {'use_ollama': True, 'ollama_model': 'custom-model'},
            {'use_ollama': False, 'hf_model': 'custom-hf-model'},
        ]
        
        for config in configurations:
            mock_model_manager = TestMockFactory.create_mock_model_manager(use_ollama=config['use_ollama'])
            generator = TextGenerator(mock_model_manager)
            
            # Should initialize without errors
            assert generator.model_manager == mock_model_manager
            assert generator.is_available() is True 