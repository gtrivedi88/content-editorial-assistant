"""
Comprehensive Test Suite for Error Density Heuristic
Tests the new "error density" circuit breaker functionality that switches from surgical
to holistic rewriting when sentences have too many errors.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Import the classes we're testing
from rewriter.assembly_line_rewriter import AssemblyLineRewriter
from rewriter.prompts import PromptGenerator
from rewriter.generators import TextGenerator
from rewriter.processors import TextProcessor


@pytest.fixture
def mock_text_generator():
    """Mock text generator for testing."""
    generator = Mock(spec=TextGenerator)
    generator.generate_text.return_value = '{"corrected_text": "This is a test correction."}'
    generator.is_available.return_value = True
    return generator


@pytest.fixture
def mock_text_processor():
    """Mock text processor for testing."""
    processor = Mock(spec=TextProcessor)
    processor.clean_generated_text.return_value = "This is a test correction."
    return processor


@pytest.fixture
def assembly_line_rewriter(mock_text_generator, mock_text_processor):
    """Create AssemblyLineRewriter instance for testing."""
    return AssemblyLineRewriter(mock_text_generator, mock_text_processor)


@pytest.fixture
def prompt_generator():
    """Create PromptGenerator instance for testing."""
    return PromptGenerator()


class TestErrorDensityAnalysis:
    """Test suite for error density analysis functionality."""
    
    def test_empty_input_density_analysis(self, assembly_line_rewriter):
        """Test density analysis with empty inputs."""
        # Test empty text
        result = assembly_line_rewriter._analyze_error_density("", [])
        assert result['max_density'] == 0
        assert result['needs_holistic_rewrite'] is False
        assert result['analysis_method'] == 'empty_input'
        
        # Test empty errors
        result = assembly_line_rewriter._analyze_error_density("Some text here.", [])
        assert result['max_density'] == 0
        assert result['needs_holistic_rewrite'] is False
        
        # Test None text
        result = assembly_line_rewriter._analyze_error_density(None, [{'type': 'test'}])
        assert result['max_density'] == 0
    
    def test_single_sentence_low_density(self, assembly_line_rewriter):
        """Test density analysis with low error density (should use normal processing)."""
        text = "This is a simple sentence with few errors."
        errors = [
            {'type': 'contractions', 'span': [10, 12], 'flagged_text': 'is'},
            {'type': 'possessives', 'span': [20, 26], 'flagged_text': 'simple'}
        ]
        
        result = assembly_line_rewriter._analyze_error_density(text, errors)
        
        assert result['max_density'] < 3.0  # Should be below threshold
        assert result['needs_holistic_rewrite'] is False
        assert result['total_sentences'] == 1
        assert len(result['high_density_sentences']) == 0
        assert result['analysis_method'] == 'weighted_sentence_density'
    
    def test_single_sentence_high_density(self, assembly_line_rewriter):
        """Test density analysis with high error density (should trigger holistic rewrite)."""
        text = "In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures."
        
        # Create multiple high-complexity errors for this sentence
        errors = [
            {'type': 'passive_voice', 'span': [0, 20], 'flagged_text': 'In order to ensure'},  # Weight: 1.8
            {'type': 'ambiguity', 'span': [40, 60], 'flagged_text': 'we need to make sure'},  # Weight: 2.0
            {'type': 'verbs', 'span': [65, 85], 'flagged_text': 'that all team members'},  # Weight: 1.4
            {'type': 'sentence_length', 'span': [0, 110], 'flagged_text': text},  # Weight: 1.5
            {'type': 'pronouns', 'span': [95, 105], 'flagged_text': 'procedures'},  # Weight: 1.5
        ]
        
        result = assembly_line_rewriter._analyze_error_density(text, errors)
        
        assert result['max_density'] > 3.0  # Should exceed threshold
        assert result['needs_holistic_rewrite'] is True
        assert result['total_sentences'] == 1
        assert len(result['high_density_sentences']) == 1
        
        # Check high density sentence details
        high_density_sentence = result['high_density_sentences'][0]
        assert high_density_sentence['error_count'] == 5
        assert high_density_sentence['weighted_density'] > 3.0
        assert high_density_sentence['sentence_text'] == text
    
    def test_multiple_sentences_mixed_density(self, assembly_line_rewriter):
        """Test density analysis with multiple sentences having different densities."""
        text = "This is a simple sentence. In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures. Another simple sentence here."
        
        errors = [
            # First sentence - low density
            {'type': 'contractions', 'span': [5, 7], 'flagged_text': 'is'},
            
            # Second sentence - high density (multiple complex errors)
            {'type': 'passive_voice', 'span': [27, 47], 'flagged_text': 'In order to ensure'},
            {'type': 'ambiguity', 'span': [70, 90], 'flagged_text': 'we need to make sure'},
            {'type': 'verbs', 'span': [95, 115], 'flagged_text': 'that all team members'},
            {'type': 'sentence_length', 'span': [27, 137], 'flagged_text': 'In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures.'},
            {'type': 'pronouns', 'span': [125, 135], 'flagged_text': 'procedures'},
            
            # Third sentence - low density
            {'type': 'possessives', 'span': [145, 150], 'flagged_text': 'simple'}
        ]
        
        result = assembly_line_rewriter._analyze_error_density(text, errors)
        
        assert result['needs_holistic_rewrite'] is True  # At least one high-density sentence
        assert result['total_sentences'] == 3
        assert len(result['high_density_sentences']) == 1  # Only the middle sentence
        
        high_density_sentence = result['high_density_sentences'][0]
        assert high_density_sentence['sentence_index'] == 1  # Middle sentence (0-indexed)
        assert high_density_sentence['error_count'] == 5
    
    def test_weighted_error_density_calculation(self, assembly_line_rewriter):
        """Test weighted error density calculation with different error types."""
        sentence = "This is a test sentence for weight calculation."
        
        # High complexity errors
        high_complexity_errors = [
            {'type': 'ambiguity', 'flagged_text': 'this'},      # Weight: 2.0
            {'type': 'passive_voice', 'flagged_text': 'is'},    # Weight: 1.8
            {'type': 'sentence_length', 'flagged_text': sentence}  # Weight: 1.5
        ]
        
        high_density = assembly_line_rewriter._calculate_weighted_error_density(high_complexity_errors, sentence)
        
        # Simple errors
        simple_errors = [
            {'type': 'contractions', 'flagged_text': 'test'},   # Weight: 0.5
            {'type': 'possessives', 'flagged_text': 'sentence'}, # Weight: 0.4
            {'type': 'currency', 'flagged_text': 'for'}         # Weight: 0.2
        ]
        
        low_density = assembly_line_rewriter._calculate_weighted_error_density(simple_errors, sentence)
        
        # High complexity errors should produce higher density
        assert high_density > low_density
        assert high_density > 4.0  # Should likely exceed threshold
        assert low_density < 3.0   # Should be manageable (adjusted for length factor)
    
    def test_sentence_length_factor_adjustment(self, assembly_line_rewriter):
        """Test that sentence length affects density thresholds appropriately."""
        # Short sentence
        short_sentence = "Bad text."
        short_errors = [
            {'type': 'ambiguity', 'flagged_text': 'Bad'},      # Weight: 2.0
            {'type': 'verbs', 'flagged_text': 'text'}          # Weight: 1.4
        ]
        
        # Long sentence
        long_sentence = "This is a very long sentence with many words that should be able to handle more errors without triggering holistic rewrite mode because the error density per word is lower."
        long_errors = [
            {'type': 'ambiguity', 'flagged_text': 'This'},     # Weight: 2.0
            {'type': 'verbs', 'flagged_text': 'is'},           # Weight: 1.4
            {'type': 'passive_voice', 'flagged_text': 'should'} # Weight: 1.8
        ]
        
        short_density = assembly_line_rewriter._calculate_weighted_error_density(short_errors, short_sentence)
        long_density = assembly_line_rewriter._calculate_weighted_error_density(long_errors, long_sentence)
        
        # Short sentence should have higher density for same weighted error count
        assert short_density > long_density
        
        # Test threshold differences
        short_exceeds = assembly_line_rewriter._exceeds_density_threshold(short_density, short_sentence)
        long_exceeds = assembly_line_rewriter._exceeds_density_threshold(long_density, long_sentence)
        
        # Short sentence more likely to exceed threshold
        if short_density > 2.0:  # If significant density
            assert short_exceeds  # Should exceed due to lower threshold
    
    def test_density_threshold_adjustment_by_sentence_length(self, assembly_line_rewriter):
        """Test that density thresholds adjust based on sentence length."""
        base_density = 3.5
        
        # Very short sentence (< 8 words)
        short_sentence = "Bad text here"
        short_exceeds = assembly_line_rewriter._exceeds_density_threshold(base_density, short_sentence)
        
        # Normal sentence (8-25 words)
        normal_sentence = "This is a normal sentence with a reasonable number of words for testing purposes"
        normal_exceeds = assembly_line_rewriter._exceeds_density_threshold(base_density, normal_sentence)
        
        # Very long sentence (> 25 words)
        long_sentence = "This is a very long sentence with many words that goes on and on and should have a higher threshold for triggering holistic rewrite mode"
        long_exceeds = assembly_line_rewriter._exceeds_density_threshold(base_density, long_sentence)
        
        # Short sentences should be most likely to trigger holistic rewrite
        assert short_exceeds is True  # Should exceed with lowered threshold
        
        # Test edge case
        edge_density = 2.5  # Just above short threshold but below normal
        short_edge = assembly_line_rewriter._exceeds_density_threshold(edge_density, short_sentence)
        normal_edge = assembly_line_rewriter._exceeds_density_threshold(edge_density, normal_sentence)
        
        assert short_edge is True   # Should exceed short threshold
        assert normal_edge is False # Should not exceed normal threshold


class TestHolisticRewritePrompt:
    """Test suite for holistic rewrite prompt generation."""
    
    def test_holistic_prompt_creation(self, prompt_generator):
        """Test basic holistic prompt creation."""
        text = "In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures."
        errors = [
            {'type': 'passive_voice', 'flagged_text': 'In order to ensure'},
            {'type': 'ambiguity', 'flagged_text': 'we need to make sure'},
            {'type': 'verbs', 'flagged_text': 'that all team members'},
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors, "paragraph")
        
        # Check that prompt contains expected elements
        assert "holistically" in prompt.lower() or "comprehensive" in prompt.lower()
        assert "improvement goals" in prompt.lower()
        assert text in prompt
        assert '{"corrected_text":' in prompt  # JSON format instruction
        assert len(errors) > 0  # Should mention error count
        
        # Should not contain detailed error-by-error instructions (unlike surgical prompts)
        assert "Error 1:" not in prompt
        assert "Error 2:" not in prompt
    
    def test_holistic_prompt_improvement_goals_structural_issues(self, prompt_generator):
        """Test that holistic prompt generates appropriate goals for structural issues."""
        text = "The system processes the data when it is clicked by users."
        errors = [
            {'type': 'passive_voice', 'flagged_text': 'is clicked by users'},
            {'type': 'ambiguity', 'flagged_text': 'The system'},
            {'type': 'pronouns', 'flagged_text': 'it'}
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors, "sentence")
        
        # Should include structural improvement goals
        assert "active voice" in prompt.lower()
        assert "clear actors" in prompt.lower()
        assert "who does what" in prompt.lower() or "specify" in prompt.lower()
    
    def test_holistic_prompt_improvement_goals_grammar_issues(self, prompt_generator):
        """Test that holistic prompt generates appropriate goals for grammar issues."""
        text = "You can't use the API, but you'll need proper authentication."
        errors = [
            {'type': 'contractions', 'flagged_text': "can't"},
            {'type': 'contractions', 'flagged_text': "you'll"},
            {'type': 'word_usage_y', 'flagged_text': 'You'}
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors, "sentence")
        
        # Should include grammar improvement goals
        assert "grammar" in prompt.lower()
        assert "contractions" in prompt.lower()
        assert "professional language" in prompt.lower()
    
    def test_holistic_prompt_improvement_goals_style_issues(self, prompt_generator):
        """Test that holistic prompt generates appropriate goals for style issues."""
        text = "This amazing feature is the best solution for users."
        errors = [
            {'type': 'legal_claims', 'flagged_text': 'amazing'},
            {'type': 'legal_claims', 'flagged_text': 'best'},
            {'type': 'tone', 'flagged_text': 'amazing'}
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors, "sentence")
        
        # Should include style improvement goals
        assert "professional" in prompt.lower()
        assert "neutral tone" in prompt.lower() or "objective" in prompt.lower()
        assert "avoid subjective" in prompt.lower() or "claims" in prompt.lower()
    
    def test_holistic_prompt_improvement_goals_technical_issues(self, prompt_generator):
        """Test that holistic prompt generates appropriate goals for technical formatting."""
        text = "Run the /usr/bin/python command and check the config.json file."
        errors = [
            {'type': 'technical_files_directories', 'flagged_text': '/usr/bin/python'},
            {'type': 'technical_files_directories', 'flagged_text': 'config.json'}
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors, "sentence")
        
        # Should include technical formatting goals
        assert "technical elements" in prompt.lower()
        assert "format" in prompt.lower()
        assert "code" in prompt.lower() or "commands" in prompt.lower()
    
    def test_holistic_prompt_json_format_requirement(self, prompt_generator):
        """Test that holistic prompt enforces JSON response format."""
        text = "Test sentence."
        errors = [{'type': 'test', 'flagged_text': 'Test'}]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors)
        
        # Should enforce JSON format
        assert '{"corrected_text":' in prompt
        assert "EXACT format" in prompt
        assert "no other text before or after" in prompt.lower()
        assert "valid JSON" in prompt
    
    def test_holistic_prompt_error_density_context(self, prompt_generator):
        """Test that holistic prompt includes error density context."""
        text = "Test sentence with many errors."
        errors = [
            {'type': 'error1', 'flagged_text': 'Test'},
            {'type': 'error2', 'flagged_text': 'sentence'},
            {'type': 'error3', 'flagged_text': 'with'},
            {'type': 'error4', 'flagged_text': 'many'},
            {'type': 'error5', 'flagged_text': 'errors'}
        ]
        
        prompt = prompt_generator.create_holistic_rewrite_prompt(text, errors)
        
        # Should mention error density context
        assert "5 errors" in prompt or "multiple" in prompt.lower()
        assert "holistic" in prompt.lower() or "comprehensive" in prompt.lower()
        assert "individual fixes" in prompt.lower() or "surgical changes" in prompt.lower()


class TestHolisticRewriteIntegration:
    """Test suite for integrated holistic rewrite functionality."""
    
    def test_holistic_rewrite_application_success(self, assembly_line_rewriter, mock_text_generator):
        """Test successful application of holistic rewrite."""
        text = "In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures."
        errors = [
            {'type': 'passive_voice', 'span': [0, 20], 'flagged_text': 'In order to ensure'},
            {'type': 'ambiguity', 'span': [40, 60], 'flagged_text': 'we need to make sure'},
            {'type': 'verbs', 'span': [65, 85], 'flagged_text': 'that all team members'},
            {'type': 'sentence_length', 'span': [0, 110], 'flagged_text': text},
        ]
        
        # Mock successful AI generation
        mock_text_generator.generate_text.return_value = '{"corrected_text": "To ensure successful deployment, inform all team members about the new procedures."}'
        
        density_analysis = {
            'max_density': 4.5,
            'high_density_sentences': [{'sentence_index': 0, 'error_count': 4}],
            'needs_holistic_rewrite': True
        }
        
        result = assembly_line_rewriter._apply_holistic_rewrite(
            text, errors, "sentence", density_analysis, None
        )
        
        assert result['processing_method'] == 'holistic_rewrite'
        assert result['errors_fixed'] == len(errors)
        assert result['confidence'] > 0.8
        assert result['holistic_approach_used'] is True
        assert 'holistic rewrite' in result['improvements'][0].lower()
        assert result['rewritten_text'] != text  # Should be changed
        
        # Verify the correct prompt type was used
        mock_text_generator.generate_text.assert_called_once()
        call_args = mock_text_generator.generate_text.call_args
        assert call_args[1]['use_case'] == 'holistic_rewrite'
    
    def test_holistic_rewrite_application_no_changes(self, assembly_line_rewriter, mock_text_generator):
        """Test holistic rewrite when AI produces no changes."""
        text = "Test sentence with high density."
        errors = [{'type': 'test', 'span': [0, 10], 'flagged_text': 'Test'}]
        
        # Mock AI returning same text (no changes)
        mock_text_generator.generate_text.return_value = f'{{"corrected_text": "{text}"}}'
        
        density_analysis = {
            'max_density': 4.0,
            'high_density_sentences': [{'sentence_index': 0, 'error_count': 1}],
            'needs_holistic_rewrite': True
        }
        
        result = assembly_line_rewriter._apply_holistic_rewrite(
            text, errors, "sentence", density_analysis, None
        )
        
        assert result['processing_method'] == 'holistic_no_changes'
        assert result['errors_fixed'] == 0
        assert result['confidence'] == 0.2
        assert result['holistic_approach_used'] is True
        assert 'error' in result
        assert result['rewritten_text'] == text  # Should be unchanged
    
    def test_holistic_rewrite_application_failure(self, assembly_line_rewriter, mock_text_generator):
        """Test holistic rewrite when AI generation fails."""
        text = "Test sentence."
        errors = [{'type': 'test', 'span': [0, 4], 'flagged_text': 'Test'}]
        
        # Mock AI generation failure
        mock_text_generator.generate_text.side_effect = Exception("AI generation failed")
        
        density_analysis = {
            'max_density': 4.0,
            'high_density_sentences': [{'sentence_index': 0, 'error_count': 1}],
            'needs_holistic_rewrite': True
        }
        
        result = assembly_line_rewriter._apply_holistic_rewrite(
            text, errors, "sentence", density_analysis, None
        )
        
        assert result['processing_method'] == 'holistic_failed'
        assert result['errors_fixed'] == 0
        assert result['confidence'] == 0.0
        assert result['holistic_approach_used'] is True
        assert 'error' in result
        assert 'AI generation failed' in result['error']
        assert result['rewritten_text'] == text  # Should be unchanged
    
    def test_holistic_confidence_calculation(self, assembly_line_rewriter):
        """Test holistic confidence calculation with various scenarios."""
        # High density, many errors, successful rewrite
        high_density_analysis = {
            'max_density': 6.0,
            'high_density_sentences': [{'sentence_index': 0}, {'sentence_index': 1}]
        }
        
        high_confidence = assembly_line_rewriter._calculate_holistic_confidence(
            high_density_analysis, error_count=8, rewrite_successful=True
        )
        
        # Low density, few errors, successful rewrite  
        low_density_analysis = {
            'max_density': 3.2,
            'high_density_sentences': [{'sentence_index': 0}]
        }
        
        low_confidence = assembly_line_rewriter._calculate_holistic_confidence(
            low_density_analysis, error_count=2, rewrite_successful=True
        )
        
        # Failed rewrite
        failed_confidence = assembly_line_rewriter._calculate_holistic_confidence(
            high_density_analysis, error_count=8, rewrite_successful=False
        )
        
        # High density and error count should produce higher confidence
        assert high_confidence > low_confidence
        assert high_confidence > 0.85  # Should be quite confident
        assert low_confidence > 0.75   # Still reasonable confidence
        
        # Failed rewrite should have very low confidence
        assert failed_confidence == 0.1
        
        # All successful confidence scores should be reasonable
        assert 0.1 <= high_confidence <= 0.95
        assert 0.1 <= low_confidence <= 0.95


class TestCircuitBreakerIntegration:
    """Test suite for the circuit breaker integration in main processing flow."""
    
    @patch('rewriter.assembly_line_rewriter.AssemblyLineRewriter._apply_holistic_rewrite')
    def test_circuit_breaker_triggers_holistic_rewrite(self, mock_holistic_rewrite, assembly_line_rewriter):
        """Test that high error density triggers holistic rewrite instead of normal processing."""
        text = "In order to ensure successful deployment, we need to make sure that all team members are aware of the new procedures."
        
        # Create high-density errors that should trigger circuit breaker
        errors = [
            {'type': 'passive_voice', 'span': [0, 20], 'flagged_text': 'In order to ensure'},
            {'type': 'ambiguity', 'span': [40, 60], 'flagged_text': 'we need to make sure'},
            {'type': 'verbs', 'span': [65, 85], 'flagged_text': 'that all team members'},
            {'type': 'sentence_length', 'span': [0, 110], 'flagged_text': text},
            {'type': 'pronouns', 'span': [95, 105], 'flagged_text': 'procedures'},
        ]
        
        # Mock holistic rewrite success
        mock_holistic_rewrite.return_value = {
            'rewritten_text': 'Improved text',
            'processing_method': 'holistic_rewrite',
            'errors_fixed': len(errors),
            'confidence': 0.85,
            'holistic_approach_used': True
        }
        
        result = assembly_line_rewriter._apply_world_class_ai_fixes(text, errors, "sentence")
        
        # Verify holistic rewrite was called instead of normal processing
        mock_holistic_rewrite.assert_called_once()
        call_args = mock_holistic_rewrite.call_args[0]
        assert call_args[0] == text  # Original text
        assert call_args[1] == errors  # All errors
        assert call_args[2] == "sentence"  # Block type
        
        # Verify circuit breaker detected high density
        density_analysis_arg = call_args[3]
        assert density_analysis_arg['needs_holistic_rewrite'] is True
        assert density_analysis_arg['max_density'] > 3.0
        
        # Verify result
        assert result['processing_method'] == 'holistic_rewrite'
        assert result['holistic_approach_used'] is True
    
    def test_circuit_breaker_allows_normal_processing(self, assembly_line_rewriter):
        """Test that low error density allows normal surgical/contextual processing."""
        text = "This is a simple sentence with minimal errors."
        
        # Create low-density errors that should NOT trigger circuit breaker
        errors = [
            {'type': 'contractions', 'span': [5, 7], 'flagged_text': 'is'},
            {'type': 'possessives', 'span': [20, 26], 'flagged_text': 'simple'}
        ]
        
        # This should go through normal processing (surgical/contextual routing)
        result = assembly_line_rewriter._apply_world_class_ai_fixes(text, errors, "sentence")
        
        # Should use hybrid processing, not holistic
        assert 'holistic' not in result['processing_method']
        assert result.get('holistic_approach_used', False) is False
        
        # Should have routed to normal processing (surgical or contextual) for simple errors
        processing_method = result.get('processing_method', '')
        assert 'surgical' in processing_method or 'contextual' in processing_method


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
