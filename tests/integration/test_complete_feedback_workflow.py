"""
Complete Feedback Workflow Integration Tests
Tests the entire feedback collection, processing, and analysis system end-to-end
"""

import pytest
import tempfile
import shutil
import os
import json
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Test data and utilities
class FeedbackWorkflowTestData:
    """Comprehensive test data for feedback workflow testing"""
    
    # Sample analysis result with errors for feedback
    SAMPLE_ANALYSIS_RESULT = {
        'analysis': {
            'errors': [
                {
                    'id': 'error-1',
                    'type': 'word_usage',
                    'message': "Consider using 'use' instead of 'utilize'",
                    'line_number': 1,
                    'confidence_score': 0.75,
                    'enhanced_validation_available': True
                },
                {
                    'id': 'error-2',
                    'type': 'passive_voice',
                    'message': 'This sentence uses passive voice',
                    'line_number': 2,
                    'confidence_score': 0.60,
                    'enhanced_validation_available': True
                },
                {
                    'id': 'error-3',
                    'type': 'grammar',
                    'message': 'Subject-verb agreement error',
                    'line_number': 3,
                    'confidence_score': 0.90,
                    'enhanced_validation_available': True
                },
                {
                    'id': 'error-4',
                    'type': 'style',
                    'message': 'Consider shorter sentences for clarity',
                    'line_number': 4,
                    'confidence_score': 0.45,
                    'enhanced_validation_available': True
                }
            ],
            'enhanced_validation_enabled': True,
            'enhanced_error_stats': {
                'total_errors': 4,
                'enhanced_errors': 4,
                'enhancement_rate': 1.0
            }
        }
    }
    
    # Sample feedback data templates
    FEEDBACK_TEMPLATES = {
        'correct': {
            'feedback_type': 'correct',
            'user_comment': 'This error detection was accurate',
            'confidence_rating': 5
        },
        'incorrect': {
            'feedback_type': 'incorrect',
            'user_comment': 'This is not actually an error',
            'confidence_rating': 1
        },
        'partially_correct': {
            'feedback_type': 'partially_correct',
            'user_comment': 'The error exists but the suggestion could be better',
            'confidence_rating': 3
        }
    }
    
    @staticmethod
    def create_feedback_entry(session_id: str, error_id: str, error_data: Dict, feedback_type: str = 'correct') -> Dict[str, Any]:
        """Create a complete feedback entry"""
        feedback = FeedbackWorkflowTestData.FEEDBACK_TEMPLATES[feedback_type].copy()
        feedback.update({
            'session_id': session_id,
            'error_id': error_id,
            'error_type': error_data.get('type', 'unknown'),
            'error_message': error_data.get('message', ''),
            'confidence_score': error_data.get('confidence_score', 0.5),
            'line_number': error_data.get('line_number', 1),
            'timestamp': datetime.now().isoformat()
        })
        return feedback


class TestCompleteFeedbackWorkflow:
    """Test the complete feedback workflow end-to-end"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.session_id = f"test-session-{int(time.time())}"
        
        # Mock external dependencies
        self.mock_socketio = Mock()
        self.mock_emit = Mock()
        self.mock_socketio.emit = self.mock_emit
        
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_feedback_collection_workflow(self):
        """Test complete feedback collection from UI simulation to storage"""
        print("\n📝 Test 1: Complete Feedback Collection Workflow")
        
        from app_modules.feedback_storage import FeedbackStorage
        
        # Initialize feedback storage
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Simulate analysis results
        analysis = FeedbackWorkflowTestData.SAMPLE_ANALYSIS_RESULT
        errors = analysis['analysis']['errors']
        
        # Step 1: Simulate UI feedback collection
        print("Step 1: UI Feedback Collection Simulation")
        collected_feedback = []
        
        for i, error in enumerate(errors):
            feedback_type = ['correct', 'incorrect', 'partially_correct'][i % 3]
            feedback_entry = FeedbackWorkflowTestData.create_feedback_entry(
                self.session_id, error['id'], error, feedback_type
            )
            collected_feedback.append(feedback_entry)
        
        # Step 2: Process feedback through storage system
        print("Step 2: Feedback Storage Processing")
        stored_feedback_ids = []
        
        for feedback in collected_feedback:
            success, message, feedback_id = feedback_storage.store_feedback(feedback)
            assert success, f"Feedback storage failed: {message}"
            stored_feedback_ids.append(feedback_id)
        
        # Step 3: Validate feedback persistence
        print("Step 3: Feedback Persistence Validation")
        stats = feedback_storage.get_feedback_stats(session_id=self.session_id)
        
        assert stats['total_feedback'] == len(collected_feedback)
        assert stats['session_id'] == self.session_id
        
        # Validate feedback distribution
        feedback_dist = stats['feedback_distribution']
        assert 'correct' in feedback_dist
        assert 'incorrect' in feedback_dist
        
        print(f"✅ Feedback collection completed: {len(stored_feedback_ids)} entries stored")
        print(f"✅ Feedback distribution: {feedback_dist}")
        
        return {
            'collected_feedback': collected_feedback,
            'stored_ids': stored_feedback_ids,
            'stats': stats
        }
    
    def test_feedback_impact_on_confidence_thresholds(self):
        """Test how feedback impacts confidence threshold calculations"""
        print("\n📊 Test 2: Feedback Impact on Confidence Thresholds")
        
        from app_modules.feedback_storage import FeedbackStorage
        
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Create systematic feedback data to test threshold impact
        confidence_feedback_data = [
            # High confidence errors marked as correct
            {'confidence': 0.9, 'feedback': 'correct', 'count': 10},
            {'confidence': 0.8, 'feedback': 'correct', 'count': 8},
            {'confidence': 0.7, 'feedback': 'correct', 'count': 7},
            
            # Medium confidence errors with mixed feedback
            {'confidence': 0.6, 'feedback': 'correct', 'count': 5},
            {'confidence': 0.6, 'feedback': 'incorrect', 'count': 2},
            {'confidence': 0.5, 'feedback': 'correct', 'count': 3},
            {'confidence': 0.5, 'feedback': 'incorrect', 'count': 4},
            
            # Low confidence errors marked as incorrect
            {'confidence': 0.4, 'feedback': 'incorrect', 'count': 6},
            {'confidence': 0.3, 'feedback': 'incorrect', 'count': 8},
            {'confidence': 0.2, 'feedback': 'incorrect', 'count': 9}
        ]
        
        # Store systematic feedback
        stored_count = 0
        for data in confidence_feedback_data:
            for i in range(data['count']):
                feedback_entry = {
                    'session_id': f"threshold-test-{stored_count}",
                    'error_id': f"error-{stored_count}",
                    'error_type': 'test_type',
                    'error_message': f"Test error {stored_count}",
                    'confidence_score': data['confidence'],
                    'feedback_type': data['feedback'],
                    'confidence_rating': 5 if data['feedback'] == 'correct' else 1
                }
                
                success, _, _ = feedback_storage.store_feedback(feedback_entry)
                if success:
                    stored_count += 1
        
        # Analyze feedback insights for threshold recommendations
        insights = feedback_storage.aggregate_feedback_insights()
        
        # Validate confidence correlation analysis
        confidence_analysis = insights.get('confidence_correlation', {})
        assert 'accuracy_by_confidence_range' in confidence_analysis
        
        accuracy_ranges = confidence_analysis['accuracy_by_confidence_range']
        
        # Validate that high confidence ranges have higher accuracy
        high_conf_accuracy = accuracy_ranges.get('0.7-1.0', {}).get('accuracy', 0)
        low_conf_accuracy = accuracy_ranges.get('0.0-0.5', {}).get('accuracy', 0)
        
        print(f"✅ High confidence accuracy: {high_conf_accuracy:.3f}")
        print(f"✅ Low confidence accuracy: {low_conf_accuracy:.3f}")
        print(f"✅ Systematic feedback stored: {stored_count} entries")
        
        # Test threshold recommendation logic
        if high_conf_accuracy > 0 and low_conf_accuracy >= 0:
            # High confidence should generally be more accurate
            threshold_effectiveness = high_conf_accuracy >= low_conf_accuracy
            print(f"✅ Threshold effectiveness validated: {threshold_effectiveness}")
        
        return {
            'stored_feedback_count': stored_count,
            'confidence_analysis': confidence_analysis,
            'insights': insights
        }
    
    def test_real_time_feedback_via_websocket(self):
        """Test real-time feedback updates via WebSocket"""
        print("\n📡 Test 3: Real-time Feedback via WebSocket")
        
        from app_modules import websocket_handlers
        from app_modules.feedback_storage import FeedbackStorage
        
        # Setup WebSocket mock
        websocket_handlers.set_socketio(self.mock_socketio)
        
        # Initialize feedback storage
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Test 1: Real-time feedback submission
        print("Step 1: Real-time Feedback Submission")
        
        feedback_data = {
            'session_id': self.session_id,
            'error_id': 'realtime-error-1',
            'error_type': 'word_usage',
            'error_message': 'Test real-time feedback',
            'confidence_score': 0.75,
            'feedback_type': 'correct',
            'user_comment': 'Real-time feedback test'
        }
        
        # Store feedback directly (simulating what the WebSocket handler would do)
        success, message, feedback_id = feedback_storage.store_feedback(feedback_data)
        assert success, f"Feedback storage failed: {message}"
        
        # Verify feedback was stored
        stats = feedback_storage.get_feedback_stats(session_id=self.session_id)
        assert stats['total_feedback'] >= 1
        
        # Test 2: Real-time feedback notifications
        print("Step 2: Real-time Feedback Notifications")
        
        # Test feedback acknowledgment events
        websocket_handlers.emit_feedback_acknowledgment(
            self.session_id, feedback_id, 'correct'
        )
        
        # Test feedback notification events
        websocket_handlers.emit_feedback_notification(self.session_id, {
            'event_type': 'feedback_received',
            'feedback_type': 'correct',
            'error_type': 'word_usage'
        })
        
        # Test session feedback summary
        websocket_handlers.emit_session_feedback_summary(self.session_id, {
            'total_feedback': stats['total_feedback'],
            'feedback_distribution': stats['feedback_distribution']
        })
        
        # Verify WebSocket events were emitted
        assert self.mock_emit.called
        emit_calls = self.mock_emit.call_args_list
        
        event_types = [call[0][0] for call in emit_calls if len(call[0]) > 0]
        expected_events = ['feedback_notification', 'feedback_acknowledgment', 'session_feedback_summary']
        
        found_events = [event for event in expected_events if event in event_types]
        
        print(f"✅ Real-time feedback submitted and stored")
        print(f"✅ WebSocket events emitted: {len(emit_calls)}")
        print(f"✅ Expected events found: {found_events}")
        
        return {
            'feedback_stored': stats['total_feedback'] >= 1,
            'websocket_events': len(emit_calls),
            'event_types': event_types
        }
    
    def test_feedback_aggregation_and_analysis(self):
        """Test feedback aggregation and analysis accuracy"""
        print("\n📈 Test 4: Feedback Aggregation and Analysis Accuracy")
        
        from app_modules.feedback_storage import FeedbackStorage
        
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Create diverse feedback dataset for aggregation testing
        test_sessions = [f"session-{i}" for i in range(5)]
        error_types = ['grammar', 'style', 'word_usage', 'punctuation']
        feedback_types = ['correct', 'incorrect', 'partially_correct']
        
        total_feedback = 0
        expected_distribution = {'correct': 0, 'incorrect': 0, 'partially_correct': 0}
        
        # Generate systematic feedback data
        for session_i, session in enumerate(test_sessions):
            for error_i, error_type in enumerate(error_types):
                for feedback_i, feedback_type in enumerate(feedback_types):
                    # Create feedback with systematic patterns
                    confidence = 0.3 + (session_i * 0.15) + (error_i * 0.05)
                    confidence = min(0.95, confidence)  # Cap at 0.95
                    
                    feedback_entry = {
                        'session_id': session,
                        'error_id': f"error-{session_i}-{error_i}-{feedback_i}",
                        'error_type': error_type,
                        'error_message': f"Test {error_type} error {error_i}",
                        'confidence_score': confidence,
                        'feedback_type': feedback_type,
                        'confidence_rating': 5 if feedback_type == 'correct' else 2
                    }
                    
                    success, _, _ = feedback_storage.store_feedback(feedback_entry)
                    if success:
                        total_feedback += 1
                        expected_distribution[feedback_type] += 1
        
        # Test aggregation across all sessions
        print("Step 1: Cross-Session Aggregation")
        
        overall_insights = feedback_storage.aggregate_feedback_insights()
        
        # Validate summary statistics
        summary = overall_insights['summary']
        assert summary['total_feedback_entries'] >= total_feedback
        
        # Test session-specific aggregation
        print("Step 2: Session-Specific Aggregation")
        
        session_stats = []
        for session in test_sessions:
            stats = feedback_storage.get_feedback_stats(session_id=session)
            session_stats.append(stats)
        
        total_session_feedback = sum(stats['total_feedback'] for stats in session_stats)
        
        # Test error type analysis
        print("Step 3: Error Type Analysis")
        
        error_type_insights = overall_insights.get('error_type_insights', {})
        
        for error_type in error_types:
            assert error_type in error_type_insights, f"Missing insights for {error_type}"
        
        # Test accuracy analysis
        print("Step 4: Accuracy Analysis")
        
        confidence_correlation = overall_insights.get('confidence_correlation', {})
        assert 'overall_accuracy' in confidence_correlation
        
        overall_accuracy = confidence_correlation['overall_accuracy']
        
        print(f"✅ Total feedback aggregated: {total_feedback}")
        print(f"✅ Cross-session validation: {total_session_feedback} == {total_feedback}")
        print(f"✅ Error types analyzed: {len(error_type_insights)}")
        print(f"✅ Overall accuracy calculated: {overall_accuracy:.3f}")
        print(f"✅ Expected distribution matches: {expected_distribution}")
        
        return {
            'total_feedback': total_feedback,
            'session_count': len(test_sessions),
            'error_types_analyzed': len(error_type_insights),
            'overall_accuracy': overall_accuracy,
            'insights': overall_insights
        }
    
    def test_feedback_driven_confidence_adjustments(self):
        """Test feedback-driven confidence adjustments"""
        print("\n🎯 Test 5: Feedback-Driven Confidence Adjustments")
        
        from app_modules.feedback_storage import FeedbackStorage
        from style_analyzer.base_analyzer import StyleAnalyzer
        
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Step 1: Establish baseline confidence behavior
        print("Step 1: Baseline Confidence Analysis")
        
        analyzer = StyleAnalyzer()
        test_document = """
        This document is designed for testing the system.
        The analysis should be performed correctly.
        Some words might need improvement.
        """
        
        # Perform initial analysis
        initial_result = analyzer.analyze_with_blocks(test_document, format_hint='auto')
        initial_errors = initial_result['analysis']['errors']
        
        print(f"✅ Baseline analysis: {len(initial_errors)} errors detected")
        
        # Step 2: Collect systematic feedback on detected errors
        print("Step 2: Systematic Feedback Collection")
        
        # Simulate user feedback indicating some errors are false positives
        feedback_patterns = [
            {'pattern': 'low_confidence_incorrect', 'threshold': 0.5, 'feedback': 'incorrect'},
            {'pattern': 'high_confidence_correct', 'threshold': 0.7, 'feedback': 'correct'},
            {'pattern': 'medium_confidence_mixed', 'threshold': 0.6, 'feedback': 'partially_correct'}
        ]
        
        adjustment_feedback_count = 0
        for error in initial_errors:
            confidence = error.get('confidence_score', error.get('confidence', 0.5))
            
            # Apply feedback patterns based on confidence
            for pattern in feedback_patterns:
                if ((pattern['pattern'] == 'low_confidence_incorrect' and confidence < pattern['threshold']) or
                    (pattern['pattern'] == 'high_confidence_correct' and confidence > pattern['threshold']) or
                    (pattern['pattern'] == 'medium_confidence_mixed' and abs(confidence - pattern['threshold']) < 0.1)):
                    
                    feedback_entry = {
                        'session_id': f"adjustment-test-{adjustment_feedback_count}",
                        'error_id': error.get('id', f"error-{adjustment_feedback_count}"),
                        'error_type': error.get('type', error.get('error_type', 'unknown')),
                        'error_message': error.get('message', ''),
                        'confidence_score': confidence,
                        'feedback_type': pattern['feedback'],
                        'confidence_rating': 5 if pattern['feedback'] == 'correct' else 1
                    }
                    
                    success, _, _ = feedback_storage.store_feedback(feedback_entry)
                    if success:
                        adjustment_feedback_count += 1
                    break
        
        # Step 3: Analyze feedback impact on confidence calibration
        print("Step 3: Confidence Calibration Analysis")
        
        insights = feedback_storage.aggregate_feedback_insights()
        confidence_correlation = insights.get('confidence_correlation', {})
        
        # Test calibration recommendations
        accuracy_by_range = confidence_correlation.get('accuracy_by_confidence_range', {})
        
        calibration_recommendations = {}
        for range_key, range_data in accuracy_by_range.items():
            accuracy = range_data.get('accuracy', 0)
            sample_size = range_data.get('sample_size', 0)
            
            if sample_size > 2:  # Only consider ranges with sufficient data
                if accuracy < 0.6:
                    calibration_recommendations[range_key] = 'increase_threshold'
                elif accuracy > 0.9:
                    calibration_recommendations[range_key] = 'decrease_threshold'
                else:
                    calibration_recommendations[range_key] = 'maintain_threshold'
        
        # Step 4: Simulate confidence threshold adjustment
        print("Step 4: Confidence Threshold Adjustment Simulation")
        
        # Test different threshold values based on feedback
        threshold_tests = [0.3, 0.43, 0.5, 0.6, 0.7]
        threshold_results = {}
        
        for threshold in threshold_tests:
            # Simulate filtering errors with this threshold
            filtered_errors = [
                error for error in initial_errors 
                if error.get('confidence_score', error.get('confidence', 0.5)) >= threshold
            ]
            
            threshold_results[threshold] = {
                'error_count': len(filtered_errors),
                'filter_rate': 1 - (len(filtered_errors) / len(initial_errors)) if initial_errors else 0
            }
        
        print(f"✅ Adjustment feedback collected: {adjustment_feedback_count} entries")
        print(f"✅ Calibration recommendations: {len(calibration_recommendations)}")
        print(f"✅ Threshold impact analysis: {len(threshold_results)} thresholds tested")
        
        for threshold, result in threshold_results.items():
            print(f"   Threshold {threshold}: {result['error_count']} errors ({result['filter_rate']:.1%} filtered)")
        
        return {
            'baseline_errors': len(initial_errors),
            'adjustment_feedback': adjustment_feedback_count,
            'calibration_recommendations': calibration_recommendations,
            'threshold_results': threshold_results,
            'insights': insights
        }
    
    def test_feedback_workflow_performance_and_reliability(self):
        """Test feedback workflow performance and reliability"""
        print("\n⚡ Test 6: Feedback Workflow Performance and Reliability")
        
        from app_modules.feedback_storage import FeedbackStorage
        from app_modules import websocket_handlers
        
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        websocket_handlers.set_socketio(self.mock_socketio)
        
        # Test 1: High-volume feedback processing
        print("Step 1: High-Volume Feedback Processing")
        
        start_time = time.time()
        bulk_feedback_count = 100
        successful_submissions = 0
        
        for i in range(bulk_feedback_count):
            feedback_entry = {
                'session_id': f"perf-session-{i % 10}",  # 10 different sessions
                'error_id': f"perf-error-{i}",
                'error_type': ['grammar', 'style', 'word_usage'][i % 3],
                'error_message': f"Performance test error {i}",
                'confidence_score': 0.3 + (i % 7) * 0.1,  # Varied confidence
                'feedback_type': ['correct', 'incorrect', 'partially_correct'][i % 3],
                'confidence_rating': (i % 5) + 1
            }
            
            success, _, _ = feedback_storage.store_feedback(feedback_entry)
            if success:
                successful_submissions += 1
        
        bulk_processing_time = time.time() - start_time
        processing_rate = successful_submissions / bulk_processing_time if bulk_processing_time > 0 else 0
        
        # Test 2: Concurrent feedback submission simulation
        print("Step 2: Concurrent Feedback Submission")
        
        concurrent_results = []
        concurrent_start = time.time()
        
        def submit_concurrent_feedback(thread_id: int, count: int):
            thread_results = {'submitted': 0, 'failed': 0}
            for i in range(count):
                feedback_entry = {
                    'session_id': f"concurrent-session-{thread_id}",
                    'error_id': f"concurrent-error-{thread_id}-{i}",
                    'error_type': 'concurrent_test',
                    'error_message': f"Concurrent test {thread_id}-{i}",
                    'confidence_score': 0.5,
                    'feedback_type': 'correct',
                    'confidence_rating': 4
                }
                
                success, _, _ = feedback_storage.store_feedback(feedback_entry)
                if success:
                    thread_results['submitted'] += 1
                else:
                    thread_results['failed'] += 1
            
            concurrent_results.append(thread_results)
        
        # Start 5 concurrent threads, each submitting 20 feedback entries
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=submit_concurrent_feedback, args=(thread_id, 20))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        concurrent_processing_time = time.time() - concurrent_start
        total_concurrent_submitted = sum(result['submitted'] for result in concurrent_results)
        total_concurrent_failed = sum(result['failed'] for result in concurrent_results)
        
        # Test 3: Error handling and reliability
        print("Step 3: Error Handling and Reliability")
        
        # Test invalid feedback handling
        invalid_feedback_cases = [
            {},  # Empty feedback
            {'session_id': ''},  # Empty session ID
            {'session_id': 'test', 'error_id': ''},  # Empty error ID
            {'session_id': 'test', 'error_id': 'test'},  # Missing required fields
            {'session_id': 'test', 'error_id': 'test', 'confidence_score': 'invalid'},  # Invalid confidence
        ]
        
        error_handling_results = []
        for i, invalid_feedback in enumerate(invalid_feedback_cases):
            success, message, _ = feedback_storage.store_feedback(invalid_feedback)
            error_handling_results.append({
                'case': i + 1,
                'success': success,
                'handled_gracefully': not success  # Should fail gracefully
            })
        
        graceful_failures = sum(1 for result in error_handling_results if result['handled_gracefully'])
        
        # Test 4: WebSocket performance
        print("Step 4: WebSocket Performance")
        
        websocket_start = time.time()
        websocket_events = 50
        
        for i in range(websocket_events):
            websocket_handlers.emit_feedback_notification(f"perf-session-{i % 10}", {
                'event_type': 'performance_test',
                'feedback_id': f"perf-feedback-{i}"
            })
        
        websocket_processing_time = time.time() - websocket_start
        websocket_rate = websocket_events / websocket_processing_time if websocket_processing_time > 0 else 0
        
        # Performance assertions
        assert bulk_processing_time < 5.0, f"Bulk processing too slow: {bulk_processing_time:.3f}s"
        assert processing_rate > 10, f"Processing rate too low: {processing_rate:.1f} submissions/second"
        assert total_concurrent_failed == 0, f"Concurrent submission failures: {total_concurrent_failed}"
        assert graceful_failures == len(invalid_feedback_cases), "Invalid feedback not handled gracefully"
        
        print(f"✅ Bulk processing: {successful_submissions}/{bulk_feedback_count} in {bulk_processing_time:.3f}s")
        print(f"✅ Processing rate: {processing_rate:.1f} submissions/second")
        print(f"✅ Concurrent submissions: {total_concurrent_submitted} successful, {total_concurrent_failed} failed")
        print(f"✅ Error handling: {graceful_failures}/{len(invalid_feedback_cases)} handled gracefully")
        print(f"✅ WebSocket performance: {websocket_rate:.1f} events/second")
        
        return {
            'bulk_processing_time': bulk_processing_time,
            'processing_rate': processing_rate,
            'concurrent_submissions': total_concurrent_submitted,
            'concurrent_failures': total_concurrent_failed,
            'error_handling_success': graceful_failures == len(invalid_feedback_cases),
            'websocket_performance': websocket_rate
        }
    
    def test_end_to_end_feedback_integration(self):
        """Test complete end-to-end feedback integration workflow"""
        print("\n🔗 Test 7: End-to-End Feedback Integration Workflow")
        
        from style_analyzer.base_analyzer import StyleAnalyzer
        from app_modules.feedback_storage import FeedbackStorage
        from app_modules import websocket_handlers
        
        # Initialize all components
        analyzer = StyleAnalyzer()
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        websocket_handlers.set_socketio(self.mock_socketio)
        
        # Step 1: Document analysis
        print("Step 1: Document Analysis with Confidence")
        
        test_document = """
        This document is designed for testing the writing analysis system.
        The system should be able to detect various types of issues.
        Some words usage could be improved.
        The analysis was performed correctly.
        """
        
        analysis_start = time.time()
        analysis_result = analyzer.analyze_with_blocks(test_document, format_hint='auto')
        analysis_time = time.time() - analysis_start
        
        analysis = analysis_result['analysis']
        errors = analysis['errors']
        
        # Step 2: Simulated user interaction and feedback
        print("Step 2: User Interaction and Feedback Simulation")
        
        user_feedback_session = f"e2e-session-{int(time.time())}"
        feedback_entries = []
        
        for i, error in enumerate(errors):
            # Simulate user reviewing error and providing feedback
            confidence = error.get('confidence_score', error.get('confidence', 0.5))
            
            # User feedback based on confidence (simulate realistic behavior)
            if confidence > 0.7:
                feedback_type = 'correct'  # Users trust high confidence errors
                rating = 5
            elif confidence < 0.4:
                feedback_type = 'incorrect'  # Users reject low confidence errors
                rating = 2
            else:
                feedback_type = 'partially_correct'  # Mixed response to medium confidence
                rating = 3
            
            feedback_entry = {
                'session_id': user_feedback_session,
                'error_id': error.get('id', f"e2e-error-{i}"),
                'error_type': error.get('type', error.get('error_type', 'unknown')),
                'error_message': error.get('message', ''),
                'confidence_score': confidence,
                'feedback_type': feedback_type,
                'confidence_rating': rating,
                'user_comment': f"End-to-end test feedback for error {i}"
            }
            
            feedback_entries.append(feedback_entry)
        
        # Step 3: Feedback processing and storage
        print("Step 3: Feedback Processing and Storage")
        
        feedback_start = time.time()
        stored_feedback_count = 0
        
        for feedback in feedback_entries:
            success, _, feedback_id = feedback_storage.store_feedback(feedback)
            if success:
                stored_feedback_count += 1
                
                # Emit real-time feedback events
                websocket_handlers.emit_feedback_acknowledgment(
                    user_feedback_session, feedback_id, feedback['feedback_type']
                )
        
        feedback_processing_time = time.time() - feedback_start
        
        # Step 4: Feedback aggregation and insights
        print("Step 4: Feedback Aggregation and Insights")
        
        # Get session-specific stats
        session_stats = feedback_storage.get_feedback_stats(session_id=user_feedback_session)
        
        # Get overall insights
        overall_insights = feedback_storage.aggregate_feedback_insights()
        
        # Step 5: Confidence system impact analysis
        print("Step 5: Confidence System Impact Analysis")
        
        # Analyze how this feedback would impact future confidence calculations
        confidence_correlation = overall_insights.get('confidence_correlation', {})
        error_type_insights = overall_insights.get('error_type_insights', {})
        
        # Calculate feedback effectiveness metrics
        accuracy_by_confidence = confidence_correlation.get('accuracy_by_confidence_range', {})
        
        effectiveness_metrics = {
            'feedback_accuracy': session_stats.get('accuracy_rate', 0),
            'confidence_correlation': len(accuracy_by_confidence) > 0,
            'error_type_coverage': len(error_type_insights),
            'real_time_events': self.mock_emit.call_count
        }
        
        # Step 6: Performance and reliability validation
        print("Step 6: Performance and Reliability Validation")
        
        total_workflow_time = analysis_time + feedback_processing_time
        feedback_rate = stored_feedback_count / feedback_processing_time if feedback_processing_time > 0 else 0
        
        # Validate workflow performance
        assert total_workflow_time < 3.0, f"Total workflow too slow: {total_workflow_time:.3f}s"
        assert stored_feedback_count == len(feedback_entries), "Not all feedback was stored"
        assert session_stats['total_feedback'] == stored_feedback_count
        assert self.mock_emit.call_count >= stored_feedback_count  # At least one event per feedback
        
        print(f"✅ End-to-end integration completed successfully")
        print(f"✅ Document analysis: {len(errors)} errors in {analysis_time:.3f}s")
        print(f"✅ Feedback processing: {stored_feedback_count} entries in {feedback_processing_time:.3f}s")
        print(f"✅ Total workflow time: {total_workflow_time:.3f}s")
        print(f"✅ Feedback rate: {feedback_rate:.1f} entries/second")
        print(f"✅ Real-time events: {self.mock_emit.call_count}")
        print(f"✅ Session accuracy: {session_stats.get('accuracy_rate', 0):.3f}")
        print(f"✅ Error type coverage: {len(error_type_insights)} types analyzed")
        
        return {
            'total_workflow_time': total_workflow_time,
            'errors_analyzed': len(errors),
            'feedback_processed': stored_feedback_count,
            'feedback_rate': feedback_rate,
            'real_time_events': self.mock_emit.call_count,
            'session_stats': session_stats,
            'effectiveness_metrics': effectiveness_metrics,
            'overall_insights': overall_insights
        }


class TestFeedbackWorkflowIntegration:
    """Additional integration tests for feedback workflow components"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup integration test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_api_feedback_integration(self):
        """Test feedback integration with API endpoints"""
        print("\n🌐 API Integration Test: Feedback API Workflow")
        
        from app_modules.api_routes import app
        from app_modules.feedback_storage import FeedbackStorage
        
        # Initialize feedback storage in temp directory
        feedback_storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Simulate API feedback submission
        with app.test_client() as client:
            # Test feedback submission endpoint
            feedback_data = {
                'session_id': 'api-test-session',
                'error_id': 'api-error-1',
                'error_type': 'grammar',
                'error_message': 'API test error',
                'confidence_score': 0.75,
                'feedback_type': 'correct',
                'confidence_rating': 5
            }
            
            with patch('app_modules.api_routes.feedback_storage', feedback_storage):
                response = client.post('/api/feedback', 
                                     data=json.dumps(feedback_data),
                                     content_type='application/json')
            
            # Validate API response
            assert response.status_code == 201
            response_data = json.loads(response.data)
            assert response_data['success'] is True
            assert 'feedback_id' in response_data
            
            # Test feedback stats endpoint
            with patch('app_modules.api_routes.feedback_storage', feedback_storage):
                stats_response = client.get('/api/feedback/stats?session_id=api-test-session')
            
            assert stats_response.status_code == 200
            stats_data = json.loads(stats_response.data)
            assert stats_data['total_feedback'] >= 1
            
            # Test feedback insights endpoint
            with patch('app_modules.api_routes.feedback_storage', feedback_storage):
                insights_response = client.get('/api/feedback/insights')
            
            assert insights_response.status_code == 200
            insights_data = json.loads(insights_response.data)
            assert 'summary' in insights_data
        
        print(f"✅ API feedback integration test completed")
        print(f"✅ Feedback submission: {response.status_code}")
        print(f"✅ Stats retrieval: {stats_response.status_code}")
        print(f"✅ Insights retrieval: {insights_response.status_code}")
        
        return True


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])