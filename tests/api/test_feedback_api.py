"""
Comprehensive Test Suite for Feedback Collection API
Tests the /api/feedback endpoints with validation, storage, and analytics
"""

import json
import pytest
import tempfile
import shutil
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Test data and utilities
class FeedbackTestData:
    """Test data for feedback API testing"""
    
    VALID_FEEDBACK = {
        "session_id": "test-session-123",
        "error_id": "error-456",
        "error_type": "word_usage",
        "error_message": "Consider more specific terminology",
        "feedback_type": "correct",
        "confidence_score": 0.75,
        "user_reason": "This suggestion is accurate and helpful"
    }
    
    MINIMAL_FEEDBACK = {
        "session_id": "minimal-session",
        "error_id": "minimal-error",
        "error_type": "style",
        "error_message": "Test error message",
        "feedback_type": "incorrect"
    }
    
    INVALID_FEEDBACK_CASES = [
        {
            "name": "missing_session_id",
            "data": {
                "error_id": "error-123",
                "error_type": "grammar",
                "error_message": "Test error",
                "feedback_type": "correct"
            },
            "expected_error": "Missing required field: session_id"
        },
        {
            "name": "invalid_feedback_type",
            "data": {
                "session_id": "test-session",
                "error_id": "error-123",
                "error_type": "grammar",
                "error_message": "Test error",
                "feedback_type": "invalid_type"
            },
            "expected_error": "Invalid feedback_type"
        },
        {
            "name": "invalid_confidence_score",
            "data": {
                "session_id": "test-session",
                "error_id": "error-123",
                "error_type": "grammar",
                "error_message": "Test error",
                "feedback_type": "correct",
                "confidence_score": 1.5
            },
            "expected_error": "confidence_score must be between 0.0 and 1.0"
        },
        {
            "name": "empty_session_id",
            "data": {
                "session_id": "",
                "error_id": "error-123",
                "error_type": "grammar",
                "error_message": "Test error",
                "feedback_type": "correct"
            },
            "expected_error": "Missing required field: session_id"
        }
    ]


class TestFeedbackStorage:
    """Test the feedback storage module directly"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Import and initialize with temp directory
        from app_modules.feedback_storage import FeedbackStorage
        self.storage = FeedbackStorage(storage_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_feedback_validation_valid_data(self):
        """Test feedback validation with valid data"""
        is_valid, message = self.storage.validate_feedback_data(FeedbackTestData.VALID_FEEDBACK)
        assert is_valid is True
        assert message == "Valid"
    
    def test_feedback_validation_minimal_data(self):
        """Test feedback validation with minimal required data"""
        is_valid, message = self.storage.validate_feedback_data(FeedbackTestData.MINIMAL_FEEDBACK)
        assert is_valid is True
        assert message == "Valid"
    
    def test_feedback_validation_invalid_cases(self):
        """Test feedback validation with various invalid cases"""
        for case in FeedbackTestData.INVALID_FEEDBACK_CASES:
            is_valid, message = self.storage.validate_feedback_data(case["data"])
            assert is_valid is False, f"Case {case['name']} should be invalid"
            assert case["expected_error"] in message, f"Case {case['name']} error message mismatch"
    
    def test_feedback_storage_and_retrieval(self):
        """Test storing and retrieving feedback"""
        # Store feedback
        success, message, feedback_id = self.storage.store_feedback(
            FeedbackTestData.VALID_FEEDBACK,
            user_agent="Test-Agent/1.0",
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert "successfully" in message
        assert feedback_id is not None
        assert len(feedback_id) == 12  # MD5 hash truncated to 12 chars
        
        # Retrieve feedback
        session_feedback = self.storage.get_session_feedback("test-session-123")
        assert len(session_feedback) == 1
        
        stored_feedback = session_feedback[0]
        assert stored_feedback.session_id == "test-session-123"
        assert stored_feedback.error_id == "error-456"
        assert stored_feedback.feedback_type == "correct"
        assert stored_feedback.confidence_score == 0.75
        assert stored_feedback.user_reason == "This suggestion is accurate and helpful"
        assert stored_feedback.user_agent == "Test-Agent/1.0"
        assert stored_feedback.ip_hash is not None  # Should be hashed
    
    def test_multiple_feedback_entries(self):
        """Test storing multiple feedback entries"""
        feedback_entries = [
            {**FeedbackTestData.VALID_FEEDBACK, "error_id": f"error-{i}"}
            for i in range(5)
        ]
        
        stored_ids = []
        for feedback in feedback_entries:
            success, message, feedback_id = self.storage.store_feedback(feedback)
            assert success is True
            stored_ids.append(feedback_id)
        
        # Check all IDs are unique
        assert len(set(stored_ids)) == 5
        
        # Check session has all feedback
        session_feedback = self.storage.get_session_feedback("test-session-123")
        assert len(session_feedback) == 5
    
    def test_feedback_statistics_generation(self):
        """Test feedback statistics generation"""
        # Store varied feedback
        feedback_data = [
            {**FeedbackTestData.VALID_FEEDBACK, "error_id": "error-1", "feedback_type": "correct", "confidence_score": 0.8},
            {**FeedbackTestData.VALID_FEEDBACK, "error_id": "error-2", "feedback_type": "incorrect", "confidence_score": 0.3},
            {**FeedbackTestData.VALID_FEEDBACK, "error_id": "error-3", "feedback_type": "partially_correct", "confidence_score": 0.6},
            {**FeedbackTestData.VALID_FEEDBACK, "error_id": "error-4", "feedback_type": "correct", "confidence_score": 0.9}
        ]
        
        for feedback in feedback_data:
            success, _, _ = self.storage.store_feedback(feedback)
            assert success is True
        
        # Get statistics
        stats = self.storage.get_feedback_stats(session_id="test-session-123")
        
        assert stats['total_feedback'] == 4
        assert stats['feedback_distribution']['correct'] == 2
        assert stats['feedback_distribution']['incorrect'] == 1
        assert stats['feedback_distribution']['partially_correct'] == 1
        
        # Check confidence analysis
        confidence_analysis = stats['confidence_analysis']
        assert 'average_confidence' in confidence_analysis
        assert confidence_analysis['average_confidence'] > 0
        assert 'confidence_distribution' in confidence_analysis
    
    def test_aggregated_insights(self):
        """Test aggregated insights generation"""
        # Use a unique session for this test to avoid interference
        unique_session = "insights-test-session"
        
        # Store feedback with different error types
        feedback_data = [
            {**FeedbackTestData.VALID_FEEDBACK, "session_id": unique_session, "error_id": "e1", "error_type": "grammar", "feedback_type": "correct"},
            {**FeedbackTestData.VALID_FEEDBACK, "session_id": unique_session, "error_id": "e2", "error_type": "grammar", "feedback_type": "incorrect"},
            {**FeedbackTestData.VALID_FEEDBACK, "session_id": unique_session, "error_id": "e3", "error_type": "style", "feedback_type": "correct"},
            {**FeedbackTestData.VALID_FEEDBACK, "session_id": unique_session, "error_id": "e4", "error_type": "word_usage", "feedback_type": "correct"}
        ]
        
        for feedback in feedback_data:
            success, _, _ = self.storage.store_feedback(feedback)
            assert success is True
        
        # Get insights - check that we have at least the feedback we just added
        insights = self.storage.aggregate_feedback_insights(days_back=1)
        
        assert 'summary' in insights
        assert insights['summary']['total_feedback_entries'] >= 4
        
        assert 'accuracy_insights' in insights
        accuracy = insights['accuracy_insights']
        assert accuracy['overall_accuracy_rate'] >= 0.5  # Should have reasonable accuracy
        
        assert 'error_type_insights' in insights
        error_type_insights = insights['error_type_insights']
        assert 'grammar' in error_type_insights
        assert 'style' in error_type_insights
        assert 'word_usage' in error_type_insights
    
    def test_ip_address_hashing(self):
        """Test IP address hashing for privacy"""
        ip1 = "192.168.1.1"
        ip2 = "192.168.1.2"
        
        hash1 = self.storage.hash_ip(ip1)
        hash2 = self.storage.hash_ip(ip2)
        
        # Hashes should be different
        assert hash1 != hash2
        
        # Hashes should be consistent
        assert self.storage.hash_ip(ip1) == hash1
        
        # Hash should be limited length
        assert len(hash1) == 16


class TestFeedbackAPI:
    """Test the feedback API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the feedback storage to use temp directory
        self.storage_patch = patch('app_modules.feedback_storage.feedback_storage')
        self.mock_storage = self.storage_patch.start()
        
        # Create real storage instance for testing
        from app_modules.feedback_storage import FeedbackStorage
        self.real_storage = FeedbackStorage(storage_dir=self.temp_dir)
        self.mock_storage.store_feedback = self.real_storage.store_feedback
        self.mock_storage.get_feedback_stats = self.real_storage.get_feedback_stats
        self.mock_storage.aggregate_feedback_insights = self.real_storage.aggregate_feedback_insights
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.storage_patch.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_app(self):
        """Create a mock Flask app for testing"""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Mock dependencies
        document_processor = Mock()
        style_analyzer = Mock()
        ai_rewriter = Mock()
        
        # Setup routes
        from app_modules.api_routes import setup_routes
        setup_routes(app, document_processor, style_analyzer, ai_rewriter)
        
        return app
    
    def test_submit_feedback_valid(self):
        """Test submitting valid feedback"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            response = client.post('/api/feedback',
                                 data=json.dumps(FeedbackTestData.VALID_FEEDBACK),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = response.get_json()
            
            assert data['success'] is True
            assert 'feedback_id' in data
            assert 'timestamp' in data
            assert 'successfully' in data['message']
    
    def test_submit_feedback_minimal(self):
        """Test submitting minimal valid feedback"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            response = client.post('/api/feedback',
                                 data=json.dumps(FeedbackTestData.MINIMAL_FEEDBACK),
                                 content_type='application/json')
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
    
    def test_submit_feedback_invalid_cases(self):
        """Test submitting invalid feedback"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            for case in FeedbackTestData.INVALID_FEEDBACK_CASES:
                response = client.post('/api/feedback',
                                     data=json.dumps(case["data"]),
                                     content_type='application/json')
                
                assert response.status_code == 400, f"Case {case['name']} should return 400"
                data = response.get_json()
                assert 'error' in data
                assert case["expected_error"] in data['error']
    
    def test_submit_feedback_no_json(self):
        """Test submitting feedback without JSON data"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            response = client.post('/api/feedback', data='not json')
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'No JSON data provided' in data['error']
    
    def test_get_feedback_stats(self):
        """Test getting feedback statistics"""
        app = self.create_mock_app()
        
        # First submit some feedback
        with app.test_client() as client:
            for i in range(3):
                feedback = {**FeedbackTestData.VALID_FEEDBACK, "error_id": f"error-{i}"}
                response = client.post('/api/feedback',
                                     data=json.dumps(feedback),
                                     content_type='application/json')
                assert response.status_code == 201
            
            # Get stats for the session
            response = client.get('/api/feedback/stats?session_id=test-session-123')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert 'statistics' in data
            stats = data['statistics']
            assert stats['total_feedback'] == 3
            assert stats['session_id'] == 'test-session-123'
    
    def test_get_feedback_stats_invalid_days(self):
        """Test getting feedback statistics with invalid days_back parameter"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            # Test invalid days_back values
            for invalid_days in [-1, 0, 366]:
                response = client.get(f'/api/feedback/stats?days_back={invalid_days}')
                assert response.status_code == 400
                data = response.get_json()
                assert 'days_back must be between 1 and 365' in data['error']
    
    def test_get_feedback_insights(self):
        """Test getting feedback insights"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            # Submit varied feedback
            feedback_data = [
                {**FeedbackTestData.VALID_FEEDBACK, "error_id": "e1", "feedback_type": "correct"},
                {**FeedbackTestData.VALID_FEEDBACK, "error_id": "e2", "feedback_type": "incorrect"},
                {**FeedbackTestData.VALID_FEEDBACK, "error_id": "e3", "feedback_type": "correct"}
            ]
            
            for feedback in feedback_data:
                response = client.post('/api/feedback',
                                     data=json.dumps(feedback),
                                     content_type='application/json')
                assert response.status_code == 201
            
            # Get insights
            response = client.get('/api/feedback/insights?days_back=1')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['success'] is True
            assert 'insights' in data
            assert data['api_version'] == '2.0'
            
            insights = data['insights']
            assert 'summary' in insights
            assert 'accuracy_insights' in insights
            assert insights['summary']['total_feedback_entries'] == 3
    
    def test_feedback_api_performance(self):
        """Test feedback API performance"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            start_time = time.time()
            
            # Submit multiple feedback entries
            for i in range(10):
                feedback = {**FeedbackTestData.VALID_FEEDBACK, "error_id": f"perf-error-{i}"}
                response = client.post('/api/feedback',
                                     data=json.dumps(feedback),
                                     content_type='application/json')
                assert response.status_code == 201
            
            submission_time = time.time() - start_time
            
            # Get stats
            stats_start = time.time()
            response = client.get('/api/feedback/stats?session_id=test-session-123')
            assert response.status_code == 200
            stats_time = time.time() - stats_start
            
            # Get insights
            insights_start = time.time()
            response = client.get('/api/feedback/insights?days_back=1')
            assert response.status_code == 200
            insights_time = time.time() - insights_start
            
            # Performance assertions
            assert submission_time < 2.0, f"Submission took too long: {submission_time:.2f}s"
            assert stats_time < 0.5, f"Stats retrieval took too long: {stats_time:.2f}s"
            assert insights_time < 1.0, f"Insights generation took too long: {insights_time:.2f}s"
    
    def test_feedback_api_security(self):
        """Test feedback API security features"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            # Test with potentially malicious data
            malicious_feedback = {
                "session_id": "test-session",
                "error_id": "<script>alert('xss')</script>",
                "error_type": "javascript:alert(1)",
                "error_message": "' OR 1=1 --",
                "feedback_type": "correct",
                "user_reason": "A" * 1001  # Exceeds length limit
            }
            
            response = client.post('/api/feedback',
                                 data=json.dumps(malicious_feedback),
                                 content_type='application/json')
            
            assert response.status_code == 400  # Should be rejected due to user_reason length
            data = response.get_json()
            assert 'user_reason must be 1000 characters or less' in data['error']
    
    def test_health_check_with_feedback(self):
        """Test health check includes feedback storage"""
        app = self.create_mock_app()
        
        with app.test_client() as client:
            response = client.get('/health')
            
            assert response.status_code == 200
            data = response.get_json()
            
            assert data['status'] == 'healthy'
            assert 'services' in data
            assert data['services']['feedback_storage'] is True


class TestFeedbackIntegration:
    """Integration tests for the complete feedback workflow"""
    
    def setup_method(self):
        """Setup integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup integration test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_complete_feedback_workflow(self):
        """Test complete feedback workflow from submission to insights"""
        from app_modules.feedback_storage import FeedbackStorage
        storage = FeedbackStorage(storage_dir=self.temp_dir)
        
        # Simulate multiple users providing feedback
        users_feedback = [
            # User 1: Mixed feedback
            {"session_id": "user1", "error_id": "e1", "error_type": "grammar", "error_message": "Grammar error", "feedback_type": "correct", "confidence_score": 0.8},
            {"session_id": "user1", "error_id": "e2", "error_type": "style", "error_message": "Style error", "feedback_type": "incorrect", "confidence_score": 0.4},
            
            # User 2: All correct
            {"session_id": "user2", "error_id": "e3", "error_type": "grammar", "error_message": "Another grammar error", "feedback_type": "correct", "confidence_score": 0.9},
            {"session_id": "user2", "error_id": "e4", "error_type": "word_usage", "error_message": "Word usage error", "feedback_type": "correct", "confidence_score": 0.7},
            
            # User 3: Partial feedback
            {"session_id": "user3", "error_id": "e5", "error_type": "style", "error_message": "Style issue", "feedback_type": "partially_correct", "confidence_score": 0.6}
        ]
        
        # Submit all feedback
        feedback_ids = []
        for feedback in users_feedback:
            success, message, feedback_id = storage.store_feedback(feedback)
            assert success is True
            feedback_ids.append(feedback_id)
        
        # Verify all feedback IDs are unique
        assert len(set(feedback_ids)) == len(feedback_ids)
        
        # Test session-specific stats
        user1_stats = storage.get_feedback_stats(session_id="user1")
        assert user1_stats['total_feedback'] == 2
        assert user1_stats['feedback_distribution']['correct'] == 1
        assert user1_stats['feedback_distribution']['incorrect'] == 1
        
        # Test overall insights
        insights = storage.aggregate_feedback_insights(days_back=1)
        assert insights['summary']['total_feedback_entries'] == 5
        assert insights['summary']['unique_sessions'] == 3
        
        # Check accuracy insights
        accuracy = insights['accuracy_insights']
        assert accuracy['overall_accuracy_rate'] == 0.6  # 3 correct out of 5
        
        # Check error type insights
        error_insights = insights['error_type_insights']
        assert 'grammar' in error_insights
        assert error_insights['grammar']['accuracy_rate'] == 1.0  # Both grammar feedbacks were correct
        
        # Test confidence correlation
        confidence_insights = insights['confidence_insights']
        assert 'average_confidence' in confidence_insights
        assert 'confidence_accuracy_correlation' in confidence_insights


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])