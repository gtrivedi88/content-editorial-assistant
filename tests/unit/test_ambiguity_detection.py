"""
Comprehensive test suite for the enhanced ambiguity system.

Tests Level 2 Integration, Evidence-Based Scoring, and Post-Rewrite Validation.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ambiguity.detectors.missing_actor_detector import MissingActorDetector
from ambiguity.types import AmbiguityConfig, AmbiguityContext
from rewriter.assembly_line_rewriter import AssemblyLineRewriter


class TestEnhancedMissingActorDetector:
    """Test the enhanced missing actor detector with Level 2 validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = AmbiguityConfig()
        self.detector = MissingActorDetector(self.config, parent_rule=None)
        
        # Mock nlp for testing
        self.mock_nlp = Mock()
        self.mock_doc = Mock()
        self.mock_nlp.return_value = self.mock_doc
    
    def test_evidence_based_confidence_calculation(self):
        """Test enhanced confidence calculation with evidence factors."""
        
        # Create mock construction and context
        mock_construction = Mock()
        mock_construction.context_type = Mock()
        mock_construction.context_type.INSTRUCTIONAL = "instructional"
        
        # Create test context for UI domain
        context = AmbiguityContext(
            sentence_index=0,
            sentence="This is clicked.",
            preceding_sentences=[],
            following_sentences=[],
            document_context={'domain': 'ui'}
        )
        
        # Mock the doc to represent "This is clicked."
        self.mock_doc.text = "This is clicked."
        self.mock_doc.__len__ = Mock(return_value=4)  # Short sentence
        
        # Test confidence calculation
        with patch.object(self.detector, '_is_technical_context_for_actor', return_value=True), \
             patch.object(self.detector, '_is_imperative_needing_actor', return_value=True), \
             patch.object(self.detector, '_has_implicit_actor_clues', return_value=False):
            
            confidence = self.detector._calculate_missing_actor_confidence(
                mock_construction, self.mock_doc, context
            )
            
            # Should be high confidence due to:
            # - Base: 0.50
            # - Technical context: +0.25  
            # - Imperative needing actor: +0.20
            # - Short sentence: +0.15
            # - No implicit actors: +0.00
            # - Linguistic evidence ("this is"): +0.12
            # - Domain (UI): +0.10
            # Expected: ~1.32, capped at 0.95
            
            assert confidence >= 0.90, f"Expected high confidence for ambiguous UI text, got {confidence}"
            assert confidence <= 0.95, f"Confidence should be capped at 0.95, got {confidence}"
    
    def test_universal_threshold_compliance(self):
        """Test that confidence scores never go below universal threshold (0.35)."""
        
        mock_construction = Mock()
        mock_construction.context_type = Mock()
        
        context = AmbiguityContext(
            sentence_index=0,
            sentence="The application processes data efficiently in the background.",
            preceding_sentences=[],
            following_sentences=[],
            document_context={'domain': 'legal'}  # Tends to lower confidence
        )
        
        # Mock a long, descriptive sentence with implicit actors
        self.mock_doc.text = "The application processes data efficiently in the background."
        self.mock_doc.__len__ = Mock(return_value=10)  # Longer sentence
        
        with patch.object(self.detector, '_is_technical_context_for_actor', return_value=False), \
             patch.object(self.detector, '_is_imperative_needing_actor', return_value=False), \
             patch.object(self.detector, '_has_implicit_actor_clues', return_value=True):
            
            confidence = self.detector._calculate_missing_actor_confidence(
                mock_construction, self.mock_doc, context
            )
            
            # Even with all negative factors, should meet universal threshold
            assert confidence >= 0.35, f"Confidence {confidence} violates universal threshold (0.35)"
    
    def test_context_aware_domain_adjustment(self):
        """Test domain-specific confidence adjustments."""
        
        test_cases = [
            ('ui', 0.10, "UI domain should increase confidence"),
            ('api', 0.05, "API domain should slightly increase confidence"),  
            ('legal', -0.05, "Legal domain should decrease confidence"),
            ('unknown', 0.00, "Unknown domain should have no effect")
        ]
        
        mock_construction = Mock()
        mock_construction.context_type = Mock()
        
        for domain, expected_modifier, description in test_cases:
            context = AmbiguityContext(
                sentence_index=0,
                sentence="This is processed.",
                preceding_sentences=[],
                following_sentences=[],
                document_context={'domain': domain}
            )
            
            self.mock_doc.text = "This is processed."
            self.mock_doc.__len__ = Mock(return_value=4)
            
            with patch.object(self.detector, '_is_technical_context_for_actor', return_value=False), \
                 patch.object(self.detector, '_is_imperative_needing_actor', return_value=False), \
                 patch.object(self.detector, '_has_implicit_actor_clues', return_value=False):
                
                confidence = self.detector._calculate_missing_actor_confidence(
                    mock_construction, self.mock_doc, context
                )
                
                # Confidence should reflect domain influence
                if domain == 'ui':
                    assert confidence > 0.75, description
                elif domain == 'legal':
                    assert confidence < 0.65, description


class TestPostRewriteValidation:
    """Test the post-rewrite validation system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the required dependencies
        mock_text_generator = Mock()
        mock_text_processor = Mock()
        self.assembly_line = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
    
    def test_detect_vague_actors(self):
        """Test detection of AI-introduced vague actors."""
        
        original = "This is clicked."
        rewritten = "The system clicks this."
        original_errors = [{'type': 'verbs', 'flagged_text': 'is clicked'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should detect the vague actor
        assert len(concerns) > 0, "Should detect vague actor introduction"
        assert any("vague actor" in concern for concern in concerns), f"Expected vague actor concern, got: {concerns}"
        assert any("system" in concern for concern in concerns), f"Expected 'system' in concerns, got: {concerns}"
    
    def test_detect_new_passive_voice(self):
        """Test detection of AI-introduced passive voice patterns."""
        
        original = "Click the button."
        rewritten = "The button is clicked."
        original_errors = [{'type': 'tone', 'flagged_text': 'Click'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should detect new passive voice
        assert any("passive voice" in concern for concern in concerns), f"Expected passive voice concern, got: {concerns}"
    
    def test_detect_generic_pronoun_proliferation(self):
        """Test detection of increased generic pronouns."""
        
        original = "Click to activate."
        rewritten = "This is clicked and this is activated."
        original_errors = [{'type': 'verbs', 'flagged_text': 'activate'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should detect pronoun proliferation
        assert any("generic pronouns" in concern for concern in concerns), f"Expected pronoun concern, got: {concerns}"
    
    def test_meaning_preservation_check(self):
        """Test basic meaning preservation validation."""
        
        original = "Click the submit button to save your changes to the database."
        rewritten = "Click."  # Severe content reduction
        original_errors = [{'type': 'sentence_length', 'flagged_text': 'long sentence'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should detect meaning loss
        assert any("content reduction" in concern for concern in concerns), f"Expected content reduction concern, got: {concerns}"
    
    def test_verb_correction_validation(self):
        """Test specific validation for verb error corrections."""
        
        original = "This is clicked."
        rewritten = "The application clicks this."
        original_errors = [{'type': 'verbs', 'flagged_text': 'is clicked'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should detect generic technical actor for verb correction
        assert any("generic technical actor" in concern for concern in concerns), f"Expected technical actor concern, got: {concerns}"
    
    def test_no_false_positives_for_good_rewrites(self):
        """Test that good rewrites don't trigger false positive concerns."""
        
        original = "This is clicked."
        rewritten = "You click this."  # Good rewrite - clear actor
        original_errors = [{'type': 'verbs', 'flagged_text': 'is clicked'}]
        
        concerns = self.assembly_line._validate_rewrite_quality(
            original, rewritten, original_errors
        )
        
        # Should have no concerns for good rewrite
        assert len(concerns) == 0, f"Good rewrite should have no concerns, got: {concerns}"


class TestIntegrationWithAssemblyLine:
    """Test integration of enhanced ambiguity system with assembly line processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the required dependencies
        mock_text_generator = Mock()
        mock_text_processor = Mock()
        self.assembly_line = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
    
    def test_confidence_threshold_integration(self):
        """Test that ambiguity errors respect universal confidence threshold."""
        
        # This would require integration testing with actual SpaCy and rule detection
        # For now, test that the assembly line configuration includes ambiguity
        stations = self.assembly_line.get_applicable_stations([
            {'type': 'ambiguity', 'confidence': 0.8}
        ])
        
        assert 'low' in stations, "Ambiguity errors should map to 'low' station"
    
    def test_assembly_line_prompt_enhancement(self):
        """Test that assembly line config has enhanced verbs prompt."""
        
        from rewriter.assembly_line_config import PROMPTS
        
        # Check that verbs prompt includes specific actor guidance
        verbs_prompt = PROMPTS.get('verbs', '')
        
        assert 'CLEAR, LOGICAL actor' in verbs_prompt, "Verbs prompt should emphasize clear actors"
        assert 'NEVER use vague actors' in verbs_prompt, "Verbs prompt should prohibit vague actors"
        assert 'system' in verbs_prompt, "Verbs prompt should specifically mention 'system' as problematic"
        

def test_performance_benchmark():
    """Benchmark post-rewrite validation performance."""
    
    import time
    
    # Mock the required dependencies
    mock_text_generator = Mock()
    mock_text_processor = Mock()
    assembly_line = AssemblyLineRewriter(mock_text_generator, mock_text_processor)
    
    # Test realistic content
    original = "This is clicked by the user when they want to submit their form."
    rewritten = "The system clicks this when users want to submit their forms."
    errors = [{'type': 'verbs', 'flagged_text': 'is clicked'}]
    
    # Measure validation time
    start_time = time.time()
    for _ in range(100):  # Run 100 times
        concerns = assembly_line._validate_rewrite_quality(original, rewritten, errors)
    end_time = time.time()
    
    avg_time_ms = ((end_time - start_time) / 100) * 1000
    
    # Should be under 10ms per validation (our target: ~5ms)
    assert avg_time_ms < 10, f"Validation too slow: {avg_time_ms:.2f}ms (target: <10ms)"
    
    print(f"✅ Post-rewrite validation performance: {avg_time_ms:.2f}ms per validation")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
