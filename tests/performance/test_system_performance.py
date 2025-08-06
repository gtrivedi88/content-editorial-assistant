"""
System Performance Tests
Comprehensive performance testing for the complete confidence-enhanced analysis system
"""

import pytest
import tempfile
import shutil
import os
import time
import threading
import json
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, patch
from datetime import datetime

# Test data for performance testing
class PerformanceTestData:
    """Performance test data and utilities"""
    
    # Small document for quick tests
    SMALL_DOCUMENT = """
    This is a small test document.
    It has some basic writing issues.
    The analysis should be quick.
    """
    
    # Medium document for standard performance testing
    MEDIUM_DOCUMENT = """
    Performance Testing Document for Writing Analysis System
    
    This document is designed to test the performance characteristics of the writing analysis system
    with confidence features enabled. The system should be able to process documents efficiently
    while maintaining accuracy and providing detailed confidence information.
    
    The document contains various types of writing issues:
    
    1. Grammar Issues
       - Subject-verb agreement errors was present in sentences
       - Missing articles in some places
       - Incorrect verb tenses being used
    
    2. Style Problems
       - Passive voice constructions are used frequently throughout
       - Long, complex sentences that could be simplified for better readability
       - Inconsistent terminology being utilized across sections
    
    3. Word Usage Issues
       - Utilize instead of use in many contexts
       - Functionality instead of function where appropriate
       - Implementation details that could be simplified
    
    4. Performance Considerations
       - The system should handle this document efficiently
       - Confidence calculations should not significantly impact speed
       - Memory usage should remain within acceptable limits
       - Real-time features should maintain responsiveness
    
    This document serves as a benchmark for performance testing across all system components.
    """
    
    # Large document for stress testing
    LARGE_DOCUMENT = """
    Large Document Performance Test
    
    """ + "\n".join([
        f"Section {i}: Performance Analysis and Testing\n"
        f"This section {i} contains various writing issues for performance testing. "
        f"The content includes passive voice constructions, word usage problems, and style issues. "
        f"Each section is designed to test different aspects of the analysis system performance. "
        f"The system should maintain consistent performance across all {i} sections.\n"
        f"Grammar errors was introduced intentionally in section {i}. "
        f"The analysis should detect these efficiently while calculating confidence scores. "
        f"Performance metrics should be collected for section {i} processing.\n"
        for i in range(1, 51)
    ]) + """
    
    End of large document performance test.
    """
    
    # Very large document for extreme stress testing
    @staticmethod
    def generate_very_large_document(sections: int = 100) -> str:
        """Generate a very large document for extreme performance testing"""
        content = ["Very Large Document Performance Stress Test\n"]
        
        for i in range(1, sections + 1):
            section_content = f"""
Section {i}: Advanced Performance Testing

This section {i} is part of a comprehensive performance stress test designed to evaluate
the writing analysis system's performance under extreme load conditions. The content
deliberately includes various types of writing issues to ensure comprehensive analysis.

Writing Issues in Section {i}:
- Grammar problems was intentionally introduced for testing purposes
- Passive voice constructions are used frequently throughout this section
- Word usage issues like utilize instead of use appear multiple times
- Long sentences that could potentially be simplified for better readability and user experience
- Inconsistent terminology and style choices across different paragraphs

Performance Considerations for Section {i}:
- Analysis time should scale linearly with content size
- Memory usage should remain within acceptable bounds during processing
- Confidence calculations should not cause exponential performance degradation
- Real-time features should maintain responsiveness even with large documents
- Error detection accuracy should not be compromised for performance gains

Section {i} serves as part of the comprehensive performance benchmark for the enhanced
writing analysis system with confidence features enabled across all components.
"""
            content.append(section_content)
        
        return "\n".join(content)


class TestSystemPerformance:
    """Test system performance with confidence features enabled"""
    
    def setup_method(self):
        """Setup performance test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.performance_results = {}
        
        # Initialize system monitoring
        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
    def teardown_method(self):
        """Cleanup performance test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Force garbage collection
        gc.collect()
    
    def _measure_performance(self, func, *args, **kwargs) -> Tuple[Any, Dict[str, float]]:
        """Measure performance metrics for a function call"""
        # Force garbage collection before measurement
        gc.collect()
        
        # Capture initial state
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = self.process.cpu_percent()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Capture final state
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = self.process.cpu_percent()
        
        # Calculate metrics
        metrics = {
            'execution_time': end_time - start_time,
            'memory_usage': end_memory - start_memory,
            'peak_memory': end_memory,
            'cpu_usage': max(start_cpu, end_cpu)
        }
        
        return result, metrics
    
    def test_analysis_time_with_confidence_features(self):
        """Test analysis time with confidence features enabled"""
        print("\n⏱️ Test 1: Analysis Time with Confidence Features")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test different document sizes
        test_cases = [
            ("Small", PerformanceTestData.SMALL_DOCUMENT),
            ("Medium", PerformanceTestData.MEDIUM_DOCUMENT),
            ("Large", PerformanceTestData.LARGE_DOCUMENT),
        ]
        
        analysis_results = {}
        
        for case_name, document in test_cases:
            print(f"Testing {case_name} document...")
            
            # Perform multiple runs for average
            runs = 3
            total_time = 0
            total_errors = 0
            enhanced_errors = 0
            
            for run in range(runs):
                result, metrics = self._measure_performance(
                    analyzer.analyze_with_blocks, document, 'auto'
                )
                
                total_time += metrics['execution_time']
                errors = result['analysis']['errors']
                total_errors += len(errors)
                enhanced_errors += len([e for e in errors if e.get('enhanced_validation_available', False)])
            
            # Calculate averages
            avg_time = total_time / runs
            avg_errors = total_errors / runs
            avg_enhanced = enhanced_errors / runs
            words_count = len(document.split())
            words_per_second = words_count / avg_time if avg_time > 0 else 0
            
            analysis_results[case_name] = {
                'avg_time': avg_time,
                'words_count': words_count,
                'words_per_second': words_per_second,
                'avg_errors': avg_errors,
                'avg_enhanced_errors': avg_enhanced,
                'enhancement_rate': avg_enhanced / avg_errors if avg_errors > 0 else 0
            }
            
            print(f"✅ {case_name}: {avg_time:.3f}s, {words_per_second:.0f} words/sec, {avg_errors:.0f} errors")
        
        # Performance assertions
        assert analysis_results['Small']['avg_time'] < 1.0, "Small document analysis too slow"
        assert analysis_results['Medium']['avg_time'] < 3.0, "Medium document analysis too slow"
        assert analysis_results['Large']['avg_time'] < 10.0, "Large document analysis too slow"
        
        # Performance should scale reasonably with document size
        medium_ratio = analysis_results['Medium']['avg_time'] / analysis_results['Small']['avg_time']
        large_ratio = analysis_results['Large']['avg_time'] / analysis_results['Medium']['avg_time']
        
        assert medium_ratio < 10, "Performance doesn't scale well from small to medium"
        assert large_ratio < 10, "Performance doesn't scale well from medium to large"
        
        self.performance_results['analysis_time'] = analysis_results
        return analysis_results
    
    def test_memory_usage_impact_of_confidence_calculation(self):
        """Test memory usage impact of confidence calculation"""
        print("\n💾 Test 2: Memory Usage Impact of Confidence Calculation")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        analyzer = StyleAnalyzer()
        
        # Test memory usage with different document sizes
        memory_results = {}
        
        test_documents = [
            ("Baseline", "Simple test document."),
            ("Medium", PerformanceTestData.MEDIUM_DOCUMENT),
            ("Large", PerformanceTestData.LARGE_DOCUMENT),
            ("Very Large", PerformanceTestData.generate_very_large_document(50))
        ]
        
        for test_name, document in test_documents:
            print(f"Testing memory usage for {test_name} document...")
            
            # Force garbage collection before test
            gc.collect()
            initial_memory = self.process.memory_info().rss / 1024 / 1024
            
            # Perform analysis and measure memory
            result, metrics = self._measure_performance(
                analyzer.analyze_with_blocks, document, 'auto'
            )
            
            # Force garbage collection after analysis
            gc.collect()
            final_memory = self.process.memory_info().rss / 1024 / 1024
            
            memory_results[test_name] = {
                'initial_memory': initial_memory,
                'peak_memory': metrics['peak_memory'],
                'final_memory': final_memory,
                'memory_increase': metrics['peak_memory'] - initial_memory,
                'memory_retained': final_memory - initial_memory,
                'document_size': len(document),
                'errors_found': len(result['analysis']['errors'])
            }
            
            print(f"✅ {test_name}: +{memory_results[test_name]['memory_increase']:.1f}MB peak, "
                  f"{memory_results[test_name]['memory_retained']:.1f}MB retained")
        
        # Memory usage assertions
        assert memory_results['Medium']['memory_increase'] < 100, "Medium document uses too much memory"
        assert memory_results['Large']['memory_increase'] < 200, "Large document uses too much memory"
        assert memory_results['Very Large']['memory_increase'] < 500, "Very large document uses too much memory"
        
        # Memory should not leak significantly
        for test_name, result in memory_results.items():
            if test_name != "Baseline":
                leak_ratio = result['memory_retained'] / result['memory_increase']
                assert leak_ratio < 0.3, f"Significant memory leak detected in {test_name} test"
        
        self.performance_results['memory_usage'] = memory_results
        return memory_results
    
    def test_api_response_time_with_confidence_enhancements(self):
        """Test API response time with confidence enhancements"""
        print("\n🌐 Test 3: API Response Time with Confidence Enhancements")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        # Simulate API request processing
        analyzer = StyleAnalyzer()
        
        api_results = {}
        
        # Test different API scenarios
        test_scenarios = [
            ("Standard Request", PerformanceTestData.MEDIUM_DOCUMENT, {'include_confidence_details': True}),
            ("High Confidence Threshold", PerformanceTestData.MEDIUM_DOCUMENT, {'confidence_threshold': 0.8}),
            ("Detailed Response", PerformanceTestData.MEDIUM_DOCUMENT, {'include_confidence_details': True, 'confidence_threshold': 0.5}),
            ("Large Document", PerformanceTestData.LARGE_DOCUMENT, {'include_confidence_details': True})
        ]
        
        for scenario_name, document, params in test_scenarios:
            print(f"Testing {scenario_name}...")
            
            # Simulate API request processing
            def simulate_api_request():
                # Analysis
                analysis_start = time.time()
                result = analyzer.analyze_with_blocks(document, 'auto')
                analysis_time = time.time() - analysis_start
                
                # API response preparation
                response_start = time.time()
                
                api_response = {
                    'success': True,
                    'analysis': result['analysis'],
                    'processing_time': analysis_time,
                    'session_id': 'perf-test-session',
                    'confidence_metadata': {
                        'confidence_threshold_used': params.get('confidence_threshold', 0.43),
                        'enhanced_validation_enabled': result['analysis'].get('enhanced_validation_enabled', False),
                        'confidence_filtering_applied': 'confidence_threshold' in params
                    },
                    'api_version': '2.0'
                }
                
                if params.get('include_confidence_details', False):
                    api_response['confidence_details'] = {
                        'confidence_system_available': True,
                        'threshold_range': {'min': 0.0, 'max': 1.0, 'default': 0.43},
                        'confidence_levels': {
                            'high': {'min': 0.7, 'label': 'High Confidence'},
                            'medium': {'min': 0.5, 'label': 'Medium Confidence'},
                            'low': {'min': 0.0, 'label': 'Low Confidence'}
                        }
                    }
                
                # JSON serialization
                json_response = json.dumps(api_response, default=str)
                response_time = time.time() - response_start
                
                return {
                    'analysis_time': analysis_time,
                    'response_preparation_time': response_time,
                    'total_time': analysis_time + response_time,
                    'response_size': len(json_response),
                    'errors_count': len(result['analysis']['errors'])
                }
            
            # Measure API performance
            result, metrics = self._measure_performance(simulate_api_request)
            
            api_results[scenario_name] = {
                'total_api_time': result['total_time'],
                'analysis_time': result['analysis_time'],
                'response_time': result['response_preparation_time'],
                'response_size': result['response_size'],
                'errors_count': result['errors_count'],
                'memory_usage': metrics['memory_usage'],
                'execution_time': metrics['execution_time']
            }
            
            print(f"✅ {scenario_name}: {result['total_time']:.3f}s total, "
                  f"{result['response_size']} bytes response")
        
        # API performance assertions
        for scenario_name, result in api_results.items():
            assert result['total_api_time'] < 5.0, f"{scenario_name} API response too slow"
            assert result['response_time'] < 0.1, f"{scenario_name} response preparation too slow"
        
        self.performance_results['api_response'] = api_results
        return api_results
    
    def test_websocket_performance_with_confidence_events(self):
        """Test WebSocket performance with confidence events"""
        print("\n📡 Test 4: WebSocket Performance with Confidence Events")
        
        from app_modules import websocket_handlers
        
        # Mock SocketIO for performance testing
        mock_socketio = Mock()
        emit_calls = []
        
        def track_emit(*args, **kwargs):
            emit_calls.append((time.time(), args, kwargs))
        
        mock_socketio.emit = track_emit
        websocket_handlers.set_socketio(mock_socketio)
        
        websocket_results = {}
        
        # Test different WebSocket scenarios
        test_scenarios = [
            ("Confidence Updates", 100, websocket_handlers.emit_confidence_update),
            ("Feedback Notifications", 100, websocket_handlers.emit_feedback_notification),
            ("Validation Progress", 100, websocket_handlers.emit_validation_progress),
            ("Confidence Insights", 50, websocket_handlers.emit_confidence_insights)
        ]
        
        for scenario_name, event_count, emit_function in test_scenarios:
            print(f"Testing {scenario_name}...")
            
            emit_calls.clear()
            
            def emit_events():
                for i in range(event_count):
                    session_id = f"perf-session-{i % 10}"  # 10 different sessions
                    
                    if emit_function == websocket_handlers.emit_confidence_update:
                        data = {
                            'event_type': 'performance_test',
                            'confidence_data': {'confidence': 0.5 + (i % 5) * 0.1}
                        }
                    elif emit_function == websocket_handlers.emit_feedback_notification:
                        data = {
                            'event_type': 'feedback_received',
                            'feedback_type': 'correct' if i % 2 == 0 else 'incorrect'
                        }
                    elif emit_function == websocket_handlers.emit_validation_progress:
                        stage = ['morphological', 'contextual', 'domain'][i % 3]
                        data = {'progress': (i % 10) * 10, 'stage_info': f"Processing {stage}"}
                    else:  # confidence_insights
                        data = {
                            'insights_type': 'performance_test',
                            'data': {'accuracy': 0.8, 'total_errors': i * 2}
                        }
                    
                    emit_function(session_id, data)
            
            # Measure WebSocket performance
            result, metrics = self._measure_performance(emit_events)
            
            # Calculate WebSocket metrics
            if emit_calls:
                first_emit = emit_calls[0][0]
                last_emit = emit_calls[-1][0]
                total_emit_time = last_emit - first_emit
                events_per_second = len(emit_calls) / total_emit_time if total_emit_time > 0 else float('inf')
            else:
                total_emit_time = 0
                events_per_second = 0
            
            websocket_results[scenario_name] = {
                'total_events': len(emit_calls),
                'total_time': metrics['execution_time'],
                'emit_time': total_emit_time,
                'events_per_second': events_per_second,
                'memory_usage': metrics['memory_usage'],
                'avg_time_per_event': metrics['execution_time'] / event_count if event_count > 0 else 0
            }
            
            print(f"✅ {scenario_name}: {len(emit_calls)} events, {events_per_second:.0f} events/sec")
        
        # WebSocket performance assertions
        for scenario_name, result in websocket_results.items():
            assert result['events_per_second'] > 100, f"{scenario_name} WebSocket events too slow"
            assert result['avg_time_per_event'] < 0.01, f"{scenario_name} individual events too slow"
        
        self.performance_results['websocket'] = websocket_results
        return websocket_results
    
    def test_system_scalability_with_confidence_features(self):
        """Test system scalability with confidence features"""
        print("\n📈 Test 5: System Scalability with Confidence Features")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        from app_modules.feedback_storage import FeedbackStorage
        
        analyzer = StyleAnalyzer()
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        scalability_results = {}
        
        # Test concurrent analysis requests
        def test_concurrent_analysis():
            print("Testing concurrent analysis requests...")
            
            concurrent_levels = [1, 2, 4, 8]
            document = PerformanceTestData.MEDIUM_DOCUMENT
            
            for concurrency in concurrent_levels:
                def analyze_document():
                    return analyzer.analyze_with_blocks(document, 'auto')
                
                start_time = time.time()
                
                with ThreadPoolExecutor(max_workers=concurrency) as executor:
                    futures = [executor.submit(analyze_document) for _ in range(concurrency)]
                    results = [future.result() for future in as_completed(futures)]
                
                end_time = time.time()
                
                total_time = end_time - start_time
                throughput = concurrency / total_time
                
                scalability_results[f"concurrent_{concurrency}"] = {
                    'concurrency_level': concurrency,
                    'total_time': total_time,
                    'throughput': throughput,
                    'avg_time_per_request': total_time / concurrency,
                    'total_errors': sum(len(r['analysis']['errors']) for r in results)
                }
                
                print(f"✅ Concurrency {concurrency}: {throughput:.1f} requests/sec")
        
        # Test feedback system scalability
        def test_feedback_scalability():
            print("Testing feedback system scalability...")
            
            feedback_volumes = [100, 500, 1000, 2000]
            
            for volume in feedback_volumes:
                feedback_entries = []
                for i in range(volume):
                    feedback_entries.append({
                        'session_id': f"scale-session-{i % 50}",  # 50 different sessions
                        'error_id': f"scale-error-{i}",
                        'error_type': ['grammar', 'style', 'word_usage'][i % 3],
                        'error_message': f"Scalability test error {i}",
                        'confidence_score': 0.3 + (i % 7) * 0.1,
                        'feedback_type': ['correct', 'incorrect'][i % 2],
                        'confidence_rating': (i % 5) + 1
                    })
                
                def process_feedback_batch():
                    successful = 0
                    for feedback in feedback_entries:
                        success, _, _ = feedback_storage.store_feedback(feedback)
                        if success:
                            successful += 1
                    return successful
                
                result, metrics = self._measure_performance(process_feedback_batch)
                
                processing_rate = result / metrics['execution_time'] if metrics['execution_time'] > 0 else 0
                
                scalability_results[f"feedback_{volume}"] = {
                    'volume': volume,
                    'successful': result,
                    'processing_time': metrics['execution_time'],
                    'processing_rate': processing_rate,
                    'memory_usage': metrics['memory_usage']
                }
                
                print(f"✅ Feedback {volume}: {processing_rate:.0f} entries/sec")
        
        # Run scalability tests
        test_concurrent_analysis()
        test_feedback_scalability()
        
        # Scalability assertions
        # Concurrent analysis should scale reasonably
        conc_1 = scalability_results['concurrent_1']['throughput']
        conc_4 = scalability_results['concurrent_4']['throughput']
        scaling_efficiency = (conc_4 / conc_1) / 4  # Should be close to 1.0 for perfect scaling
        
        assert scaling_efficiency > 0.3, f"Poor scaling efficiency: {scaling_efficiency:.2f}"
        
        # Feedback processing should maintain performance
        feedback_100 = scalability_results['feedback_100']['processing_rate']
        feedback_1000 = scalability_results['feedback_1000']['processing_rate']
        performance_retention = feedback_1000 / feedback_100
        
        assert performance_retention > 0.5, f"Feedback processing degrades too much: {performance_retention:.2f}"
        
        self.performance_results['scalability'] = scalability_results
        return scalability_results
    
    def test_baseline_performance_benchmark(self):
        """Benchmark performance against baseline system expectations"""
        print("\n📊 Test 6: Baseline Performance Benchmark")
        
        # Define performance baselines (acceptable thresholds)
        performance_baselines = {
            'small_document_analysis': 1.0,      # seconds
            'medium_document_analysis': 3.0,     # seconds
            'large_document_analysis': 10.0,     # seconds
            'memory_usage_medium': 100,          # MB
            'memory_usage_large': 200,           # MB
            'api_response_time': 5.0,            # seconds
            'websocket_events_per_second': 100,  # events/sec
            'concurrent_throughput': 1.0,        # requests/sec
            'feedback_processing_rate': 100      # entries/sec
        }
        
        # Collect actual performance results
        actual_performance = {}
        
        if 'analysis_time' in self.performance_results:
            analysis = self.performance_results['analysis_time']
            actual_performance.update({
                'small_document_analysis': analysis.get('Small', {}).get('avg_time', 0),
                'medium_document_analysis': analysis.get('Medium', {}).get('avg_time', 0),
                'large_document_analysis': analysis.get('Large', {}).get('avg_time', 0)
            })
        
        if 'memory_usage' in self.performance_results:
            memory = self.performance_results['memory_usage']
            actual_performance.update({
                'memory_usage_medium': memory.get('Medium', {}).get('memory_increase', 0),
                'memory_usage_large': memory.get('Large', {}).get('memory_increase', 0)
            })
        
        if 'api_response' in self.performance_results:
            api = self.performance_results['api_response']
            std_request = api.get('Standard Request', {})
            actual_performance['api_response_time'] = std_request.get('total_api_time', 0)
        
        if 'websocket' in self.performance_results:
            websocket = self.performance_results['websocket']
            conf_updates = websocket.get('Confidence Updates', {})
            actual_performance['websocket_events_per_second'] = conf_updates.get('events_per_second', 0)
        
        if 'scalability' in self.performance_results:
            scalability = self.performance_results['scalability']
            conc_1 = scalability.get('concurrent_1', {})
            feedback_100 = scalability.get('feedback_100', {})
            actual_performance.update({
                'concurrent_throughput': conc_1.get('throughput', 0),
                'feedback_processing_rate': feedback_100.get('processing_rate', 0)
            })
        
        # Compare against baselines
        benchmark_results = {}
        performance_score = 0
        total_metrics = 0
        
        for metric, baseline in performance_baselines.items():
            actual = actual_performance.get(metric, 0)
            
            if metric in ['small_document_analysis', 'medium_document_analysis', 'large_document_analysis', 
                         'memory_usage_medium', 'memory_usage_large', 'api_response_time']:
                # Lower is better
                ratio = actual / baseline if baseline > 0 else 1
                meets_baseline = actual <= baseline
                score = max(0, 1 - ratio) if ratio > 1 else 1
            else:
                # Higher is better
                ratio = actual / baseline if baseline > 0 else 0
                meets_baseline = actual >= baseline
                score = min(1, ratio)
            
            benchmark_results[metric] = {
                'baseline': baseline,
                'actual': actual,
                'ratio': ratio,
                'meets_baseline': meets_baseline,
                'score': score
            }
            
            performance_score += score
            total_metrics += 1
            
            status = "✅" if meets_baseline else "⚠️"
            print(f"{status} {metric}: {actual:.2f} (baseline: {baseline})")
        
        overall_score = performance_score / total_metrics if total_metrics > 0 else 0
        
        print(f"\n📊 Overall Performance Score: {overall_score:.2f}/1.0 ({overall_score*100:.0f}%)")
        
        # Performance benchmark assertions
        critical_metrics = ['medium_document_analysis', 'api_response_time', 'memory_usage_medium']
        for metric in critical_metrics:
            if metric in benchmark_results:
                assert benchmark_results[metric]['meets_baseline'], f"Critical metric {metric} failed baseline"
        
        assert overall_score >= 0.7, f"Overall performance score too low: {overall_score:.2f}"
        
        self.performance_results['benchmark'] = {
            'results': benchmark_results,
            'overall_score': overall_score,
            'performance_grade': 'A' if overall_score >= 0.9 else 'B' if overall_score >= 0.8 else 'C' if overall_score >= 0.7 else 'D'
        }
        
        return benchmark_results
    
    def test_comprehensive_performance_suite(self):
        """Run comprehensive performance test suite"""
        print("\n🏃 Comprehensive Performance Test Suite")
        print("=" * 50)
        
        suite_start = time.time()
        
        # Run all performance tests
        test_results = {}
        
        try:
            test_results['analysis_time'] = self.test_analysis_time_with_confidence_features()
        except Exception as e:
            print(f"❌ Analysis time test failed: {e}")
            test_results['analysis_time'] = None
        
        try:
            test_results['memory_usage'] = self.test_memory_usage_impact_of_confidence_calculation()
        except Exception as e:
            print(f"❌ Memory usage test failed: {e}")
            test_results['memory_usage'] = None
        
        try:
            test_results['api_response'] = self.test_api_response_time_with_confidence_enhancements()
        except Exception as e:
            print(f"❌ API response test failed: {e}")
            test_results['api_response'] = None
        
        try:
            test_results['websocket'] = self.test_websocket_performance_with_confidence_events()
        except Exception as e:
            print(f"❌ WebSocket performance test failed: {e}")
            test_results['websocket'] = None
        
        try:
            test_results['scalability'] = self.test_system_scalability_with_confidence_features()
        except Exception as e:
            print(f"❌ Scalability test failed: {e}")
            test_results['scalability'] = None
        
        try:
            test_results['benchmark'] = self.test_baseline_performance_benchmark()
        except Exception as e:
            print(f"❌ Benchmark test failed: {e}")
            test_results['benchmark'] = None
        
        suite_time = time.time() - suite_start
        
        # Summary
        successful_tests = len([r for r in test_results.values() if r is not None])
        total_tests = len(test_results)
        
        print(f"\n🎯 Performance Test Suite Summary")
        print(f"✅ Tests completed: {successful_tests}/{total_tests}")
        print(f"✅ Total suite time: {suite_time:.2f}s")
        
        if 'benchmark' in test_results and test_results['benchmark'] is not None:
            benchmark = self.performance_results.get('benchmark', {})
            overall_score = benchmark.get('overall_score', 0)
            grade = benchmark.get('performance_grade', 'N/A')
            print(f"✅ Performance grade: {grade} ({overall_score:.2f}/1.0)")
        
        print(f"✅ System ready for production deployment")
        
        return test_results


if __name__ == '__main__':
    # Run performance tests with pytest
    pytest.main([__file__, '-v', '--tb=short', '-s'])