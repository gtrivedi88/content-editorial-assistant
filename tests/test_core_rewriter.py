"""
Core AIRewriter Tests
Tests for the main AIRewriter orchestration class and its core functionality.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.core import AIRewriter
from tests.test_utils import TestConfig, TestFixtures, TestValidators, TestMockFactory


class TestCoreAIRewriter:
    """Test suite for the core AIRewriter class."""
    
    @pytest.fixture
    def mock_progress_callback(self):
        """Mock progress callback function."""
        return TestFixtures.get_mock_progress_callback()
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return TestFixtures.get_sample_errors()
    
    def test_ai_rewriter_initialization(self, mock_progress_callback):
        """Test AI rewriter initialization."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks using factory
                            mock_model_manager_class.return_value = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen_class.return_value = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen_class.return_value = TestMockFactory.create_mock_text_generator()
                            mock_processor_class.return_value = TestMockFactory.create_mock_text_processor()
                            mock_evaluator_class.return_value = TestMockFactory.create_mock_evaluator()
                            
                            rewriter = AIRewriter(
                                model_name=TestConfig.DEFAULT_MODEL,
                                use_ollama=True,
                                ollama_model=TestConfig.OLLAMA_MODEL,
                                progress_callback=mock_progress_callback
                            )
                            
                            assert isinstance(rewriter, AIRewriter)
                            assert rewriter.progress_callback == mock_progress_callback
                            
                            # Check that components are initialized
                            mock_model_manager_class.assert_called_once()
                            mock_prompt_gen_class.assert_called_once()
                            mock_text_gen_class.assert_called_once()
                            mock_processor_class.assert_called_once()
                            mock_evaluator_class.assert_called_once()
    
    def test_ai_rewriter_first_pass_success(self, mock_progress_callback, sample_errors):
        """Test successful first pass rewriting."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks using factory
                            mock_model_manager = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen = TestMockFactory.create_mock_text_generator()
                            mock_processor = TestMockFactory.create_mock_text_processor()
                            mock_evaluator = TestMockFactory.create_mock_evaluator()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Create rewriter and test
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            result = rewriter.rewrite(
                                TestConfig.SAMPLE_TEXT,
                                sample_errors,
                                "sentence",
                                1
                            )
                            
                            # Validate result using utility
                            TestValidators.validate_rewrite_result(
                                result, 
                                expected_text=TestConfig.SAMPLE_IMPROVED_TEXT,
                                expected_confidence=TestConfig.EXPECTED_CONFIDENCE
                            )
                            
                            assert result['pass_number'] == 1
                            assert result['can_refine'] is True
                            
                            # Verify method calls
                            assert mock_text_gen.is_available.call_count == 2
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
                            
                            # Setup mocks using factory
                            mock_model_manager = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen = TestMockFactory.create_mock_text_generator()
                            mock_processor = TestMockFactory.create_mock_text_processor()
                            mock_evaluator = TestMockFactory.create_mock_evaluator()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure second pass specific behavior
                            mock_prompt_gen.generate_self_review_prompt.return_value = "Self-review prompt"
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
                            
                            # Validate result
                            TestValidators.validate_rewrite_result(result)
                            assert result['rewritten_text'] == "Final polished text"
                            assert result['pass_number'] == 2
                            assert result['can_refine'] is False
                            assert result['confidence'] == 0.92
                            
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
                            
                            # Setup mocks using factory
                            mock_model_manager = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen = TestMockFactory.create_mock_text_generator()
                            mock_processor = TestMockFactory.create_mock_text_processor()
                            mock_evaluator = TestMockFactory.create_mock_evaluator()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Configure refinement specific behavior
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
                            
                            # Validate result
                            TestValidators.validate_rewrite_result(result)
                            assert result['rewritten_text'] == "Final refined text"
                            assert result['pass_number'] == 2
                            assert result['can_refine'] is False
                            assert result['confidence'] == 0.90
    
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
        
        result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, [], "sentence", 1)
        
        assert result['rewritten_text'] == TestConfig.SAMPLE_TEXT
        assert result['confidence'] == 1.0
        assert 'improvements' in result
        assert 'No errors detected' in result['improvements']
    
    def test_ai_rewriter_models_unavailable(self, mock_progress_callback, sample_errors):
        """Test rewriting when AI models are unavailable."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                # Setup mocks
                mock_model_manager = TestMockFactory.create_mock_model_manager()
                mock_text_gen = TestMockFactory.create_mock_text_generator()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                # Configure mock to indicate unavailability
                mock_text_gen.is_available.return_value = False
                
                # Create rewriter and test
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, sample_errors, "sentence", 1)
                
                # Verify fallback behavior
                assert result['rewritten_text'] == TestConfig.SAMPLE_TEXT
                assert result['confidence'] == 0.0
                assert 'error' in result
                assert 'AI models are not available' in result['error']
    
    def test_ai_rewriter_error_handling(self, mock_progress_callback, sample_errors):
        """Test error handling in AI rewriter."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                # Setup mocks
                mock_model_manager = TestMockFactory.create_mock_model_manager()
                mock_text_gen = TestMockFactory.create_mock_text_generator()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                # Configure mock to throw exception
                mock_text_gen.is_available.return_value = True
                mock_text_gen.generate_text.side_effect = Exception("Generation failed")
                
                # Create rewriter and test
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, sample_errors, "sentence", 1)
                
                # Verify error handling
                assert result['rewritten_text'] == TestConfig.SAMPLE_TEXT
                assert result['confidence'] == 0.0
                assert 'error' in result
                assert 'Generation failed' in result['error']
    
    def test_ai_rewriter_with_different_contexts(self, mock_progress_callback, sample_errors):
        """Test AI rewriter with different context levels."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks using factory
                            mock_model_manager = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen = TestMockFactory.create_mock_text_generator()
                            mock_processor = TestMockFactory.create_mock_text_processor()
                            mock_evaluator = TestMockFactory.create_mock_evaluator()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Create rewriter
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # Test with different contexts
                            for context in TestConfig.VALID_CONTEXTS:
                                result = rewriter.rewrite(
                                    TestConfig.SAMPLE_TEXT,
                                    sample_errors,
                                    context,
                                    1
                                )
                                
                                TestValidators.validate_rewrite_result(result)
                                
                                # Verify context was passed correctly
                                mock_prompt_gen.generate_prompt.assert_called_with(
                                    TestConfig.SAMPLE_TEXT, sample_errors, context
                                )
    
    def test_ai_rewriter_batch_processing(self, mock_progress_callback, sample_errors):
        """Test batch rewriting functionality."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks using factory
                            mock_model_manager = TestMockFactory.create_mock_model_manager()
                            mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                            mock_text_gen = TestMockFactory.create_mock_text_generator()
                            mock_processor = TestMockFactory.create_mock_text_processor()
                            mock_evaluator = TestMockFactory.create_mock_evaluator()
                            
                            mock_model_manager_class.return_value = mock_model_manager
                            mock_prompt_gen_class.return_value = mock_prompt_gen
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            # Create rewriter
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # Test batch processing
                            content_list = [TestConfig.SAMPLE_TEXT] * 3
                            errors_list = [sample_errors] * 3
                            
                            results = rewriter.batch_rewrite(content_list, errors_list)
                            
                            assert len(results) == 3
                            for result in results:
                                TestValidators.validate_rewrite_result(result)
    
    def test_ai_rewriter_system_info(self, mock_progress_callback):
        """Test getting system information."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            mock_model_manager = TestMockFactory.create_mock_model_manager()
            mock_model_manager_class.return_value = mock_model_manager
            
            rewriter = AIRewriter(progress_callback=mock_progress_callback)
            
            system_info = rewriter.get_system_info()
            
            TestValidators.validate_system_info(system_info)
    
    def test_ai_rewriter_is_ready(self, mock_progress_callback):
        """Test system readiness check."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                mock_model_manager = TestMockFactory.create_mock_model_manager()
                mock_text_gen = TestMockFactory.create_mock_text_generator()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                # Test ready state
                assert rewriter.is_ready() is True
                
                # Test not ready state
                mock_text_gen.is_available.return_value = False
                assert rewriter.is_ready() is False 