"""
Enhanced Error Consolidator Integration Tests

Tests the confidence-based enhancements to ErrorConsolidator including:
- Confidence-based error prioritization
- Confidence averaging for merged errors  
- Confidence threshold filtering
- Integration with validation pipeline
- Performance impact assessment
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import json
from typing import Dict, List, Any

try:
    from error_consolidation.consolidator import ErrorConsolidator
    CONSOLIDATOR_AVAILABLE = True
except ImportError:
    CONSOLIDATOR_AVAILABLE = False

# Mock for when consolidator is not available
class MockErrorConsolidator:
    def __init__(self, *args, **kwargs):
        self.enable_enhanced_validation = False
    
    def consolidate(self, errors):
        return errors


class TestEnhancedErrorConsolidator(unittest.TestCase):
    """Test enhanced error consolidator with confidence features."""
    
    def setUp(self):
        """Set up test environment."""
        if not CONSOLIDATOR_AVAILABLE:
            self.skipTest("ErrorConsolidator not available")
        
        # Create test consolidator with enhanced validation
        self.consolidator = ErrorConsolidator(
            enable_enhanced_validation=True,
            confidence_threshold=0.4
        )
        
        # Create basic consolidator for comparison
        self.basic_consolidator = ErrorConsolidator(
            enable_enhanced_validation=False
        )
        
        # Sample errors with confidence scores
        self.sample_errors = [
            {
                'type': 'word_usage_a',
                'message': 'Use "another" instead of "an other"',
                'severity': 'medium',
                'sentence': 'This is an other example.',
                'sentence_index': 0,
                'span': (8, 16),
                'confidence_score': 0.85,
                'suggestions': ['another']
            },
            {
                'type': 'verbs',
                'message': 'Consider using active voice',
                'severity': 'low',
                'sentence': 'This is an other example.',
                'sentence_index': 0,
                'span': (8, 16),  # Same span
                'confidence_score': 0.65,
                'suggestions': ['rewrite in active voice']
            },
            {
                'type': 'word_usage_b',
                'message': 'Word usage issue detected',
                'severity': 'high',
                'sentence': 'Another sentence here.',
                'sentence_index': 1,
                'span': (0, 7),
                'confidence_score': 0.25,  # Below threshold
                'suggestions': ['improve word choice']
            },
            {
                'type': 'punctuation',
                'message': 'Missing comma',
                'severity': 'medium',
                'sentence': 'Third sentence with issue.',
                'sentence_index': 2,
                'span': (5, 13),
                'confidence_score': 0.75,
                'suggestions': ['add comma']
            }
        ]

    def test_enhanced_consolidator_initialization(self):
        """Test that enhanced consolidator initializes correctly."""
        self.assertTrue(self.consolidator.enable_enhanced_validation)
        self.assertEqual(self.consolidator.confidence_threshold, 0.4)
        self.assertIsNotNone(self.consolidator.confidence_stats)
        
        # Check that enhanced validation components are available
        status = self.consolidator.get_enhanced_validation_status()
        self.assertIn('enhanced_validation_enabled', status)
        self.assertIn('confidence_threshold', status)

    def test_confidence_based_filtering(self):
        """Test that errors below confidence threshold are filtered out."""
        # Process errors with confidence filtering
        filtered_errors = self.consolidator.consolidate(self.sample_errors)
        
        # Should filter out the error with confidence 0.25 (below 0.4 threshold)
        self.assertEqual(len(filtered_errors), 2)  # 2 consolidated + 1 individual = 3 total minus 1 filtered
        
        # Check that the low-confidence error was filtered
        error_types = {error['type'] for error in filtered_errors}
        self.assertNotIn('word_usage_b', error_types)
        
        # Check statistics
        stats = self.consolidator.get_consolidation_stats()
        self.assertIn('confidence_stats', stats)
        self.assertEqual(stats['confidence_stats']['filtered_by_confidence'], 1)

    def test_confidence_based_prioritization(self):
        """Test that higher confidence errors are prioritized in consolidation."""
        # Create errors with same span but different confidence
        high_conf_error = {
            'type': 'word_usage_a',
            'message': 'High confidence message',
            'severity': 'low',
            'sentence': 'Test sentence.',
            'sentence_index': 0,
            'span': (0, 4),
            'confidence_score': 0.9,
            'suggestions': ['high conf suggestion']
        }
        
        low_conf_error = {
            'type': 'verbs',
            'message': 'Low confidence message',
            'severity': 'high',  # Higher severity but lower confidence
            'sentence': 'Test sentence.',
            'sentence_index': 0,
            'span': (0, 4),  # Same span
            'confidence_score': 0.5,
            'suggestions': ['low conf suggestion']
        }
        
        errors = [low_conf_error, high_conf_error]
        consolidated = self.consolidator.consolidate(errors)
        
        # Should have 1 consolidated error
        self.assertEqual(len(consolidated), 1)
        
        # The primary error should be the high-confidence one despite lower severity
        merged_error = consolidated[0]
        self.assertEqual(merged_error['message'], 'High confidence message')
        self.assertIn('high conf suggestion', merged_error['suggestions'])

    def test_confidence_averaging_for_merged_errors(self):
        """Test that confidence is properly averaged for merged errors."""
        # Create multiple errors with same span
        errors_same_span = [
            {
                'type': 'word_usage_a',
                'message': 'First error',
                'severity': 'medium',
                'sentence': 'Test sentence.',
                'sentence_index': 0,
                'span': (0, 4),
                'confidence_score': 0.8,
                'suggestions': ['suggestion 1']
            },
            {
                'type': 'verbs',
                'message': 'Second error',
                'severity': 'high',
                'sentence': 'Test sentence.',
                'sentence_index': 0,
                'span': (0, 4),
                'confidence_score': 0.6,
                'suggestions': ['suggestion 2']
            },
            {
                'type': 'punctuation',
                'message': 'Third error',
                'severity': 'low',
                'sentence': 'Test sentence.',
                'sentence_index': 0,
                'span': (0, 4),
                'confidence_score': 0.7,
                'suggestions': ['suggestion 3']
            }
        ]
        
        consolidated = self.consolidator.consolidate(errors_same_span)
        
        # Should have 1 merged error
        self.assertEqual(len(consolidated), 1)
        
        merged_error = consolidated[0]
        
        # Should have confidence calculation metadata
        self.assertIn('confidence_score', merged_error)
        self.assertIn('confidence_calculation', merged_error)
        
        confidence_calc = merged_error['confidence_calculation']
        self.assertIn('method', confidence_calc)
        self.assertIn('weighted_average', confidence_calc)
        self.assertIn('simple_average', confidence_calc)
        self.assertIn('individual_confidences', confidence_calc)
        
        # Check that confidence is reasonable (between individual values)
        final_confidence = merged_error['confidence_score']
        self.assertGreaterEqual(final_confidence, 0.6)
        self.assertLessEqual(final_confidence, 0.8)

    def test_consolidation_quality_with_confidence(self):
        """Test that consolidation quality improves with confidence data."""
        # Process with enhanced consolidator
        enhanced_result = self.consolidator.consolidate(self.sample_errors.copy())
        
        # Process with basic consolidator
        basic_result = self.basic_consolidator.consolidate(self.sample_errors.copy())
        
        # Enhanced consolidator should filter out low-confidence errors
        self.assertLessEqual(len(enhanced_result), len(basic_result))
        
        # Enhanced results should have better overall confidence
        if enhanced_result:
            enhanced_confidences = [
                self.consolidator._extract_confidence_score(error) 
                for error in enhanced_result
            ]
            avg_enhanced = sum(enhanced_confidences) / len(enhanced_confidences)
            
            basic_confidences = [
                self.consolidator._extract_confidence_score(error) 
                for error in basic_result
            ]
            avg_basic = sum(basic_confidences) / len(basic_confidences)
            
            # Enhanced should have higher average confidence due to filtering
            self.assertGreaterEqual(avg_enhanced, avg_basic)

    def test_performance_impact_of_confidence_aware_consolidation(self):
        """Test performance impact of confidence-aware features."""
        # Create larger test dataset
        large_errors = []
        for i in range(50):
            large_errors.append({
                'type': f'type_{i % 5}',
                'message': f'Error message {i}',
                'severity': ['low', 'medium', 'high'][i % 3],
                'sentence': f'Sentence {i // 10}.',
                'sentence_index': i // 10,
                'span': (i % 20, (i % 20) + 5),
                'confidence_score': 0.3 + (i % 7) * 0.1,
                'suggestions': [f'suggestion_{i}']
            })
        
        # Measure enhanced consolidation time
        start_time = time.time()
        enhanced_result = self.consolidator.consolidate(large_errors.copy())
        enhanced_time = time.time() - start_time
        
        # Measure basic consolidation time
        start_time = time.time()
        basic_result = self.basic_consolidator.consolidate(large_errors.copy())
        basic_time = time.time() - start_time
        
        # Performance should be reasonable (not more than 2x slower)
        performance_ratio = enhanced_time / basic_time if basic_time > 0 else 1
        self.assertLess(performance_ratio, 2.0)
        
        # Get performance stats
        stats = self.consolidator.get_consolidation_stats()
        self.assertIn('confidence_stats', stats)

    def test_confidence_threshold_filtering(self):
        """Test different confidence thresholds."""
        # Test with very low threshold
        low_threshold_consolidator = ErrorConsolidator(
            enable_enhanced_validation=True,
            confidence_threshold=0.1
        )
        
        low_result = low_threshold_consolidator.consolidate(self.sample_errors.copy())
        
        # Test with high threshold
        high_threshold_consolidator = ErrorConsolidator(
            enable_enhanced_validation=True,
            confidence_threshold=0.8
        )
        
        high_result = high_threshold_consolidator.consolidate(self.sample_errors.copy())
        
        # High threshold should filter more errors
        self.assertLessEqual(len(high_result), len(low_result))

    def test_consolidation_result_accuracy(self):
        """Test accuracy of consolidated results."""
        consolidated = self.consolidator.consolidate(self.sample_errors.copy())
        
        for error in consolidated:
            # All errors should have required fields
            self.assertIn('type', error)
            self.assertIn('message', error)
            self.assertIn('severity', error)
            
            # Consolidated errors should have metadata
            if error.get('is_consolidated', False):
                self.assertIn('consolidated_from', error)
                self.assertIn('consolidation_count', error)
                
                # Should have confidence data if enhanced
                if self.consolidator.enable_enhanced_validation:
                    self.assertIn('confidence_score', error)

    def test_integration_with_complete_error_processing_pipeline(self):
        """Test integration with complete error processing pipeline."""
        # Simulate a complete pipeline
        errors = self.sample_errors.copy()
        
        # Step 1: Initial processing (simulate rule detection)
        for error in errors:
            error['processed_by'] = 'rule_engine'
        
        # Step 2: Consolidation with confidence
        consolidated = self.consolidator.consolidate(errors)
        
        # Step 3: Verify pipeline integrity
        for error in consolidated:
            self.assertIn('processed_by', error)
            
            # Enhanced errors should have confidence data
            if self.consolidator.enable_enhanced_validation:
                confidence = self.consolidator._extract_confidence_score(error)
                self.assertGreaterEqual(confidence, self.consolidator.confidence_threshold)
        
        # Step 4: Check final statistics
        stats = self.consolidator.get_consolidation_stats()
        self.assertIn('total_errors_input', stats)
        self.assertIn('total_errors_output', stats)
        
        if self.consolidator.enable_enhanced_validation:
            self.assertIn('confidence_stats', stats)
            self.assertIn('enhanced_validation_status', stats)

    def test_json_serialization_of_enhanced_errors(self):
        """Test that enhanced errors can be JSON serialized."""
        consolidated = self.consolidator.consolidate(self.sample_errors.copy())
        
        # All errors should be JSON serializable
        for error in consolidated:
            try:
                json_str = json.dumps(error)
                restored_error = json.loads(json_str)
                self.assertIsInstance(restored_error, dict)
            except (TypeError, ValueError) as e:
                self.fail(f"Error not JSON serializable: {e}")

    def test_backward_compatibility(self):
        """Test that enhanced consolidator maintains backward compatibility."""
        # Create errors without confidence scores
        legacy_errors = [
            {
                'type': 'word_usage',
                'message': 'Legacy error message',
                'severity': 'medium',
                'sentence': 'Legacy sentence.',
                'sentence_index': 0,
                'span': (0, 6),
                'suggestions': ['legacy suggestion']
            }
        ]
        
        # Should still process successfully
        result = self.consolidator.consolidate(legacy_errors)
        self.assertEqual(len(result), 1)
        
        # Should estimate confidence for legacy errors
        error = result[0]
        if self.consolidator.enable_enhanced_validation:
            confidence = self.consolidator._extract_confidence_score(error)
            self.assertGreater(confidence, 0)

    def test_confidence_distribution_tracking(self):
        """Test confidence distribution statistics."""
        # Process errors with various confidence levels
        varied_errors = [
            {'type': 'high', 'confidence_score': 0.9, 'severity': 'high', 'sentence': 'test', 'sentence_index': 0, 'span': (0, 1), 'message': 'high'},
            {'type': 'medium', 'confidence_score': 0.6, 'severity': 'medium', 'sentence': 'test', 'sentence_index': 1, 'span': (0, 1), 'message': 'medium'},
            {'type': 'low', 'confidence_score': 0.3, 'severity': 'low', 'sentence': 'test', 'sentence_index': 2, 'span': (0, 1), 'message': 'low'}
        ]
        
        # Set low threshold to include all
        low_threshold_consolidator = ErrorConsolidator(
            enable_enhanced_validation=True,
            confidence_threshold=0.2
        )
        
        result = low_threshold_consolidator.consolidate(varied_errors)
        stats = low_threshold_consolidator.get_consolidation_stats()
        
        # Check confidence distribution
        conf_dist = stats['confidence_stats']['confidence_distribution']
        self.assertIn('high', conf_dist)
        self.assertIn('medium', conf_dist)
        self.assertIn('low', conf_dist)


class TestErrorConsolidatorFallbacks(unittest.TestCase):
    """Test fallback behavior when enhanced validation is not available."""
    
    def test_graceful_degradation_without_enhanced_validation(self):
        """Test that consolidator works without enhanced validation."""
        # Force disable enhanced validation
        consolidator = ErrorConsolidator(enable_enhanced_validation=False)
        
        self.assertFalse(consolidator.enable_enhanced_validation)
        
        # Should still consolidate errors normally
        errors = [
            {
                'type': 'test_type',
                'message': 'Test message',
                'severity': 'medium',
                'sentence': 'Test sentence.',
                'sentence_index': 0,
                'span': (0, 4),
                'suggestions': ['test suggestion']
            }
        ]
        
        result = consolidator.consolidate(errors)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['message'], 'Test message')


if __name__ == '__main__':
    unittest.main()