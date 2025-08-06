"""
Comprehensive Test Suite for Enhanced WebSocket Handlers
Tests confidence events, feedback notifications, and validation progress
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Test data and utilities
class WebSocketTestData:
    """Test data for WebSocket testing"""
    
    SAMPLE_SESSION_ID = "ws-test-session-123"
    SAMPLE_FEEDBACK_DATA = {
        "session_id": "ws-test-session-123",
        "error_id": "ws-error-456",
        "error_type": "word_usage",
        "error_message": "Consider better terminology",
        "feedback_type": "correct",
        "confidence_score": 0.8
    }
    
    SAMPLE_CONFIDENCE_DATA = {
        "event_type": "confidence_calculation",
        "error_count": 5,
        "high_confidence_count": 3,
        "average_confidence": 0.75
    }
    
    SAMPLE_VALIDATION_PROGRESS = {
        "total_errors": 10,
        "validated_errors": 7,
        "validation_rate": 0.7,
        "current_stage": "morphological_validation"
    }
    
    SAMPLE_INSIGHTS_DATA = {
        "accuracy_rate": 0.85,
        "confidence_distribution": {
            "high": 60,
            "medium": 30,
            "low": 10
        },
        "error_type_accuracy": {
            "grammar": 0.9,
            "style": 0.8,
            "word_usage": 0.75
        }
    }


class TestWebSocketHandlers:
    """Test the enhanced WebSocket handlers"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock SocketIO instance
        self.mock_socketio = Mock()
        self.mock_emit = Mock()
        self.mock_socketio.emit = self.mock_emit
        
        # Import and setup the handlers with mock
        from app_modules import websocket_handlers
        websocket_handlers.set_socketio(self.mock_socketio)
        self.handlers = websocket_handlers
        
        # Clear active sessions
        self.handlers.active_sessions.clear()
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Clear active sessions
        self.handlers.active_sessions.clear()
    
    def test_emit_confidence_update(self):
        """Test confidence update emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        confidence_data = WebSocketTestData.SAMPLE_CONFIDENCE_DATA
        
        self.handlers.emit_confidence_update(session_id, confidence_data)
        
        # Verify emission was called
        assert self.mock_emit.called
        
        # Check the emitted event
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'confidence_update'
        assert event_data['session_id'] == session_id
        assert event_data['event_type'] == confidence_data['event_type']
        assert 'timestamp' in event_data
        
        # Check session was auto-added
        assert session_id in self.handlers.active_sessions
    
    def test_emit_validation_progress(self):
        """Test validation progress emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        validation_stage = "confidence_analysis"
        progress_data = WebSocketTestData.SAMPLE_VALIDATION_PROGRESS
        
        self.handlers.emit_validation_progress(session_id, validation_stage, progress_data)
        
        # Verify emission was called
        assert self.mock_emit.called
        
        # Check the emitted event
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'validation_progress'
        assert event_data['session_id'] == session_id
        assert event_data['validation_stage'] == validation_stage
        assert event_data['total_errors'] == progress_data['total_errors']
        assert 'timestamp' in event_data
    
    def test_emit_feedback_notification(self):
        """Test feedback notification emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        feedback_data = {
            "event_type": "feedback_submitted",
            "feedback_id": "fb-123",
            "feedback_type": "correct"
        }
        
        self.handlers.emit_feedback_notification(session_id, feedback_data)
        
        # Verify emission was called
        assert self.mock_emit.called
        
        # Check the emitted event
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'feedback_notification'
        assert event_data['session_id'] == session_id
        assert event_data['event_type'] == feedback_data['event_type']
        assert event_data['feedback_id'] == feedback_data['feedback_id']
        assert 'timestamp' in event_data
    
    def test_emit_confidence_insights(self):
        """Test confidence insights emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        insights_data = WebSocketTestData.SAMPLE_INSIGHTS_DATA
        
        self.handlers.emit_confidence_insights(session_id, insights_data)
        
        # Verify emission was called
        assert self.mock_emit.called
        
        # Check the emitted event
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'confidence_insights'
        assert event_data['session_id'] == session_id
        assert event_data['event_type'] == 'confidence_insights'
        assert event_data['accuracy_rate'] == insights_data['accuracy_rate']
        assert 'timestamp' in event_data
    
    def test_broadcast_confidence_threshold_change(self):
        """Test confidence threshold change broadcasting"""
        new_threshold = 0.6
        changed_by_session = "admin-session-123"
        
        self.handlers.broadcast_confidence_threshold_change(new_threshold, changed_by_session)
        
        # Verify broadcast emission was called
        assert self.mock_emit.called
        
        # Check the broadcast event
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        call_kwargs = call_args[1]
        
        assert event_name == 'confidence_update'
        assert event_data['event_type'] == 'threshold_changed'
        assert event_data['new_threshold'] == new_threshold
        assert event_data['changed_by_session'] == changed_by_session
        assert call_kwargs['broadcast'] is True
    
    def test_emit_validation_stats(self):
        """Test validation statistics emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        validation_stats = {
            "total_validations": 100,
            "successful_validations": 85,
            "validation_rate": 0.85
        }
        
        self.handlers.emit_validation_stats(session_id, validation_stats)
        
        # Should trigger confidence update with stats
        assert self.mock_emit.called
        
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'confidence_update'
        assert event_data['event_type'] == 'validation_statistics'
        assert event_data['stats'] == validation_stats
    
    def test_emit_error_confidence_breakdown(self):
        """Test error confidence breakdown emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        error_breakdown = [
            {"error_type": "grammar", "confidence": 0.9, "count": 5},
            {"error_type": "style", "confidence": 0.7, "count": 3},
            {"error_type": "word_usage", "confidence": 0.6, "count": 2}
        ]
        
        self.handlers.emit_error_confidence_breakdown(session_id, error_breakdown)
        
        assert self.mock_emit.called
        
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'confidence_update'
        assert event_data['event_type'] == 'error_confidence_breakdown'
        assert event_data['breakdown'] == error_breakdown
    
    def test_emit_feedback_acknowledgment(self):
        """Test feedback acknowledgment emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        feedback_id = "feedback-abc123"
        feedback_type = "incorrect"
        
        self.handlers.emit_feedback_acknowledgment(session_id, feedback_id, feedback_type)
        
        assert self.mock_emit.called
        
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'feedback_notification'
        assert event_data['event_type'] == 'feedback_acknowledged'
        assert event_data['feedback_id'] == feedback_id
        assert event_data['feedback_type'] == feedback_type
    
    def test_emit_session_feedback_summary(self):
        """Test session feedback summary emission"""
        session_id = WebSocketTestData.SAMPLE_SESSION_ID
        feedback_summary = {
            "total_feedback": 10,
            "feedback_distribution": {
                "correct": 7,
                "incorrect": 2,
                "partially_correct": 1
            },
            "average_confidence": 0.75
        }
        
        self.handlers.emit_session_feedback_summary(session_id, feedback_summary)
        
        assert self.mock_emit.called
        
        call_args = self.mock_emit.call_args
        event_name = call_args[0][0]
        event_data = call_args[0][1]
        
        assert event_name == 'feedback_notification'
        assert event_data['event_type'] == 'session_feedback_summary'
        assert event_data['summary'] == feedback_summary
    
    def test_websocket_without_socketio_initialized(self):
        """Test WebSocket functions when SocketIO is not initialized"""
        # Clear the socketio instance
        self.handlers._socketio = None
        
        # Test that functions handle missing SocketIO gracefully
        self.handlers.emit_confidence_update("test-session", {"test": "data"})
        self.handlers.emit_validation_progress("test-session", "test-stage", {"test": "data"})
        self.handlers.emit_feedback_notification("test-session", {"test": "data"})
        
        # Should not have called emit since SocketIO is not initialized
        assert not self.mock_emit.called
    
    def test_websocket_performance_metrics(self):
        """Test WebSocket performance metrics"""
        # Add some test sessions
        test_sessions = ["session-1", "session-2", "session-3"]
        for session in test_sessions:
            self.handlers.active_sessions.add(session)
        
        metrics = self.handlers.get_websocket_performance_metrics()
        
        assert metrics['active_sessions_count'] == 3
        assert set(metrics['active_sessions']) == set(test_sessions)
        assert metrics['websocket_initialized'] is True
        assert 'timestamp' in metrics
    
    def test_websocket_health_validation(self):
        """Test WebSocket health validation"""
        # Test healthy state
        health = self.handlers.validate_websocket_health()
        
        assert health['status'] == 'healthy'
        assert health['socketio_initialized'] is True
        assert health['can_emit'] is True
        assert 'timestamp' in health
        
        # Test unhealthy state (no SocketIO)
        self.handlers._socketio = None
        health = self.handlers.validate_websocket_health()
        
        assert health['status'] == 'unhealthy'
        assert health['socketio_initialized'] is False
        assert 'issues' in health
        assert 'SocketIO not initialized' in health['issues']
    
    def test_session_management_with_events(self):
        """Test session management integration with events"""
        session_id = "session-mgmt-test"
        
        # Verify session is not active initially
        assert not self.handlers.is_session_active(session_id)
        
        # Emit an event which should auto-add the session
        self.handlers.emit_confidence_update(session_id, {"test": "data"})
        
        # Verify session was auto-added
        assert self.handlers.is_session_active(session_id)
        assert session_id in self.handlers.active_sessions
        
        # Test session cleanup
        self.handlers.cleanup_session(session_id)
        assert not self.handlers.is_session_active(session_id)
    
    def test_multiple_concurrent_sessions(self):
        """Test handling multiple concurrent sessions"""
        session_ids = [f"concurrent-session-{i}" for i in range(5)]
        
        # Emit events to multiple sessions
        for i, session_id in enumerate(session_ids):
            confidence_data = {
                "event_type": "test_event",
                "session_index": i
            }
            self.handlers.emit_confidence_update(session_id, confidence_data)
        
        # Verify all sessions were added
        assert len(self.handlers.active_sessions) == 5
        for session_id in session_ids:
            assert session_id in self.handlers.active_sessions
        
        # Verify all emit calls were made
        assert self.mock_emit.call_count == 5


class TestWebSocketEventHandlers:
    """Test the WebSocket event handlers setup"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_socketio = Mock()
        self.mock_emit = Mock()
        
        # Mock flask_socketio functions
        self.mock_flask_emit = Mock()
        self.mock_join_room = Mock()
        self.mock_leave_room = Mock()
        
        # Store handlers for testing
        self.handler_functions = {}
    
    def test_websocket_handler_setup(self):
        """Test WebSocket handler setup"""
        from app_modules.websocket_handlers import setup_websocket_handlers
        
        # Mock socketio.on decorator
        def mock_on(event_name):
            def decorator(func):
                self.handler_functions[event_name] = func
                return func
            return decorator
        
        self.mock_socketio.on = mock_on
        
        # Setup handlers
        setup_websocket_handlers(self.mock_socketio)
        
        # Verify expected handlers were registered
        expected_events = [
            'connect', 'disconnect', 'join_session', 'leave_session', 'ping',
            'request_confidence_update', 'submit_feedback_realtime',
            'request_validation_status', 'subscribe_insights'
        ]
        
        for event in expected_events:
            assert event in self.handler_functions, f"Handler for '{event}' not registered"
    
    def test_confidence_request_handler(self):
        """Test confidence request handler"""
        from app_modules.websocket_handlers import setup_websocket_handlers
        
        # Setup handlers
        def mock_on(event_name):
            def decorator(func):
                self.handler_functions[event_name] = func
                return func
            return decorator
        
        self.mock_socketio.on = mock_on
        setup_websocket_handlers(self.mock_socketio)
        
        # Test confidence request handler
        handler = self.handler_functions['request_confidence_update']
        
        # Mock emit function
        with patch('flask_socketio.emit') as mock_emit:
            test_data = {'session_id': 'test-session-123'}
            handler(test_data)
            
            # Verify acknowledgment was emitted
            assert mock_emit.called
            call_args = mock_emit.call_args[0]
            event_name = call_args[0]
            event_data = call_args[1]
            
            assert event_name == 'confidence_request_received'
            assert event_data['session_id'] == 'test-session-123'
    
    def test_realtime_feedback_handler(self):
        """Test real-time feedback handler"""
        from app_modules.websocket_handlers import setup_websocket_handlers
        
        # Setup handlers
        def mock_on(event_name):
            def decorator(func):
                self.handler_functions[event_name] = func
                return func
            return decorator
        
        self.mock_socketio.on = mock_on
        setup_websocket_handlers(self.mock_socketio)
        
        # Test feedback handler
        handler = self.handler_functions['submit_feedback_realtime']
        
        # Mock feedback storage
        mock_storage = Mock()
        mock_storage.store_feedback.return_value = (True, "Feedback stored", "fb-123")
        
        with patch('flask_socketio.emit') as mock_emit, \
             patch('app_modules.websocket_handlers.feedback_storage', mock_storage):
            
            test_data = {
                'session_id': 'test-session-123',
                'feedback_data': WebSocketTestData.SAMPLE_FEEDBACK_DATA
            }
            handler(test_data)
            
            # Verify feedback was processed
            assert mock_storage.store_feedback.called
            
            # Verify success response was emitted
            assert mock_emit.called
            
            # Check that feedback_processed event was emitted
            emit_calls = mock_emit.call_args_list
            event_names = [call[0][0] for call in emit_calls]
            assert 'feedback_processed' in event_names
    
    def test_validation_status_handler(self):
        """Test validation status request handler"""
        from app_modules.websocket_handlers import setup_websocket_handlers
        
        # Setup handlers
        def mock_on(event_name):
            def decorator(func):
                self.handler_functions[event_name] = func
                return func
            return decorator
        
        self.mock_socketio.on = mock_on
        setup_websocket_handlers(self.mock_socketio)
        
        # Test validation status handler
        handler = self.handler_functions['request_validation_status']
        
        with patch('flask_socketio.emit') as mock_emit:
            test_data = {'session_id': 'test-session-123'}
            handler(test_data)
            
            # Verify validation status was emitted
            assert mock_emit.called
            call_args = mock_emit.call_args[0]
            event_name = call_args[0]
            event_data = call_args[1]
            
            assert event_name == 'validation_status'
            assert event_data['session_id'] == 'test-session-123'
            assert event_data['enhanced_validation_enabled'] is True
    
    def test_insights_subscription_handler(self):
        """Test insights subscription handler"""
        from app_modules.websocket_handlers import setup_websocket_handlers
        
        # Setup handlers
        def mock_on(event_name):
            def decorator(func):
                self.handler_functions[event_name] = func
                return func
            return decorator
        
        self.mock_socketio.on = mock_on
        setup_websocket_handlers(self.mock_socketio)
        
        # Test insights subscription handler
        handler = self.handler_functions['subscribe_insights']
        
        with patch('flask_socketio.emit') as mock_emit, \
             patch('flask_socketio.join_room') as mock_join_room:
            
            test_data = {
                'session_id': 'test-session-123',
                'insights_type': 'accuracy'
            }
            handler(test_data)
            
            # Verify room was joined
            assert mock_join_room.called
            join_args = mock_join_room.call_args[0]
            assert join_args[0] == 'insights_test-session-123'
            
            # Verify subscription confirmation was emitted
            assert mock_emit.called
            call_args = mock_emit.call_args[0]
            event_name = call_args[0]
            event_data = call_args[1]
            
            assert event_name == 'insights_subscribed'
            assert event_data['session_id'] == 'test-session-123'
            assert event_data['insights_type'] == 'accuracy'


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.mock_socketio = Mock()
        self.mock_emit = Mock()
        self.mock_socketio.emit = self.mock_emit
        
        from app_modules import websocket_handlers
        websocket_handlers.set_socketio(self.mock_socketio)
        self.handlers = websocket_handlers
        
        # Clear active sessions
        self.handlers.active_sessions.clear()
    
    def test_complete_confidence_workflow(self):
        """Test complete confidence update workflow"""
        session_id = "integration-test-session"
        
        # 1. Emit confidence calculation start
        self.handlers.emit_validation_progress(session_id, "confidence_calculation", {
            "status": "starting",
            "total_errors": 10
        })
        
        # 2. Emit confidence updates during processing
        self.handlers.emit_confidence_update(session_id, {
            "event_type": "confidence_progress",
            "processed_errors": 5,
            "average_confidence": 0.75
        })
        
        # 3. Emit final confidence results
        self.handlers.emit_confidence_update(session_id, {
            "event_type": "confidence_completed",
            "total_errors": 10,
            "high_confidence_errors": 7,
            "medium_confidence_errors": 2,
            "low_confidence_errors": 1
        })
        
        # Verify all emissions occurred
        assert self.mock_emit.call_count == 3
        
        # Verify session was managed properly
        assert session_id in self.handlers.active_sessions
    
    def test_complete_feedback_workflow(self):
        """Test complete feedback notification workflow"""
        session_id = "feedback-integration-test"
        
        # 1. Emit feedback submission acknowledgment
        self.handlers.emit_feedback_acknowledgment(session_id, "fb-123", "correct")
        
        # 2. Emit feedback processing notification
        self.handlers.emit_feedback_notification(session_id, {
            "event_type": "feedback_processing",
            "feedback_id": "fb-123",
            "status": "analyzing"
        })
        
        # 3. Emit session feedback summary
        self.handlers.emit_session_feedback_summary(session_id, {
            "total_feedback": 5,
            "latest_feedback_id": "fb-123"
        })
        
        # Verify all feedback events were emitted
        assert self.mock_emit.call_count == 3
        
        # Check that all were feedback_notification events
        for call in self.mock_emit.call_args_list:
            event_name = call[0][0]
            assert event_name == 'feedback_notification'
    
    def test_performance_with_multiple_events(self):
        """Test performance with multiple concurrent events"""
        import time
        
        start_time = time.time()
        
        # Emit multiple events rapidly
        for i in range(100):
            session_id = f"perf-session-{i % 10}"  # 10 concurrent sessions
            
            self.handlers.emit_confidence_update(session_id, {
                "event_type": "performance_test",
                "iteration": i
            })
            
            if i % 20 == 0:  # Emit validation progress every 20 iterations
                self.handlers.emit_validation_progress(session_id, "performance_test", {
                    "iteration": i,
                    "progress": i
                })
        
        end_time = time.time()
        
        # Performance assertions
        total_time = end_time - start_time
        assert total_time < 1.0, f"Performance test took too long: {total_time:.3f}s"
        
        # Verify all events were emitted
        expected_emissions = 100 + 5  # 100 confidence updates + 5 validation progress
        assert self.mock_emit.call_count == expected_emissions
        
        # Verify session management
        assert len(self.handlers.active_sessions) == 10  # 10 unique sessions


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])