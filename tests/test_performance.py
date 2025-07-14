"""
Performance and Stress Testing Suite
Tests system performance under various load conditions, memory usage, response times,
and scalability scenarios to ensure enterprise-ready performance.
"""

import pytest
import time
import threading
import multiprocessing
import psutil
import os
import sys
import gc
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from unittest.mock import MagicMock, patch
import tempfile
import json
from typing import List, Dict, Any
import statistics

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestConfig, TestFixtures, TestMockFactory


class PerformanceMonitor:
    """Performance monitoring utilities for testing."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process()
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        gc.collect()  # Force garbage collection for accurate memory measurement
    
    def stop_monitoring(self):
        """Stop performance monitoring and return metrics."""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        # Ensure monitoring was started
        if self.start_time is None or self.start_memory is None:
            raise ValueError("Monitoring was not started. Call start_monitoring() first.")
        
        return {
            'execution_time': self.end_time - self.start_time,
            'memory_start_mb': self.start_memory,
            'memory_end_mb': self.end_memory,
            'memory_delta_mb': self.end_memory - self.start_memory,
            'cpu_percent': self.process.cpu_percent()
        }
    
    @staticmethod
    def get_system_metrics():
        """Get current system metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'available_memory_mb': psutil.virtual_memory().available / 1024 / 1024,
            'disk_usage_percent': psutil.disk_usage('/').percent
        }


class TestPerformance:
    """Performance testing for core components."""
    
    def test_style_analyzer_performance(self):
        """Test style analyzer performance with various text sizes."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        monitor = PerformanceMonitor()
        
        # Test with different text sizes
        test_sizes = [
            (100, "Small text"),
            (1000, "Medium text"),
            (5000, "Large text"),
            (10000, "Very large text")
        ]
        
        performance_results = []
        
        for word_count, description in test_sizes:
            # Generate test text
            test_text = " ".join([TestConfig.SAMPLE_TEXT] * (word_count // len(TestConfig.SAMPLE_TEXT.split()) + 1))
            test_text = " ".join(test_text.split()[:word_count])
            
            monitor.start_monitoring()
            
            # Perform analysis
            result = analyzer.analyze(test_text)
            
            metrics = monitor.stop_monitoring()
            metrics['word_count'] = word_count
            metrics['description'] = description
            metrics['errors_found'] = len(result.get('errors', []))
            
            performance_results.append(metrics)
            
            # Performance assertions
            assert metrics['execution_time'] < 30.0, f"Analysis took too long for {description}: {metrics['execution_time']:.2f}s"
            assert metrics['memory_delta_mb'] < 100, f"Memory usage too high for {description}: {metrics['memory_delta_mb']:.2f}MB"
        
        # Verify performance scales reasonably
        small_time = performance_results[0]['execution_time']
        large_time = performance_results[-1]['execution_time']
        
        # Large text should not be more than 10x slower than small text
        assert large_time / small_time < 10, f"Performance degradation too severe: {large_time/small_time:.2f}x"
        
        # Results collected for analysis
        assert len(performance_results) > 0, "No performance results collected"
    
    def test_ai_rewriter_performance(self):
        """Test AI rewriter performance under load."""
        from rewriter.core import AIRewriter
        
        # Use mock to avoid actual AI calls
        with patch('rewriter.models.ModelManager') as mock_manager_class:
            mock_manager = TestMockFactory.create_mock_model_manager(use_ollama=True)
            mock_manager_class.return_value = mock_manager
            
            with patch('rewriter.generators.TextGenerator') as mock_generator_class:
                mock_generator = TestMockFactory.create_mock_text_generator()
                mock_generator_class.return_value = mock_generator
                
                rewriter = AIRewriter(use_ollama=True)
                monitor = PerformanceMonitor()
                
                # Test rewriting performance
                test_cases = [
                    (TestConfig.SAMPLE_TEXT, "Short text"),
                    (TestConfig.SAMPLE_TEXT * 10, "Medium text"),
                    (TestConfig.SAMPLE_TEXT * 50, "Long text")
                ]
                
                performance_results = []
                
                for test_text, description in test_cases:
                    sample_errors = TestFixtures.get_sample_errors()
                    
                    monitor.start_monitoring()
                    
                    # Perform rewriting
                    result = rewriter.rewrite(test_text, sample_errors, TestConfig.VALID_CONTEXTS[0])
                    
                    metrics = monitor.stop_monitoring()
                    metrics['text_length'] = len(test_text)
                    metrics['description'] = description
                    
                    performance_results.append(metrics)
                    
                    # Performance assertions
                    assert metrics['execution_time'] < 30.0, f"Rewriting took too long for {description}: {metrics['execution_time']:.2f}s"
                    assert result is not None, f"Rewriting failed for {description}"
                
                return performance_results
    
    def test_concurrent_analysis_performance(self):
        """Test performance under concurrent analysis requests."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        num_threads = 5
        num_requests_per_thread = 10
        
        def analyze_text(thread_id):
            """Analyze text in a thread."""
            results = []
            for i in range(num_requests_per_thread):
                start_time = time.time()
                
                test_text = f"{TestConfig.SAMPLE_TEXT} Thread {thread_id} Request {i}"
                result = analyzer.analyze(test_text)
                
                end_time = time.time()
                results.append({
                    'thread_id': thread_id,
                    'request_id': i,
                    'execution_time': end_time - start_time,
                    'errors_found': len(result.get('errors', []))
                })
            return results
        
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Execute concurrent analysis
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(analyze_text, i) for i in range(num_threads)]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        overall_metrics = monitor.stop_monitoring()
        
        # Calculate statistics
        execution_times = [r['execution_time'] for r in all_results]
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Performance assertions
        assert len(all_results) == num_threads * num_requests_per_thread
        assert avg_time < 2.0, f"Average analysis time too high: {avg_time:.2f}s"
        assert max_time < 5.0, f"Maximum analysis time too high: {max_time:.2f}s"
        assert overall_metrics['execution_time'] < 30.0, f"Overall concurrent execution too slow: {overall_metrics['execution_time']:.2f}s"
        
        return {
            'total_requests': len(all_results),
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'overall_metrics': overall_metrics
        }
    
    def test_memory_usage_stability(self):
        """Test memory usage stability over repeated operations."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        process = psutil.Process()
        
        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_readings = [initial_memory]
        
        # Perform repeated analysis
        for i in range(50):
            test_text = f"{TestConfig.SAMPLE_TEXT} Iteration {i}"
            analyzer.analyze(test_text)
            
            # Record memory every 10 iterations
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory)
        
        # Calculate memory growth
        final_memory = memory_readings[-1]
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_readings)
        
        # Memory stability assertions
        assert memory_growth < 50, f"Memory growth too high: {memory_growth:.2f}MB"
        assert max_memory - initial_memory < 100, f"Peak memory usage too high: {max_memory - initial_memory:.2f}MB"
        
        # Check for memory leaks (growth should be minimal)
        if len(memory_readings) > 2:
            recent_growth = memory_readings[-1] - memory_readings[-3]
            assert recent_growth < 20, f"Recent memory growth suggests leak: {recent_growth:.2f}MB"
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': memory_growth,
            'max_memory_mb': max_memory,
            'memory_readings': memory_readings
        }


class TestStressTesting:
    """Stress testing for system limits and edge cases."""
    
    def test_large_document_processing(self):
        """Test processing of very large documents."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        monitor = PerformanceMonitor()
        
        # Create a very large document (approximately 100KB)
        large_text = TestConfig.SAMPLE_TEXT * 1000
        
        monitor.start_monitoring()
        
        try:
            result = analyzer.analyze(large_text)
            metrics = monitor.stop_monitoring()
            
            # Stress test assertions
            assert result is not None, "Large document analysis failed"
            assert metrics['execution_time'] < 60.0, f"Large document analysis too slow: {metrics['execution_time']:.2f}s"
            assert metrics['memory_delta_mb'] < 200, f"Large document memory usage too high: {metrics['memory_delta_mb']:.2f}MB"
            
            return {
                'document_size_chars': len(large_text),
                'execution_time': metrics['execution_time'],
                'memory_usage_mb': metrics['memory_delta_mb'],
                'errors_found': len(result.get('errors', []))
            }
            
        except Exception as e:
            metrics = monitor.stop_monitoring()
            pytest.fail(f"Large document processing failed: {e}")
    
    def test_rapid_sequential_requests(self):
        """Test handling of rapid sequential requests."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        num_requests = 100
        
        start_time = time.time()
        results = []
        
        for i in range(num_requests):
            test_text = f"{TestConfig.SAMPLE_TEXT} Request {i}"
            request_start = time.time()
            
            result = analyzer.analyze(test_text)
            
            request_end = time.time()
            results.append({
                'request_id': i,
                'execution_time': request_end - request_start,
                'success': result is not None
            })
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        successful_requests = sum(1 for r in results if r['success'])
        avg_time = statistics.mean(r['execution_time'] for r in results)
        throughput = successful_requests / total_time
        
        # Stress test assertions
        assert successful_requests == num_requests, f"Some requests failed: {successful_requests}/{num_requests}"
        assert avg_time < 1.0, f"Average request time too high: {avg_time:.2f}s"
        assert throughput > 10, f"Throughput too low: {throughput:.2f} requests/second"
        
        return {
            'total_requests': num_requests,
            'successful_requests': successful_requests,
            'total_time': total_time,
            'avg_time': avg_time,
            'throughput': throughput
        }
    
    def test_error_condition_performance(self):
        """Test performance under error conditions."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        monitor = PerformanceMonitor()
        
        error_conditions = [
            ("", "Empty text"),
            ("   ", "Whitespace only"),
            ("a" * 100000, "Extremely long single word"),
            ("!" * 1000, "Special characters only"),
            ("\n" * 1000, "Newlines only")
        ]
        
        results = []
        
        for test_text, description in error_conditions:
            monitor.start_monitoring()
            
            try:
                result = analyzer.analyze(test_text)
                metrics = monitor.stop_monitoring()
                
                results.append({
                    'description': description,
                    'execution_time': metrics['execution_time'],
                    'memory_delta_mb': metrics['memory_delta_mb'],
                    'success': result is not None,
                    'error': None
                })
                
                # Error condition performance assertions
                assert metrics['execution_time'] < 10.0, f"Error condition processing too slow for {description}: {metrics['execution_time']:.2f}s"
                
            except Exception as e:
                metrics = monitor.stop_monitoring()
                results.append({
                    'description': description,
                    'execution_time': metrics['execution_time'],
                    'memory_delta_mb': metrics['memory_delta_mb'],
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def test_resource_exhaustion_handling(self):
        """Test system behavior under resource exhaustion."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test with progressively larger texts until we hit limits
        max_size = 1000000  # 1MB of text
        step_size = 100000   # 100KB increments
        
        results = []
        
        for size in range(step_size, max_size + 1, step_size):
            test_text = "A" * size
            
            try:
                start_time = time.time()
                result = analyzer.analyze(test_text)
                end_time = time.time()
                
                results.append({
                    'text_size_chars': size,
                    'execution_time': end_time - start_time,
                    'success': True,
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
                })
                
                # If it takes too long, stop the test
                if end_time - start_time > 30.0:
                    break
                    
            except Exception as e:
                results.append({
                    'text_size_chars': size,
                    'execution_time': 0,
                    'success': False,
                    'error': str(e),
                    'memory_mb': psutil.Process().memory_info().rss / 1024 / 1024
                })
                break
        
        # Verify graceful degradation
        successful_results = [r for r in results if r['success']]
        assert len(successful_results) > 0, "No successful results under resource pressure"
        
        # Check that performance degrades gracefully
        if len(successful_results) > 1:
            time_growth = successful_results[-1]['execution_time'] / successful_results[0]['execution_time']
            assert time_growth < 100, f"Performance degradation too severe: {time_growth:.2f}x"
        
        return results


class TestScalability:
    """Scalability testing for enterprise deployment scenarios."""
    
    def test_multi_process_scalability(self):
        """Test scalability across multiple processes."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        def analyze_in_process(process_id, num_requests):
            """Analyze text in a separate process."""
            analyzer = StyleAnalyzer()
            results = []
            
            for i in range(num_requests):
                test_text = f"{TestConfig.SAMPLE_TEXT} Process {process_id} Request {i}"
                start_time = time.time()
                
                result = analyzer.analyze(test_text)
                
                end_time = time.time()
                results.append({
                    'process_id': process_id,
                    'request_id': i,
                    'execution_time': end_time - start_time,
                    'success': result is not None
                })
            
            return results
        
        num_processes = min(4, multiprocessing.cpu_count())
        requests_per_process = 20
        
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            futures = [
                executor.submit(analyze_in_process, i, requests_per_process)
                for i in range(num_processes)
            ]
            
            all_results = []
            for future in futures:
                all_results.extend(future.result())
        
        total_time = time.time() - start_time
        
        # Calculate scalability metrics
        total_requests = len(all_results)
        successful_requests = sum(1 for r in all_results if r['success'])
        throughput = successful_requests / total_time
        avg_time = statistics.mean(r['execution_time'] for r in all_results)
        
        # Scalability assertions
        assert successful_requests == total_requests, f"Some requests failed: {successful_requests}/{total_requests}"
        assert throughput > 5, f"Multi-process throughput too low: {throughput:.2f} requests/second"
        assert avg_time < 2.0, f"Average request time too high: {avg_time:.2f}s"
        
        return {
            'num_processes': num_processes,
            'requests_per_process': requests_per_process,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'total_time': total_time,
            'throughput': throughput,
            'avg_time': avg_time
        }
    
    def test_configuration_scalability(self):
        """Test configuration system scalability."""
        from src.config import Config
        
        # Test creating many configuration instances
        num_configs = 1000
        
        start_time = time.time()
        configs = []
        
        for i in range(num_configs):
            config = Config()
            configs.append(config)
            
            # Verify each config is properly initialized
            assert config.SECRET_KEY is not None
            assert config.OLLAMA_MODEL is not None
        
        creation_time = time.time() - start_time
        
        # Test configuration method calls
        start_time = time.time()
        
        for config in configs:
            ai_config = config.get_ai_config()
            upload_config = config.get_upload_config()
            
            assert 'model_type' in ai_config
            assert 'max_content_length' in upload_config
        
        access_time = time.time() - start_time
        
        # Scalability assertions
        assert creation_time < 5.0, f"Configuration creation too slow: {creation_time:.2f}s for {num_configs} configs"
        assert access_time < 2.0, f"Configuration access too slow: {access_time:.2f}s for {num_configs * 2} calls"
        
        return {
            'num_configs': num_configs,
            'creation_time': creation_time,
            'access_time': access_time,
            'creation_rate': num_configs / creation_time,
            'access_rate': (num_configs * 2) / access_time
        }
    
    def test_memory_scalability(self):
        """Test memory usage scalability with increasing load."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        process = psutil.Process()
        
        # Test with increasing numbers of concurrent operations
        load_levels = [1, 5, 10, 20, 50]
        memory_results = []
        
        for load_level in load_levels:
            gc.collect()  # Clean up before measurement
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            def analyze_text(thread_id):
                """Analyze text in a thread."""
                for i in range(10):  # 10 requests per thread
                    test_text = f"{TestConfig.SAMPLE_TEXT} Load {load_level} Thread {thread_id} Request {i}"
                    analyzer.analyze(test_text)
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(analyze_text, i) for i in range(load_level)]
                for future in futures:
                    future.result()
            
            end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024
            
            memory_results.append({
                'load_level': load_level,
                'initial_memory_mb': initial_memory,
                'final_memory_mb': final_memory,
                'memory_delta_mb': final_memory - initial_memory,
                'execution_time': end_time - start_time,
                'total_requests': load_level * 10
            })
        
        # Verify memory usage scales reasonably
        for result in memory_results:
            # Memory growth should be reasonable for the load level
            expected_max_growth = result['load_level'] * 10  # 10MB per load level max
            assert result['memory_delta_mb'] < expected_max_growth, f"Memory growth too high for load level {result['load_level']}: {result['memory_delta_mb']:.2f}MB"
        
        return memory_results


class TestBenchmarking:
    """Benchmarking tests for performance baselines."""
    
    def test_baseline_performance_benchmark(self):
        """Establish baseline performance benchmarks."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Standard benchmark test
        benchmark_text = TestConfig.SAMPLE_TEXT * 100  # ~1000 words
        num_iterations = 10
        
        execution_times = []
        memory_deltas = []
        
        for i in range(num_iterations):
            monitor = PerformanceMonitor()
            monitor.start_monitoring()
            
            result = analyzer.analyze(benchmark_text)
            
            metrics = monitor.stop_monitoring()
            execution_times.append(metrics['execution_time'])
            memory_deltas.append(metrics['memory_delta_mb'])
        
        # Calculate benchmark statistics
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        std_time = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        avg_memory = statistics.mean(memory_deltas)
        
        # Performance benchmarks (these establish baselines)
        benchmark_results = {
            'benchmark_text_length': len(benchmark_text),
            'num_iterations': num_iterations,
            'avg_execution_time': avg_time,
            'median_execution_time': median_time,
            'std_execution_time': std_time,
            'avg_memory_delta_mb': avg_memory,
            'max_execution_time': max(execution_times),
            'min_execution_time': min(execution_times)
        }
        
        # Reasonable baseline assertions
        assert avg_time < 5.0, f"Baseline performance too slow: {avg_time:.2f}s"
        assert avg_memory < 50, f"Baseline memory usage too high: {avg_memory:.2f}MB"
        assert std_time < avg_time * 0.5, f"Performance too inconsistent: std={std_time:.2f}s, avg={avg_time:.2f}s"
        
        return benchmark_results
    
    def test_regression_detection(self):
        """Test for performance regression detection."""
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Simulate baseline performance (this would be stored from previous runs)
        baseline_time = 2.0  # seconds
        baseline_memory = 20  # MB
        
        # Current performance test
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        test_text = TestConfig.SAMPLE_TEXT * 100
        result = analyzer.analyze(test_text)
        
        metrics = monitor.stop_monitoring()
        
        # Regression detection
        time_regression = (metrics['execution_time'] - baseline_time) / baseline_time
        memory_regression = (metrics['memory_delta_mb'] - baseline_memory) / baseline_memory
        
        # Regression thresholds (20% degradation is concerning)
        assert time_regression < 0.2, f"Performance regression detected: {time_regression:.1%} slower than baseline"
        assert memory_regression < 0.2, f"Memory regression detected: {memory_regression:.1%} more memory than baseline"
        
        return {
            'baseline_time': baseline_time,
            'current_time': metrics['execution_time'],
            'time_regression': time_regression,
            'baseline_memory': baseline_memory,
            'current_memory': metrics['memory_delta_mb'],
            'memory_regression': memory_regression
        } 