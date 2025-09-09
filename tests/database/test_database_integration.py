"""
Integration tests for database functionality
"""

import pytest
import tempfile
import os
from flask import Flask
from database import init_db, db
from database.services import database_service
from database.models import UserSession, Document, RuleViolation, StyleRule, AnalysisSession
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    init_db(app)
    
    with app.app_context():
        db.create_all()
        # Initialize default rules
        database_service.initialize_default_rules()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def test_session_creation(app):
    """Test user session creation."""
    with app.app_context():
        session_id = database_service.create_user_session(
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )
        
        assert session_id is not None
        session = UserSession.query.filter_by(session_id=session_id).first()
        assert session is not None
        assert session.user_agent == "test-agent"
        assert session.ip_hash is not None  # Should be hashed

def test_document_storage(app):
    """Test document storage."""
    with app.app_context():
        session_id = database_service.create_user_session()
        
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test document content for analysis.",
            filename="test.txt",
            document_format="txt",
            content_type="concept"
        )
        
        assert document_id is not None
        assert analysis_id is not None
        
        document = Document.query.filter_by(document_id=document_id).first()
        assert document is not None
        assert document.original_content == "Test document content for analysis."
        assert document.filename == "test.txt"
        assert document.document_format == "txt"

def test_analysis_workflow(app):
    """Test complete analysis workflow."""
    with app.app_context():
        # Create session and document
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="This is a test document with some content that might have errors.",
            filename="test.txt"
        )
        
        # Start analysis
        started = database_service.start_analysis(analysis_id)
        assert started is True
        
        # Verify analysis is in processing state
        analysis = AnalysisSession.query.filter_by(analysis_id=analysis_id).first()
        assert analysis.status.value == "processing"
        
        # Store analysis results
        violations = [
            {
                'rule_id': 'passive_voice',
                'error_text': 'might have',
                'error_message': 'Consider using active voice',
                'error_position': 45,
                'end_position': 55,
                'line_number': 1,
                'column_number': 45,
                'severity': 'medium',
                'confidence_score': 0.8,
                'suggestion': 'Use active voice instead'
            },
            {
                'rule_id': 'sentence_length',
                'error_text': 'This is a test document with some content that might have errors.',
                'error_message': 'Sentence is too long',
                'error_position': 0,
                'end_position': 65,
                'line_number': 1,
                'severity': 'low',
                'confidence_score': 0.6
            }
        ]
        
        success = database_service.store_analysis_results(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations,
            processing_time=1.5,
            total_blocks_analyzed=1
        )
        
        assert success is True
        
        # Verify violations were stored
        stored_violations = RuleViolation.query.filter_by(analysis_id=analysis_id).all()
        assert len(stored_violations) == 2
        assert stored_violations[0].rule_id in ['passive_voice', 'sentence_length']
        assert stored_violations[0].confidence_score > 0

def test_feedback_storage(app):
    """Test feedback storage."""
    with app.app_context():
        # Create session, document, and analysis with violations
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content",
            filename="test.txt"
        )
        
        # Store a violation
        violations = [
            {
                'rule_id': 'passive_voice',
                'error_text': 'test error',
                'error_message': 'Test error message',
                'error_position': 0,
                'confidence_score': 0.7
            }
        ]
        
        database_service.store_analysis_results(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations
        )
        
        violation = RuleViolation.query.filter_by(analysis_id=analysis_id).first()
        
        # Store feedback
        success, feedback_id = database_service.store_user_feedback(
            session_id=session_id,
            violation_id=violation.violation_id,
            feedback_data={
                'error_type': 'passive_voice',
                'error_message': 'Test error message',
                'feedback_type': 'correct',
                'confidence_score': 0.8,
                'user_reason': 'This is actually correct'
            },
            user_agent="test-browser",
            ip_address="127.0.0.1"
        )
        
        assert success is True
        assert feedback_id is not None

def test_session_analytics(app):
    """Test session analytics."""
    with app.app_context():
        session_id = database_service.create_user_session()
        
        # Upload multiple documents
        doc1_id, analysis1_id = database_service.process_document_upload(
            session_id=session_id,
            content="First document content",
            filename="doc1.txt"
        )
        
        doc2_id, analysis2_id = database_service.process_document_upload(
            session_id=session_id,
            content="Second document content",
            filename="doc2.txt"
        )
        
        # Store violations for first document
        violations = [
            {
                'rule_id': 'passive_voice',
                'error_text': 'test',
                'error_message': 'Test message',
                'error_position': 0
            }
        ]
        
        database_service.store_analysis_results(
            analysis_id=analysis1_id,
            document_id=doc1_id,
            violations=violations
        )
        
        # Get analytics
        analytics = database_service.get_session_analytics(session_id)
        
        assert 'session_id' in analytics
        assert analytics['total_documents'] == 2
        assert analytics['total_analyses'] == 2
        assert analytics['total_violations'] == 1
        assert len(analytics['document_summary']) == 2

def test_rule_performance(app):
    """Test rule performance analytics."""
    with app.app_context():
        # Create test data
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content for rule performance",
            filename="test.txt"
        )
        
        # Store violations
        violations = [
            {
                'rule_id': 'passive_voice',
                'error_text': 'test',
                'error_message': 'Test message',
                'error_position': 0,
                'confidence_score': 0.8
            }
        ]
        
        database_service.store_analysis_results(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations
        )
        
        violation = RuleViolation.query.filter_by(analysis_id=analysis_id).first()
        
        # Store feedback
        database_service.store_user_feedback(
            session_id=session_id,
            violation_id=violation.violation_id,
            feedback_data={
                'error_type': 'passive_voice',
                'error_message': 'Test message',
                'feedback_type': 'correct'
            }
        )
        
        # Get rule performance
        performance = database_service.get_rule_performance('passive_voice')
        
        assert 'rule_id' in performance
        assert performance['rule_id'] == 'passive_voice'
        assert performance['total_violations'] == 1
        assert performance['average_confidence'] == 0.8
        assert 'feedback_stats' in performance
        assert performance['feedback_stats']['total'] == 1

def test_rewrite_workflow(app):
    """Test rewrite workflow."""
    with app.app_context():
        # Create session and document
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Original text that needs rewriting",
            filename="test.txt"
        )
        
        # Start rewrite session
        rewrite_id = database_service.start_rewrite_session(
            session_id=session_id,
            document_id=document_id,
            rewrite_type="full_document",
            rewrite_mode="comprehensive",
            model_provider="ollama",
            model_name="llama3:8b"
        )
        
        assert rewrite_id is not None
        
        # Store rewrite results
        results = [
            {
                'original_text': 'Original text that needs rewriting',
                'rewritten_text': 'Improved text that has been rewritten',
                'improvements_made': ['clarity', 'conciseness'],
                'quality_score': 0.85,
                'processing_time': 2.3,
                'tokens_used': 45,
                'readability_before': 65.2,
                'readability_after': 72.8
            }
        ]
        
        success = database_service.store_rewrite_results(
            rewrite_id=rewrite_id,
            results=results,
            total_processing_time=2.5,
            total_tokens_used=50
        )
        
        assert success is True

def test_model_usage_stats(app):
    """Test model usage statistics."""
    with app.app_context():
        session_id = database_service.create_user_session()
        
        # Create rewrite session which logs model usage
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content",
            filename="test.txt"
        )
        
        rewrite_id = database_service.start_rewrite_session(
            session_id=session_id,
            document_id=document_id,
            model_provider="ollama",
            model_name="llama3:8b"
        )
        
        # Get usage stats
        stats = database_service.get_model_usage_stats(session_id=session_id)
        
        assert 'total_operations' in stats
        assert stats['total_operations'] >= 1
        assert 'success_rate' in stats

def test_system_health(app):
    """Test system health check."""
    with app.app_context():
        health = database_service.get_system_health()
        
        assert 'status' in health
        assert health['status'] == 'healthy'
        assert 'database_connection' in health
        assert health['database_connection'] is True
        assert 'timestamp' in health

def test_error_handling(app):
    """Test error handling in service methods."""
    with app.app_context():
        # Test getting non-existent session
        analytics = database_service.get_session_analytics('non-existent-session')
        assert 'error' in analytics
        
        # Test getting non-existent analysis
        results = database_service.get_analysis_results('non-existent-analysis')
        assert 'error' in results
        
        # Test feedback for non-existent violation
        success, message = database_service.store_user_feedback(
            session_id='test-session',
            violation_id='non-existent-violation',
            feedback_data={
                'error_type': 'test',
                'error_message': 'Test',
                'feedback_type': 'correct'
            }
        )
        assert success is False
        assert 'not found' in message

def test_cleanup_operations(app):
    """Test cleanup operations."""
    with app.app_context():
        # Create old session (we can't easily manipulate timestamps in this test,
        # but we can test the method doesn't crash)
        session_id = database_service.create_user_session()
        
        cleanup_result = database_service.cleanup_expired_sessions(hours_old=24)
        
        assert 'expired_sessions' in cleanup_result
        assert 'hours_threshold' in cleanup_result
        assert cleanup_result['hours_threshold'] == 24

def test_default_rules_initialization(app):
    """Test default rules initialization."""
    with app.app_context():
        # Rules should already be initialized by the fixture
        rules = StyleRule.query.all()
        assert len(rules) >= 5  # We initialize 5 default rules
        
        # Check specific rules exist
        passive_voice_rule = StyleRule.query.filter_by(rule_id='passive_voice').first()
        assert passive_voice_rule is not None
        assert passive_voice_rule.rule_name == 'Passive Voice Detection'
        assert passive_voice_rule.is_enabled is True

def test_data_integrity(app):
    """Test data integrity and relationships."""
    with app.app_context():
        # Create related data
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content",
            filename="test.txt"
        )
        
        # Verify relationships work
        session = UserSession.query.filter_by(session_id=session_id).first()
        assert len(session.documents) == 1
        assert len(session.analysis_sessions) == 1
        
        document = Document.query.filter_by(document_id=document_id).first()
        assert document.session_id == session_id
        assert len(document.analysis_sessions) == 1
        
        analysis = AnalysisSession.query.filter_by(analysis_id=analysis_id).first()
        assert analysis.session_id == session_id
        assert analysis.document_id == document_id
