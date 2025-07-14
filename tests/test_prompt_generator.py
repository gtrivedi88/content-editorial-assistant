"""
Prompt Generator Tests
Tests for the PromptGenerator class that handles prompt creation and configuration.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import yaml

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.prompts import PromptGenerator
from tests.test_utils import TestConfig, TestFixtures, TestValidators


class TestPromptGenerator:
    """Test suite for the PromptGenerator class."""
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return TestFixtures.get_sample_errors()
    
    def test_prompt_generator_initialization(self):
        """Test PromptGenerator initialization."""
        
        with patch('os.path.isdir', return_value=True):
            with patch('os.listdir', return_value=['language_and_grammar.yaml']):
                with patch('builtins.open', mock_open(read_data=yaml.dump({'rules': {}}))):
                    
                    generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
                    
                    assert generator.style_guide_name == 'ibm_style'
                    assert generator.use_ollama is True
                    assert generator.prompt_config is not None
    
    def test_prompt_generator_config_loading(self):
        """Test prompt configuration loading."""
        
        mock_config = {
            'rules': {
                'language_and_grammar': {
                    'passive_voice': {
                        'primary_command': 'Convert passive voice to active voice',
                        'instruction': 'Rewrite sentences to use active voice'
                    }
                }
            }
        }
        
        with patch('os.path.isdir', return_value=True):
            with patch('os.listdir', return_value=['language_and_grammar.yaml']):
                with patch('builtins.open', mock_open(read_data=yaml.dump(mock_config))):
                    
                    generator = PromptGenerator(style_guide='ibm_style')
                    
                    assert generator.prompt_config is not None
                    assert 'language_and_grammar' in generator.prompt_config
    
    def test_prompt_generator_missing_directory(self):
        """Test behavior when configuration directory is missing."""
        
        with patch('os.path.isdir', return_value=False):
            generator = PromptGenerator(style_guide='nonexistent_style')
            
            assert generator.style_guide_name == 'nonexistent_style'
            assert generator.prompt_config == {}
    
    def test_prompt_generation_with_errors(self, sample_errors):
        """Test prompt generation with detected errors."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Mock the config loading
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
            
            # Validate using utility
            TestValidators.validate_prompt_content(
                prompt, 
                should_contain=['active voice', 'sentence']
            )
    
    def test_prompt_generation_without_errors(self):
        """Test prompt generation without detected errors."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, [], "sentence")
        
        TestValidators.validate_prompt_content(
            prompt,
            should_contain=['improve']
        )
    
    def test_self_review_prompt_generation(self, sample_errors):
        """Test self-review prompt generation."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompt = generator.generate_self_review_prompt("First pass result", sample_errors)
        
        TestValidators.validate_prompt_content(
            prompt,
            should_contain=['First pass result', 'FINAL POLISHED VERSION']
        )
    
    def test_ollama_prompt_building(self, sample_errors):
        """Test Ollama-specific prompt building."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Mock the config
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
            
            # Ollama prompts should have specific structure
            TestValidators.validate_prompt_content(
                prompt,
                should_contain=['PRIMARY GOAL', 'ADDITIONAL INSTRUCTIONS', 'Original text', 'Improved text']
            )
    
    def test_huggingface_prompt_building(self, sample_errors):
        """Test Hugging Face-specific prompt building."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=False)
        
        # Mock the config
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
            
            # HF prompts should have different structure
            TestValidators.validate_prompt_content(
                prompt,
                should_contain=['Task:', 'PRIMARY GOAL', 'ADDITIONAL INSTRUCTIONS']
            )
    
    def test_prompt_length_management(self, sample_errors):
        """Test that prompts stay within length limits."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Create many errors to test length management
        many_errors = sample_errors * 10
        
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, many_errors, "sentence")
            
            # Should stay within reasonable length limits
            assert len(prompt) <= TestConfig.MAX_PROMPT_LENGTH * 2  # Allow some flexibility
    
    def test_error_prioritization(self, sample_errors):
        """Test that errors are prioritized correctly."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Mock config
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
            
            # High severity errors should be addressed
            TestValidators.validate_prompt_content(prompt)
    
    def test_context_awareness(self, sample_errors):
        """Test that prompts are context-aware."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            for context in TestConfig.VALID_CONTEXTS:
                prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, sample_errors, context)
                
                # Should contain context information
                TestValidators.validate_prompt_content(prompt)
    
    def test_multi_pass_prompts(self, sample_errors):
        """Test multi-pass prompt generation."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompts = generator.generate_multi_pass_prompts(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
        
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        
        for prompt_info in prompts:
            assert 'prompt' in prompt_info
            assert 'pass_number' in prompt_info
            assert 'error_count' in prompt_info
            assert 'focus' in prompt_info
            
            TestValidators.validate_prompt_content(prompt_info['prompt'])
    
    def test_optimal_strategy_selection(self, sample_errors):
        """Test optimal processing strategy selection."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Test with few errors
        strategy = generator.get_optimal_processing_strategy(TestConfig.SAMPLE_TEXT, sample_errors[:1], "sentence")
        assert strategy['strategy'] in ['single_pass', 'single_pass_smart']
        
        # Test with many errors
        many_errors = sample_errors * 10
        strategy = generator.get_optimal_processing_strategy(TestConfig.SAMPLE_TEXT, many_errors, "sentence")
        assert strategy['strategy'] in ['multi_pass', 'single_pass_smart']
    
    def test_optimal_prompts_generation(self, sample_errors):
        """Test optimal prompt generation."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompts = generator.generate_optimal_prompts(TestConfig.SAMPLE_TEXT, sample_errors, "sentence")
        
        assert isinstance(prompts, list)
        assert len(prompts) > 0
        
        for prompt_info in prompts:
            assert 'prompt' in prompt_info
            assert 'strategy' in prompt_info
            TestValidators.validate_prompt_content(prompt_info['prompt'])
    
    def test_severity_to_priority_mapping(self):
        """Test severity to priority mapping."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Test mapping
        assert generator._map_severity_to_priority('high') == 'urgent'
        assert generator._map_severity_to_priority('medium') == 'high'
        assert generator._map_severity_to_priority('low') == 'medium'
        assert generator._map_severity_to_priority('unknown') == 'medium'
    
    def test_configuration_file_loading_error(self):
        """Test handling of configuration file loading errors."""
        
        with patch('os.path.isdir', return_value=True):
            with patch('os.listdir', return_value=['invalid.yaml']):
                with patch('builtins.open', mock_open(read_data='invalid: yaml: content: [')):
                    
                    generator = PromptGenerator(style_guide='ibm_style')
                    
                    # Should handle invalid YAML gracefully
                    assert generator.prompt_config == {}
    
    def test_ambiguity_error_handling(self):
        """Test handling of ambiguity errors specifically."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        ambiguity_errors = [
            {
                'type': 'ambiguity',
                'subtype': 'missing_actor',
                'message': 'Missing actor in passive voice',
                'severity': 'high',
                'sentence': 'The configuration is updated automatically.',
                'suggestions': ['Specify who or what updates the configuration']
            }
        ]
        
        mock_config = TestFixtures.get_mock_prompt_config()
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt(TestConfig.SAMPLE_TEXT, ambiguity_errors, "sentence")
            
            # Should handle ambiguity errors using their subtype
            TestValidators.validate_prompt_content(prompt)
    
    def test_empty_content_handling(self):
        """Test handling of empty content."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompt = generator.generate_prompt("", [], "sentence")
        
        # Should return a generic improvement prompt
        TestValidators.validate_prompt_content(
            prompt,
            should_contain=['improve', 'clear', 'concise']
        ) 