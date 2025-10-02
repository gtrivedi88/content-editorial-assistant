"""
Comprehensive End-to-End Test Suite for Block-Level Rewriting (Phase 4)
Tests the complete block processing pipeline with performance monitoring.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any
import tempfile
import os


# Test fixtures
@pytest.fixture
def app():
    """Create test Flask application."""
    from app import create_app
    from config import TestingConfig
    
    # Create app - handle potential tuple return from create_app
    app_result = create_app(TestingConfig)
    
    # If create_app returns a tuple, extract the app
    if isinstance(app_result, tuple):
        app = app_result[0]
    else:
        app = app_result
    
    app.config.update({
        'TESTING': True,
        'BLOCK_PROCESSING_TIMEOUT': 5,  # Shorter timeout for tests
        'ENABLE_PERFORMANCE_MONITORING': True
    })
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def websocket_mock():
    """Mock WebSocket for testing."""
    mock_socketio = Mock()
    
    # Import and patch websocket handlers
    from app_modules import websocket_handlers
    websocket_handlers.set_socketio(mock_socketio)
    
    return mock_socketio


@pytest.fixture
def sample_block_data():
    """Sample block data for testing."""
    return {
        'block_content': 'The implementation was done by the team and the testing was conducted by experts.',
        'block_errors': [
            {
                'type': 'passive_voice',
                'flagged_text': 'was done',
                'position': 20,
                'message': 'Consider using active voice'
            },
            {
                'type': 'passive_voice', 
                'flagged_text': 'was conducted',
                'position': 55,
                'message': 'Consider using active voice'
            }
        ],
        'block_type': 'paragraph',
        'block_id': 'test-block-001',
        'session_id': 'test-session-123'
    }


class TestBlockRewriteAPI:
    """Test the block rewrite API endpoints."""
    
    def test_block_rewrite_endpoint_exists(self, client):
        """Test that the block rewrite endpoint exists."""
        response = client.post('/rewrite-block', 
                              data=json.dumps({}),
                              content_type='application/json')
        
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
    
    def test_block_rewrite_with_valid_data(self, client, sample_block_data):
        """Test block rewrite with valid input data."""
        response = client.post('/rewrite-block',
                              data=json.dumps(sample_block_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        # Verify response structure
        assert 'rewritten_text' in result
        assert 'confidence' in result
        assert 'errors_fixed' in result
        assert 'improvements' in result
        assert 'block_id' in result
        
        # Verify block ID matches
        assert result['block_id'] == sample_block_data['block_id']
        
        # Verify errors were addressed
        if result.get('success', True):
            assert result['errors_fixed'] > 0
    
    def test_block_rewrite_invalid_input(self, client):
        """Test block rewrite with invalid input data."""
        # Empty content
        response = client.post('/rewrite-block',
                              data=json.dumps({'block_content': ''}),
                              content_type='application/json')
        assert response.status_code == 400
        
        # Malformed JSON
        response = client.post('/rewrite-block',
                              data='invalid json',
                              content_type='application/json')
        assert response.status_code == 400


class TestPerformanceMonitoring:
    """Test performance monitoring and metrics collection."""
    
    def test_performance_metrics_collection(self, websocket_mock):
        """Test that performance metrics are collected during block processing."""
        from app_modules.websocket_handlers import (
            record_block_processing_time,
            get_performance_summary,
            record_websocket_event
        )
        
        # Record some test metrics
        record_block_processing_time('test-block-001', 15.5, True)
        record_block_processing_time('test-block-002', 22.3, True)
        record_block_processing_time('test-block-003', 8.1, False)  # Failed processing
        
        record_websocket_event('block_processing_start', 'test-session-001')
        record_websocket_event('block_processing_complete', 'test-session-001')
        
        # Get performance summary
        summary = get_performance_summary()
        
        # Verify metrics are collected
        assert 'total_blocks_processed' in summary
        assert 'total_errors' in summary
        assert 'average_processing_time' in summary
        assert 'success_rate' in summary
        assert 'websocket_events' in summary
        
        # Verify calculated metrics
        assert summary['total_blocks_processed'] == 2  # 2 successful
        assert summary['total_errors'] == 1  # 1 failed
        assert summary['success_rate'] == 2/3  # 2 out of 3 successful
        assert summary['average_processing_time'] > 0


class TestCompleteWorkflow:
    """Test complete block rewrite workflow from start to finish."""
    
    def test_complete_block_workflow(self, client, websocket_mock, sample_block_data):
        """Test full workflow: API call → processing → WebSocket events → result."""
        
        # Track WebSocket events
        emitted_events = []
        
        def mock_emit(event_type, data, **kwargs):
            emitted_events.append({
                'event_type': event_type,
                'data': data,
                'kwargs': kwargs
            })
        
        websocket_mock.emit.side_effect = mock_emit
        
        # Make API call
        start_time = time.time()
        response = client.post('/rewrite-block',
                              data=json.dumps(sample_block_data),
                              content_type='application/json')
        processing_time = time.time() - start_time
        
        # Verify API response
        assert response.status_code == 200
        result = json.loads(response.data)
        
        # Verify processing completed
        assert 'rewritten_text' in result
        assert result['block_id'] == sample_block_data['block_id']
        
        # Verify performance requirements
        assert processing_time < 30  # Must complete within 30 seconds
    
    def test_performance_benchmarks(self, client, sample_block_data):
        """Test that block processing meets performance requirements."""
        
        # Test multiple blocks to get average processing time
        processing_times = []
        
        for i in range(3):  # Test 3 blocks
            block_data = sample_block_data.copy()
            block_data['block_id'] = f'benchmark-block-{i}'
            block_data['session_id'] = f'benchmark-session-{i}'
            
            start_time = time.time()
            response = client.post('/rewrite-block',
                                  data=json.dumps(block_data),
                                  content_type='application/json')
            processing_time = time.time() - start_time
            
            assert response.status_code == 200
            processing_times.append(processing_time)
        
        # Calculate average processing time
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        
        # Verify performance requirements
        assert avg_processing_time < 25  # Average < 25 seconds
        assert max_processing_time < 30  # Maximum < 30 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])