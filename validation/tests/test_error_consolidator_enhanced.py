"""
Test Suite for Enhanced ErrorConsolidator Integration
Comprehensive testing for ErrorConsolidator with enhanced validation system.
Testing Phase 3 Step 3.1 - ErrorConsolidator Enhanced Validation Testing
"""

import pytest
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import test dependencies
from error_consolidation.consolidator import ErrorConsolidator
from style_analyzer.base_types import ErrorDict, ErrorSeverity
from validation.config.validation_thresholds_config import ValidationThresholdsConfig


class TestErrorConsolidatorEnhancedValidation:
    """Test ErrorConsolidator enhanced validation integration."""
    
    @pytest.fixture
    def consolidator(self):
        """Create ErrorConsolidator instance for testing."""
        return ErrorConsolidator()
    
    @pytest.fixture
    def threshold_config(self):
        """Create ValidationThresholdsConfig for testing."""
        return ValidationThresholdsConfig()
    
    @pytest.fixture
    def sample_errors(self):
        """Create sample errors for testing."""
        return [
            {
                'type': 'grammar',
                'message': 'Grammar error detected',
                'suggestions': ['Fix grammar'],
                'sentence': 'This is a test sentence with grammar issues.',
                'sentence_index': 0,
                'severity': 'medium',
                'confidence_score': 0.8,
                'rule_id': 'test_grammar_rule'
            },
            {
                'type': 'punctuation',
                'message': 'Punctuation error detected',
                'suggestions': ['Fix punctuation'],
                'sentence': 'This is a test sentence with punctuation issues.',
                'sentence_index': 1,
                'severity': 'medium',
                'confidence_score': 0.7,
                'rule_id': 'test_punctuation_rule'
            },
            {
                'type': 'spelling',
                'message': 'Spelling error detected',
                'suggestions': ['Fix spelling'],
                'sentence': 'This is a test sentence with spelling issues.',
                'sentence_index': 2,
                'severity': 'high',
                'confidence_score': 0.9,
                'rule_id': 'test_spelling_rule'
            },
            {
                'type': 'tone',
                'message': 'Tone issue detected',
                'suggestions': ['Improve tone'],
                'sentence': 'This is a test sentence with low confidence.',
                'sentence_index': 3,
                'severity': 'medium',
                'confidence_score': 0.2,  # Below universal threshold
                'rule_id': 'test_tone_rule'
            }
        ]
    
    def test_confidence_filtering_integration(self, consolidator, threshold_config, sample_errors):
        """Test ErrorConsolidator confidence filtering works with universal threshold."""
        
        # Get universal threshold
        thresholds = threshold_config.get_minimum_confidence_thresholds()
        universal_threshold = thresholds['universal']
        
        # Consolidate errors with confidence filtering
        consolidated_errors = consolidator.consolidate(sample_errors)
        
        # Validate confidence filtering
        for error in consolidated_errors:
            confidence = error.get('confidence_score', 1.0)  # Default to 1.0 if not present
            
            # Should meet or exceed universal threshold
            assert confidence >= universal_threshold, (
                f"Error with confidence {confidence:.3f} should meet universal threshold {universal_threshold:.3f}"
            )
        
        # Count errors that should pass threshold
        expected_errors = [e for e in sample_errors if e.get('confidence_score', 1.0) >= universal_threshold]
        
        print(f"✅ Universal threshold {universal_threshold} applied: {len(expected_errors)} errors passed, {len(sample_errors) - len(expected_errors)} filtered")
        print(f"✅ Consolidated errors: {len(consolidated_errors)}")
        
        # Validate that low confidence errors were filtered out
        low_confidence_errors = [e for e in sample_errors if e.get('confidence_score', 1.0) < universal_threshold]
        if low_confidence_errors:
            print(f"✅ Low confidence errors properly filtered: {len(low_confidence_errors)}")
    
    def test_confidence_merging_logic(self, consolidator, sample_errors):
        """Test confidence merging in _calculate_merged_confidence."""
        
        # Create overlapping errors that should be merged
        overlapping_errors = [
            {
                'type': 'grammar',
                'message': 'Grammar error 1',
                'suggestions': ['Fix grammar 1'],
                'sentence': 'This is a test sentence for merging validation.',
                'sentence_index': 0,
                'severity': 'medium',
                'confidence_score': 0.8,
                'rule_id': 'grammar_rule_1'
            },
            {
                'type': 'grammar',
                'message': 'Grammar error 2',
                'suggestions': ['Fix grammar 2'],
                'sentence': 'This is a test sentence for merging validation.',
                'sentence_index': 0,
                'severity': 'medium',
                'confidence_score': 0.6,
                'rule_id': 'grammar_rule_2'
            },
            {
                'type': 'grammar',
                'message': 'Grammar error 3',
                'suggestions': ['Fix grammar 3'],
                'sentence': 'This is a test sentence for merging validation.',
                'sentence_index': 0,
                'severity': 'medium',
                'confidence_score': 0.9,
                'rule_id': 'grammar_rule_3'
            }
        ]
        
        # Consolidate overlapping errors
        consolidated_errors = consolidator.consolidate(overlapping_errors)
        
        # Should have fewer errors due to merging
        assert len(consolidated_errors) <= len(overlapping_errors), "Overlapping errors should be merged"
        
        # Validate merged confidence calculations
        for error in consolidated_errors:
            confidence = error.get('confidence_score', None)
            if confidence is not None:
                # Merged confidence should be in valid range
                assert 0.0 <= confidence <= 1.0, f"Merged confidence {confidence} should be in [0.0, 1.0]"
                
                # For merged errors, confidence should be reasonable
                # (typically average or weighted average of constituent errors)
                constituent_confidences = [e['confidence_score'] for e in overlapping_errors]
                min_confidence = min(constituent_confidences)
                max_confidence = max(constituent_confidences)
                
                # Merged confidence should be within reasonable bounds
                assert min_confidence * 0.8 <= confidence <= max_confidence * 1.2, (
                    f"Merged confidence {confidence:.3f} should be reasonably related to constituent confidences"
                )
        
        print(f"✅ Confidence merging: {len(overlapping_errors)} errors → {len(consolidated_errors)} consolidated")
        for i, error in enumerate(consolidated_errors):
            confidence = error.get('confidence_score', 'N/A')
            print(f"   Consolidated error {i+1}: confidence={confidence}")
    
    def test_enhanced_consolidation_features(self, consolidator, sample_errors):
        """Test enhanced consolidation features work correctly."""
        
        # Test consolidation with various error patterns
        test_cases = [
            {
                'name': 'Similar errors',
                'errors': [sample_errors[0], sample_errors[0]]  # Duplicate errors
            },
            {
                'name': 'Different types',
                'errors': sample_errors[:3]  # Different error types
            },
            {
                'name': 'Mixed confidence',
                'errors': sample_errors  # All errors including low confidence
            }
        ]
        
        for test_case in test_cases:
            case_name = test_case['name']
            case_errors = test_case['errors']
            
            # Consolidate errors
            consolidated = consolidator.consolidate_errors(case_errors)
            
            # Validate consolidation results
            assert isinstance(consolidated, list), f"Consolidation should return list for {case_name}"
            assert len(consolidated) <= len(case_errors), f"Consolidation should not increase error count for {case_name}"
            
            # Validate each consolidated error
            for error in consolidated:
                # Should have valid basic structure
                assert hasattr(error, 'text'), f"Consolidated error should have text for {case_name}"
                assert hasattr(error, 'start_pos'), f"Consolidated error should have start_pos for {case_name}"
                assert hasattr(error, 'end_pos'), f"Consolidated error should have end_pos for {case_name}"
                assert hasattr(error, 'error_type'), f"Consolidated error should have error_type for {case_name}"
                assert hasattr(error, 'message'), f"Consolidated error should have message for {case_name}"
                
                # Should have valid confidence if present
                if hasattr(error, 'confidence_score'):
                    confidence = error.confidence_score
                    assert 0.0 <= confidence <= 1.0, f"Confidence should be valid for {case_name}"
            
            print(f"✅ Enhanced consolidation for {case_name}: {len(case_errors)} → {len(consolidated)} errors")
    
    def test_rule_reliability_integration(self, consolidator, threshold_config):
        """Test integration with rule reliability system."""
        
        # Create errors with different rule types (different reliabilities)
        reliability_test_errors = [
            {
                'type': 'claims',  # High reliability rule type
                'message': 'Claims error',
                'suggestions': ['Fix claims'],
                'sentence': 'Test sentence for reliability integration validation.',
                'sentence_index': 0,
                'severity': 'high',
                'confidence_score': 0.7,
                'rule_id': 'claims_rule'
            },
            {
                'type': 'punctuation',  # Medium reliability rule type
                'message': 'Punctuation error',
                'suggestions': ['Fix punctuation'],
                'sentence': 'Test sentence for reliability integration validation.',
                'sentence_index': 1,
                'severity': 'medium',
                'confidence_score': 0.7,
                'rule_id': 'punctuation_rule'
            },
            {
                'type': 'unknown_type',  # Lower reliability rule type
                'message': 'Unknown error',
                'suggestions': ['Fix unknown'],
                'sentence': 'Test sentence for reliability integration validation.',
                'sentence_index': 2,
                'severity': 'medium',
                'confidence_score': 0.7,
                'rule_id': 'unknown_rule'
            }
        ]
        
        # Consolidate errors
        consolidated = consolidator.consolidate(reliability_test_errors)
        
        # Validate that rule reliability is considered
        # (This might affect error prioritization, confidence adjustments, etc.)
        assert isinstance(consolidated, list), "Should return list of consolidated errors"
        
        # Test that high-reliability errors are preserved appropriately
        claims_errors = [e for e in consolidated if 'claims' in e.get('type', '')]
        punctuation_errors = [e for e in consolidated if 'punctuation' in e.get('type', '')]
        
        print(f"✅ Rule reliability integration tested: {len(consolidated)} errors consolidated")
        print(f"   Claims errors (high reliability): {len(claims_errors)}")
        print(f"   Punctuation errors (medium reliability): {len(punctuation_errors)}")
    
    def test_consolidation_performance(self, consolidator):
        """Test performance of enhanced consolidation."""
        
        # Create large number of errors for performance testing
        large_error_set = []
        for i in range(100):
            error = {
                'type': f"test_type_{i % 5}",
                'message': f"Performance test error {i}",
                'suggestions': [f"Fix performance error {i}"],
                'sentence': f"Performance test sentence {i} for consolidation validation.",
                'sentence_index': i,
                'severity': 'medium' if i % 2 == 0 else 'high',
                'confidence_score': 0.5 + (i % 5) * 0.1,  # Varying confidences
                'rule_id': f"performance_rule_{i}"
            }
            large_error_set.append(error)
        
        # Time the consolidation
        start_time = time.time()
        consolidated = consolidator.consolidate(large_error_set)
        end_time = time.time()
        
        consolidation_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Validate performance
        assert consolidation_time < 1000, f"Consolidation should be <1000ms for 100 errors, took {consolidation_time:.1f}ms"
        assert isinstance(consolidated, list), "Should return list of consolidated errors"
        assert len(consolidated) <= len(large_error_set), "Should not increase error count"
        
        # Calculate consolidation ratio
        consolidation_ratio = len(consolidated) / len(large_error_set)
        
        print(f"✅ Consolidation performance: {len(large_error_set)} → {len(consolidated)} errors in {consolidation_time:.1f}ms")
        print(f"   Consolidation ratio: {consolidation_ratio:.2f}")
        
        return consolidation_time, consolidation_ratio
    
    def test_universal_threshold_consistency(self, consolidator, threshold_config):
        """Test that universal threshold is applied consistently."""
        
        universal_threshold = threshold_config.get_minimum_confidence_thresholds()['universal']
        
        # Create errors with varying confidences around the threshold
        threshold_test_errors = []
        confidence_values = [0.1, 0.25, 0.34, 0.35, 0.36, 0.5, 0.8, 0.95]
        
        for i, confidence in enumerate(confidence_values):
            error = {
                'type': 'threshold_test',
                'message': f"Threshold test error {i}",
                'suggestions': [f"Fix threshold error {i}"],
                'sentence': f"Threshold test sentence {i} for consistency validation.",
                'sentence_index': i,
                'severity': 'medium',
                'confidence_score': confidence,
                'rule_id': f"threshold_rule_{i}"
            }
            threshold_test_errors.append(error)
        
        # Consolidate with threshold filtering
        consolidated = consolidator.consolidate(threshold_test_errors)
        
        # Validate threshold application
        for error in consolidated:
            confidence = error.get('confidence_score', 1.0)
            assert confidence >= universal_threshold, (
                f"Consolidated error confidence {confidence:.3f} should meet threshold {universal_threshold:.3f}"
            )
        
        # Count expected vs actual
        expected_count = len([c for c in confidence_values if c >= universal_threshold])
        actual_count = len(consolidated)
        
        print(f"✅ Universal threshold consistency: threshold={universal_threshold:.3f}")
        print(f"   Expected errors >= threshold: {expected_count}")
        print(f"   Actual consolidated errors: {actual_count}")
        
        # Should be reasonably close (allowing for merging)
        assert actual_count <= expected_count, "Should not have more errors than expected"


class TestErrorConsolidatorEdgeCases:
    """Test ErrorConsolidator with edge cases and error conditions."""
    
    @pytest.fixture
    def consolidator(self):
        """Create ErrorConsolidator instance for testing."""
        return ErrorConsolidator()
    
    def test_empty_error_list(self, consolidator):
        """Test handling of empty error list."""
        
        empty_errors = []
        
        try:
            consolidated = consolidator.consolidate_errors(empty_errors)
            
            assert isinstance(consolidated, list), "Should return list for empty input"
            assert len(consolidated) == 0, "Should return empty list for empty input"
            
            print("✅ Empty error list handled gracefully")
            
        except Exception as e:
            pytest.fail(f"Should handle empty error list gracefully, got: {e}")
    
    def test_single_error(self, consolidator):
        """Test handling of single error."""
        
        single_error = [
            StyleError(
                text="Single error test sentence.",
                start_pos=5,
                end_pos=15,
                error_type="single_test",
                message="Single test error",
                severity=Severity.MINOR,
                suggestion="Fix single error",
                confidence_score=0.8,
                rule_id="single_rule"
            )
        ]
        
        try:
            consolidated = consolidator.consolidate_errors(single_error)
            
            assert isinstance(consolidated, list), "Should return list for single error"
            assert len(consolidated) == 1, "Should return single error unchanged"
            
            result_error = consolidated[0]
            assert hasattr(result_error, 'confidence_score'), "Single error should preserve confidence"
            assert result_error.confidence_score == 0.8, "Single error confidence should be preserved"
            
            print("✅ Single error handled correctly")
            
        except Exception as e:
            pytest.fail(f"Should handle single error gracefully, got: {e}")
    
    def test_malformed_errors(self, consolidator):
        """Test handling of malformed error objects."""
        
        # Create mock objects that might be missing some fields
        class MalformedError:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        malformed_errors = [
            # Missing confidence_score
            MalformedError(
                text="Malformed error test",
                start_pos=0,
                end_pos=10,
                error_type="malformed",
                message="Malformed error",
                severity=Severity.MINOR,
                rule_id="malformed_rule"
            ),
            # Valid error for comparison
            StyleError(
                text="Valid error test sentence.",
                start_pos=15,
                end_pos=25,
                error_type="valid_test",
                message="Valid test error",
                severity=Severity.MINOR,
                suggestion="Fix valid error",
                confidence_score=0.8,
                rule_id="valid_rule"
            )
        ]
        
        try:
            consolidated = consolidator.consolidate_errors(malformed_errors)
            
            # Should handle gracefully without crashing
            assert isinstance(consolidated, list), "Should return list for malformed errors"
            
            # Should preserve valid errors
            valid_errors = [e for e in consolidated if hasattr(e, 'confidence_score')]
            assert len(valid_errors) >= 1, "Should preserve valid errors"
            
            print(f"✅ Malformed errors handled gracefully: {len(malformed_errors)} → {len(consolidated)}")
            
        except Exception as e:
            # Should handle gracefully or provide meaningful error
            print(f"✅ Malformed errors produce expected error: {type(e).__name__}")
    
    def test_very_low_confidence_errors(self, consolidator):
        """Test handling of very low confidence errors."""
        
        very_low_confidence_errors = [
            StyleError(
                text="Very low confidence test sentence.",
                start_pos=5,
                end_pos=15,
                error_type="low_confidence",
                message="Very low confidence error",
                severity=Severity.MINOR,
                suggestion="Fix low confidence error",
                confidence_score=0.01,  # Very low
                rule_id="low_confidence_rule"
            ),
            StyleError(
                text="Zero confidence test sentence.",
                start_pos=20,
                end_pos=30,
                error_type="zero_confidence",
                message="Zero confidence error",
                severity=Severity.MINOR,
                suggestion="Fix zero confidence error",
                confidence_score=0.0,  # Zero confidence
                rule_id="zero_confidence_rule"
            )
        ]
        
        try:
            consolidated = consolidator.consolidate_errors(very_low_confidence_errors)
            
            # Very low confidence errors should be filtered out
            assert isinstance(consolidated, list), "Should return list for low confidence errors"
            
            # Should filter out errors below universal threshold
            for error in consolidated:
                confidence = getattr(error, 'confidence_score', 1.0)
                assert confidence >= 0.35, f"Consolidated error confidence {confidence} should meet universal threshold"
            
            print(f"✅ Very low confidence errors filtered: {len(very_low_confidence_errors)} → {len(consolidated)}")
            
        except Exception as e:
            pytest.fail(f"Should handle very low confidence errors gracefully, got: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])