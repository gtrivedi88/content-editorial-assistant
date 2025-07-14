"""
Integration Tests
End-to-end integration tests for the AI rewriting system.
"""

import pytest
import os
import sys
import threading
import time
from unittest.mock import patch, MagicMock

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.core import AIRewriter
from tests.test_utils import TestConfig, TestFixtures, TestValidators, TestMockFactory


class TestIntegration:
    """Integration test suite for the AI rewriting system."""
    
    @pytest.fixture
    def mock_progress_callback(self):
        """Mock progress callback function."""
        return TestFixtures.get_mock_progress_callback()
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return TestFixtures.get_sample_errors()
    
    def test_end_to_end_rewriting_workflow(self, mock_progress_callback, sample_errors):
        """Test complete end-to-end rewriting workflow."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup full system mocks
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
                            
                            # Initialize system
                            rewriter = AIRewriter(
                                model_name=TestConfig.DEFAULT_MODEL,
                                use_ollama=True,
                                ollama_model=TestConfig.OLLAMA_MODEL,
                                progress_callback=mock_progress_callback
                            )
                            
                            # Execute first pass
                            first_result = rewriter.rewrite(
                                TestConfig.SAMPLE_TEXT,
                                sample_errors,
                                "sentence",
                                1
                            )
                            
                            # Validate first pass
                            TestValidators.validate_rewrite_result(first_result)
                            assert first_result['pass_number'] == 1
                            assert first_result['can_refine'] is True
                            
                            # Execute second pass
                            second_result = rewriter.refine_text(
                                first_result['rewritten_text'],
                                sample_errors,
                                "sentence"
                            )
                            
                            # Validate second pass
                            TestValidators.validate_rewrite_result(second_result)
                            assert second_result['pass_number'] == 2
                            assert second_result['can_refine'] is False
    
    def test_ai_rewriter_progress_callbacks(self, sample_errors):
        """Test progress callback functionality throughout workflow."""
        
        progress_calls = []
        
        def progress_callback(step, status, detail, progress):
            progress_calls.append((step, status, detail, progress))
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
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
                            
                            # Create rewriter with progress callback
                            rewriter = AIRewriter(progress_callback=progress_callback)
                            
                            # Test first pass
                            result = rewriter.rewrite(
                                TestConfig.SAMPLE_TEXT,
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
    
    def test_ai_rewriter_large_content(self, mock_progress_callback, sample_errors):
        """Test AI rewriter with large content."""
        
        large_content = "This is a test sentence. " * 500  # Large content
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
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
                            
                            # Configure for large content
                            mock_processor.clean_generated_text.return_value = "Cleaned large content"
                            mock_evaluator.evaluate_rewrite_quality.return_value = {
                                'improvements': ['Large content improvements'],
                                'confidence': 0.80,
                                'model_used': TestConfig.DEFAULT_MODEL
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
                            TestValidators.validate_rewrite_result(result)
                            assert result['confidence'] == 0.80
    
    def test_ai_rewriter_concurrent_requests(self, mock_progress_callback, sample_errors):
        """Test concurrent AI rewriting requests."""
        
        results = []
        
        def rewrite_request(content, index):
            with patch('rewriter.core.ModelManager') as mock_model_manager_class:
                with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                    with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                        with patch('rewriter.core.TextProcessor') as mock_processor_class:
                            with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                                
                                # Setup unique mocks for each thread
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
                                
                                # Configure unique responses
                                mock_processor.clean_generated_text.return_value = f"Cleaned {index}"
                                mock_evaluator.evaluate_rewrite_quality.return_value = {
                                    'improvements': [f'Improvements {index}'],
                                    'confidence': 0.85,
                                    'model_used': TestConfig.DEFAULT_MODEL
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
    
    def test_ai_rewriter_system_info_integration(self, mock_progress_callback):
        """Test system information integration."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                mock_model_manager = TestMockFactory.create_mock_model_manager()
                mock_text_gen = TestMockFactory.create_mock_text_generator()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                system_info = rewriter.get_system_info()
                
                TestValidators.validate_system_info(system_info)
    
    def test_configuration_driven_workflow(self, mock_progress_callback, sample_errors):
        """Test configuration-driven workflow without hardcoding."""
        
        configurations = [
            {
                'model_name': TestConfig.DEFAULT_MODEL,
                'use_ollama': True,
                'ollama_model': TestConfig.OLLAMA_MODEL
            },
            {
                'model_name': 'custom-hf-model',
                'use_ollama': False,
                'ollama_model': None
            }
        ]
        
        for config in configurations:
            with patch('rewriter.core.ModelManager') as mock_model_manager_class:
                with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                    with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                        with patch('rewriter.core.TextProcessor') as mock_processor_class:
                            with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                                
                                # Setup mocks based on configuration
                                mock_model_manager = TestMockFactory.create_mock_model_manager(
                                    use_ollama=config['use_ollama']
                                )
                                mock_prompt_gen = TestMockFactory.create_mock_prompt_generator()
                                mock_text_gen = TestMockFactory.create_mock_text_generator()
                                mock_processor = TestMockFactory.create_mock_text_processor()
                                mock_evaluator = TestMockFactory.create_mock_evaluator()
                                
                                mock_model_manager_class.return_value = mock_model_manager
                                mock_prompt_gen_class.return_value = mock_prompt_gen
                                mock_text_gen_class.return_value = mock_text_gen
                                mock_processor_class.return_value = mock_processor
                                mock_evaluator_class.return_value = mock_evaluator
                                
                                # Create rewriter with configuration
                                rewriter = AIRewriter(
                                    progress_callback=mock_progress_callback,
                                    **config
                                )
                                
                                result = rewriter.rewrite(
                                    TestConfig.SAMPLE_TEXT,
                                    sample_errors,
                                    "sentence",
                                    1
                                )
                                
                                TestValidators.validate_rewrite_result(result)
    
    def test_error_recovery_workflow(self, mock_progress_callback, sample_errors):
        """Test error recovery across the entire workflow."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                
                mock_model_manager = TestMockFactory.create_mock_model_manager()
                mock_text_gen = TestMockFactory.create_mock_text_generator()
                
                mock_model_manager_class.return_value = mock_model_manager
                mock_text_gen_class.return_value = mock_text_gen
                
                # Simulate various failure scenarios
                failure_scenarios = [
                    {'is_available': False, 'expected_error': 'AI models are not available'},
                    {'generate_exception': Exception("Generation failed"), 'expected_error': 'Generation failed'}
                ]
                
                for scenario in failure_scenarios:
                    if 'is_available' in scenario:
                        mock_text_gen.is_available.return_value = scenario['is_available']
                    else:
                        mock_text_gen.is_available.return_value = True
                    
                    if 'generate_exception' in scenario:
                        mock_text_gen.generate_text.side_effect = scenario['generate_exception']
                    else:
                        mock_text_gen.generate_text.side_effect = None
                        mock_text_gen.generate_text.return_value = TestConfig.SAMPLE_RAW_RESPONSE
                    
                    rewriter = AIRewriter(progress_callback=mock_progress_callback)
                    
                    result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, sample_errors, "sentence", 1)
                    
                    # Should handle failures gracefully
                    assert 'error' in result
                    assert scenario['expected_error'] in result['error']
                    assert result['rewritten_text'] == TestConfig.SAMPLE_TEXT  # Fallback to original
    
    def test_scalable_batch_processing(self, mock_progress_callback, sample_errors):
        """Test scalable batch processing capabilities."""
        
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
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
                            
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # Test batch processing with different sizes
                            batch_sizes = [1, 5, 10]
                            
                            for batch_size in batch_sizes:
                                content_list = [f"{TestConfig.SAMPLE_TEXT} {i}" for i in range(batch_size)]
                                errors_list = [sample_errors] * batch_size
                                
                                results = rewriter.batch_rewrite(content_list, errors_list)
                                
                                assert len(results) == batch_size
                                for result in results:
                                    TestValidators.validate_rewrite_result(result) 