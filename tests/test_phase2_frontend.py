"""
Phase 2 Frontend End-to-End Testing
Tests the complete frontend block-level rewriting implementation.
"""

import pytest
import time
from unittest.mock import Mock, patch
from rewriter.assembly_line_rewriter import AssemblyLineRewriter
from rewriter.generators import TextGenerator
from rewriter.processors import TextProcessor


class TestPhase2Frontend:
    """Test suite for Phase 2 frontend implementation."""
    
    @pytest.fixture
    def sample_block_with_errors(self):
        """Sample block with various error types for testing."""
        return {
            'content': 'The implementation was done by the team and the system should be used by users.',
            'errors': [
                {'type': 'passive_voice', 'flagged_text': 'was done'},
                {'type': 'passive_voice', 'flagged_text': 'should be used'},
                {'type': 'second_person', 'flagged_text': 'users'}
            ],
            'block_type': 'paragraph',
            'block_id': 'block-0'
        }
    
    @pytest.fixture 
    def critical_error_block(self):
        """Block with critical/urgent errors."""
        return {
            'content': 'Our system will guarantee 100% uptime for all users.',
            'errors': [
                {'type': 'legal_claims', 'flagged_text': 'guarantee 100% uptime'},
                {'type': 'second_person', 'flagged_text': 'Our system'}
            ],
            'block_type': 'paragraph',
            'block_id': 'block-1'
        }
    
    @pytest.fixture
    def clean_block(self):
        """Block with no errors."""
        return {
            'content': 'This is a clean paragraph with no style issues.',
            'errors': [],
            'block_type': 'paragraph',
            'block_id': 'block-2'
        }
    
    def test_block_priority_calculation(self, sample_block_with_errors, critical_error_block, clean_block):
        """Test block priority calculation based on error types."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor) 
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Test mixed priority block (should be yellow for high priority)
        stations = rewriter.get_applicable_stations(sample_block_with_errors['errors'])
        assert 'urgent' in stations  # second_person is urgent
        assert 'high' in stations    # passive_voice is high
        
        # Test critical priority block (should be red)
        critical_stations = rewriter.get_applicable_stations(critical_error_block['errors'])
        assert 'urgent' in critical_stations
        assert len(critical_stations) == 1  # Only urgent station needed
        
        # Test clean block (should be green)
        clean_stations = rewriter.get_applicable_stations(clean_block['errors'])
        assert clean_stations == []
    
    def test_dynamic_station_detection(self):
        """Test that only relevant stations are detected for different error types."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        test_cases = [
            # Only urgent errors
            ([{'type': 'legal_claims'}], ['urgent']),
            # Only high priority errors  
            ([{'type': 'passive_voice'}], ['high']),
            # Only medium priority errors
            ([{'type': 'contractions'}], ['medium']),
            # Only low priority errors
            ([{'type': 'punctuation_commas'}], ['low']),
            # Mixed priorities
            ([
                {'type': 'legal_claims'},    # urgent
                {'type': 'passive_voice'},   # high
                {'type': 'contractions'},    # medium
                {'type': 'tone'}            # low
            ], ['urgent', 'high', 'medium', 'low']),
            # No errors
            ([], [])
        ]
        
        for errors, expected_stations in test_cases:
            stations = rewriter.get_applicable_stations(errors)
            assert stations == expected_stations, f"Failed for {[e['type'] for e in errors]}: expected {expected_stations}, got {stations}"
    
    def test_station_display_names(self):
        """Test station display name mapping."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
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
    
    def test_block_level_processing(self, sample_block_with_errors):
        """Test complete block-level processing pipeline."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup realistic mock responses
        mock_text_generator.generate_text.return_value = "The team implemented the solution and the system enables users to complete tasks."
        mock_text_processor.clean_generated_text.return_value = "The team implemented the solution and the system enables users to complete tasks."
        
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Process the block
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_with_errors['content'],
            sample_block_with_errors['errors'],
            sample_block_with_errors['block_type']
        )
        
        # Verify result structure
        assert 'rewritten_text' in result
        assert 'applicable_stations' in result
        assert 'block_type' in result
        assert 'errors_fixed' in result
        assert 'confidence' in result
        assert result['assembly_line_used'] is True
        
        # Verify block-specific metadata
        assert result['block_type'] == 'paragraph'
        assert result['errors_fixed'] == 3
        assert len(result['applicable_stations']) >= 1
    
    def test_clean_block_processing(self, clean_block):
        """Test processing of blocks with no errors."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        result = rewriter.apply_block_level_assembly_line_fixes(
            clean_block['content'],
            clean_block['errors'],
            clean_block['block_type']
        )
        
        # Verify clean block response
        assert result['errors_fixed'] == 0
        assert result['confidence'] == 1.0
        assert result['applicable_stations'] == []
        assert 'Block is already clean' in str(result.get('improvements', []))
        assert result['rewritten_text'] == clean_block['content']
    
    def test_error_handling(self, sample_block_with_errors):
        """Test error handling in block processing."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup mock to raise exception
        mock_text_generator.generate_text.side_effect = Exception("AI model unavailable")
        
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_with_errors['content'],
            sample_block_with_errors['errors'],
            sample_block_with_errors['block_type']
        )
        
        # Verify error handling
        assert 'error' in result
        assert result['errors_fixed'] == 0
        assert result['confidence'] == 0.0
        assert 'AI model unavailable' in result['error']
    
    def test_performance_requirements(self, sample_block_with_errors):
        """Test that block processing meets performance requirements."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        # Setup fast mock responses
        mock_text_generator.generate_text.return_value = "Improved text"
        mock_text_processor.clean_generated_text.return_value = "Improved text"
        
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        # Time the processing
        start_time = time.time()
        result = rewriter.apply_block_level_assembly_line_fixes(
            sample_block_with_errors['content'],
            sample_block_with_errors['errors'],
            sample_block_with_errors['block_type']
        )
        processing_time = time.time() - start_time
        
        # Core logic should be very fast with mocks
        assert processing_time < 1.0
        assert result['errors_fixed'] == 3
    
    def test_block_type_context_preservation(self):
        """Test that block type context is preserved throughout processing."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
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
    
    def test_wildcard_error_type_handling(self):
        """Test handling of wildcard error types (word_usage_*, punctuation_*, etc.)."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        wildcard_tests = [
            (['word_usage_a', 'word_usage_impact'], ['medium']),
            (['punctuation_commas', 'punctuation_periods'], ['low']),
            (['technical_commands'], ['medium']),
            (['references_crossref'], ['low'])
        ]
        
        for error_types, expected_stations in wildcard_tests:
            errors = [{'type': error_type} for error_type in error_types]
            stations = rewriter.get_applicable_stations(errors)
            assert stations == expected_stations, f"Failed for {error_types}: expected {expected_stations}, got {stations}"
    
    def test_frontend_integration_readiness(self):
        """Test that backend provides all data needed by frontend."""
        mock_text_generator = Mock(spec=TextGenerator)
        mock_text_processor = Mock(spec=TextProcessor)
        
        mock_text_generator.generate_text.return_value = "Improved text"
        mock_text_processor.clean_generated_text.return_value = "Improved text"
        
        rewriter = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
        
        test_errors = [
            {'type': 'passive_voice', 'flagged_text': 'was done'},
            {'type': 'legal_claims', 'flagged_text': 'guarantee'}
        ]
        
        result = rewriter.apply_block_level_assembly_line_fixes(
            "Test content was done and we guarantee results.",
            test_errors,
            'paragraph'
        )
        
        # Verify all required fields for frontend are present
        required_fields = [
            'rewritten_text',
            'confidence', 
            'errors_fixed',
            'applicable_stations',
            'block_type',
            'assembly_line_used'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify station display names are available
        for station in result['applicable_stations']:
            display_name = rewriter.get_station_display_name(station)
            assert display_name != station  # Should be human-readable
            assert len(display_name) > len(station)  # Should be descriptive


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
