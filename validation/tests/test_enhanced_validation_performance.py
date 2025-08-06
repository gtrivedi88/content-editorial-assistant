"""
Enhanced Validation Performance Testing Suite
Comprehensive performance benchmarking for the enhanced confidence validation system.
Testing Phase 3 Step 3.2 - Performance & Production Readiness
"""

import pytest
import time
import threading
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import psutil
import os

# Import validation system components
from validation.confidence.confidence_calculator import ConfidenceCalculator
from validation.multi_pass.validation_pipeline import ValidationPipeline, PipelineConfiguration
from validation.confidence.context_analyzer import ContextAnalyzer
from validation.confidence.rule_reliability import get_rule_reliability_coefficient
from error_consolidation.consolidator import ErrorConsolidator
from rules import RulesRegistry


class TestEnhancedValidationPerformance:
    """Performance tests for the enhanced validation system."""
    
    @pytest.fixture(scope="class")
    def performance_test_data(self):
        """Create performance test datasets of various sizes."""
        
        # Small documents (50-200 words)
        small_docs = [
            "This is a short document for testing performance. It contains basic grammar and style patterns that should be detected quickly.",
            "Performance testing requires careful measurement. We need to ensure our validation system scales properly.",
            "Configuration management is crucial for production systems. Testing helps identify bottlenecks early."
        ]
        
        # Medium documents (500-1000 words)
        medium_doc = """
        Enhanced confidence validation represents a significant advancement in automated writing analysis.
        The system integrates multiple sophisticated components including content-type detection,
        rule reliability coefficients, and normalized confidence scoring to provide consistent,
        accurate feedback across diverse document types.
        
        Content-type detection utilizes pattern-based classification combined with statistical
        feature extraction to identify technical, procedural, narrative, legal, and marketing
        content with over 85% accuracy. This classification enables context-aware confidence
        adjustments that improve the relevance and reliability of detected issues.
        
        Rule reliability coefficients provide a systematic approach to weighting different
        rule types based on their historical accuracy and applicability. High-reliability
        rules like claims detection and personal information scanning receive coefficients
        near 0.90, while general grammar rules receive moderate coefficients around 0.80.
        
        The universal threshold system eliminates the complexity of content-specific and
        rule-specific threshold management by implementing a single, well-tuned threshold
        of 0.35 that works effectively across all document types and rule combinations.
        
        Performance optimization includes aggressive caching at multiple levels, from
        linguistic analysis results to pattern matching outcomes. The system maintains
        sub-100ms response times for typical documents while providing comprehensive
        validation coverage through the multi-pass validation pipeline.
        
        Production deployment considerations include monitoring confidence score distributions,
        tracking error detection rates, and maintaining system performance under concurrent
        load. The enhanced validation system provides detailed performance metrics and
        confidence explanations to support continuous improvement and troubleshooting.
        """
        
        # Large documents (2000+ words)
        large_doc = medium_doc * 4  # Replicate to create larger test document
        
        return {
            'small': small_docs,
            'medium': [medium_doc] * 3,
            'large': [large_doc] * 2
        }
    
    @pytest.fixture(scope="class")
    def validation_components(self):
        """Initialize validation system components for testing."""
        
        components = {}
        
        try:
            # Initialize confidence calculator
            components['confidence_calculator'] = ConfidenceCalculator(
                cache_results=True,
                enable_layer_caching=True
            )
            
            # Initialize validation pipeline
            pipeline_config = PipelineConfiguration(
                enable_morphological=True,
                enable_contextual=True,
                enable_domain=True,
                enable_cross_rule=True,
                enable_early_termination=True,
                timeout_seconds=10.0
            )
            components['validation_pipeline'] = ValidationPipeline(pipeline_config)
            
            # Initialize context analyzer
            components['context_analyzer'] = ContextAnalyzer()
            
            # Initialize error consolidator
            components['error_consolidator'] = ErrorConsolidator(
                confidence_threshold=0.35,
                enable_enhanced_validation=True
            )
            
            # Initialize rules registry
            components['rules_registry'] = RulesRegistry(
                enable_consolidation=True,
                enable_enhanced_validation=True,
                confidence_threshold=0.35
            )
            
            return components
            
        except Exception as e:
            pytest.skip(f"Could not initialize validation components: {e}")
    
    def test_confidence_calculator_performance(self, validation_components, performance_test_data):
        """Test ConfidenceCalculator performance meets benchmarks."""
        
        confidence_calculator = validation_components['confidence_calculator']
        
        print("\n🔧 Testing ConfidenceCalculator Performance:")
        
        performance_results = {}
        
        for doc_size, documents in performance_test_data.items():
            print(f"\n   📄 Testing {doc_size} documents...")
            
            processing_times = []
            
            for i, document in enumerate(documents):
                start_time = time.perf_counter()
                
                # Test confidence calculation
                try:
                    confidence_result = confidence_calculator.calculate_confidence(
                        text=document,
                        error_position=len(document) // 2,  # Middle of document
                        rule_type='grammar',
                        content_type='general'
                    )
                    
                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    processing_times.append(processing_time)
                    
                    # Validate confidence result
                    assert hasattr(confidence_result, 'final_confidence'), "Should return confidence result"
                    assert 0.0 <= confidence_result.final_confidence <= 1.0, "Confidence should be in valid range"
                    
                except Exception as e:
                    pytest.fail(f"ConfidenceCalculator failed on {doc_size} document {i}: {e}")
            
            # Calculate performance statistics
            avg_time = statistics.mean(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)
            std_dev = statistics.stdev(processing_times) if len(processing_times) > 1 else 0
            
            performance_results[doc_size] = {
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'min_time_ms': min_time,
                'std_dev_ms': std_dev,
                'sample_count': len(processing_times)
            }
            
            print(f"      ⏱️  Average: {avg_time:.2f}ms, Max: {max_time:.2f}ms, Min: {min_time:.2f}ms")
            
            # Performance benchmarks
            if doc_size == 'small':
                assert avg_time < 50, f"Small document processing should be <50ms, got {avg_time:.2f}ms"
            elif doc_size == 'medium':
                assert avg_time < 100, f"Medium document processing should be <100ms, got {avg_time:.2f}ms"
            elif doc_size == 'large':
                assert avg_time < 200, f"Large document processing should be <200ms, got {avg_time:.2f}ms"
        
        print(f"\n   ✅ ConfidenceCalculator performance benchmarks met")
        return performance_results
    
    def test_validation_pipeline_performance(self, validation_components, performance_test_data):
        """Test ValidationPipeline performance."""
        
        validation_pipeline = validation_components['validation_pipeline']
        
        print("\n🔄 Testing ValidationPipeline Performance:")
        
        performance_results = {}
        
        for doc_size, documents in performance_test_data.items():
            print(f"\n   📄 Testing {doc_size} documents...")
            
            processing_times = []
            
            for i, document in enumerate(documents):
                start_time = time.perf_counter()
                
                try:
                    # Create mock error for validation
                    mock_error = {
                        'type': 'grammar',
                        'message': 'Test error for validation',
                        'suggestions': ['Test suggestion'],
                        'sentence': document[:100] + "..." if len(document) > 100 else document,
                        'sentence_index': 0,
                        'severity': 'medium',
                        'confidence_score': 0.7,
                        'rule_id': 'test_rule'
                    }
                    
                    # Test validation pipeline
                    validation_result = validation_pipeline.validate_error(
                        error=mock_error,
                        context={'text': document, 'document_type': 'general'}
                    )
                    
                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    processing_times.append(processing_time)
                    
                    # Validate result
                    assert validation_result is not None, "Should return validation result"
                    
                except Exception as e:
                    pytest.fail(f"ValidationPipeline failed on {doc_size} document {i}: {e}")
            
            # Calculate performance statistics
            avg_time = statistics.mean(processing_times)
            max_time = max(processing_times)
            
            performance_results[doc_size] = {
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'sample_count': len(processing_times)
            }
            
            print(f"      ⏱️  Average: {avg_time:.2f}ms, Max: {max_time:.2f}ms")
            
            # Performance benchmarks
            if doc_size == 'small':
                assert avg_time < 100, f"Small document validation should be <100ms, got {avg_time:.2f}ms"
            elif doc_size == 'medium':
                assert avg_time < 200, f"Medium document validation should be <200ms, got {avg_time:.2f}ms"
            elif doc_size == 'large':
                assert avg_time < 400, f"Large document validation should be <400ms, got {avg_time:.2f}ms"
        
        print(f"\n   ✅ ValidationPipeline performance benchmarks met")
        return performance_results
    
    def test_content_type_detection_performance(self, validation_components, performance_test_data):
        """Test content-type detection performance."""
        
        context_analyzer = validation_components['context_analyzer']
        
        print("\n🔍 Testing Content-Type Detection Performance:")
        
        performance_results = {}
        
        for doc_size, documents in performance_test_data.items():
            print(f"\n   📄 Testing {doc_size} documents...")
            
            processing_times = []
            
            for i, document in enumerate(documents):
                start_time = time.perf_counter()
                
                try:
                    # Test content-type detection
                    content_type = context_analyzer.detect_content_type(document)
                    
                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    processing_times.append(processing_time)
                    
                    # Validate result
                    assert content_type is not None, "Should return content type"
                    
                except Exception as e:
                    pytest.fail(f"Content-type detection failed on {doc_size} document {i}: {e}")
            
            # Calculate performance statistics
            avg_time = statistics.mean(processing_times)
            max_time = max(processing_times)
            
            performance_results[doc_size] = {
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'sample_count': len(processing_times)
            }
            
            print(f"      ⏱️  Average: {avg_time:.2f}ms, Max: {max_time:.2f}ms")
            
            # Performance benchmark: realistic for NLP-based content analysis
            if doc_size == 'small':
                assert avg_time < 15, f"Small document content-type detection should be <15ms, got {avg_time:.2f}ms"
            elif doc_size == 'medium':
                assert avg_time < 30, f"Medium document content-type detection should be <30ms, got {avg_time:.2f}ms"
            elif doc_size == 'large':
                assert avg_time < 80, f"Large document content-type detection should be <80ms, got {avg_time:.2f}ms"
        
        print(f"\n   ✅ Content-type detection performance benchmarks met")
        return performance_results
    
    def test_error_consolidator_performance(self, validation_components, performance_test_data):
        """Test ErrorConsolidator performance with various error counts."""
        
        error_consolidator = validation_components['error_consolidator']
        
        print("\n🔄 Testing ErrorConsolidator Performance:")
        
        # Create test error sets of various sizes
        error_sets = {
            'small': 10,
            'medium': 50,
            'large': 200
        }
        
        performance_results = {}
        
        for set_name, error_count in error_sets.items():
            print(f"\n   📋 Testing {set_name} error set ({error_count} errors)...")
            
            # Generate test errors
            test_errors = []
            for i in range(error_count):
                error = {
                    'type': f'test_type_{i % 5}',
                    'message': f'Test error {i}',
                    'suggestions': [f'Fix error {i}'],
                    'sentence': f'Test sentence {i} with some content to analyze.',
                    'sentence_index': i,
                    'severity': 'medium' if i % 2 == 0 else 'high',
                    'confidence_score': 0.4 + (i % 6) * 0.1,  # Varying confidences
                    'rule_id': f'test_rule_{i}'
                }
                test_errors.append(error)
            
            processing_times = []
            
            # Test consolidation performance multiple times
            for trial in range(3):
                start_time = time.perf_counter()
                
                try:
                    consolidated_errors = error_consolidator.consolidate(test_errors)
                    
                    end_time = time.perf_counter()
                    processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
                    processing_times.append(processing_time)
                    
                    # Validate consolidation worked
                    assert isinstance(consolidated_errors, list), "Should return list of errors"
                    assert len(consolidated_errors) <= len(test_errors), "Should not increase error count"
                    
                except Exception as e:
                    pytest.fail(f"ErrorConsolidator failed on {set_name} set trial {trial}: {e}")
            
            # Calculate performance statistics
            avg_time = statistics.mean(processing_times)
            max_time = max(processing_times)
            
            performance_results[set_name] = {
                'avg_time_ms': avg_time,
                'max_time_ms': max_time,
                'error_count': error_count,
                'sample_count': len(processing_times)
            }
            
            print(f"      ⏱️  Average: {avg_time:.2f}ms, Max: {max_time:.2f}ms")
            
            # Performance benchmarks based on error count
            if set_name == 'small':
                assert avg_time < 50, f"Small error set consolidation should be <50ms, got {avg_time:.2f}ms"
            elif set_name == 'medium':
                assert avg_time < 200, f"Medium error set consolidation should be <200ms, got {avg_time:.2f}ms"
            elif set_name == 'large':
                assert avg_time < 1000, f"Large error set consolidation should be <1000ms, got {avg_time:.2f}ms"
        
        print(f"\n   ✅ ErrorConsolidator performance benchmarks met")
        return performance_results
    
    def test_concurrent_validation_performance(self, validation_components):
        """Test system performance under concurrent load."""
        
        confidence_calculator = validation_components['confidence_calculator']
        
        print("\n🔀 Testing Concurrent Validation Performance:")
        
        # Test concurrent confidence calculations
        test_texts = [
            "Concurrent processing test document with various content patterns.",
            "Performance under load requires careful resource management and optimization.",
            "Multi-threaded validation should maintain consistent performance characteristics.",
            "System stability during concurrent operations is crucial for production deployment."
        ]
        
        def calculate_confidence_worker(text_index):
            """Worker function for concurrent confidence calculation."""
            text = test_texts[text_index % len(test_texts)]
            
            try:
                start_time = time.perf_counter()
                
                confidence_result = confidence_calculator.calculate_confidence(
                    text=text,
                    error_position=len(text) // 2,
                    rule_type='grammar',
                    content_type='general'
                )
                
                end_time = time.perf_counter()
                processing_time = (end_time - start_time) * 1000
                
                return {
                    'success': True,
                    'processing_time_ms': processing_time,
                    'confidence': confidence_result.final_confidence if hasattr(confidence_result, 'final_confidence') else None
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'processing_time_ms': None
                }
        
        # Test with various thread counts
        thread_counts = [1, 2, 5, 10]
        concurrent_results = {}
        
        for thread_count in thread_counts:
            print(f"\n   🧵 Testing with {thread_count} concurrent threads...")
            
            start_time = time.perf_counter()
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                # Submit tasks
                futures = [executor.submit(calculate_confidence_worker, i) for i in range(thread_count * 3)]
                
                # Collect results
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=10)
                        results.append(result)
                    except Exception as e:
                        results.append({'success': False, 'error': str(e)})
            
            end_time = time.perf_counter()
            total_time = (end_time - start_time) * 1000
            
            # Analyze results
            successful_results = [r for r in results if r['success']]
            failed_results = [r for r in results if not r['success']]
            
            if successful_results:
                processing_times = [r['processing_time_ms'] for r in successful_results]
                avg_processing_time = statistics.mean(processing_times)
                max_processing_time = max(processing_times)
            else:
                avg_processing_time = None
                max_processing_time = None
            
            concurrent_results[thread_count] = {
                'total_time_ms': total_time,
                'avg_processing_time_ms': avg_processing_time,
                'max_processing_time_ms': max_processing_time,
                'success_count': len(successful_results),
                'failure_count': len(failed_results),
                'success_rate': len(successful_results) / len(results) * 100
            }
            
            print(f"      ⏱️  Total: {total_time:.2f}ms")
            print(f"      📊 Success rate: {concurrent_results[thread_count]['success_rate']:.1f}%")
            if avg_processing_time:
                print(f"      ⏱️  Avg per task: {avg_processing_time:.2f}ms")
            
            # Performance benchmarks
            assert concurrent_results[thread_count]['success_rate'] >= 90, f"Success rate should be ≥90%, got {concurrent_results[thread_count]['success_rate']:.1f}%"
            
            if avg_processing_time:
                # Allow some degradation under concurrent load
                max_acceptable_time = 150 * thread_count * 0.1  # Scale with thread count
                assert avg_processing_time < max_acceptable_time, f"Concurrent processing too slow: {avg_processing_time:.2f}ms"
        
        print(f"\n   ✅ Concurrent validation performance benchmarks met")
        return concurrent_results
    
    def test_memory_usage_performance(self, validation_components, performance_test_data):
        """Test memory usage patterns during validation."""
        
        print("\n💾 Testing Memory Usage Performance:")
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"   📊 Initial memory usage: {initial_memory:.1f} MB")
        
        confidence_calculator = validation_components['confidence_calculator']
        memory_measurements = []
        
        # Process documents and measure memory
        for doc_size, documents in performance_test_data.items():
            print(f"\n   📄 Processing {doc_size} documents...")
            
            for i, document in enumerate(documents):
                # Process document
                try:
                    confidence_result = confidence_calculator.calculate_confidence(
                        text=document,
                        error_position=len(document) // 2,
                        rule_type='grammar',
                        content_type='general'
                    )
                    
                    # Measure memory after processing
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_measurements.append(current_memory)
                    
                except Exception as e:
                    print(f"      ❌ Error processing document {i}: {e}")
        
        # Analyze memory usage
        if memory_measurements:
            max_memory = max(memory_measurements)
            final_memory = memory_measurements[-1]
            memory_increase = max_memory - initial_memory
            
            print(f"   📊 Peak memory usage: {max_memory:.1f} MB")
            print(f"   📊 Final memory usage: {final_memory:.1f} MB")
            print(f"   📊 Memory increase: {memory_increase:.1f} MB")
            
            # Memory usage benchmarks
            assert memory_increase < 100, f"Memory increase should be <100MB, got {memory_increase:.1f}MB"
            
            # Force garbage collection and measure memory after cleanup
            gc.collect()
            cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
            print(f"   📊 Memory after cleanup: {cleanup_memory:.1f} MB")
            
            print(f"\n   ✅ Memory usage performance acceptable")
            
            return {
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': max_memory,
                'final_memory_mb': final_memory,
                'cleanup_memory_mb': cleanup_memory,
                'memory_increase_mb': memory_increase
            }
        else:
            pytest.fail("No memory measurements collected")


class TestProductionReadiness:
    """Production readiness validation tests."""
    
    @pytest.fixture(scope="class")
    def validation_components(self):
        """Initialize validation system components for production readiness testing."""
        
        components = {}
        
        try:
            # Initialize confidence calculator
            components['confidence_calculator'] = ConfidenceCalculator(
                cache_results=True,
                enable_layer_caching=True
            )
            
            return components
            
        except Exception as e:
            pytest.skip(f"Could not initialize validation components: {e}")
    
    def test_system_stability_under_load(self, validation_components):
        """Test system stability under sustained load."""
        
        print("\n🔧 Testing System Stability Under Load:")
        
        confidence_calculator = validation_components['confidence_calculator']
        
        # Test sustained processing
        test_duration_seconds = 30
        test_text = "This is a sustained load test document with typical content patterns for validation."
        
        start_time = time.time()
        processed_count = 0
        errors = []
        
        print(f"   ⏱️  Running sustained load for {test_duration_seconds} seconds...")
        
        while time.time() - start_time < test_duration_seconds:
            try:
                confidence_result = confidence_calculator.calculate_confidence(
                    text=test_text,
                    error_position=len(test_text) // 2,
                    rule_type='grammar',
                    content_type='general'
                )
                processed_count += 1
                
                # Brief pause to avoid overwhelming
                time.sleep(0.01)
                
            except Exception as e:
                errors.append(str(e))
        
        end_time = time.time()
        actual_duration = end_time - start_time
        processing_rate = processed_count / actual_duration
        
        print(f"   📊 Processed {processed_count} requests in {actual_duration:.1f}s")
        print(f"   📊 Processing rate: {processing_rate:.1f} requests/second")
        print(f"   📊 Error count: {len(errors)}")
        
        # Stability benchmarks
        assert len(errors) == 0, f"Should have no errors during sustained load, got {len(errors)}"
        assert processing_rate > 5, f"Processing rate should be >5 req/sec, got {processing_rate:.1f}"
        
        print(f"   ✅ System stability under load validated")
        
        return {
            'duration_seconds': actual_duration,
            'processed_count': processed_count,
            'processing_rate': processing_rate,
            'error_count': len(errors)
        }
    
    def test_edge_case_performance(self, validation_components):
        """Test performance with edge case inputs."""
        
        print("\n⚡ Testing Edge Case Performance:")
        
        confidence_calculator = validation_components['confidence_calculator']
        
        edge_cases = {
            'empty_text': "",
            'very_short': "Hi.",
            'very_long': "This is a very long sentence. " * 100,
            'special_chars': "Testing with émojis 🎯 and spëcial characters!",
            'numbers_only': "123 456 789 000",
            'mixed_content': "API endpoint /v1/users returns JSON: {'status': 200, 'data': [...]}"
        }
        
        edge_case_results = {}
        
        for case_name, test_text in edge_cases.items():
            print(f"\n   🔍 Testing {case_name}...")
            
            try:
                start_time = time.perf_counter()
                
                confidence_result = confidence_calculator.calculate_confidence(
                    text=test_text,
                    error_position=max(1, len(test_text) // 2),
                    rule_type='grammar',
                    content_type='general'
                )
                
                end_time = time.perf_counter()
                processing_time = (end_time - start_time) * 1000
                
                edge_case_results[case_name] = {
                    'success': True,
                    'processing_time_ms': processing_time,
                    'confidence': confidence_result.final_confidence if hasattr(confidence_result, 'final_confidence') else None
                }
                
                print(f"      ⏱️  Processed in {processing_time:.2f}ms")
                
                # Edge case performance should still be reasonable
                assert processing_time < 200, f"Edge case {case_name} processing too slow: {processing_time:.2f}ms"
                
            except Exception as e:
                edge_case_results[case_name] = {
                    'success': False,
                    'error': str(e),
                    'processing_time_ms': None
                }
                print(f"      ❌ Error: {e}")
                
                # Some edge cases might fail gracefully, but system should not crash
                assert "crashed" not in str(e).lower(), f"System should not crash on edge case {case_name}"
        
        successful_cases = sum(1 for result in edge_case_results.values() if result['success'])
        total_cases = len(edge_cases)
        success_rate = successful_cases / total_cases * 100
        
        print(f"\n   📊 Edge case success rate: {success_rate:.1f}% ({successful_cases}/{total_cases})")
        
        # Should handle most edge cases gracefully
        assert success_rate >= 80, f"Edge case success rate should be ≥80%, got {success_rate:.1f}%"
        
        print(f"   ✅ Edge case performance validated")
        
        return edge_case_results