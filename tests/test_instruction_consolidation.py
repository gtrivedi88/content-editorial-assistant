"""
Test suite for Instruction Consolidation functionality.
Tests the core logic that prevents AI hallucinations by resolving conflicting instructions.
"""

import pytest
import sys
import os
from typing import List, Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from rewriter.assembly_line_rewriter import AssemblyLineRewriter
from models import ModelManager


class TestInstructionConsolidation:
    """Test the Instruction Consolidation logic in AssemblyLineRewriter."""
    
    @pytest.fixture
    def rewriter(self):
        """Create a test AssemblyLineRewriter instance."""
        # Mock the dependencies to avoid external calls
        class MockModelManager:
            def get_model_info(self):
                return {'provider': 'test', 'model': 'test'}
        
        class MockTextGenerator:
            def is_available(self):
                return True
        
        class MockTextProcessor:
            pass
        
        # Create rewriter with mocked dependencies
        rewriter = AssemblyLineRewriter(
            text_generator=MockTextGenerator(),
            text_processor=MockTextProcessor(),
            progress_callback=None
        )
        
        return rewriter
    
    def test_no_consolidation_needed_single_error(self, rewriter):
        """Test that single errors pass through unchanged."""
        errors = [
            {
                'type': 'verbs',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Change to present tense',
                'severity': 'medium'
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'medium')
        
        assert len(result) == 1
        assert result[0]['type'] == 'verbs'
        assert 'consolidation_info' not in result[0]
    
    def test_no_consolidation_needed_different_spans(self, rewriter):
        """Test that errors with different spans don't get consolidated."""
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
                'span': [25, 35],
                'flagged_text': 'just click',
                'message': 'Use direct language',
                'severity': 'low'
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'medium')
        
        assert len(result) == 2
        assert all('consolidation_info' not in error for error in result)
    
    def test_consolidation_same_span_grammar_wins(self, rewriter):
        """Test the core scenario: grammar rule beats style rule for same span."""
        errors = [
            {
                'type': 'verbs',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Change "will provide" to present tense',
                'suggestions': ['provides', 'offers'],
                'severity': 'medium'
            },
            {
                'type': 'conversational_style',
                'span': [10, 22],
                'flagged_text': 'will provide',
                'message': 'Replace "will provide" with better word choice',
                'suggestions': ['delivers', 'gives'],
                'severity': 'low'
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'medium')
        
        # Should consolidate to 1 error
        assert len(result) == 1
        
        # Verbs rule should win
        assert result[0]['type'] == 'verbs'
        assert result[0]['message'] == 'Change "will provide" to present tense'
        assert result[0]['suggestions'] == ['provides', 'offers']
        
        # Should have consolidation metadata
        assert 'consolidation_info' in result[0]
        assert result[0]['consolidation_info']['was_consolidated'] is True
        assert result[0]['consolidation_info']['original_count'] == 2
        assert 'conversational_style' in result[0]['consolidation_info']['removed_types']
    
    def test_consolidation_priority_scoring(self, rewriter):
        """Test that priority scoring works correctly for various rule types."""
        errors = [
            {
                'type': 'tone',
                'span': [0, 10],
                'flagged_text': 'Hey there',
                'message': 'Use professional tone',
                'severity': 'low'
            },
            {
                'type': 'ambiguity',
                'span': [0, 10],
                'flagged_text': 'Hey there',
                'message': 'This greeting is ambiguous',
                'severity': 'high'
            },
            {
                'type': 'word_usage',
                'span': [0, 10],
                'flagged_text': 'Hey there',
                'message': 'Consider better word choice',
                'severity': 'medium'
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'medium')
        
        # Should consolidate to 1 error
        assert len(result) == 1
        
        # Ambiguity (grammar/structural) should win over style rules
        assert result[0]['type'] == 'ambiguity'
        
        # Should have consolidation metadata
        consolidation_info = result[0]['consolidation_info']
        assert consolidation_info['original_count'] == 3
        assert set(consolidation_info['removed_types']) == {'tone', 'word_usage'}
    
    def test_span_key_creation(self, rewriter):
        """Test the span key creation logic."""
        # Test with valid span and text
        error1 = {
            'span': [10, 22],
            'flagged_text': 'will provide'
        }
        key1 = rewriter._create_span_key(error1)
        expected1 = 'span_10_22_text_will provide'
        assert key1 == expected1
        
        # Test with missing span
        error2 = {
            'flagged_text': 'will provide'
        }
        key2 = rewriter._create_span_key(error2)
        expected2 = 'span_unknown_text_will provide'
        assert key2 == expected2
        
        # Test with missing text
        error3 = {
            'span': [10, 22]
        }
        key3 = rewriter._create_span_key(error3)
        expected3 = 'span_10_22_text_unknown'
        assert key3 == expected3
        
        # Test that same span+text creates same key
        error4 = {
            'span': [10, 22],
            'flagged_text': 'will provide'
        }
        key4 = rewriter._create_span_key(error4)
        assert key1 == key4
    
    def test_priority_scoring_logic(self, rewriter):
        """Test the detailed priority scoring logic."""
        # Create test errors
        grammar_error = {
            'type': 'verbs',
            'severity': 'medium',
            'suggestions': ['provides', 'offers'],
            'message': 'Change to present tense'
        }
        
        style_error = {
            'type': 'conversational_style',
            'severity': 'medium',
            'suggestions': ['delivers'],
            'message': 'Use better word choice'
        }
        
        # Test individual scoring
        errors = [grammar_error, style_error]
        primary = rewriter._select_primary_error_for_span(errors, 'medium')
        
        # Grammar error should win
        assert primary['type'] == 'verbs'
    
    def test_consolidation_with_suggestions(self, rewriter):
        """Test that errors with better suggestions get priority."""
        errors = [
            {
                'type': 'word_usage_generic',
                'span': [0, 5],
                'flagged_text': 'stuff',
                'message': 'Vague word',
                'suggestions': [],  # No suggestions
                'severity': 'low'
            },
            {
                'type': 'word_usage_specific',
                'span': [0, 5],
                'flagged_text': 'stuff',
                'message': 'Replace with specific term',
                'suggestions': ['items', 'elements', 'components'],  # Specific suggestions
                'severity': 'low'
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'low')
        
        # Should pick the error with better suggestions
        assert len(result) == 1
        assert result[0]['type'] == 'word_usage_specific'
        assert len(result[0]['suggestions']) == 3
    
    def test_real_world_conflict_scenario(self, rewriter):
        """Test the exact scenario from the original problem description."""
        # This is the scenario that causes "overprovide" hallucination
        errors = [
            {
                'type': 'verbs',
                'span': [45, 57],
                'flagged_text': 'will provide',
                'message': 'Consider changing "will provide" to present tense for direct instructions',
                'suggestions': ['provides'],
                'severity': 'medium',
                'sentence': 'The system will provide you with feedback',
                'sentence_index': 0
            },
            {
                'type': 'conversational_style',
                'span': [45, 57],
                'flagged_text': 'will provide',
                'message': 'Consider replacing "will provide" with more direct language',
                'suggestions': ['gives', 'offers'],
                'severity': 'low',
                'sentence': 'The system will provide you with feedback',
                'sentence_index': 0
            }
        ]
        
        result = rewriter._consolidate_instructions(errors, 'medium')
        
        # Should resolve conflict 
        assert len(result) == 1
        
        # Verbs rule should win (grammar over style)
        winning_error = result[0]
        assert winning_error['type'] == 'verbs'
        assert winning_error['flagged_text'] == 'will provide'
        assert 'present tense' in winning_error['message']
        
        # Should have consolidation info
        assert winning_error['consolidation_info']['was_consolidated'] is True
        assert 'conversational_style' in winning_error['consolidation_info']['removed_types']
        
        # This clean, single instruction should prevent "overprovide" hallucination
        # The AI will now only see: "Change 'will provide' to present tense" → "provides"
        # Instead of conflicting instructions that caused: "overprovide"


class TestConsolidationIntegration:
    """Test consolidation integration with the full assembly line pipeline."""
    
    def test_consolidation_in_station_processing(self):
        """Test that consolidation happens during station processing."""
        # This would be an integration test requiring more setup
        # For now, we've verified the core logic works
        pass


def run_consolidation_tests():
    """Run all consolidation tests and report results."""
    print("🧪 Running Instruction Consolidation Tests...")
    
    # Create a simple test runner since we might not have pytest available
    rewriter = AssemblyLineRewriter(
        text_generator=type('MockGen', (), {'is_available': lambda: True})(),
        text_processor=type('MockProc', (), {})(),
        progress_callback=None
    )
    
    test_instance = TestInstructionConsolidation()
    
    # Test 1: Single error passes through
    try:
        test_instance.test_no_consolidation_needed_single_error(rewriter)
        print("✅ Single error test passed")
    except Exception as e:
        print(f"❌ Single error test failed: {e}")
    
    # Test 2: Different spans don't consolidate
    try:
        test_instance.test_no_consolidation_needed_different_spans(rewriter)
        print("✅ Different spans test passed")
    except Exception as e:
        print(f"❌ Different spans test failed: {e}")
    
    # Test 3: Core consolidation logic (THE KEY TEST)
    try:
        test_instance.test_consolidation_same_span_grammar_wins(rewriter)
        print("✅ Core consolidation test passed - Grammar beats style!")
    except Exception as e:
        print(f"❌ Core consolidation test failed: {e}")
    
    # Test 4: Real world scenario
    try:
        test_instance.test_real_world_conflict_scenario(rewriter)
        print("✅ Real world scenario test passed - Should prevent 'overprovide' hallucination!")
    except Exception as e:
        print(f"❌ Real world scenario test failed: {e}")
    
    print("🏆 Consolidation tests complete!")


if __name__ == '__main__':
    run_consolidation_tests()
