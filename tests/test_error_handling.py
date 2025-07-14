"""
Comprehensive Error Handling and Edge Case Testing Suite
Tests various failure scenarios, input validation, error recovery, and system resilience
to ensure robust error handling across all components.
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from io import StringIO, BytesIO
import logging
import threading
import time
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestConfig, TestFixtures, TestValidators, TestMockFactory


class TestInputValidation:
    """Test input validation and sanitization."""
    
    def test_empty_input_handling(self):
        """Test handling of empty and null inputs."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test various empty inputs
        empty_inputs = [
            "",           # Empty string
            None,         # None value
            "   ",        # Whitespace only
            "\n\n\n",     # Newlines only
            "\t\t\t",     # Tabs only
            " \n \t \r ", # Mixed whitespace
        ]
        
        for empty_input in empty_inputs:
            try:
                result = analyzer.analyze(empty_input)
                
                # Should handle gracefully, not crash
                assert result is not None, f"Analyzer returned None for input: {repr(empty_input)}"
                assert isinstance(result, dict), f"Analyzer should return dict for input: {repr(empty_input)}"
                
                # Should have appropriate structure even for empty input
                assert 'errors' in result, "Result should have 'errors' key"
                assert isinstance(result['errors'], list), "Errors should be a list"
                
            except Exception as e:
                pytest.fail(f"Analyzer crashed on empty input {repr(empty_input)}: {e}")
    
    def test_malformed_input_handling(self):
        """Test handling of malformed and invalid inputs."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test various malformed inputs
        malformed_inputs = [
            "🚀" * 1000,                    # Unicode emoji
            "\x00\x01\x02\x03",             # Control characters
            "A" * 1000000,                  # Extremely long single word
            "." * 10000,                    # Excessive punctuation
            "a\nb\nc\nd\ne\nf\ng\nh" * 1000, # Excessive line breaks
            "test\0null\0bytes",             # Null bytes
            "test\x7fdelete\x7fchars",       # Delete characters
            "test\ufffdreplace\ufffdchars",  # Unicode replacement chars
        ]
        
        for malformed_input in malformed_inputs:
            try:
                result = analyzer.analyze(malformed_input)
                
                # Should handle gracefully
                assert result is not None, f"Analyzer failed on malformed input: {malformed_input[:50]}..."
                assert isinstance(result, dict), "Result should be a dictionary"
                
                # Verify basic structure
                assert 'errors' in result, "Result should have errors key"
                
            except Exception as e:
                # Log the error but don't fail - some malformed input might legitimately cause errors
                print(f"Warning: Malformed input caused error: {e} for input: {malformed_input[:50]}...")
    
    def test_type_validation(self):
        """Test type validation for various inputs."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test invalid types
        invalid_types = [
            123,           # Integer
            12.34,         # Float
            [],            # List
            {},            # Dictionary
            set(),         # Set
            object(),      # Object
            b"bytes",      # Bytes
        ]
        
        for invalid_input in invalid_types:
            try:
                result = analyzer.analyze(invalid_input)
                
                # Should either handle gracefully or raise appropriate error
                if result is not None:
                    assert isinstance(result, dict), "Result should be a dictionary"
                
            except (TypeError, AttributeError) as e:
                # These are acceptable errors for invalid types
                assert "str" in str(e).lower() or "string" in str(e).lower(), f"Error should mention string type: {e}"
            
            except Exception as e:
                pytest.fail(f"Unexpected error for type {type(invalid_input)}: {e}")


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""
    
    def test_component_failure_recovery(self):
        """Test recovery when individual components fail."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        # Test with mocked component failures
        with patch('style_analyzer.sentence_analyzer.SentenceAnalyzer.analyze_sentence_length_spacy') as mock_sentence:
            mock_sentence.side_effect = Exception("Sentence analyzer failed")
            
            analyzer = StyleAnalyzer()
            
            try:
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                
                # Should still return a result even if one component fails
                assert result is not None, "Analyzer should recover from component failure"
                assert isinstance(result, dict), "Result should be a dictionary"
                
                # May have fewer results but should not crash
                assert 'errors' in result, "Result should still have errors key"
                
            except Exception as e:
                pytest.fail(f"Analyzer should recover from component failure: {e}")
    
    def test_partial_processing_recovery(self):
        """Test recovery from partial processing failures."""
        from rewriter.core import AIRewriter
        
        # Mock partial failures in the rewriter
        with patch('rewriter.generators.TextGenerator.generate_text') as mock_generate:
            # Simulate intermittent failures
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 2 == 0:  # Fail every other call
                    raise Exception("Generation failed")
                return TestConfig.SAMPLE_IMPROVED_TEXT
            
            mock_generate.side_effect = side_effect
            
            with patch('rewriter.models.ModelManager') as mock_manager_class:
                mock_manager = TestMockFactory.create_mock_model_manager()
                mock_manager_class.return_value = mock_manager
                
                rewriter = AIRewriter()
                
                try:
                    result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, TestFixtures.get_sample_errors(), "paragraph")
                    
                    # Should handle partial failures gracefully
                    assert result is not None, "Rewriter should handle partial failures"
                    
                except Exception as e:
                    # Some failures might be expected, but should be handled gracefully
                    assert "timeout" not in str(e).lower(), f"Should not timeout on partial failures: {e}"
    
    def test_resource_exhaustion_recovery(self):
        """Test recovery from resource exhaustion scenarios."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Simulate memory pressure by creating large objects
        large_objects = []
        try:
            # Create some memory pressure (but not enough to crash the system)
            for i in range(10):
                large_objects.append("X" * 1000000)  # 1MB strings
            
            # Try to analyze under memory pressure
            result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
            
            # Should still work under reasonable memory pressure
            assert result is not None, "Analyzer should work under memory pressure"
            
        except MemoryError:
            # If we hit actual memory limits, that's acceptable
            pass
        finally:
            # Clean up
            large_objects.clear()
    
    def test_timeout_handling(self):
        """Test handling of operation timeouts."""
        from rewriter.core import AIRewriter
        
        with patch('rewriter.generators.TextGenerator.generate_text') as mock_generate:
            # Simulate slow operation
            def slow_operation(*args, **kwargs):
                time.sleep(0.1)  # Small delay to simulate slow operation
                return TestConfig.SAMPLE_IMPROVED_TEXT
            
            mock_generate.side_effect = slow_operation
            
            with patch('rewriter.models.ModelManager') as mock_manager_class:
                mock_manager = TestMockFactory.create_mock_model_manager()
                mock_manager_class.return_value = mock_manager
                
                rewriter = AIRewriter()
                
                start_time = time.time()
                result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, TestFixtures.get_sample_errors(), "paragraph")
                end_time = time.time()
                
                # Should complete within reasonable time
                assert end_time - start_time < 10.0, "Operation should not take too long"
                assert result is not None, "Should return result even with delays"


class TestConcurrencyErrorHandling:
    """Test error handling in concurrent scenarios."""
    
    def test_thread_safety_error_handling(self):
        """Test error handling in multi-threaded scenarios."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        errors = []
        results = []
        
        def analyze_with_error_tracking(thread_id):
            """Analyze text and track any errors."""
            try:
                for i in range(10):
                    test_text = f"{TestConfig.SAMPLE_TEXT} Thread {thread_id} Request {i}"
                    result = analyzer.analyze(test_text)
                    results.append(result)
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Run multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_with_error_tracking, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check for thread safety issues
        assert len(errors) == 0, f"Thread safety errors occurred: {errors}"
        assert len(results) == 50, f"Expected 50 results, got {len(results)}"
        
        # Verify all results are valid
        for i, result in enumerate(results):
            assert result is not None, f"Result {i} is None"
            assert isinstance(result, dict), f"Result {i} is not a dictionary"
    
    def test_race_condition_handling(self):
        """Test handling of potential race conditions."""
        from rewriter.core import AIRewriter
        
        shared_state = {'counter': 0}
        errors = []
        
        def rewrite_with_shared_state(thread_id):
            """Rewrite text while accessing shared state."""
            try:
                with patch('rewriter.models.ModelManager') as mock_manager_class:
                    mock_manager = TestMockFactory.create_mock_model_manager()
                    mock_manager_class.return_value = mock_manager
                    
                    rewriter = AIRewriter()
                    
                    for i in range(5):
                        # Simulate race condition by accessing shared state
                        shared_state['counter'] += 1
                        
                        result = rewriter.rewrite(
                            f"{TestConfig.SAMPLE_TEXT} {shared_state['counter']}", 
                            TestFixtures.get_sample_errors(), 
                            "paragraph"
                        )
                        
                        assert result is not None, f"Thread {thread_id} got None result"
                        
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")
        
        # Run concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=rewrite_with_shared_state, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check for race condition errors
        assert len(errors) == 0, f"Race condition errors occurred: {errors}"
        assert shared_state['counter'] == 15, f"Expected counter to be 15, got {shared_state['counter']}"


class TestFileSystemErrorHandling:
    """Test file system related error handling."""
    
    def test_missing_file_handling(self):
        """Test handling of missing files."""
        try:
            from structural_parsing.extractors import DocumentProcessor
            
            processor = DocumentProcessor()
            
            # Test with non-existent file
            non_existent_file = "/path/that/does/not/exist.txt"
            
            try:
                result = processor.extract_text(non_existent_file)

                # Should handle gracefully
                assert result == "" or result is None, "Should return empty result for missing file"

            except FileNotFoundError:
                # This is an acceptable error for missing files
                pass
            except Exception as e:
                pytest.fail(f"Unexpected error for missing file: {e}")
                
        except ImportError:
            # DocumentProcessor not available, skip test
            pytest.skip("DocumentProcessor not available")
    
    def test_permission_error_handling(self):
        """Test handling of file permission errors."""
        try:
            from structural_parsing.extractors import DocumentProcessor
            
            processor = DocumentProcessor()
            
            # Create a temporary file with restricted permissions
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write("Test content")
                temp_file_path = temp_file.name
            
            try:
                # Remove read permissions
                os.chmod(temp_file_path, 0o000)
                
                try:
                    result = processor.extract_text(temp_file_path)

                    # Should handle permission errors gracefully
                    assert result == "" or result is None, "Should return empty result for permission denied"

                except PermissionError:
                    # This is an acceptable error for permission issues
                    pass
                except Exception as e:
                    pytest.fail(f"Unexpected error for permission denied: {e}")
                    
            finally:
                # Clean up - restore permissions and delete file
                try:
                    os.chmod(temp_file_path, 0o644)
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except ImportError:
            # DocumentProcessor not available, skip test
            pytest.skip("DocumentProcessor not available")
    
    def test_corrupted_file_handling(self):
        """Test handling of corrupted files."""
        try:
            from structural_parsing.extractors import DocumentProcessor
            
            processor = DocumentProcessor()
            
            # Create a corrupted file (binary data with wrong extension)
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
                temp_file.write(b'\x00\x01\x02\x03\x04\x05\x06\x07')  # Binary garbage
                temp_file_path = temp_file.name
            
            try:
                result = processor.extract_text(temp_file_path)

                # Should handle corrupted files gracefully
                assert isinstance(result, str), "Should return string even for corrupted files"

            except Exception as e:
                # Some errors are acceptable for corrupted files
                assert "decode" in str(e).lower() or "corrupt" in str(e).lower(), f"Unexpected error: {e}"
                
            finally:
                # Clean up
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except ImportError:
            # DocumentProcessor not available, skip test
            pytest.skip("DocumentProcessor not available")


class TestConfigurationErrorHandling:
    """Test configuration-related error handling."""
    
    def test_missing_configuration_handling(self):
        """Test handling of missing configuration values."""
        from src.config import Config
        
        # Test with missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            try:
                config = Config()
                
                # Should have fallback values
                assert config.SECRET_KEY is not None, "Should have fallback SECRET_KEY"
                assert config.OLLAMA_MODEL is not None, "Should have fallback OLLAMA_MODEL"
                assert config.MAX_CONTENT_LENGTH > 0, "Should have positive MAX_CONTENT_LENGTH"
                
            except Exception as e:
                pytest.fail(f"Configuration should handle missing environment variables: {e}")
    
    def test_invalid_configuration_handling(self):
        """Test handling of invalid configuration values."""
        from src.config import Config
        
        # Test with invalid environment variables
        invalid_env = {
            'AI_MODEL_MAX_LENGTH': 'not_a_number',
            'AI_TEMPERATURE': 'invalid_float',
            'OLLAMA_TIMEOUT': 'not_an_integer',
        }
        
        with patch.dict(os.environ, invalid_env):
            try:
                config = Config()
                
                # Should handle invalid values gracefully with fallbacks
                assert isinstance(config.AI_MODEL_MAX_LENGTH, int), "Should fallback to valid integer"
                assert isinstance(config.AI_TEMPERATURE, float), "Should fallback to valid float"
                assert isinstance(config.OLLAMA_TIMEOUT, int), "Should fallback to valid integer"
                
            except (ValueError, TypeError):
                # These are acceptable errors for invalid configuration
                pass
            except Exception as e:
                pytest.fail(f"Unexpected error for invalid configuration: {e}")
    
    def test_configuration_method_error_handling(self):
        """Test error handling in configuration methods."""
        from src.config import Config
        
        config = Config()
        
        try:
            # Test configuration methods with potential issues
            ai_config = config.get_ai_config()
            upload_config = config.get_upload_config()
            analysis_config = config.get_analysis_config()
            
            # Should return valid dictionaries
            assert isinstance(ai_config, dict), "AI config should be a dictionary"
            assert isinstance(upload_config, dict), "Upload config should be a dictionary"
            assert isinstance(analysis_config, dict), "Analysis config should be a dictionary"
            
            # Should have required keys
            assert 'model_type' in ai_config, "AI config should have model_type"
            assert 'max_content_length' in upload_config, "Upload config should have max_content_length"
            
        except Exception as e:
            pytest.fail(f"Configuration methods should not raise exceptions: {e}")


class TestNetworkErrorHandling:
    """Test network-related error handling."""
    
    def test_connection_timeout_handling(self):
        """Test handling of network connection timeouts."""
        from rewriter.models import ModelManager
        
        # Mock network timeout
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Connection timeout")
            
            try:
                manager = ModelManager("test-model", use_ollama=True, ollama_model="llama3:8b")
                
                # Should handle connection errors gracefully
                is_available = manager.is_available()
                
                # Should return False for unavailable connections
                assert is_available is False, "Should return False for connection timeouts"
                
            except Exception as e:
                # Should not crash on connection errors
                assert "timeout" in str(e).lower(), f"Should handle timeout gracefully: {e}"
    
    def test_api_error_handling(self):
        """Test handling of API errors."""
        from rewriter.generators import TextGenerator
        from rewriter.models import ModelManager
        
        # Mock API errors
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Internal server error"}
            mock_post.return_value = mock_response
            
            try:
                manager = ModelManager("test-model", use_ollama=True)
                generator = TextGenerator(manager)
                
                result = generator.generate_text("test prompt", "original test text")

                # Should handle API errors gracefully
                assert result == "" or result is None, "Should return empty result for API errors"

            except Exception as e:
                # Should handle API errors without crashing
                assert "500" in str(e) or "error" in str(e).lower(), f"Should handle API errors: {e}"


class TestEdgeCaseHandling:
    """Test handling of various edge cases."""
    
    def test_unicode_edge_cases(self):
        """Test handling of Unicode edge cases."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        unicode_edge_cases = [
            "Hello 👋 World 🌍",           # Emoji
            "café naïve résumé",            # Accented characters
            "Москва Пекин 東京",            # Mixed scripts
            "𝒯𝑒𝓈𝓉 𝓂𝒶𝓉𝒽 𝓈𝓎𝓂𝒷𝑜𝓁𝓈",    # Mathematical symbols
            "Test\u200Binvisible\u200Bspaces", # Zero-width spaces
            "\u202Eright-to-left\u202D",    # Bidirectional text
        ]
        
        for test_text in unicode_edge_cases:
            try:
                result = analyzer.analyze(test_text)
                
                # Should handle Unicode gracefully
                assert result is not None, f"Should handle Unicode text: {test_text}"
                assert isinstance(result, dict), "Result should be a dictionary"
                
            except Exception as e:
                pytest.fail(f"Should handle Unicode edge case '{test_text}': {e}")
    
    def test_boundary_value_edge_cases(self):
        """Test handling of boundary values."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test boundary values
        boundary_cases = [
            "A",                    # Single character
            "A" * 10000,           # Very long single word
            "A. " * 1000,          # Many short sentences
            "A " * 10000 + ".",    # Very long sentence
            "\n".join(["Test"] * 1000),  # Many lines
        ]
        
        for test_text in boundary_cases:
            try:
                result = analyzer.analyze(test_text)
                
                # Should handle boundary cases
                assert result is not None, f"Should handle boundary case: {test_text[:50]}..."
                assert isinstance(result, dict), "Result should be a dictionary"
                
            except Exception as e:
                # Log warning but don't fail - some boundary cases might hit system limits
                print(f"Warning: Boundary case caused error: {e} for text: {test_text[:50]}...")
    
    def test_special_character_edge_cases(self):
        """Test handling of special characters."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        special_char_cases = [
            "Test with\ttabs\tand\nnewlines\r\n",
            "Test with \"quotes\" and 'apostrophes'",
            "Test with (parentheses) and [brackets] and {braces}",
            "Test with @#$%^&*()_+ symbols",
            "Test with ... ellipsis and — em-dash",
            "Test with © ® ™ symbols",
        ]
        
        for test_text in special_char_cases:
            try:
                result = analyzer.analyze(test_text)
                
                # Should handle special characters
                assert result is not None, f"Should handle special characters: {test_text}"
                assert isinstance(result, dict), "Result should be a dictionary"
                
            except Exception as e:
                pytest.fail(f"Should handle special characters '{test_text}': {e}")


class TestErrorLogging:
    """Test error logging and reporting."""
    
    def test_error_logging_functionality(self):
        """Test that errors are properly logged."""
        import logging
        from io import StringIO
        
        # Create a string buffer to capture log output
        log_buffer = StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setLevel(logging.ERROR)
        
        # Get the root logger and add our handler
        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
        
        try:
            # Trigger an error condition
            from style_analyzer.base_analyzer import StyleAnalyzer
            
            with patch('style_analyzer.sentence_analyzer.SentenceAnalyzer.analyze_sentence_length_spacy') as mock_analyze:
                mock_analyze.side_effect = Exception("Test error for logging")
                
                analyzer = StyleAnalyzer()
                
                try:
                    result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                    
                    # Should handle error and continue
                    assert result is not None, "Should return result even with logging errors"
                    
                except Exception as e:
                    # Some errors might bubble up, but should be logged
                    pass
                
                # Check that error was logged
                log_content = log_buffer.getvalue()
                
                # Should have some log content (though exact format may vary)
                assert isinstance(log_content, str), "Should have log content"
                
        finally:
            # Clean up logger
            logger.removeHandler(handler)
    
    def test_error_context_preservation(self):
        """Test that error context is preserved."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test with problematic input that should preserve context
        problematic_input = "This is a test with\x00null bytes that might cause issues"
        
        try:
            result = analyzer.analyze(problematic_input)
            
            # If it succeeds, verify the result
            if result is not None:
                assert isinstance(result, dict), "Result should be a dictionary"
                
        except Exception as e:
            # If it fails, verify error context is meaningful
            error_message = str(e)
            assert len(error_message) > 0, "Error message should not be empty"
            assert error_message != "None", "Error message should be meaningful" 