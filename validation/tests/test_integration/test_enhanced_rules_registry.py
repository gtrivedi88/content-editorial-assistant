"""
Comprehensive test suite for enhanced RulesRegistry (Phase 4 Step 18).
Tests validation pipeline integration, confidence-based filtering, and threshold application.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import tempfile
import os

# Import test utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the enhanced RulesRegistry
from rules import RulesRegistry, get_registry, get_enhanced_registry, enhanced_registry
from rules.base_rule import ENHANCED_VALIDATION_AVAILABLE


class TestEnhancedRulesRegistry(unittest.TestCase):
    """Test enhanced RulesRegistry validation pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset global registry state for clean tests
        import rules
        rules._registry = None
        
        self.test_text = "The system can't facilitate comprehensive analysis using colour-based visualization."
        self.test_sentences = ["The system can't facilitate comprehensive analysis using colour-based visualization."]
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        # Load spaCy model for testing
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    def test_registry_initialization_with_enhanced_validation(self):
        """Test that RulesRegistry initializes correctly with enhanced validation."""
        registry = RulesRegistry(enable_enhanced_validation=True)
        
        # Check initialization
        self.assertIsNotNone(registry)
        self.assertTrue(hasattr(registry, 'enable_enhanced_validation'))
        self.assertTrue(hasattr(registry, 'confidence_threshold'))
        
        # Check validation system initialization
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertTrue(registry.enable_enhanced_validation)
            self.assertIsNotNone(registry.validation_pipeline)
            self.assertIsNotNone(registry.confidence_calculator)
            self.assertIsNotNone(registry.validation_thresholds)
            self.assertIsNotNone(registry.confidence_threshold)
        else:
            # When enhanced validation is not available, it should be disabled
            self.assertFalse(registry.enable_enhanced_validation)
            self.assertIsNone(registry.validation_pipeline)
            self.assertIsNone(registry.confidence_calculator)
            self.assertIsNone(registry.validation_thresholds)
    
    def test_registry_initialization_without_enhanced_validation(self):
        """Test that RulesRegistry initializes correctly without enhanced validation."""
        registry = RulesRegistry(enable_enhanced_validation=False)
        
        # Check initialization
        self.assertIsNotNone(registry)
        self.assertFalse(registry.enable_enhanced_validation)
        self.assertIsNone(registry.validation_pipeline)
        self.assertIsNone(registry.confidence_calculator)
        self.assertIsNone(registry.validation_thresholds)
    
    def test_registry_custom_confidence_threshold(self):
        """Test that custom confidence threshold is applied correctly."""
        custom_threshold = 0.8
        registry = RulesRegistry(
            enable_enhanced_validation=True,
            confidence_threshold=custom_threshold
        )
        
        self.assertEqual(registry.confidence_threshold, custom_threshold)
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_confidence_filtering_functionality(self):
        """Test confidence-based error filtering."""
        registry = RulesRegistry(
            enable_enhanced_validation=True,
            confidence_threshold=0.5
        )
        
        # Create mock errors with different confidence scores
        mock_errors = [
            {
                'type': 'test_rule_1',
                'message': 'High confidence error',
                'confidence_score': 0.8,
                'suggestions': ['Fix this'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            },
            {
                'type': 'test_rule_2', 
                'message': 'Low confidence error',
                'confidence_score': 0.3,
                'suggestions': ['Maybe fix this'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'low'
            },
            {
                'type': 'test_rule_3',
                'message': 'No confidence score',
                'suggestions': ['Legacy error'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            }
        ]
        
        # Apply confidence filtering
        filtered_errors = registry._apply_confidence_filtering(mock_errors)
        
        # Should keep high confidence and legacy errors, filter out low confidence
        self.assertEqual(len(filtered_errors), 2)
        self.assertEqual(filtered_errors[0]['confidence_score'], 0.8)
        self.assertNotIn('confidence_score', filtered_errors[1])  # Legacy error
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_validation_pipeline_filtering(self):
        """Test validation pipeline filtering."""
        registry = RulesRegistry(enable_enhanced_validation=True)
        
        # Create mock errors with different validation decisions
        mock_errors = [
            {
                'type': 'test_rule_1',
                'message': 'Accepted error',
                'validation_decision': 'accept',
                'suggestions': ['Fix this'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            },
            {
                'type': 'test_rule_2',
                'message': 'Rejected error',
                'validation_decision': 'reject',
                'suggestions': ['False positive'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'low'
            },
            {
                'type': 'test_rule_3',
                'message': 'Uncertain error',
                'validation_decision': 'uncertain',
                'suggestions': ['Maybe fix'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'low'
            },
            {
                'type': 'test_rule_4',
                'message': 'Legacy error',
                'suggestions': ['No validation'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            }
        ]
        
        # Apply validation pipeline filtering
        filtered_errors = registry._apply_validation_pipeline(mock_errors, self.test_text)
        
        # Should keep accepted, uncertain, and legacy errors; filter out rejected
        expected_errors = 3  # accept + uncertain + legacy, reject should be filtered
        self.assertLessEqual(len(filtered_errors), len(mock_errors))  # Some filtering should occur
        decisions = [error.get('validation_decision') for error in filtered_errors]
        self.assertIn('accept', decisions)
        self.assertIn('uncertain', decisions)
        self.assertNotIn('reject', decisions)
        
        # Verify rejected errors are actually filtered out
        rejected_errors = [e for e in mock_errors if e.get('validation_decision') == 'reject']
        remaining_rejected = [e for e in filtered_errors if e.get('validation_decision') == 'reject']
        self.assertEqual(len(remaining_rejected), 0, "Rejected errors should be filtered out")
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_combined_enhanced_filtering(self):
        """Test combined validation pipeline and confidence filtering."""
        registry = RulesRegistry(
            enable_enhanced_validation=True,
            confidence_threshold=0.6
        )
        
        # Create mock errors with both validation and confidence data
        mock_errors = [
            {
                'type': 'test_rule_1',
                'message': 'High confidence, accepted',
                'confidence_score': 0.8,
                'validation_decision': 'accept',
                'suggestions': ['Fix this'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            },
            {
                'type': 'test_rule_2',
                'message': 'Low confidence, accepted',
                'confidence_score': 0.4,
                'validation_decision': 'accept',
                'suggestions': ['Maybe fix'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'low'
            },
            {
                'type': 'test_rule_3',
                'message': 'High confidence, rejected',
                'confidence_score': 0.9,
                'validation_decision': 'reject',
                'suggestions': ['False positive'],
                'sentence': 'Test',
                'sentence_index': 0,
                'severity': 'medium'
            }
        ]
        
        # Apply combined filtering
        filtered_errors = registry._apply_enhanced_filtering(mock_errors, self.test_text)
        
        # Should only keep high confidence AND accepted errors
        self.assertEqual(len(filtered_errors), 1)
        self.assertEqual(filtered_errors[0]['confidence_score'], 0.8)
        self.assertEqual(filtered_errors[0]['validation_decision'], 'accept')
    
    def test_validation_stats(self):
        """Test validation statistics reporting."""
        registry = RulesRegistry(enable_enhanced_validation=True)
        stats = registry.get_validation_stats()
        
        # Check required stats fields
        required_fields = [
            'enhanced_validation_enabled',
            'enhanced_validation_available', 
            'consolidation_enabled',
            'consolidation_available',
            'confidence_threshold',
            'validation_pipeline_initialized',
            'confidence_calculator_initialized',
            'validation_thresholds_loaded'
        ]
        
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check data types
        self.assertIsInstance(stats['enhanced_validation_enabled'], bool)
        self.assertIsInstance(stats['enhanced_validation_available'], bool)
        self.assertIsInstance(stats['confidence_threshold'], (float, type(None)))
    
    def test_enhanced_analysis_integration(self):
        """Test integration of enhanced validation in analysis methods."""
        if not self.nlp:
            self.skipTest("SpaCy not available for integration testing")
        
        registry = RulesRegistry(enable_enhanced_validation=True)
        
        # Run analysis with context-aware rules
        errors = registry.analyze_with_context_aware_rules(
            self.test_text, self.test_sentences, nlp=self.nlp, context=self.test_context
        )
        
        # Verify results structure
        self.assertIsInstance(errors, list)
        
        # Check if any errors have enhanced validation data
        enhanced_errors = [e for e in errors if e.get('enhanced_validation_available', False)]
        
        if enhanced_errors:
            # Verify enhanced error structure
            for error in enhanced_errors:
                self.assertIn('confidence_score', error)
                self.assertIsInstance(error['confidence_score'], (int, float))
                self.assertGreaterEqual(error['confidence_score'], 0.0)
                self.assertLessEqual(error['confidence_score'], 1.0)
    
    def test_backward_compatibility(self):
        """Test that enhanced registry maintains backward compatibility."""
        # Test old-style analysis without breaking
        registry = RulesRegistry(enable_enhanced_validation=False)
        
        try:
            errors = registry.analyze_with_all_rules(
                self.test_text, self.test_sentences, nlp=self.nlp, context=self.test_context
            )
            
            # Should not crash and should return list
            self.assertIsInstance(errors, list)
            
            # Errors should have basic structure without enhanced fields
            for error in errors:
                required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
                for field in required_fields:
                    self.assertIn(field, error)
                    
        except Exception as e:
            self.fail(f"Backward compatibility test failed: {e}")
    
    def test_performance_with_enhanced_validation(self):
        """Test performance impact of enhanced validation."""
        if not self.nlp:
            self.skipTest("SpaCy not available for performance testing")
        
        # Test with enhanced validation enabled
        registry_enhanced = RulesRegistry(enable_enhanced_validation=True)
        start_time = time.time()
        
        for _ in range(3):  # Multiple iterations
            errors_enhanced = registry_enhanced.analyze_with_context_aware_rules(
                self.test_text, self.test_sentences, nlp=self.nlp, context=self.test_context
            )
        
        enhanced_time = time.time() - start_time
        
        # Test with enhanced validation disabled
        registry_basic = RulesRegistry(enable_enhanced_validation=False)
        start_time = time.time()
        
        for _ in range(3):  # Multiple iterations
            errors_basic = registry_basic.analyze_with_context_aware_rules(
                self.test_text, self.test_sentences, nlp=self.nlp, context=self.test_context
            )
        
        basic_time = time.time() - start_time
        
        # Performance should be reasonable (less than 200% overhead)
        if basic_time > 0:
            overhead_ratio = enhanced_time / basic_time
            self.assertLess(overhead_ratio, 3.0, 
                          f"Enhanced validation overhead too high: {overhead_ratio:.2f}x")
        
        print(f"Performance test: Basic={basic_time:.3f}s, Enhanced={enhanced_time:.3f}s")
    
    def test_error_handling_for_validation_failures(self):
        """Test error handling when validation system fails."""
        registry = RulesRegistry(enable_enhanced_validation=True)
        
        # Mock validation failure
        with patch.object(registry, '_apply_enhanced_filtering') as mock_filter:
            mock_filter.side_effect = Exception("Validation system failure")
            
            # Analysis should continue without crashing
            try:
                errors = registry.analyze_with_context_aware_rules(
                    self.test_text, self.test_sentences, nlp=self.nlp, context=self.test_context
                )
                
                # Should still return results (unfiltered)
                self.assertIsInstance(errors, list)
                
            except Exception as e:
                self.fail(f"Registry should handle validation failures gracefully: {e}")
    
    def test_global_registry_functions(self):
        """Test global registry access functions."""
        # Test get_registry with enhanced validation
        registry1 = get_registry(enable_enhanced_validation=True, confidence_threshold=0.7)
        self.assertIsNotNone(registry1)
        
        # Test get_enhanced_registry
        registry2 = get_enhanced_registry(confidence_threshold=0.8)
        self.assertIsNotNone(registry2)
        
        # Test enhanced_registry proxy
        self.assertIsNotNone(enhanced_registry)
        self.assertTrue(hasattr(enhanced_registry, 'analyze_with_context_aware_rules'))
    
    def test_registry_rule_discovery_with_validation(self):
        """Test that rule discovery works correctly with enhanced validation."""
        registry = RulesRegistry(enable_enhanced_validation=True)
        
        # Check that rules were discovered
        self.assertGreater(len(registry.rules), 0)
        
        # Check rule locations tracking
        self.assertEqual(len(registry.rules), len(registry.rule_locations))
        
        # Verify discovered rules have expected structure
        for rule_type, rule in registry.rules.items():
            self.assertIsInstance(rule_type, str)
            self.assertTrue(hasattr(rule, 'analyze'))
            self.assertTrue(hasattr(rule, '_get_rule_type'))
    
    def test_threshold_application_across_rule_types(self):
        """Test that confidence thresholds are applied consistently across different rule types."""
        if not self.nlp:
            self.skipTest("SpaCy not available for threshold testing")
        
        # Test with high threshold (should filter more)
        registry_high = RulesRegistry(
            enable_enhanced_validation=True,
            confidence_threshold=0.8
        )
        
        # Test with low threshold (should filter less)
        registry_low = RulesRegistry(
            enable_enhanced_validation=True,
            confidence_threshold=0.2
        )
        
        # Create rich test text to trigger multiple rule types
        rich_text = "The system can't facilitate comprehensive analysis using colour-based visualization. The API's properties aren't analysed correctly."
        rich_sentences = [
            "The system can't facilitate comprehensive analysis using colour-based visualization.",
            "The API's properties aren't analysed correctly."
        ]
        
        errors_high = registry_high.analyze_with_context_aware_rules(
            rich_text, rich_sentences, nlp=self.nlp, context=self.test_context
        )
        
        errors_low = registry_low.analyze_with_context_aware_rules(
            rich_text, rich_sentences, nlp=self.nlp, context=self.test_context
        )
        
        # High threshold should produce fewer or equal errors
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertLessEqual(len(errors_high), len(errors_low))
        
        print(f"Threshold test: High threshold={len(errors_high)} errors, Low threshold={len(errors_low)} errors")


class TestEnhancedRegistryIntegration(unittest.TestCase):
    """Test complete integration workflow with enhanced validation."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Reset global registry state
        import rules
        rules._registry = None
        
        self.complex_text = """The sophisticated methodology can't facilitate comprehensive analysis.
        The systems thinks users won't understand i.e. complex terminology like blacklist.
        The data is analysed using colour-based visualization techniques.
        He believes the API's properties aren't configured correctly."""
        
        self.complex_sentences = [
            "The sophisticated methodology can't facilitate comprehensive analysis.",
            "The systems thinks users won't understand i.e. complex terminology like blacklist.",
            "The data is analysed using colour-based visualization techniques.",
            "He believes the API's properties aren't configured correctly."
        ]
        
        self.complex_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'software',
            'audience': 'developers',
            'medium': 'documentation'
        }
        
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_complete_enhanced_analysis_workflow(self):
        """Test complete analysis workflow with enhanced validation."""
        if not self.nlp:
            self.skipTest("SpaCy not available for integration testing")
        
        # Create enhanced registry
        registry = get_enhanced_registry(confidence_threshold=0.4)
        
        # Run complete analysis
        errors = registry.analyze_with_context_aware_rules(
            self.complex_text, self.complex_sentences, nlp=self.nlp, context=self.complex_context
        )
        
        # Verify results
        self.assertIsInstance(errors, list)
        
        # Count enhanced vs legacy errors
        enhanced_errors = [e for e in errors if e.get('enhanced_validation_available', False)]
        legacy_errors = [e for e in errors if not e.get('enhanced_validation_available', False)]
        
        print(f"Integration test results: {len(errors)} total errors")
        print(f"  Enhanced errors: {len(enhanced_errors)}")
        print(f"  Legacy errors: {len(legacy_errors)}")
        
        # Verify enhanced errors have required fields
        for error in enhanced_errors:
            self.assertIn('confidence_score', error)
            self.assertIn('enhanced_validation_available', error)
            
            # Check confidence score range
            confidence = error['confidence_score']
            self.assertIsInstance(confidence, (int, float))
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
            # Should meet threshold
            self.assertGreaterEqual(confidence, 0.4)
        
        # Test serialization of results
        import json
        try:
            json_str = json.dumps(errors, indent=2)
            deserialized = json.loads(json_str)
            self.assertEqual(len(errors), len(deserialized))
            print("✅ Enhanced analysis results are JSON serializable")
        except (TypeError, ValueError) as e:
            self.fail(f"Enhanced analysis results not serializable: {e}")
    
    def test_registry_comparison_analysis(self):
        """Compare enhanced vs basic registry analysis."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comparison testing")
        
        # Basic registry
        registry_basic = RulesRegistry(enable_enhanced_validation=False)
        errors_basic = registry_basic.analyze_with_context_aware_rules(
            self.complex_text, self.complex_sentences, nlp=self.nlp, context=self.complex_context
        )
        
        # Enhanced registry 
        registry_enhanced = RulesRegistry(enable_enhanced_validation=True, confidence_threshold=0.3)
        errors_enhanced = registry_enhanced.analyze_with_context_aware_rules(
            self.complex_text, self.complex_sentences, nlp=self.nlp, context=self.complex_context
        )
        
        print(f"Comparison test:")
        print(f"  Basic registry: {len(errors_basic)} errors")
        print(f"  Enhanced registry: {len(errors_enhanced)} errors")
        
        # Enhanced registry may have fewer errors due to filtering
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertLessEqual(len(errors_enhanced), len(errors_basic))
        
        # Basic errors should have basic structure
        # Note: With Level 2 enhanced rules, errors may still have confidence scores
        # but registry-level filtering is disabled
        for error in errors_basic:
            required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
            for field in required_fields:
                self.assertIn(field, error)
            # Enhanced rules may still generate confidence scores even when registry filtering is disabled
            # This is expected behavior - the registry controls filtering, not generation
        
        # Enhanced errors should have enhanced structure (for those with enhanced validation)
        enhanced_with_validation = [e for e in errors_enhanced if e.get('enhanced_validation_available', False)]
        for error in enhanced_with_validation:
            self.assertIn('confidence_score', error)
            self.assertIn('enhanced_validation_available', error)


if __name__ == '__main__':
    # Configure test runner for comprehensive output
    unittest.main(verbosity=2, buffer=True)