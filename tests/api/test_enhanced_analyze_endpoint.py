"""
Comprehensive Test Suite for Enhanced Analysis API Endpoint
Tests the /analyze endpoint with confidence features, threshold parameters, and backward compatibility
"""

import json
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from werkzeug.test import Client

# Test data and utilities
class TestData:
    """Test data for API endpoint testing"""
    
    SIMPLE_TEXT = "This is a test document. It has some issues."
    
    COMPLEX_TEXT = """
    This document contains various writing issues that should be detected by the system.
    
    Some of the common problems include:
    - Passive voice constructions
    - Overly complex sentences that could be simplified
    - Inconsistent terminology usage
    - Missing punctuation in certain places
    """
    
    UNICODE_TEXT = "This text contains Unicode characters: 'curly quotes' and em-dashes."
    
    MINIMAL_REQUEST = {
        "content": SIMPLE_TEXT,
        "session_id": "test-session-123"
    }
    
    ENHANCED_REQUEST = {
        "content": COMPLEX_TEXT,
        "session_id": "test-session-456",
        "confidence_threshold": 0.6,
        "include_confidence_details": True,
        "format_hint": "asciidoc"
    }
    
    LEGACY_REQUEST = {
        "content": SIMPLE_TEXT,
        "format_hint": "auto"
        # No session_id - should be auto-generated
        # No confidence parameters - should use defaults
    }


class MockStyleAnalyzer:
    """Mock style analyzer for testing"""
    
    def __init__(self):
        self.structural_analyzer = Mock()
        self.structural_analyzer.confidence_threshold = 0.43
        self.structural_analyzer.rules_registry = Mock()
        self.structural_analyzer.rules_registry.set_confidence_threshold = Mock()
        
    def analyze_with_blocks(self, content, format_hint):
        """Mock analysis with confidence data"""
        # Simulate different responses based on content
        errors = []
        if "issues" in content.lower():
            errors = [
                {
                    'type': 'word_usage',
                    'message': 'Consider more specific terminology',
                    'confidence_score': 0.75,
                    'enhanced_validation_available': True,
                    'line_number': 1,
                    'text_segment': 'issues'
                },
                {
                    'type': 'passive_voice',
                    'message': 'Consider using active voice',
                    'confidence_score': 0.45,
                    'enhanced_validation_available': True,
                    'line_number': 3,
                    'text_segment': 'should be detected'
                }
            ]
        
        enhanced_error_stats = {
            'total_errors': len(errors),
            'enhanced_errors': len([e for e in errors if e.get('enhanced_validation_available', False)]),
            'enhancement_rate': 1.0 if errors else 0.0
        }
        
        validation_performance = {
            'total_validations': len(errors),
            'consensus_validations': len(errors),
            'average_confidence': sum(e.get('confidence_score', 0.5) for e in errors) / len(errors) if errors else 0.5
        }
        
        analysis = {
            'errors': errors,
            'total_errors': len(errors),
            'enhanced_validation_enabled': True,
            'confidence_threshold': self.structural_analyzer.confidence_threshold,
            'enhanced_error_stats': enhanced_error_stats,
            'validation_performance': validation_performance,
            'statistics': {
                'word_count': len(content.split()),
                'sentence_count': content.count('.') + content.count('!') + content.count('?'),
                'paragraph_count': content.count('\n\n') + 1
            }
        }
        
        structural_blocks = [
            {
                'type': 'paragraph',
                'content': content[:100] + '...' if len(content) > 100 else content,
                'errors': errors[:1] if errors else []
            }
        ]
        
        return {
            'analysis': analysis,
            'structural_blocks': structural_blocks,
            'has_structure': True
        }


def create_test_app():
    """Create Flask test application with mocked dependencies"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Mock dependencies
    document_processor = Mock()
    style_analyzer = MockStyleAnalyzer()
    ai_rewriter = Mock()
    
    # Import and setup routes
    from app_modules.api_routes import setup_routes
    from app_modules.websocket_handlers import emit_progress, emit_completion
    
    # Mock websocket functions
    with patch('app_modules.api_routes.emit_progress') as mock_emit_progress, \
         patch('app_modules.api_routes.emit_completion') as mock_emit_completion:
        
        setup_routes(app, document_processor, style_analyzer, ai_rewriter)
        
        # Store mocks for verification
        app.mock_emit_progress = mock_emit_progress
        app.mock_emit_completion = mock_emit_completion
        app.style_analyzer = style_analyzer
    
    return app


class TestEnhancedAnalyzeEndpoint:
    """Comprehensive test suite for enhanced analyze endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create test application"""
        return create_test_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_basic_analysis_request(self, client):
        """Test basic analysis request without confidence parameters"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.MINIMAL_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Basic response structure
        assert data['success'] is True
        assert 'analysis' in data
        assert 'processing_time' in data
        assert 'session_id' in data
        assert data['session_id'] == 'test-session-123'
        
        # Enhanced features
        assert 'confidence_metadata' in data
        assert 'api_version' in data
        assert data['api_version'] == '2.0'
        assert data['backward_compatible'] is True
    
    def test_enhanced_analysis_with_confidence_threshold(self, client):
        """Test analysis with confidence threshold parameter"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.ENHANCED_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Confidence metadata
        confidence_metadata = data['confidence_metadata']
        assert confidence_metadata['confidence_threshold_used'] == 0.6
        assert confidence_metadata['confidence_filtering_applied'] is True
        assert confidence_metadata['enhanced_validation_enabled'] is True
        
        # Enhanced error statistics
        assert 'enhanced_error_stats' in confidence_metadata
        stats = confidence_metadata['enhanced_error_stats']
        assert 'total_errors' in stats
        assert 'enhanced_errors' in stats
        assert 'enhancement_rate' in stats
        
        # Confidence details
        assert 'confidence_details' in data
        details = data['confidence_details']
        assert details['confidence_system_available'] is True
        assert 'threshold_range' in details
        assert 'confidence_levels' in details
        
        # Verify confidence levels structure
        levels = details['confidence_levels']
        assert 'HIGH' in levels
        assert 'MEDIUM' in levels
        assert 'LOW' in levels
        for level_name, level_info in levels.items():
            assert 'threshold' in level_info
            assert 'description' in level_info
    
    def test_backward_compatibility_legacy_request(self, client):
        """Test backward compatibility with legacy API requests"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.LEGACY_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should work without confidence parameters
        assert data['success'] is True
        assert 'analysis' in data
        
        # Should auto-generate session_id
        assert 'session_id' in data
        assert data['session_id'] != ''
        
        # Should use default confidence threshold
        confidence_metadata = data['confidence_metadata']
        assert confidence_metadata['confidence_threshold_used'] == 0.43  # Default
        assert confidence_metadata['confidence_filtering_applied'] is False
        
        # Should include confidence details by default
        assert 'confidence_details' in data
    
    def test_confidence_threshold_validation(self, client):
        """Test confidence threshold parameter validation"""
        # Test with valid threshold
        valid_request = {**TestData.MINIMAL_REQUEST, "confidence_threshold": 0.8}
        response = client.post('/analyze',
                             data=json.dumps(valid_request),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['confidence_metadata']['confidence_threshold_used'] == 0.8
        
        # Test with boundary values
        for threshold in [0.0, 0.5, 1.0]:
            request_data = {**TestData.MINIMAL_REQUEST, "confidence_threshold": threshold}
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            assert response.status_code == 200
            data = response.get_json()
            assert data['confidence_metadata']['confidence_threshold_used'] == threshold
    
    def test_include_confidence_details_parameter(self, client):
        """Test include_confidence_details parameter"""
        # Test with confidence details enabled
        request_with_details = {**TestData.MINIMAL_REQUEST, "include_confidence_details": True}
        response = client.post('/analyze',
                             data=json.dumps(request_with_details),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'confidence_details' in data
        
        # Test with confidence details disabled
        request_without_details = {**TestData.MINIMAL_REQUEST, "include_confidence_details": False}
        response = client.post('/analyze',
                             data=json.dumps(request_without_details),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'confidence_details' not in data
    
    def test_unicode_content_handling(self, client):
        """Test handling of Unicode content with confidence features"""
        unicode_request = {**TestData.MINIMAL_REQUEST, "content": TestData.UNICODE_TEXT}
        response = client.post('/analyze',
                             data=json.dumps(unicode_request, ensure_ascii=False),
                             content_type='application/json; charset=utf-8')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Should handle Unicode without errors
        assert 'confidence_metadata' in data
        assert data['confidence_metadata']['enhanced_validation_enabled'] is True
    
    def test_error_handling_malformed_request(self, client):
        """Test error handling for malformed requests"""
        # Missing content
        response = client.post('/analyze',
                             data=json.dumps({"session_id": "test"}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'No content provided' in data['error']
        
        # Invalid JSON
        response = client.post('/analyze',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code in [400, 500]  # Depends on Flask version
        
        # Empty request
        response = client.post('/analyze',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
    
    def test_performance_with_confidence_calculation(self, client):
        """Test API performance impact of confidence calculation"""
        start_time = time.time()
        
        # Make multiple requests to test performance
        for i in range(5):
            request_data = {
                **TestData.ENHANCED_REQUEST,
                "session_id": f"perf-test-{i}",
                "confidence_threshold": 0.5 + (i * 0.1)
            }
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            
            # Verify performance data is included
            assert 'processing_time' in data
            assert data['processing_time'] > 0
            
            # Verify confidence threshold was applied
            expected_threshold = 0.5 + (i * 0.1)
            assert abs(data['confidence_metadata']['confidence_threshold_used'] - expected_threshold) < 0.01
        
        total_time = time.time() - start_time
        
        # Performance should be reasonable (< 5 seconds for 5 requests)
        assert total_time < 5.0, f"Performance test took too long: {total_time:.2f}s"
    
    def test_structural_blocks_with_confidence(self, client):
        """Test structural blocks include confidence information"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.ENHANCED_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should include structural blocks
        assert 'structural_blocks' in data
        blocks = data['structural_blocks']
        assert len(blocks) > 0
        
        # Each block should have error information
        for block in blocks:
            assert 'type' in block
            assert 'content' in block
            if 'errors' in block and block['errors']:
                for error in block['errors']:
                    assert 'confidence_score' in error or 'confidence' in error
    
    def test_validation_performance_metrics(self, client):
        """Test validation performance metrics in response"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.ENHANCED_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should include validation performance
        confidence_metadata = data['confidence_metadata']
        if 'validation_performance' in confidence_metadata:
            perf = confidence_metadata['validation_performance']
            assert 'total_validations' in perf
            assert 'consensus_validations' in perf
            assert 'average_confidence' in perf
            
            # Sanity checks
            assert perf['total_validations'] >= 0
            assert perf['consensus_validations'] >= 0
            assert 0.0 <= perf['average_confidence'] <= 1.0
    
    def test_api_version_and_compatibility_flags(self, client):
        """Test API version and compatibility indicators"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.MINIMAL_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # API version should indicate enhanced features
        assert data['api_version'] == '2.0'
        assert data['backward_compatible'] is True
        
        # Should have confidence metadata even for basic requests
        assert 'confidence_metadata' in data
        confidence_metadata = data['confidence_metadata']
        assert 'confidence_threshold_used' in confidence_metadata
        assert 'enhanced_validation_enabled' in confidence_metadata
        assert 'confidence_filtering_applied' in confidence_metadata
    
    def test_websocket_progress_events_with_confidence(self, client, app):
        """Test WebSocket progress events include confidence information"""
        response = client.post('/analyze',
                             data=json.dumps(TestData.ENHANCED_REQUEST),
                             content_type='application/json')
        
        assert response.status_code == 200
        
        # Verify progress events were emitted
        assert app.mock_emit_progress.called
        assert app.mock_emit_completion.called
        
        # Check progress event calls
        progress_calls = app.mock_emit_progress.call_args_list
        assert len(progress_calls) >= 1
        
        # Check completion event
        completion_calls = app.mock_emit_completion.call_args_list
        assert len(completion_calls) == 1
        
        # Verify completion event includes confidence data
        session_id, success, response_data = completion_calls[0][0]
        assert success is True
        assert 'confidence_metadata' in response_data
        assert 'api_version' in response_data


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])