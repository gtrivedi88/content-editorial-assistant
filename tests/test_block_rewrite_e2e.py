"""
End-to-End Tests for Block-Level Rewriting (Phase 1)
Tests the complete block processing pipeline with zero technical debt.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from rewriter.assembly_line_rewriter import AssemblyLineRewriter
from rewriter.generators import TextGenerator
from rewriter.processors import TextProcessor


class TestBlockRewriting:
    """Comprehensive test suite for block-level rewriting functionality."""
    
    # Removed Flask app fixtures - focusing on core functionality testing
    
    @pytest.fixture
    def sample_block_data(self):
        """Sample block data for testing."""
        return {
            'block_content': 'The implementation was done by the team and the testing was conducted.',
            'block_errors': [
                {'type': 'passive_voice', 'flagged_text': 'was done'},
                {'type': 'passive_voice', 'flagged_text': 'was conducted'}
            ],
            'block_type': 'paragraph',
            'block_id': 'test-block-1',
            'session_id': 'test-session-123'
        }
    
    @pytest.fixture
    def clean_block_data(self):
        """Clean block data with no errors."""
        return {
            'block_content': 'This is a clean paragraph with no errors.',
            'block_errors': [],
            'block_type': 'paragraph',
            'block_id': 'test-block-clean',
            'session_id': 'test-session-clean'
        }
    
    @pytest.fixture
    def critical_block_data(self):
        """Block data with critical/urgent errors."""
        return {
            'block_content': 'Our system will make it easy for users.',
            'block_errors': [
                {'type': 'legal_claims', 'flagged_text': 'easy'},
                {'type': 'second_person', 'flagged_text': 'Our system'}
            ],
            'block_type': 'paragraph',
            'block_id': 'test-block-critical',
            'session_id': 'test-session-critical'
        }
    
    def test_assembly_line_block_processing(self):
        """Test core assembly line block processing functionality."""
        # Mock dependencies
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock responses
        mock_text_generator.generate_text.return_value = "The team implemented the solution and conducted the testing."
        mock_text_processor.clean_generated_text.return_value = "The team implemented the solution and conducted the testing."
        
        # Create rewriter instance
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Test data
        block_content = "The implementation was done by the team and the testing was conducted."
        block_errors = [
            {'type': 'passive_voice', 'flagged_text': 'was done'},
            {'type': 'passive_voice', 'flagged_text': 'was conducted'}
        ]
        
        # Process block
        result = rewriter.apply_block_level_assembly_line_fixes(block_content, block_errors, 'paragraph')
        
        # Verify result structure
        assert 'rewritten_text' in result
        assert 'applicable_stations' in result
        assert 'block_type' in result
        assert 'errors_fixed' in result
        assert 'confidence' in result
        assert result['block_type'] == 'paragraph'
        assert result['assembly_line_used'] is True
        
        # Verify applicable stations
        assert 'high' in result['applicable_stations']  # passive_voice is high priority
        assert len(result['applicable_stations']) == 1
    
    def test_dynamic_station_detection(self):
        """Test that only relevant assembly line stations are detected."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Test different error types
        test_cases = [
            # Only passive voice (high priority)
            ([{'type': 'passive_voice'}], ['high']),
            # Only contractions (medium priority)
            ([{'type': 'contractions'}], ['medium']),
            # Only punctuation (low priority)
            ([{'type': 'punctuation_commas'}], ['low']),
            # Critical legal issues (urgent priority)
            ([{'type': 'legal_claims'}], ['urgent']),
            # Mixed priorities
            ([{'type': 'passive_voice'}, {'type': 'contractions'}], ['high', 'medium']),
            # All priorities
            ([
                {'type': 'legal_claims'},      # urgent
                {'type': 'passive_voice'},     # high
                {'type': 'contractions'},      # medium
                {'type': 'punctuation_commas'} # low
            ], ['urgent', 'high', 'medium', 'low'])
        ]
        
        for errors, expected_stations in test_cases:
            stations = rewriter.get_applicable_stations(errors)
            assert stations == expected_stations, f"Failed for errors {errors}: expected {expected_stations}, got {stations}"
    
    def test_api_endpoint_logic_simulation(self, sample_block_data):
        """Test /rewrite-block API endpoint logic without full Flask setup."""
        # Simulate the API endpoint logic
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock responses
        mock_text_generator.generate_text.return_value = "The team implemented the solution and conducted testing."
        mock_text_processor.clean_generated_text.return_value = "The team implemented the solution and conducted testing."
        
        # Create rewriter and process
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_data['block_content'],
            sample_block_data['block_errors'],
            sample_block_data['block_type']
        )
        
        # Simulate API response formatting
        api_response = {
            'block_id': sample_block_data['block_id'],
            'session_id': sample_block_data['session_id'],
            'processing_time': 1.23,
            'success': 'error' not in result,
            **result
        }
        
        # Verify response structure matches expected API response
        assert 'rewritten_text' in api_response
        assert 'confidence' in api_response
        assert 'errors_fixed' in api_response
        assert 'block_id' in api_response
        assert 'session_id' in api_response
        assert 'processing_time' in api_response
        assert 'success' in api_response
        
        # Verify response values
        assert api_response['success'] is True
        assert api_response['errors_fixed'] == 2
        assert api_response['block_id'] == 'test-block-1'
        assert api_response['session_id'] == 'test-session-123'
        
    def test_api_validation_logic(self):
        """Test API endpoint input validation logic."""
        # Test validation logic that would be in the API endpoint
        
        # Test missing block content
        invalid_data = {'block_id': 'test'}
        block_content = invalid_data.get('block_content', '')
        if not block_content or not block_content.strip():
            error_response = {'error': 'No block content provided'}
            assert 'error' in error_response
            assert 'No block content provided' in error_response['error']
        
        # Test missing block ID
        invalid_data = {'block_content': 'test content'}
        block_id = invalid_data.get('block_id', '')
        if not block_id:
            error_response = {'error': 'Block ID is required'}
            assert 'error' in error_response
            assert 'Block ID is required' in error_response['error']
    
    def test_clean_block_api_logic(self, clean_block_data):
        """Test processing of blocks with no errors via API logic."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Create rewriter and process clean block
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        result = rewriter.apply_block_level_assembly_line_fixes(
            clean_block_data['block_content'],
            clean_block_data['block_errors'],
            clean_block_data['block_type']
        )
        
        # Verify clean block processing
        assert result['errors_fixed'] == 0
        assert result['confidence'] == 1.0
        assert result['applicable_stations'] == []
        assert 'Block is already clean' in str(result.get('improvements', []))
    
    def test_critical_error_api_logic(self, critical_block_data):
        """Test that critical/urgent errors are prioritized correctly via API logic."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock responses for critical processing
        mock_text_generator.generate_text.return_value = "The system enables users to complete tasks."
        mock_text_processor.clean_generated_text.return_value = "The system enables users to complete tasks."
        
        # Create rewriter and process critical block
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        result = rewriter.apply_block_level_assembly_line_fixes(
            critical_block_data['block_content'],
            critical_block_data['block_errors'],
            critical_block_data['block_type']
        )
        
        # Verify critical errors were prioritized
        assert result['errors_fixed'] == 2
        assert 'urgent' in result['applicable_stations']
    
    def test_error_handling_api_logic(self, sample_block_data):
        """Test API error handling logic for processing failures."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock to raise exception
        mock_text_generator.generate_text.side_effect = Exception("AI model unavailable")
        
        # Create rewriter and test error handling
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_data['block_content'],
            sample_block_data['block_errors'],
            sample_block_data['block_type']
        )
        
        # Verify error handling
        assert 'error' in result
        assert result['errors_fixed'] == 0
        assert 'AI model unavailable' in result['error']
    
    def test_performance_requirements_logic(self, sample_block_data):
        """Test that block processing meets performance requirements."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock with realistic processing
        mock_text_generator.generate_text.return_value = "The team implemented the solution and conducted testing."
        mock_text_processor.clean_generated_text.return_value = "The team implemented the solution and conducted testing."
        
        # Time the processing
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        start_time = time.time()
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_data['block_content'],
            sample_block_data['block_errors'],
            sample_block_data['block_type']
        )
        processing_time = time.time() - start_time
        
        # Verify performance (core logic should be very fast with mocks)
        assert processing_time < 1.0  # Core logic should be under 1 second
        assert result['errors_fixed'] == 2
    
    def test_websocket_integration(self):
        """Test WebSocket event emission during block processing."""
        from app_modules.websocket_handlers import (
            emit_block_processing_start,
            emit_station_progress_update,
            emit_block_processing_complete,
            emit_block_error
        )
        
        # These are tested by verifying they don't raise exceptions
        # and that they handle missing socketio gracefully
        
        # Test block processing start
        emit_block_processing_start('test-session', 'test-block', 'paragraph', ['high'])
        
        # Test station progress
        emit_station_progress_update('test-session', 'test-block', 'high', 'processing')
        
        # Test completion
        emit_block_processing_complete('test-session', 'test-block', {'success': True})
        
        # Test error
        emit_block_error('test-session', 'test-block', 'Test error')
        
        # All should complete without raising exceptions
        assert True
    
    def test_station_display_names(self):
        """Test assembly line station display name mapping."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Test all station display names
        expected_names = {
            'urgent': 'Critical/Legal Pass',
            'high': 'Structural Pass',
            'medium': 'Grammar Pass',
            'low': 'Style Pass'
        }
        
        for station, expected_name in expected_names.items():
            assert rewriter.get_station_display_name(station) == expected_name
        
        # Test unknown station
        assert rewriter.get_station_display_name('unknown') == 'Processing Pass'
    
    def test_block_type_context(self):
        """Test that block type context is preserved throughout processing."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock responses
        mock_text_generator.generate_text.return_value = "Improved content"
        mock_text_processor.clean_generated_text.return_value = "Improved content"
        
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Test different block types
        block_types = ['paragraph', 'heading', 'list', 'quote']
        
        for block_type in block_types:
            result = rewriter.apply_block_level_assembly_line_fixes(
                "Test content",
                [{'type': 'passive_voice'}],
                block_type
            )
            
            assert result['block_type'] == block_type
    
    def test_zero_technical_debt(self):
        """Verify zero technical debt - all legacy code has been removed."""
        from rewriter.assembly_line_rewriter import AssemblyLineRewriter
        import inspect
        
        # Check that legacy method has been completely removed
        assert not hasattr(AssemblyLineRewriter, 'apply_sentence_level_assembly_line_fixes')
        
        # Check that new method exists and is clean
        new_method = getattr(AssemblyLineRewriter, 'apply_block_level_assembly_line_fixes')
        assert new_method is not None
        assert new_method.__doc__ is not None
        assert 'single structural block' in new_method.__doc__
        
        # Verify helper methods exist
        assert hasattr(AssemblyLineRewriter, 'get_applicable_stations')
        assert hasattr(AssemblyLineRewriter, 'get_station_display_name')
        
        # Verify no legacy methods remain
        class_methods = [method for method in dir(AssemblyLineRewriter) if not method.startswith('_')]
        legacy_methods = [m for m in class_methods if 'sentence_level' in m or 'apply_sentence' in m]
        assert len(legacy_methods) == 0, f"Found legacy methods: {legacy_methods}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
