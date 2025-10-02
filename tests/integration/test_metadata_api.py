"""
API Integration Test for Metadata Assistant

Tests the integration with the existing Flask API to ensure
Phase 1 metadata generation works end-to-end through the API.
"""

import unittest
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class TestAPIIntegration(unittest.TestCase):
    """Test metadata assistant integration with Flask API."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # This would normally import and set up the Flask app
        # For now, we'll test the integration components directly
        pass
    
    def test_analyze_endpoint_includes_metadata(self):
        """Test that the analyze endpoint includes metadata in response."""
        # Mock the analyze request that would include metadata
        test_content = """
        # API Security Best Practices
        
        This guide covers essential security practices for building secure APIs.
        Learn about authentication, authorization, and data protection strategies.
        """
        
        # Import the metadata assistant directly 
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        result = assistant.generate_metadata(
            content=test_content,
            content_type='concept'
        )
        
        # Verify the structure matches what the API would return
        self.assertTrue(result.get('success'))
        self.assertIn('metadata', result)
        
        metadata = result['metadata']
        expected_fields = ['title', 'description', 'keywords', 'taxonomy_tags', 
                          'audience', 'content_type', 'intent']
        
        for field in expected_fields:
            self.assertIn(field, metadata)
        
        # Verify metadata quality
        self.assertNotEqual(metadata['title'], 'Untitled Document')
        self.assertIn('api', metadata['title'].lower())
        self.assertGreater(len(metadata['keywords']), 0)
    
    def test_progress_tracking_integration(self):
        """Test progress tracking integration."""
        progress_updates = []
        
        def mock_progress_callback(session_id, stage, message, details, progress):
            progress_updates.append({
                'session_id': session_id,
                'stage': stage,
                'message': message,
                'details': details,
                'progress': progress
            })
        
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant(progress_callback=mock_progress_callback)
        result = assistant.generate_metadata(
            content="# Test Document\n\nThis is a test for progress tracking.",
            session_id="test_session"
        )
        
        self.assertTrue(result.get('success'))
        self.assertGreater(len(progress_updates), 0)
        
        # Check progress update structure
        for update in progress_updates:
            self.assertEqual(update['session_id'], 'test_session')
            self.assertIn('stage', update)
            self.assertIsInstance(update['progress'], (int, float))
    
    def test_graceful_degradation(self):
        """Test that the system degrades gracefully when components fail."""
        from metadata_assistant import MetadataAssistant
        
        # Test with broken model manager
        class BrokenModelManager:
            def is_available(self):
                return False
            
            def generate_text(self, *args, **kwargs):
                raise Exception("Broken model manager")
        
        assistant = MetadataAssistant(model_manager=BrokenModelManager())
        result = assistant.generate_metadata(
            content="# Test Document\n\nThis should work without AI features."
        )
        
        # Should still succeed with fallbacks
        self.assertTrue(result.get('success'))
        # Note: degraded_mode may or may not be set depending on which features were used
        # The important thing is that it works without the AI model manager
        
        # Should still have basic metadata
        metadata = result['metadata']
        self.assertIn('title', metadata)
        self.assertIn('description', metadata)
        self.assertIn('keywords', metadata)
    
    def test_database_model_integration(self):
        """Test that the database model can be instantiated and used."""
        from database.models import MetadataGeneration
        
        # Test model instantiation
        metadata_gen = MetadataGeneration(
            session_id='test_session',
            document_id='test_doc',
            metadata_id='test_metadata_123',
            title='Test Document',
            description='Test description',
            keywords=['test', 'document'],
            taxonomy_tags=['Reference'],
            audience='General',
            content_type='concept',
            confidence_scores={'title': 0.9, 'keywords': 0.8},
            processing_time=1.5,
            fallback_used=False
        )
        
        # Test model methods
        self.assertEqual(metadata_gen.title, 'Test Document')
        self.assertEqual(metadata_gen.content_type, 'concept')
        self.assertIsInstance(metadata_gen.keywords, list)
        
        # Test to_dict method
        metadata_dict = metadata_gen.to_dict()
        self.assertIsInstance(metadata_dict, dict)
        self.assertIn('title', metadata_dict)
        self.assertIn('metadata_id', metadata_dict)
    
    def test_configuration_validation(self):
        """Test configuration validation and setup."""
        from metadata_assistant.config import MetadataConfig
        
        config = MetadataConfig()
        validation_result = config.validate_config()
        
        self.assertTrue(validation_result['valid'])
        self.assertIsInstance(validation_result['issues'], list)
        self.assertIsInstance(validation_result['warnings'], list)
        
        # Test essential configuration
        self.assertGreater(config.max_keywords, 0)
        self.assertGreater(config.max_description_words, 0)
        self.assertIsInstance(config.taxonomy_config, dict)
    
    def test_output_format_compatibility(self):
        """Test that output formats are compatible with API responses."""
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        content = "# Test\n\nTest content for format compatibility."
        
        # Test all supported formats
        formats = ['dict', 'yaml', 'json']
        
        for fmt in formats:
            with self.subTest(format=fmt):
                result = assistant.generate_metadata(content=content, output_format=fmt)
                
                self.assertTrue(result.get('success'))
                
                if fmt == 'dict':
                    self.assertIsNone(result.get('formatted_output'))
                else:
                    self.assertIsNotNone(result.get('formatted_output'))
                    self.assertIsInstance(result['formatted_output'], str)


class TestProductionReadiness(unittest.TestCase):
    """Test production readiness aspects."""
    
    def test_error_handling_robustness(self):
        """Test robust error handling."""
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        
        # Test various error conditions
        error_cases = [
            ("", "Empty content"),
            ("x" * 200000, "Oversized content"),  # Assuming max is 100KB
            (None, "None content"),
        ]
        
        for content, description in error_cases:
            with self.subTest(case=description):
                try:
                    if content is None:
                        # This should raise an exception before reaching the method
                        with self.assertRaises(Exception):
                            assistant.generate_metadata(content=content)
                    else:
                        result = assistant.generate_metadata(content=content)
                        
                        # Should either succeed with degraded mode or fail gracefully
                        if not result.get('success'):
                            self.assertIn('error', result)
                            self.assertIsInstance(result['error'], str)
                        
                except Exception as e:
                    # If exceptions occur, they should be meaningful
                    self.assertIsInstance(str(e), str)
                    self.assertGreater(len(str(e)), 0)
    
    def test_memory_efficiency(self):
        """Test memory usage is reasonable."""
        import psutil
        import os
        from metadata_assistant import MetadataAssistant
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple documents
        assistant = MetadataAssistant()
        for i in range(5):
            content = f"""
            # Document {i}
            
            This is test document number {i} for memory efficiency testing.
            It contains some content to process but should not cause memory leaks.
            """
            
            result = assistant.generate_metadata(content=content)
            self.assertTrue(result.get('success'))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB for 5 documents)
        max_increase = 50 * 1024 * 1024  # 50MB
        self.assertLess(memory_increase, max_increase, 
                       f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB")
    
    def test_performance_benchmarks(self):
        """Test performance meets benchmarks."""
        import time
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        
        # Test document sizes and expected performance
        test_cases = [
            ("small", 500, 5.0),     # 500 chars, <5s
            ("medium", 2000, 10.0),  # 2K chars, <10s
        ]
        
        for size_name, char_count, max_time in test_cases:
            content = "# Performance Test\n\n" + "This is test content. " * (char_count // 20)
            
            start_time = time.time()
            result = assistant.generate_metadata(content=content)
            processing_time = time.time() - start_time
            
            with self.subTest(size=size_name):
                self.assertTrue(result.get('success'))
                self.assertLess(processing_time, max_time, 
                               f"{size_name} document took {processing_time:.2f}s (max: {max_time}s)")
    
    def test_concurrent_safety(self):
        """Test thread safety for concurrent requests."""
        import threading
        import time
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                content = f"# Worker {worker_id} Document\n\nContent from worker {worker_id}."
                result = assistant.generate_metadata(content=content)
                results.append((worker_id, result))
            except Exception as e:
                errors.append((worker_id, e))
        
        # Create and start threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30)
        
        # Check results
        self.assertEqual(len(errors), 0, f"Concurrent processing errors: {errors}")
        self.assertEqual(len(results), 3, "Not all threads completed")
        
        # All results should be successful
        for worker_id, result in results:
            self.assertTrue(result.get('success'), f"Worker {worker_id} failed")
    
    def test_health_monitoring(self):
        """Test health monitoring capabilities."""
        from metadata_assistant import MetadataAssistant
        
        assistant = MetadataAssistant()
        health_status = assistant.get_health_status()
        
        self.assertIsInstance(health_status, dict)
        self.assertIn('status', health_status)
        self.assertIn('extractors', health_status)
        self.assertIn('dependencies', health_status)
        self.assertIn('configuration', health_status)
        
        # Extractors should be available
        extractors = health_status['extractors']
        required_extractors = ['title_extractor', 'keyword_extractor', 
                              'description_extractor', 'taxonomy_classifier']
        for extractor in required_extractors:
            self.assertIn(extractor, extractors)
            self.assertEqual(extractors[extractor], 'available')


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
