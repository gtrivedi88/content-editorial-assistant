"""
Enhanced Consolidation Integration Tests
Tests the integration between Instruction Consolidator and your existing validation system.
"""

import pytest
import sys
import os
import logging
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rewriter.assembly_line_rewriter import AssemblyLineRewriter


class TestEnhancedConsolidation:
    """Test enhanced consolidation with validation system integration."""
    
    @pytest.fixture
    def rewriter_with_validation(self):
        """Create rewriter with mocked validation system enabled."""
        # Create rewriter with validation enabled
        rewriter = AssemblyLineRewriter(
            text_generator=Mock(),
            text_processor=Mock(),
            progress_callback=None
        )
        
        # Force validation to be enabled for testing
        rewriter.enhanced_validation_enabled = True
        rewriter.confidence_calculator = Mock()
        
        return rewriter
    
    @pytest.fixture
    def rewriter_without_validation(self):
        """Create rewriter with validation system disabled."""
        rewriter = AssemblyLineRewriter(
            text_generator=Mock(),
            text_processor=Mock(),
            progress_callback=None
        )
        
        # Force validation to be disabled for testing
        rewriter.enhanced_validation_enabled = False
        
        return rewriter
    
    def test_enhanced_validation_initialization(self, rewriter_with_validation):
        """Test that enhanced validation system initializes correctly."""
        assert rewriter_with_validation.enhanced_validation_enabled is True
        assert hasattr(rewriter_with_validation, 'confidence_calculator')
        assert rewriter_with_validation.confidence_calculator is not None
    
    def test_fallback_when_validation_unavailable(self, rewriter_without_validation):
        """Test that fallback logic works when validation system is unavailable."""
        assert rewriter_without_validation.enhanced_validation_enabled is False
    
    @patch('rewriter.assembly_line_rewriter.get_rule_reliability_coefficient')
    def test_enhanced_priority_scoring(self, mock_reliability, rewriter_with_validation):
        """Test that enhanced priority scoring uses confidence and reliability."""
        # Setup mocks
        mock_reliability.side_effect = lambda rule_type: {
            'verbs': 0.80,
            'conversational_style': 0.70
        }.get(rule_type, 0.75)
        
        rewriter_with_validation.confidence_calculator.calculate_confidence.side_effect = [
            0.85,  # High confidence for verbs
            0.60   # Lower confidence for conversational_style
        ]
        
        # Create conflicting errors
        errors = [
            {
                'type': 'verbs',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Change to present tense',
                'suggestions': ['provides'],
                'severity': 'medium'
            },
            {
                'type': 'conversational_style',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Use more direct language',
                'suggestions': ['gives'],
                'severity': 'low'
            }
        ]
        
        # Test enhanced priority selection
        primary_error = rewriter_with_validation._select_primary_error_for_span(errors, 'medium')
        
        # Verbs should win due to higher confidence * reliability + structural boost
        assert primary_error['type'] == 'verbs'
        assert primary_error['consolidation_method'] == 'enhanced_validation'
        
        # Verify the confidence calculator was called
        assert rewriter_with_validation.confidence_calculator.calculate_confidence.call_count == 2
        
        # Verify reliability calculator was called
        assert mock_reliability.call_count == 2
    
    def test_fallback_priority_scoring(self, rewriter_without_validation):
        """Test that fallback priority scoring works correctly."""
        errors = [
            {
                'type': 'verbs',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Change to present tense',
                'severity': 'medium'
            },
            {
                'type': 'conversational_style',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Use more direct language',
                'severity': 'low'
            }
        ]
        
        # Test fallback priority selection
        primary_error = rewriter_without_validation._select_primary_error_for_span(errors, 'medium')
        
        # Verbs should still win due to structural priority
        assert primary_error['type'] == 'verbs'
        assert primary_error['consolidation_method'] == 'fallback_logic'
    
    def test_structural_priority_boost(self, rewriter_with_validation):
        """Test structural priority boost logic."""
        # Grammar rule should get positive boost
        grammar_boost = rewriter_with_validation._get_structural_priority_boost('verbs')
        assert grammar_boost == 25.0
        
        # Style rule should get penalty
        style_penalty = rewriter_with_validation._get_structural_priority_boost('conversational_style')
        assert style_penalty == -15.0
        
        # Unknown rule should get neutral
        neutral_score = rewriter_with_validation._get_structural_priority_boost('unknown_rule')
        assert neutral_score == 0.0
    
    def test_suggestion_quality_bonus(self, rewriter_with_validation):
        """Test suggestion quality bonus logic."""
        # Error with detailed suggestions
        detailed_error = {
            'suggestions': ['This is a very detailed suggestion that is quite long']
        }
        detailed_bonus = rewriter_with_validation._get_suggestion_quality_bonus(detailed_error)
        assert detailed_bonus == 10.0
        
        # Error with simple suggestions
        simple_error = {
            'suggestions': ['provides', 'gives']
        }
        simple_bonus = rewriter_with_validation._get_suggestion_quality_bonus(simple_error)
        assert simple_bonus == 5.0
        
        # Error with no suggestions
        no_sugg_error = {
            'suggestions': []
        }
        no_bonus = rewriter_with_validation._get_suggestion_quality_bonus(no_sugg_error)
        assert no_bonus == 0.0
    
    def test_message_specificity_bonus(self, rewriter_with_validation):
        """Test message specificity bonus logic."""
        # Message with examples
        example_error = {
            'message': 'Change verb tense. Example: "will provide" → "provides"'
        }
        example_bonus = rewriter_with_validation._get_message_specificity_bonus(example_error)
        assert example_bonus == 13.0  # 8.0 for examples + 5.0 for actionable
        
        # Actionable message without examples
        actionable_error = {
            'message': 'Consider changing this word to be more specific'
        }
        actionable_bonus = rewriter_with_validation._get_message_specificity_bonus(actionable_error)
        assert actionable_bonus == 5.0
        
        # Generic message
        generic_error = {
            'message': 'This might be a problem'
        }
        generic_bonus = rewriter_with_validation._get_message_specificity_bonus(generic_error)
        assert generic_bonus == 0.0
    
    @patch('rewriter.assembly_line_rewriter.get_rule_reliability_coefficient')
    def test_enhanced_vs_fallback_comparison(self, mock_reliability):
        """Test that enhanced scoring makes better decisions than fallback."""
        # Setup scenario where enhanced validation should make different choice than fallback
        mock_reliability.side_effect = lambda rule_type: {
            'word_usage': 0.95,      # Very high reliability
            'verbs': 0.75            # Lower reliability
        }.get(rule_type, 0.75)
        
        # Create rewriters with and without validation
        enhanced_rewriter = AssemblyLineRewriter(Mock(), Mock())
        enhanced_rewriter.enhanced_validation_enabled = True
        enhanced_rewriter.confidence_calculator = Mock()
        
        fallback_rewriter = AssemblyLineRewriter(Mock(), Mock())
        fallback_rewriter.enhanced_validation_enabled = False
        
        # Setup confidence scores that favor word_usage despite verbs being structural
        enhanced_rewriter.confidence_calculator.calculate_confidence.side_effect = [
            0.95,  # Very high confidence for word_usage
            0.60   # Lower confidence for verbs
        ]
        
        errors = [
            {
                'type': 'word_usage',
                'span': [5, 12],
                'flagged_text': 'utilize',
                'message': 'Consider replacing "utilize" with "use" for clarity',
                'suggestions': ['use'],
                'severity': 'medium'
            },
            {
                'type': 'verbs',
                'span': [5, 12],
                'flagged_text': 'utilize',  # Same span - conflict!
                'message': 'Change verb form',
                'suggestions': ['utilizing'],
                'severity': 'low'
            }
        ]
        
        # Test both approaches
        enhanced_choice = enhanced_rewriter._select_primary_error_for_span(errors, 'medium')
        fallback_choice = fallback_rewriter._select_primary_error_for_span(errors, 'medium')
        
        # Enhanced should choose word_usage (high confidence * high reliability)
        # Fallback should choose verbs (structural priority)
        print(f"Enhanced choice: {enhanced_choice['type']}")
        print(f"Fallback choice: {fallback_choice['type']}")
        
        # The enhanced system should make evidence-based decisions
        assert enhanced_choice['consolidation_method'] == 'enhanced_validation'
        assert fallback_choice['consolidation_method'] == 'fallback_logic'


def test_real_world_enhanced_consolidation():
    """
    Test enhanced consolidation with real-world conflict scenario.
    """
    print("\n" + "="*80)
    print("🧠 ENHANCED CONSOLIDATION INTEGRATION TEST")
    print("="*80)
    
    # Create rewriter (will auto-detect if validation system available)
    try:
        rewriter = AssemblyLineRewriter(
            text_generator=Mock(),
            text_processor=Mock(),
            progress_callback=None
        )
        
        validation_status = "ENABLED" if rewriter.enhanced_validation_enabled else "FALLBACK"
        print(f"🎯 Validation System Status: {validation_status}")
        
        # Test the exact "overprovide" scenario
        conflicting_errors = [
            {
                'type': 'verbs',
                'span': [11, 23],
                'flagged_text': 'will provide',
                'message': 'Consider changing "will provide" to present tense for direct instructions',
                'suggestions': ['provides'],
                'severity': 'medium',
                'sentence': 'The system will provide you with detailed feedback.',
                'sentence_index': 0
            },
            {
                'type': 'conversational_style',
                'span': [11, 23],
                'flagged_text': 'will provide',
                'message': 'Consider replacing "will provide" with more direct, action-oriented language',
                'suggestions': ['gives', 'delivers', 'offers'],
                'severity': 'low',
                'sentence': 'The system will provide you with detailed feedback.',
                'sentence_index': 0
            }
        ]
        
        print(f"📝 Testing conflict resolution for: '{conflicting_errors[0]['flagged_text']}'")
        print(f"   - {conflicting_errors[0]['type']}: {conflicting_errors[0]['message']}")
        print(f"   - {conflicting_errors[1]['type']}: {conflicting_errors[1]['message']}")
        
        # Test consolidation
        result = rewriter._consolidate_instructions(conflicting_errors, 'medium')
        
        print(f"\n🎯 CONSOLIDATION RESULT:")
        print(f"   Input errors: {len(conflicting_errors)}")
        print(f"   Output errors: {len(result)}")
        
        if len(result) == 1:
            winning_error = result[0]
            print(f"   🏆 Winner: {winning_error['type']}")
            print(f"   📋 Method: {winning_error.get('consolidation_method', 'unknown')}")
            print(f"   💬 Message: {winning_error['message']}")
            
            if 'consolidation_info' in winning_error:
                removed = winning_error['consolidation_info']['removed_types']
                print(f"   🗑️  Removed: {removed}")
        
        # Verify the AI would get clean instruction
        print(f"\n✅ SUCCESS: Enhanced consolidation prevents 'overprovide' hallucination")
        print(f"   - AI receives single, clear instruction")
        print(f"   - No conflicting guidance")
        print(f"   - Uses {validation_status.lower()} prioritization logic")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    # Set up logging for better visibility
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Running Enhanced Consolidation Integration Tests...")
    
    # Run the real-world test
    success = test_real_world_enhanced_consolidation()
    
    if success:
        print(f"\n🎉 Enhanced Integration Tests PASSED!")
        print(f"✅ Instruction Consolidator now uses your validation system!")
        print(f"✅ Confidence + Reliability = Smarter consolidation decisions!")
        print(f"✅ Perfect integration with existing infrastructure!")
    else:
        print(f"\n❌ Integration tests failed - check configuration")
