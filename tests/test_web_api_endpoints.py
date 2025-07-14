"""
Comprehensive Test Suite for Web API Endpoints
Tests all Flask routes, file uploads, analysis, AI rewriting, health checks,
WebSocket communication, and error handling scenarios.
"""

import os
import sys
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from flask import Flask
from flask_socketio import SocketIO
import uuid
from datetime import datetime
import time
import threading

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_modules.app_factory import create_app
from src.config import Config


class TestWebAPIEndpoints:
    """Comprehensive test suite for all web API endpoints."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        # Create test configuration
        class TestConfig(Config):
            TESTING = True
            SECRET_KEY = 'test-secret-key'
            UPLOAD_FOLDER = tempfile.mkdtemp()
            MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
            WTF_CSRF_ENABLED = False
            
        app, socketio = create_app(TestConfig)
        app.config['TESTING'] = True
        
        # Store socketio for WebSocket tests
        app.extensions['socketio'] = socketio
        
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def socketio_client(self, app):
        """Create SocketIO test client."""
        return app.extensions['socketio'].test_client(app)
    
    # ===============================
    # INDEX ROUTE TESTS
    # ===============================
    
    def test_index_route_success(self, client):
        """Test successful index page loading."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'html' in response.data.lower()
    
    def test_index_route_template_error(self, client):
        """Test index route with template error."""
        with patch('app_modules.api_routes.render_template') as mock_render:
            mock_render.side_effect = Exception("Template error")
            response = client.get('/')
            assert response.status_code == 500
    
    # ===============================
    # FILE UPLOAD TESTS
    # ===============================
    
    def test_upload_file_success_txt(self, client):
        """Test successful text file upload."""
        file_content = b"This is a test document with some content."
        
        response = client.post('/upload', data={
            'file': (BytesIO(file_content), 'test.txt')
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
        assert data['filename'] == 'test.txt'
    
    def test_upload_file_success_pdf(self, client):
        """Test PDF file upload."""
        # Create mock PDF content
        pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        
        with patch('app_modules.api_routes.document_processor.extract_text') as mock_extract:
            mock_extract.return_value = "Extracted PDF text"
            
            response = client.post('/upload', data={
                'file': (BytesIO(pdf_content), 'test.pdf')
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['content'] == "Extracted PDF text"
    
    def test_upload_file_success_docx(self, client):
        """Test DOCX file upload."""
        # Create mock DOCX content
        docx_content = b"PK\x03\x04\x14\x00\x00\x00"  # ZIP header for DOCX
        
        with patch('app_modules.api_routes.document_processor.extract_text') as mock_extract:
            mock_extract.return_value = "Extracted DOCX text"
            
            response = client.post('/upload', data={
                'file': (BytesIO(docx_content), 'test.docx')
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['content'] == "Extracted DOCX text"
    
    def test_upload_file_success_markdown(self, client):
        """Test Markdown file upload."""
        md_content = b"# Test Document\n\nThis is a **markdown** document."
        
        response = client.post('/upload', data={
            'file': (BytesIO(md_content), 'test.md')
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
        assert data['filename'] == 'test.md'
    
    def test_upload_file_success_asciidoc(self, client):
        """Test AsciiDoc file upload."""
        adoc_content = b"= Test Document\n\nThis is an AsciiDoc document."
        
        response = client.post('/upload', data={
            'file': (BytesIO(adoc_content), 'test.adoc')
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'content' in data
        assert data['filename'] == 'test.adoc'
    
    def test_upload_no_file(self, client):
        """Test upload without file."""
        response = client.post('/upload', data={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'No file selected'
    
    def test_upload_empty_filename(self, client):
        """Test upload with empty filename."""
        response = client.post('/upload', data={
            'file': (BytesIO(b"content"), '')
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'No file selected'
    
    def test_upload_unsupported_format(self, client):
        """Test upload with unsupported file format."""
        response = client.post('/upload', data={
            'file': (BytesIO(b"content"), 'test.xyz')
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'File type not supported'
    
    def test_upload_file_too_large(self, client):
        """Test upload with file too large."""
        large_content = b"x" * (17 * 1024 * 1024)  # 17MB, exceeds 16MB limit
        
        response = client.post('/upload', data={
            'file': (BytesIO(large_content), 'large.txt')
        })
        
        assert response.status_code == 413
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'File too large'
    
    def test_upload_extraction_failure(self, client):
        """Test upload with text extraction failure."""
        with patch('app_modules.api_routes.document_processor.extract_text') as mock_extract:
            mock_extract.return_value = None
            
            response = client.post('/upload', data={
                'file': (BytesIO(b"content"), 'test.txt')
            })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data
            assert data['error'] == 'Failed to extract text from file'
    
    def test_upload_processing_exception(self, client):
        """Test upload with processing exception."""
        with patch('app_modules.api_routes.document_processor.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Processing error")
            
            response = client.post('/upload', data={
                'file': (BytesIO(b"content"), 'test.txt')
            })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Upload failed' in data['error']
    
    def test_upload_file_cleanup(self, client):
        """Test that uploaded files are cleaned up."""
        file_content = b"This is a test document."
        
        with patch('os.remove') as mock_remove:
            response = client.post('/upload', data={
                'file': (BytesIO(file_content), 'test.txt')
            })
            
            assert response.status_code == 200
            # File cleanup should be attempted
            mock_remove.assert_called_once()
    
    # ===============================
    # ANALYZE CONTENT TESTS
    # ===============================
    
    def test_analyze_content_success(self, client):
        """Test successful content analysis."""
        content = "This is a test document with some passive voice issues."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [
                        {
                            'type': 'passive_voice',
                            'message': 'Passive voice detected',
                            'suggestions': ['Use active voice'],
                            'severity': 'medium'
                        }
                    ],
                    'statistics': {'word_count': 10, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [
                    {
                        'type': 'paragraph',
                        'content': content,
                        'start_line': 1,
                        'end_line': 1
                    }
                ],
                'has_structure': True
            }
            
            response = client.post('/analyze', 
                                 data=json.dumps({
                                     'content': content,
                                     'format_hint': 'auto',
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'analysis' in data
            assert 'structural_blocks' in data
            assert data['session_id'] == 'test-session'
    
    def test_analyze_content_no_content(self, client):
        """Test analysis with no content."""
        response = client.post('/analyze',
                             data=json.dumps({'content': ''}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'No content provided'
    
    def test_analyze_content_generated_session_id(self, client):
        """Test analysis with generated session ID."""
        content = "Test content for analysis."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 4, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 90}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            response = client.post('/analyze',
                                 data=json.dumps({'content': content}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'session_id' in data
            assert data['session_id'] != ''
    
    def test_analyze_content_with_format_hint(self, client):
        """Test analysis with specific format hint."""
        content = "# Test Document\n\nThis is markdown content."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 5, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            response = client.post('/analyze',
                                 data=json.dumps({
                                     'content': content,
                                     'format_hint': 'markdown'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify format hint was passed
            mock_analyze.assert_called_once_with(content, format_hint='markdown')
    
    def test_analyze_content_analysis_exception(self, client):
        """Test analysis with analyzer exception."""
        content = "Test content."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.side_effect = Exception("Analysis error")
            
            response = client.post('/analyze',
                                 data=json.dumps({
                                     'content': content,
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Analysis failed' in data['error']
    
    def test_analyze_content_websocket_progress(self, client, socketio_client):
        """Test WebSocket progress updates during analysis."""
        content = "Test content for analysis."
        
        # Mock the analysis to simulate progress
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 4, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 90}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            # Mock WebSocket emit functions
            with patch('app_modules.api_routes.emit_progress') as mock_emit:
                response = client.post('/analyze',
                                     data=json.dumps({
                                         'content': content,
                                         'session_id': 'test-session'
                                     }),
                                     content_type='application/json')
                
                assert response.status_code == 200
                
                # Verify progress updates were sent
                assert mock_emit.call_count >= 4  # Multiple progress updates
                
                # Check specific progress steps
                call_args = [call[0] for call in mock_emit.call_args_list]
                session_ids = [args[0] for args in call_args]
                assert all(sid == 'test-session' for sid in session_ids)
    
    # ===============================
    # AI REWRITE TESTS
    # ===============================
    
    def test_rewrite_content_success(self, client):
        """Test successful AI rewrite (Pass 1)."""
        content = "This document is written in passive voice."
        errors = [
            {
                'type': 'passive_voice',
                'message': 'Passive voice detected',
                'suggestions': ['Use active voice']
            }
        ]
        
        with patch('app_modules.api_routes.ai_rewriter.rewrite') as mock_rewrite:
            mock_rewrite.return_value = {
                'rewritten_text': 'The author wrote this document in active voice.',
                'improvements': ['Converted to active voice'],
                'confidence': 0.85,
                'model_used': 'llama3:8b'
            }
            
            response = client.post('/rewrite',
                                 data=json.dumps({
                                     'content': content,
                                     'errors': errors,
                                     'context': 'sentence',
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'rewritten_text' in data
            assert data['pass_number'] == 1
            assert data['can_refine'] is True
            assert data['session_id'] == 'test-session'
    
    def test_rewrite_content_no_content(self, client):
        """Test rewrite with no content."""
        response = client.post('/rewrite',
                             data=json.dumps({'content': ''}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'No content provided'
    
    def test_rewrite_content_generated_session_id(self, client):
        """Test rewrite with generated session ID."""
        content = "Test content for rewriting."
        
        with patch('app_modules.api_routes.ai_rewriter.rewrite') as mock_rewrite:
            mock_rewrite.return_value = {
                'rewritten_text': 'Improved test content for rewriting.',
                'improvements': ['Enhanced clarity'],
                'confidence': 0.75,
                'model_used': 'llama3:8b'
            }
            
            response = client.post('/rewrite',
                                 data=json.dumps({'content': content}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'session_id' in data
            assert data['session_id'] != ''
    
    def test_rewrite_content_with_context(self, client):
        """Test rewrite with specific context."""
        content = "Test content."
        
        with patch('app_modules.api_routes.ai_rewriter.rewrite') as mock_rewrite:
            mock_rewrite.return_value = {
                'rewritten_text': 'Improved test content.',
                'improvements': ['Better clarity'],
                'confidence': 0.8,
                'model_used': 'llama3:8b'
            }
            
            response = client.post('/rewrite',
                                 data=json.dumps({
                                     'content': content,
                                     'context': 'paragraph'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify context was passed
            mock_rewrite.assert_called_once_with(content, [], 'paragraph')
    
    def test_rewrite_content_rewriter_exception(self, client):
        """Test rewrite with rewriter exception."""
        content = "Test content."
        
        with patch('app_modules.api_routes.ai_rewriter.rewrite') as mock_rewrite:
            mock_rewrite.side_effect = Exception("Rewrite error")
            
            response = client.post('/rewrite',
                                 data=json.dumps({
                                     'content': content,
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Rewrite failed' in data['error']
    
    # ===============================
    # AI REFINE TESTS (Pass 2)
    # ===============================
    
    def test_refine_content_success(self, client):
        """Test successful AI refinement (Pass 2)."""
        first_pass_result = "The author wrote this document in active voice."
        original_errors = [
            {
                'type': 'passive_voice',
                'message': 'Passive voice detected'
            }
        ]
        
        with patch('app_modules.api_routes.ai_rewriter.refine_text') as mock_refine:
            mock_refine.return_value = {
                'rewritten_text': 'The author clearly wrote this document using active voice.',
                'improvements': ['Added clarity', 'Refined wording'],
                'confidence': 0.9,
                'model_used': 'llama3:8b',
                'pass_number': 2
            }
            
            response = client.post('/refine',
                                 data=json.dumps({
                                     'first_pass_result': first_pass_result,
                                     'original_errors': original_errors,
                                     'context': 'sentence',
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'refined' in data
            assert data['pass_number'] == 2
            assert data['can_refine'] is False
            assert data['session_id'] == 'test-session'
    
    def test_refine_content_no_first_pass(self, client):
        """Test refine with no first pass result."""
        response = client.post('/refine',
                             data=json.dumps({'first_pass_result': ''}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'No first pass result provided'
    
    def test_refine_content_with_context(self, client):
        """Test refine with specific context."""
        first_pass_result = "Improved content."
        
        with patch('app_modules.api_routes.ai_rewriter.refine_text') as mock_refine:
            mock_refine.return_value = {
                'rewritten_text': 'Further improved content.',
                'improvements': ['Additional refinement'],
                'confidence': 0.85,
                'model_used': 'llama3:8b',
                'pass_number': 2
            }
            
            response = client.post('/refine',
                                 data=json.dumps({
                                     'first_pass_result': first_pass_result,
                                     'context': 'paragraph'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify context was passed
            mock_refine.assert_called_once_with(first_pass_result, [], 'paragraph')
    
    def test_refine_content_refiner_exception(self, client):
        """Test refine with refiner exception."""
        first_pass_result = "Test content."
        
        with patch('app_modules.api_routes.ai_rewriter.refine_text') as mock_refine:
            mock_refine.side_effect = Exception("Refinement error")
            
            response = client.post('/refine',
                                 data=json.dumps({
                                     'first_pass_result': first_pass_result,
                                     'session_id': 'test-session'
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Refinement failed' in data['error']
    
    # ===============================
    # HEALTH CHECK TESTS
    # ===============================
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        with patch('app_modules.api_routes.Config.is_ollama_enabled') as mock_ollama_enabled:
            mock_ollama_enabled.return_value = False
            
            response = client.get('/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'healthy'
            assert 'timestamp' in data
            assert 'version' in data
            assert 'services' in data
    
    def test_health_check_with_ollama_available(self, client):
        """Test health check with Ollama available."""
        with patch('app_modules.api_routes.Config.is_ollama_enabled') as mock_ollama_enabled:
            mock_ollama_enabled.return_value = True
            
            with patch('app_modules.api_routes.Config.OLLAMA_BASE_URL', 'http://localhost:11434'):
                with patch('app_modules.api_routes.Config.OLLAMA_MODEL', 'llama3:8b'):
                    with patch('requests.get') as mock_get:
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'models': [{'name': 'llama3:8b'}]
                        }
                        mock_get.return_value = mock_response
                        
                        response = client.get('/health')
                        
                        assert response.status_code == 200
                        data = json.loads(response.data)
                        assert data['status'] == 'healthy'
                        assert data['ollama_status'] == 'available'
                        assert data['ollama_model'] == 'llama3:8b'
    
    def test_health_check_with_ollama_unavailable(self, client):
        """Test health check with Ollama unavailable."""
        with patch('app_modules.api_routes.Config.is_ollama_enabled') as mock_ollama_enabled:
            mock_ollama_enabled.return_value = True
            
            with patch('app_modules.api_routes.Config.OLLAMA_BASE_URL', 'http://localhost:11434'):
                with patch('requests.get') as mock_get:
                    mock_get.side_effect = Exception("Connection failed")
                    
                    response = client.get('/health')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['status'] == 'healthy'
                    assert data['ollama_status'] == 'connection_failed'
    
    def test_health_check_with_ollama_model_not_found(self, client):
        """Test health check with Ollama model not found."""
        with patch('app_modules.api_routes.Config.is_ollama_enabled') as mock_ollama_enabled:
            mock_ollama_enabled.return_value = True
            
            with patch('app_modules.api_routes.Config.OLLAMA_BASE_URL', 'http://localhost:11434'):
                with patch('app_modules.api_routes.Config.OLLAMA_MODEL', 'missing-model'):
                    with patch('requests.get') as mock_get:
                        mock_response = Mock()
                        mock_response.status_code = 200
                        mock_response.json.return_value = {
                            'models': [{'name': 'other-model'}]
                        }
                        mock_get.return_value = mock_response
                        
                        response = client.get('/health')
                        
                        assert response.status_code == 200
                        data = json.loads(response.data)
                        assert data['status'] == 'healthy'
                        assert data['ollama_status'] == 'model_not_found'
    
    def test_health_check_exception(self, client):
        """Test health check with exception."""
        with patch('app_modules.api_routes.Config.is_ollama_enabled') as mock_ollama_enabled:
            mock_ollama_enabled.side_effect = Exception("Config error")
            
            response = client.get('/health')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'unhealthy'
            assert 'error' in data
            assert 'timestamp' in data
    
    # ===============================
    # WEBSOCKET TESTS
    # ===============================
    
    def test_websocket_connect(self, socketio_client):
        """Test WebSocket connection."""
        socketio_client.connect()
        
        # Should receive connection confirmation
        received = socketio_client.get_received()
        assert len(received) > 0
        assert received[0]['name'] == 'connected'
        assert 'session_id' in received[0]['args'][0]
    
    def test_websocket_disconnect(self, socketio_client):
        """Test WebSocket disconnection."""
        socketio_client.connect()
        socketio_client.disconnect()
        
        # Should handle disconnection gracefully
        assert not socketio_client.is_connected()
    
    def test_websocket_join_session(self, socketio_client):
        """Test joining a WebSocket session."""
        socketio_client.connect()
        
        # Join a specific session
        socketio_client.emit('join_session', {'session_id': 'test-session'})
        
        # Should receive session joined confirmation
        received = socketio_client.get_received()
        
        # Find the session_joined event
        session_joined_event = None
        for event in received:
            if event['name'] == 'session_joined':
                session_joined_event = event
                break
        
        assert session_joined_event is not None
        assert session_joined_event['args'][0]['session_id'] == 'test-session'
    
    def test_websocket_join_session_no_id(self, socketio_client):
        """Test joining session without session ID."""
        socketio_client.connect()
        
        # Join without session ID
        socketio_client.emit('join_session', {})
        
        # Should receive error
        received = socketio_client.get_received()
        
        # Find the error event
        error_event = None
        for event in received:
            if event['name'] == 'error':
                error_event = event
                break
        
        assert error_event is not None
        assert 'No session ID provided' in error_event['args'][0]['message']
    
    def test_websocket_progress_emission(self, socketio_client):
        """Test WebSocket progress emission."""
        from app_modules.websocket_handlers import emit_progress
        
        socketio_client.connect()
        
        # Emit progress
        emit_progress('test-session', 'test_step', 'Test status', 'Test detail', 50)
        
        # Should receive progress update
        received = socketio_client.get_received()
        
        # Find the progress event
        progress_event = None
        for event in received:
            if event['name'] == 'progress':
                progress_event = event
                break
        
        if progress_event:
            progress_data = progress_event['args'][0]
            assert progress_data['session_id'] == 'test-session'
            assert progress_data['step'] == 'test_step'
            assert progress_data['status'] == 'Test status'
            assert progress_data['progress'] == 50
    
    # ===============================
    # ERROR HANDLING TESTS
    # ===============================
    
    def test_404_error_json(self, client):
        """Test 404 error with JSON request."""
        response = client.get('/nonexistent', headers={'Content-Type': 'application/json'})
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Resource not found'
        assert data['status_code'] == 404
    
    def test_404_error_html(self, client):
        """Test 404 error with HTML request."""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        # Should return HTML error page or fallback
        assert response.data is not None
    
    def test_500_error_json(self, client):
        """Test 500 error with JSON request."""
        # Create a route that raises an exception
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            response = client.post('/analyze',
                                 data=json.dumps({'content': 'test'}),
                                 content_type='application/json')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Analysis failed' in data['error']
    
    def test_413_error_file_too_large(self, client):
        """Test 413 error for file too large."""
        # This is already tested in upload tests, but adding for completeness
        large_content = b"x" * (17 * 1024 * 1024)  # 17MB
        
        response = client.post('/upload', data={
            'file': (BytesIO(large_content), 'large.txt')
        })
        
        assert response.status_code == 413
        data = json.loads(response.data)
        assert data['error'] == 'File too large'
    
    # ===============================
    # CONCURRENT REQUEST TESTS
    # ===============================
    
    def test_concurrent_analysis_requests(self, client):
        """Test concurrent analysis requests."""
        content = "Test content for concurrent analysis."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 5, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            def make_request():
                return client.post('/analyze',
                                 data=json.dumps({
                                     'content': content,
                                     'session_id': f'session-{threading.current_thread().ident}'
                                 }),
                                 content_type='application/json')
            
            # Start multiple threads
            threads = []
            results = []
            
            for i in range(5):
                thread = threading.Thread(target=lambda: results.append(make_request()))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All requests should succeed
            assert len(results) == 5
            for response in results:
                assert response.status_code == 200
    
    def test_concurrent_upload_requests(self, client):
        """Test concurrent upload requests."""
        def make_upload():
            return client.post('/upload', data={
                'file': (BytesIO(b"Test content"), f'test-{threading.current_thread().ident}.txt')
            })
        
        # Start multiple threads
        threads = []
        results = []
        
        for i in range(3):
            thread = threading.Thread(target=lambda: results.append(make_upload()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 3
        for response in results:
            assert response.status_code == 200
    
    # ===============================
    # EDGE CASE TESTS
    # ===============================
    
    def test_analyze_extremely_long_content(self, client):
        """Test analysis with extremely long content."""
        # Create very long content
        long_content = "This is a test sentence. " * 1000
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 5000, 'sentence_count': 1000},
                    'technical_metrics': {'readability_score': 70}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            response = client.post('/analyze',
                                 data=json.dumps({'content': long_content}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_analyze_special_characters(self, client):
        """Test analysis with special characters."""
        special_content = "Test with émojis 🚀 and spécial charactërs: àáâãäå çñü"
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 8, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            response = client.post('/analyze',
                                 data=json.dumps({'content': special_content}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_analyze_empty_lines_and_whitespace(self, client):
        """Test analysis with empty lines and whitespace."""
        whitespace_content = "\n\n   \n\nTest content with lots of whitespace.   \n\n\n"
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 6, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            response = client.post('/analyze',
                                 data=json.dumps({'content': whitespace_content}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_upload_binary_file_as_text(self, client):
        """Test uploading a binary file with text extension."""
        binary_content = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
        
        with patch('app_modules.api_routes.document_processor.extract_text') as mock_extract:
            mock_extract.return_value = "Extracted text from binary file"
            
            response = client.post('/upload', data={
                'file': (BytesIO(binary_content), 'binary.txt')
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_rewrite_with_empty_errors_list(self, client):
        """Test rewrite with empty errors list."""
        content = "Perfect content with no errors."
        
        with patch('app_modules.api_routes.ai_rewriter.rewrite') as mock_rewrite:
            mock_rewrite.return_value = {
                'rewritten_text': content,  # No changes needed
                'improvements': [],
                'confidence': 0.95,
                'model_used': 'llama3:8b'
            }
            
            response = client.post('/rewrite',
                                 data=json.dumps({
                                     'content': content,
                                     'errors': []
                                 }),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['rewritten_text'] == content
    
    def test_session_id_persistence(self, client):
        """Test session ID persistence across requests."""
        session_id = str(uuid.uuid4())
        content = "Test content for session persistence."
        
        with patch('app_modules.api_routes.style_analyzer.analyze_with_blocks') as mock_analyze:
            mock_analyze.return_value = {
                'analysis': {
                    'errors': [],
                    'statistics': {'word_count': 5, 'sentence_count': 1},
                    'technical_metrics': {'readability_score': 85}
                },
                'structural_blocks': [],
                'has_structure': False
            }
            
            # First request
            response1 = client.post('/analyze',
                                  data=json.dumps({
                                      'content': content,
                                      'session_id': session_id
                                  }),
                                  content_type='application/json')
            
            assert response1.status_code == 200
            data1 = json.loads(response1.data)
            assert data1['session_id'] == session_id
            
            # Second request with same session ID
            response2 = client.post('/analyze',
                                  data=json.dumps({
                                      'content': content,
                                      'session_id': session_id
                                  }),
                                  content_type='application/json')
            
            assert response2.status_code == 200
            data2 = json.loads(response2.data)
            assert data2['session_id'] == session_id


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 