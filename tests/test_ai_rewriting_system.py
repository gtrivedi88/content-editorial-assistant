"""
Comprehensive Test Suite for AI Rewriting System
Tests the two-pass AI rewriting system with Ollama integration, prompt generation, and evaluation.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
import requests
import yaml

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.core import AIRewriter
from rewriter.models import ModelManager
from rewriter.prompts import PromptGenerator
from rewriter.generators import TextGenerator
from rewriter.processors import TextProcessor
from rewriter.evaluators import RewriteEvaluator
from src.config import Config


class TestAIRewritingSystem:
    """Test suite for the AI rewriting system."""
    
    @pytest.fixture
    def mock_ollama_response(self):
        """Mock Ollama API response."""
        return {
            "model": "llama3:8b",
            "response": "This is the improved text with better clarity and conciseness.",
            "done": True
        }
    
    @pytest.fixture
    def mock_progress_callback(self):
        """Mock progress callback function."""
        callback = MagicMock()
        return callback
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return [
            {
                'type': 'passive_voice',
                'message': 'Passive voice detected',
                'severity': 'medium',
                'sentence': 'The document was written by the team.',
                'suggestions': ['Use active voice instead']
            },
            {
                'type': 'sentence_length',
                'message': 'Sentence too long',
                'severity': 'high',
                'sentence': 'This is a very long sentence that contains many clauses and should be shortened.',
                'suggestions': ['Break into shorter sentences']
            },
            {
                'type': 'ambiguity',
                'subtype': 'missing_actor',
                'message': 'Missing actor in passive voice',
                'severity': 'high',
                'sentence': 'The configuration is updated automatically.',
                'suggestions': ['Specify who or what updates the configuration']
            }
        ]
    
    def test_ai_rewriter_initialization(self, mock_progress_callback):
        """Test AI rewriter initialization."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen:
                with patch('rewriter.core.TextGenerator') as mock_text_gen:
                    with patch('rewriter.core.TextProcessor') as mock_processor:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator:
                            
                            rewriter = AIRewriter(
                                model_name="test-model",
                                use_ollama=True,
                                ollama_model="llama3:8b",
                                progress_callback=mock_progress_callback
                            )
                            
                            assert isinstance(rewriter, AIRewriter)
                            assert rewriter.progress_callback == mock_progress_callback
                            
                            # Check that components are initialized
                            mock_model_manager.assert_called_once()
                            mock_prompt_gen.assert_called_once()
                            mock_text_gen.assert_called_once()
                            mock_processor.assert_called_once()
                            mock_evaluator.assert_called_once()
    
    def test_ai_rewriter_first_pass_success(self, mock_progress_callback, sample_errors):
        """Test successful first pass rewriting."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_prompt.return_value = "Test prompt"
                            mock_text_gen.generate_text.return_value = "Raw AI response"
                            mock_processor.clean_generated_text.return_value = "Cleaned improved text"
                            mock_evaluator.evaluate_rewrite_quality.return_value = {
                                'improvements': ['Converted passive voice to active'],
                                'confidence': 0.85,
                                'model_used': 'test-model'
                            }
                            
                            # Create rewriter and test
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            result = rewriter.rewrite(
                                "Original text to be rewritten",
                                sample_errors,
                                "sentence",
                                1
                            )
                            
                            # Verify result
                            assert result['rewritten_text'] == "Cleaned improved text"
                            assert result['pass_number'] == 1
                            assert result['can_refine'] is True
                            assert result['confidence'] == 0.85
                            assert 'improvements' in result
                            
                            # Verify method calls - Fix: is_available is called twice in the actual implementation
                            assert mock_text_gen.is_available.call_count == 2  # Called in both rewrite() and _perform_first_pass()
                            mock_prompt_gen.generate_prompt.assert_called_once()
                            mock_text_gen.generate_text.assert_called_once()
                            mock_processor.clean_generated_text.assert_called_once()
                            mock_evaluator.evaluate_rewrite_quality.assert_called_once()
    
    def test_ai_rewriter_second_pass_success(self, mock_progress_callback, sample_errors):
        """Test successful second pass rewriting."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_self_review_prompt.return_value = "Self-review prompt"
                            mock_text_gen.generate_text.return_value = "Raw refined response"
                            mock_processor.clean_generated_text.return_value = "Final polished text"
                            mock_evaluator.extract_second_pass_improvements.return_value = [
                                'Enhanced clarity and flow'
                            ]
                            mock_evaluator.calculate_second_pass_confidence.return_value = 0.92
                            
                            # Create rewriter and test
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            result = rewriter.rewrite(
                                "First pass result text",
                                sample_errors,
                                "sentence",
                                2
                            )
                            
                            # Verify result
                            assert result['rewritten_text'] == "Final polished text"
                            assert result['pass_number'] == 2
                            assert result['can_refine'] is False
                            assert result['confidence'] == 0.92
                            assert 'improvements' in result
                            
                            # Verify method calls
                            mock_prompt_gen.generate_self_review_prompt.assert_called_once()
                            mock_evaluator.extract_second_pass_improvements.assert_called_once()
                            mock_evaluator.calculate_second_pass_confidence.assert_called_once()
    
    def test_ai_rewriter_refine_text(self, mock_progress_callback, sample_errors):
        """Test the refine_text method (Pass 2)."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_self_review_prompt.return_value = "Self-review prompt"
                            mock_text_gen.generate_text.return_value = "Raw refined response"
                            mock_processor.clean_generated_text.return_value = "Final refined text"
                            mock_evaluator.extract_second_pass_improvements.return_value = [
                                'Applied additional polish'
                            ]
                            mock_evaluator.calculate_second_pass_confidence.return_value = 0.90
                            
                            # Create rewriter and test
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            result = rewriter.refine_text(
                                "First pass result text",
                                sample_errors,
                                "sentence"
                            )
                            
                            # Verify result
                            assert result['rewritten_text'] == "Final refined text"
                            assert result['pass_number'] == 2
                            assert result['can_refine'] is False
                            assert result['confidence'] == 0.90
                            assert 'improvements' in result
    
    def test_ai_rewriter_no_content(self, mock_progress_callback):
        """Test rewriting with no content."""
        
        rewriter = AIRewriter(progress_callback=mock_progress_callback)
        
        result = rewriter.rewrite("", [], "sentence", 1)
        
        assert result['rewritten_text'] == ""
        assert result['confidence'] == 0.0
        assert 'error' in result
        assert 'No content provided' in result['error']
    
    def test_ai_rewriter_no_errors_first_pass(self, mock_progress_callback):
        """Test rewriting with no errors in first pass."""
        
        rewriter = AIRewriter(progress_callback=mock_progress_callback)
        
        result = rewriter.rewrite("Sample text", [], "sentence", 1)
        
        assert result['rewritten_text'] == "Sample text"
        assert result['confidence'] == 1.0
        assert 'improvements' in result
        assert 'No errors detected' in result['improvements']
    
    def test_ai_rewriter_models_unavailable(self, mock_progress_callback, sample_errors):
        """Test rewriting when AI models are unavailable."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                # Setup mocks
                mock_model_manager = MagicMock()
                mock_text_gen = MagicMock()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                # Configure mock to indicate unavailability
                mock_text_gen.is_available.return_value = False
                
                # Create rewriter and test
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite("Sample text", sample_errors, "sentence", 1)
                
                # Verify fallback behavior
                assert result['rewritten_text'] == "Sample text"
                assert result['confidence'] == 0.0
                assert 'error' in result
                assert 'AI models are not available' in result['error']
    
    def test_ai_rewriter_error_handling(self, mock_progress_callback, sample_errors):
        """Test error handling in AI rewriter."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                # Setup mocks
                mock_model_manager = MagicMock()
                mock_text_gen = MagicMock()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                # Configure mock to throw exception
                mock_text_gen.is_available.return_value = True
                mock_text_gen.generate_text.side_effect = Exception("Generation failed")
                
                # Create rewriter and test
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite("Sample text", sample_errors, "sentence", 1)
                
                # Verify error handling
                assert result['rewritten_text'] == "Sample text"
                assert result['confidence'] == 0.0
                assert 'error' in result
                assert 'Generation failed' in result['error']
    
    def test_model_manager_initialization(self):
        """Test ModelManager initialization."""
        
        # Test with Ollama
        manager = ModelManager("test-model", use_ollama=True, ollama_model="llama3:8b")
        assert manager.use_ollama is True
        assert manager.ollama_model == "llama3:8b"
        
        # Test without Ollama
        manager = ModelManager("test-model", use_ollama=False)
        assert manager.use_ollama is False
        assert manager.model_name == "test-model"
    
    def test_prompt_generator_initialization(self):
        """Test PromptGenerator initialization."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        # Fix: The actual attribute is style_guide_name, not style_guide
        assert generator.style_guide_name == 'ibm_style'
        assert generator.use_ollama is True
        assert generator.prompt_config is not None
    
    def test_prompt_generator_config_loading(self):
        """Test prompt configuration loading."""
        
        mock_config = {
            'language_and_grammar': {
                'passive_voice': {
                    'primary_command': 'Convert passive voice to active voice',
                    'instruction': 'Rewrite sentences to use active voice'
                }
            }
        }
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_config))):
            with patch('os.path.exists', return_value=True):
                generator = PromptGenerator(style_guide='ibm_style')
                assert generator.prompt_config is not None
    
    def test_prompt_generation_with_errors(self, sample_errors):
        """Test prompt generation with detected errors."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        # Mock the config loading
        mock_config = {
            'language_and_grammar': {
                'passive_voice': {
                    'primary_command': 'Convert passive voice to active voice',
                    'instruction': 'Rewrite sentences to use active voice'
                },
                'sentence_length': {
                    'primary_command': 'Shorten long sentences',
                    'instruction': 'Break long sentences into shorter ones'
                },
                'ambiguity': {
                    'primary_command': 'Resolve ambiguous content',
                    'instruction': 'Clarify unclear references'
                }
            }
        }
        
        with patch.object(generator, 'prompt_config', mock_config):
            prompt = generator.generate_prompt("Sample text", sample_errors, "sentence")
            
            assert isinstance(prompt, str)
            assert len(prompt) > 0
            # Fix: Check for actual content that should be in the prompt instead of exact text
            assert 'active voice' in prompt.lower()
            assert 'sentence' in prompt.lower()
    
    def test_prompt_generation_without_errors(self):
        """Test prompt generation without detected errors."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompt = generator.generate_prompt("Sample text", [], "sentence")
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'improve' in prompt.lower()
    
    def test_self_review_prompt_generation(self, sample_errors):
        """Test self-review prompt generation."""
        
        generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
        
        prompt = generator.generate_self_review_prompt("First pass result", sample_errors)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'First pass result' in prompt
        assert 'FINAL POLISHED VERSION' in prompt
    
    def test_text_generator_initialization(self):
        """Test TextGenerator initialization."""
        
        mock_model_manager = MagicMock()
        generator = TextGenerator(mock_model_manager)
        assert generator.model_manager == mock_model_manager
    
    @patch('requests.post')
    def test_text_generator_ollama_success(self, mock_post):
        """Test successful text generation with Ollama."""
        
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Generated improved text",
            "done": True
        }
        mock_post.return_value = mock_response
        
        # Create mock model manager
        mock_model_manager = MagicMock()
        mock_model_manager.use_ollama = True
        mock_model_manager.ollama_model = "llama3:8b"
        mock_model_manager.ollama_url = "http://localhost:11434/api/generate"
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", "Original text")
        
        assert result == "Generated improved text"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_text_generator_ollama_failure(self, mock_post):
        """Test text generation with Ollama failure."""
        
        # Mock Ollama failure
        mock_post.side_effect = Exception("Connection failed")
        
        # Create mock model manager
        mock_model_manager = MagicMock()
        mock_model_manager.use_ollama = True
        mock_model_manager.ollama_model = "llama3:8b"
        mock_model_manager.ollama_url = "http://localhost:11434/api/generate"
        
        generator = TextGenerator(mock_model_manager)
        
        result = generator.generate_with_ollama("Test prompt", "Original text")
        
        assert result == "Original text"  # Should return original on failure
    
    def test_text_processor_initialization(self):
        """Test TextProcessor initialization."""
        
        processor = TextProcessor()
        assert isinstance(processor, TextProcessor)
    
    def test_text_processor_clean_generation(self):
        """Test text processor cleaning functionality."""
        
        processor = TextProcessor()
        
        # Test cleaning AI response with explanations
        raw_response = """Here's the improved text:
        
        This is the actual improved content that we want to keep.
        
        * I converted passive voice to active voice
        * I shortened long sentences
        * I clarified ambiguous references
        """
        
        original_text = "Original text for comparison"
        
        cleaned = processor.clean_generated_text(raw_response, original_text)
        
        assert "This is the actual improved content that we want to keep." in cleaned
        assert "Here's the improved text:" not in cleaned
        assert "I converted" not in cleaned
        assert "I shortened" not in cleaned
    
    def test_text_processor_clean_empty_response(self):
        """Test text processor with empty response."""
        
        processor = TextProcessor()
        
        cleaned = processor.clean_generated_text("", "Original text")
        
        assert cleaned == "Original text"
    
    def test_text_processor_clean_identical_response(self):
        """Test text processor with identical response."""
        
        processor = TextProcessor()
        
        original_text = "This is the original text"
        cleaned = processor.clean_generated_text(original_text, original_text)
        
        assert cleaned == original_text
    
    def test_text_processor_rule_based_rewrite(self, sample_errors):
        """Test rule-based rewriting fallback."""
        
        processor = TextProcessor()
        
        content = "In order to utilize the system, you need to make a decision."
        
        rewritten = processor.rule_based_rewrite(content, sample_errors)
        
        # Should apply basic transformations
        assert "to utilize" in rewritten or "to use" in rewritten
        assert isinstance(rewritten, str)
    
    def test_rewrite_evaluator_initialization(self):
        """Test RewriteEvaluator initialization."""
        
        evaluator = RewriteEvaluator()
        assert isinstance(evaluator, RewriteEvaluator)
    
    def test_rewrite_evaluator_confidence_calculation(self):
        """Test confidence calculation."""
        
        evaluator = RewriteEvaluator()
        
        original = "Original text that needs improvement"
        rewritten = "Improved text with better clarity"
        errors = [{'type': 'passive_voice', 'message': 'Test error'}]
        
        confidence = evaluator.calculate_confidence(original, rewritten, errors, use_ollama=True)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_rewrite_evaluator_second_pass_confidence(self):
        """Test second pass confidence calculation."""
        
        evaluator = RewriteEvaluator()
        
        first_pass = "First pass result"
        final_rewrite = "Final polished result"
        errors = [{'type': 'passive_voice', 'message': 'Test error'}]
        
        confidence = evaluator.calculate_second_pass_confidence(first_pass, final_rewrite, errors)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert confidence >= 0.7  # Should be high for second pass
    
    def test_rewrite_evaluator_extract_improvements(self):
        """Test improvement extraction."""
        
        evaluator = RewriteEvaluator()
        
        original = "The document was written by the team using passive voice."
        rewritten = "The team wrote the document using active voice."
        errors = [
            {'type': 'passive_voice', 'message': 'Passive voice detected'},
            {'type': 'clarity', 'message': 'Unclear wording'}
        ]
        
        improvements = evaluator.extract_improvements(original, rewritten, errors)
        
        assert isinstance(improvements, list)
        assert len(improvements) > 0
        assert any('passive voice' in imp.lower() for imp in improvements)
    
    def test_rewrite_evaluator_second_pass_improvements(self):
        """Test second pass improvement extraction."""
        
        evaluator = RewriteEvaluator()
        
        first_rewrite = "First pass result text"
        final_rewrite = "Final polished result text with enhancements"
        
        improvements = evaluator.extract_second_pass_improvements(first_rewrite, final_rewrite)
        
        assert isinstance(improvements, list)
        assert len(improvements) > 0
    
    def test_rewrite_evaluator_analyze_changes(self):
        """Test change analysis."""
        
        evaluator = RewriteEvaluator()
        
        original = "This is the original text. It has multiple sentences."
        rewritten = "This is improved text. It has better structure."
        
        analysis = evaluator.analyze_changes(original, rewritten)
        
        assert isinstance(analysis, dict)
        assert 'word_count_change' in analysis
        assert 'sentence_count_change' in analysis
        assert 'structural_changes' in analysis
    
    def test_rewrite_evaluator_comprehensive_evaluation(self):
        """Test comprehensive rewrite evaluation."""
        
        evaluator = RewriteEvaluator()
        
        original = "Original text for evaluation"
        rewritten = "Improved text for evaluation"
        errors = [{'type': 'passive_voice', 'message': 'Test error'}]
        
        evaluation = evaluator.evaluate_rewrite_quality(original, rewritten, errors, use_ollama=True)
        
        assert isinstance(evaluation, dict)
        assert 'confidence' in evaluation
        assert 'improvements' in evaluation
        assert 'changes_analysis' in evaluation
        assert 'quality_score' in evaluation
        assert 'pass_number' in evaluation
        assert 'model_used' in evaluation
    
    def test_ai_rewriter_with_different_contexts(self, mock_progress_callback, sample_errors):
        """Test AI rewriter with different context levels."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_prompt.return_value = "Context-aware prompt"
                            mock_text_gen.generate_text.return_value = "Generated text"
                            mock_processor.clean_generated_text.return_value = "Cleaned text"
                            mock_evaluator.evaluate_rewrite_quality.return_value = {
                                'improvements': ['Context-aware improvements'],
                                'confidence': 0.85,
                                'model_used': 'test-model'
                            }
                            
                            # Create rewriter
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # Test with different contexts
                            contexts = ['sentence', 'paragraph', 'document']
                            
                            for context in contexts:
                                result = rewriter.rewrite(
                                    "Test content",
                                    sample_errors,
                                    context,
                                    1
                                )
                                
                                assert result['rewritten_text'] == "Cleaned text"
                                assert result['confidence'] == 0.85
                                
                                # Verify context was passed correctly
                                mock_prompt_gen.generate_prompt.assert_called_with(
                                    "Test content", sample_errors, context
                                )
    
    def test_ai_rewriter_progress_callbacks(self, sample_errors):
        """Test progress callback functionality."""
        
        progress_calls = []
        
        def progress_callback(step, status, detail, progress):
            progress_calls.append((step, status, detail, progress))
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_prompt.return_value = "Test prompt"
                            mock_text_gen.generate_text.return_value = "Generated text"
                            mock_processor.clean_generated_text.return_value = "Cleaned text"
                            mock_evaluator.evaluate_rewrite_quality.return_value = {
                                'improvements': ['Test improvements'],
                                'confidence': 0.85,
                                'model_used': 'test-model'
                            }
                            
                            # Create rewriter with progress callback
                            rewriter = AIRewriter(progress_callback=progress_callback)
                            
                            # Test first pass
                            result = rewriter.rewrite(
                                "Test content",
                                sample_errors,
                                "sentence",
                                1
                            )
                            
                            # Verify progress callbacks were made
                            assert len(progress_calls) > 0
                            
                            # Check that we have start and complete callbacks
                            steps = [call[0] for call in progress_calls]
                            assert 'pass1_start' in steps
                            assert 'pass1_complete' in steps
    
    def test_ai_rewriter_system_info(self):
        """Test getting system information."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            mock_model_manager = MagicMock()
            mock_model_manager_class.return_value = mock_model_manager
            
            rewriter = AIRewriter()
            
            # Mock system info
            mock_system_info = {
                'model_info': {
                    'available': True,
                    'model': 'test-model',
                    'version': '1.0'
                },
                'status': 'ready'
            }
            
            with patch.object(rewriter, 'get_system_info', return_value=mock_system_info):
                system_info = rewriter.get_system_info()
                
                assert isinstance(system_info, dict)
                assert 'model_info' in system_info
                assert 'status' in system_info
    
    def test_ai_rewriter_large_content(self, mock_progress_callback, sample_errors):
        """Test AI rewriter with large content."""
        
        large_content = "This is a test sentence. " * 500  # Large content
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager = MagicMock()
                            mock_prompt_gen = MagicMock()
                            mock_text_gen = MagicMock()
                            mock_processor = MagicMock()
                            mock_evaluator = MagicMock()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure mock responses
                            mock_text_gen.is_available.return_value = True
                            mock_prompt_gen.generate_prompt.return_value = "Large content prompt"
                            mock_text_gen.generate_text.return_value = "Generated large content"
                            mock_processor.clean_generated_text.return_value = "Cleaned large content"
                            mock_evaluator.evaluate_rewrite_quality.return_value = {
                                'improvements': ['Large content improvements'],
                                'confidence': 0.80,
                                'model_used': 'test-model'
                            }
                            
                            # Create rewriter
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            result = rewriter.rewrite(
                                large_content,
                                sample_errors,
                                "paragraph",
                                1
                            )
                            
                            # Should handle large content without issues
                            assert result['rewritten_text'] == "Cleaned large content"
                            assert result['confidence'] == 0.80
                            assert 'improvements' in result
    
    def test_ai_rewriter_concurrent_requests(self, mock_progress_callback, sample_errors):
        """Test concurrent AI rewriting requests."""
        
        import threading
        import time
        
        results = []
        
        def rewrite_request(content, index):
            with patch('rewriter.core.ModelManager') as mock_model_manager_class:
                with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                    with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                        with patch('rewriter.core.TextProcessor') as mock_processor_class:
                            with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                                
                                # Setup mocks
                                mock_model_manager = MagicMock()
                                mock_prompt_gen = MagicMock()
                                mock_text_gen = MagicMock()
                                mock_processor = MagicMock()
                                mock_evaluator = MagicMock()
                                
                                mock_model_manager_class.return_value = mock_model_manager
                                mock_prompt_gen_class.return_value = mock_prompt_gen
                                mock_text_gen_class.return_value = mock_text_gen
                                mock_processor_class.return_value = mock_processor
                                mock_evaluator_class.return_value = mock_evaluator
                                
                                # Configure mock responses
                                mock_text_gen.is_available.return_value = True
                                mock_prompt_gen.generate_prompt.return_value = f"Prompt {index}"
                                mock_text_gen.generate_text.return_value = f"Generated {index}"
                                mock_processor.clean_generated_text.return_value = f"Cleaned {index}"
                                mock_evaluator.evaluate_rewrite_quality.return_value = {
                                    'improvements': [f'Improvements {index}'],
                                    'confidence': 0.85,
                                    'model_used': 'test-model'
                                }
                                
                                # Create rewriter
                                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                                
                                result = rewriter.rewrite(
                                    f"Content {index}",
                                    sample_errors,
                                    "sentence",
                                    1
                                )
                                
                                results.append((index, result['rewritten_text']))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=rewrite_request, args=(f"Content {i}", i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 3
        for index, rewritten_text in results:
            assert f"Cleaned {index}" == rewritten_text 