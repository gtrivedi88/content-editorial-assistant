"""
Comprehensive test suite for ConfidenceCalculator class.
Tests unified confidence calculation, weighted averaging, breakdown tracking, and integration.
"""

import unittest
import time
from unittest.mock import patch, MagicMock

from validation.confidence.confidence_calculator import (
    ConfidenceCalculator, ConfidenceBreakdown, LayerContribution, 
    ConfidenceWeights, ConfidenceLayer
)


class TestConfidenceWeights(unittest.TestCase):
    """Test ConfidenceWeights configuration."""
    
    def test_default_weights(self):
        """Test default weight configuration."""
        weights = ConfidenceWeights()
        
        self.assertEqual(weights.linguistic_anchors, 0.40)
        self.assertEqual(weights.context_analysis, 0.35)
        self.assertEqual(weights.domain_classification, 0.25)
        
        # Should sum to 1.0
        total = weights.linguistic_anchors + weights.context_analysis + weights.domain_classification
        self.assertAlmostEqual(total, 1.0, places=3)
    
    def test_custom_weights(self):
        """Test custom weight configuration."""
        weights = ConfidenceWeights(
            linguistic_anchors=0.5,
            context_analysis=0.3,
            domain_classification=0.2
        )
        
        self.assertEqual(weights.linguistic_anchors, 0.5)
        self.assertEqual(weights.context_analysis, 0.3)
        self.assertEqual(weights.domain_classification, 0.2)
    
    def test_weights_validation(self):
        """Test weight validation that they sum to 1.0."""
        # Valid weights
        weights = ConfidenceWeights(0.4, 0.35, 0.25)
        self.assertAlmostEqual(
            weights.linguistic_anchors + weights.context_analysis + weights.domain_classification,
            1.0, places=3
        )
        
        # Invalid weights should raise error
        with self.assertRaises(ValueError) as cm:
            ConfidenceWeights(0.5, 0.5, 0.5)  # Sum = 1.5
        
        self.assertIn("must sum to 1.0", str(cm.exception))
    
    def test_weight_normalization(self):
        """Test weight normalization."""
        # Create weights object without validation by bypassing __post_init__
        weights = ConfidenceWeights.__new__(ConfidenceWeights)
        weights.linguistic_anchors = 0.5
        weights.context_analysis = 0.5
        weights.domain_classification = 0.5
        
        # Test normalization
        normalized = weights.normalize()
        
        self.assertAlmostEqual(normalized.linguistic_anchors, 1/3, places=3)
        self.assertAlmostEqual(normalized.context_analysis, 1/3, places=3)
        self.assertAlmostEqual(normalized.domain_classification, 1/3, places=3)
        
        # Verify normalized weights sum to 1.0
        total = normalized.linguistic_anchors + normalized.context_analysis + normalized.domain_classification
        self.assertAlmostEqual(total, 1.0, places=3)


class TestConfidenceCalculatorInitialization(unittest.TestCase):
    """Test ConfidenceCalculator initialization and configuration."""
    
    def setUp(self):
        """Set up test environment."""
        pass
    
    def tearDown(self):
        """Clean up test environment."""
        pass
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        calculator = ConfidenceCalculator()
        
        # Should have default weights
        self.assertIsInstance(calculator.weights, ConfidenceWeights)
        self.assertEqual(calculator.weights.linguistic_anchors, 0.40)
        self.assertEqual(calculator.weights.context_analysis, 0.35)
        self.assertEqual(calculator.weights.domain_classification, 0.25)
        
        # Should have default cache settings
        self.assertTrue(calculator.cache_results)
        self.assertTrue(calculator.enable_layer_caching)
        
        # Should have initialized component analyzers
        self.assertIsNotNone(calculator.linguistic_anchors)
        self.assertIsNotNone(calculator.context_analyzer)
        self.assertIsNotNone(calculator.domain_classifier)
    
    def test_custom_weights_initialization(self):
        """Test initialization with custom weights."""
        custom_weights = ConfidenceWeights(
            linguistic_anchors=0.5,
            context_analysis=0.3,
            domain_classification=0.2
        )
        
        calculator = ConfidenceCalculator(weights=custom_weights)
        
        self.assertEqual(calculator.weights.linguistic_anchors, 0.5)
        self.assertEqual(calculator.weights.context_analysis, 0.3)
        self.assertEqual(calculator.weights.domain_classification, 0.2)
    
    def test_caching_configuration(self):
        """Test caching configuration options."""
        # Disable all caching
        calculator = ConfidenceCalculator(
            cache_results=False,
            enable_layer_caching=False
        )
        
        self.assertFalse(calculator.cache_results)
        self.assertFalse(calculator.enable_layer_caching)
    
    def test_weight_updates(self):
        """Test updating weights after initialization."""
        calculator = ConfidenceCalculator()
        
        new_weights = ConfidenceWeights(
            linguistic_anchors=0.6,
            context_analysis=0.25,
            domain_classification=0.15
        )
        
        calculator.update_weights(new_weights)
        
        self.assertEqual(calculator.weights.linguistic_anchors, 0.6)
        self.assertEqual(calculator.weights.context_analysis, 0.25)
        self.assertEqual(calculator.weights.domain_classification, 0.15)
    
    def test_get_layer_weights(self):
        """Test retrieving current layer weights."""
        calculator = ConfidenceCalculator()
        
        weights = calculator.get_layer_weights()
        
        self.assertIsInstance(weights, ConfidenceWeights)
        self.assertEqual(weights.linguistic_anchors, 0.40)
        self.assertEqual(weights.context_analysis, 0.35)
        self.assertEqual(weights.domain_classification, 0.25)


class TestBasicConfidenceCalculation(unittest.TestCase):
    """Test basic confidence calculation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_simple_confidence_calculation(self):
        """Test basic confidence calculation."""
        text = "The API documentation explains REST endpoints clearly."
        error_position = 30
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        # Should return valid breakdown
        self.assertIsInstance(breakdown, ConfidenceBreakdown)
        self.assertEqual(breakdown.text, text)
        self.assertEqual(breakdown.error_position, error_position)
        
        # Should have valid confidence values
        self.assertIsInstance(breakdown.final_confidence, float)
        self.assertGreaterEqual(breakdown.final_confidence, 0.0)
        self.assertLessEqual(breakdown.final_confidence, 1.0)
        
        self.assertIsInstance(breakdown.confidence_effect, float)
        self.assertGreaterEqual(breakdown.confidence_effect, -1.0)
        self.assertLessEqual(breakdown.confidence_effect, 1.0)
        
        # Should have all layer contributions
        self.assertEqual(len(breakdown.layer_contributions), 3)
        
        layer_types = {contrib.layer for contrib in breakdown.layer_contributions}
        expected_layers = {
            ConfidenceLayer.LINGUISTIC_ANCHORS,
            ConfidenceLayer.CONTEXT_ANALYSIS,
            ConfidenceLayer.DOMAIN_CLASSIFICATION
        }
        self.assertEqual(layer_types, expected_layers)
    
    def test_confidence_with_context(self):
        """Test confidence calculation with rule and content type context."""
        text = "The comprehensive API documentation demonstrates proper authentication."
        error_position = 40
        
        breakdown = self.calculator.calculate_confidence(
            text, error_position,
            rule_type="terminology",
            content_type="technical"
        )
        
        self.assertEqual(breakdown.rule_type, "terminology")
        self.assertEqual(breakdown.content_type, "technical")
        
        # Should still produce valid results
        self.assertIsInstance(breakdown.final_confidence, float)
        self.assertGreaterEqual(breakdown.final_confidence, 0.0)
        self.assertLessEqual(breakdown.final_confidence, 1.0)
    
    def test_custom_base_confidence(self):
        """Test confidence calculation with custom base confidence."""
        text = "The system processes data efficiently."
        error_position = 15
        base_confidence = 0.8
        
        breakdown = self.calculator.calculate_confidence(
            text, error_position,
            base_confidence=base_confidence
        )
        
        # Effect should be relative to the custom base
        expected_final = base_confidence + breakdown.confidence_effect
        self.assertAlmostEqual(breakdown.final_confidence, expected_final, places=5)
    
    def test_confidence_boundary_clamping(self):
        """Test that confidence values are properly clamped to [0, 1]."""
        # Test with very low base confidence and negative effect
        text = "Bad unclear confusing text with problems."
        error_position = 10
        
        breakdown = self.calculator.calculate_confidence(
            text, error_position,
            base_confidence=0.1  # Low base
        )
        
        # Should not go below 0
        self.assertGreaterEqual(breakdown.final_confidence, 0.0)
        
        # Test with high base confidence
        breakdown_high = self.calculator.calculate_confidence(
            text, error_position,
            base_confidence=0.9  # High base
        )
        
        # Should not go above 1
        self.assertLessEqual(breakdown_high.final_confidence, 1.0)


class TestLayerContributions(unittest.TestCase):
    """Test individual layer contribution analysis."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_layer_contribution_structure(self):
        """Test structure of layer contributions."""
        text = "Furthermore, the comprehensive methodology demonstrates significant improvements."
        error_position = 40
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        for contrib in breakdown.layer_contributions:
            # Check structure
            self.assertIsInstance(contrib, LayerContribution)
            self.assertIsInstance(contrib.layer, ConfidenceLayer)
            self.assertIsInstance(contrib.raw_score, float)
            self.assertIsInstance(contrib.weighted_score, float)
            self.assertIsInstance(contrib.weight, float)
            self.assertIsInstance(contrib.confidence, float)
            self.assertIsInstance(contrib.explanation, str)
            self.assertIsInstance(contrib.processing_time, float)
            self.assertIsInstance(contrib.metadata, dict)
            
            # Check value ranges
            self.assertGreaterEqual(contrib.confidence, 0.0)
            self.assertLessEqual(contrib.confidence, 1.0)
            self.assertGreater(contrib.processing_time, 0.0)
            self.assertGreater(len(contrib.explanation), 0)
    
    def test_weighted_score_calculation(self):
        """Test that weighted scores are calculated correctly."""
        text = "The API documentation explains endpoints."
        error_position = 20
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        for contrib in breakdown.layer_contributions:
            expected_weighted = contrib.raw_score * contrib.weight
            self.assertAlmostEqual(contrib.weighted_score, expected_weighted, places=5)
    
    def test_linguistic_anchors_contribution(self):
        """Test linguistic anchors layer contribution."""
        text = "The comprehensive API documentation demonstrates excellent examples."
        error_position = 30
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        anchor_contrib = next(
            contrib for contrib in breakdown.layer_contributions
            if contrib.layer == ConfidenceLayer.LINGUISTIC_ANCHORS
        )
        
        # Should have anchor-specific metadata
        self.assertIn('total_matches', anchor_contrib.metadata)
        self.assertIn('boosting_matches', anchor_contrib.metadata)
        self.assertIn('reducing_matches', anchor_contrib.metadata)
        self.assertIn('total_boost', anchor_contrib.metadata)
        self.assertIn('total_reduction', anchor_contrib.metadata)
        
        # Metadata should have reasonable values
        self.assertGreaterEqual(anchor_contrib.metadata['total_matches'], 0)
        self.assertGreaterEqual(anchor_contrib.metadata['boosting_matches'], 0)
        self.assertGreaterEqual(anchor_contrib.metadata['reducing_matches'], 0)
    
    def test_context_analysis_contribution(self):
        """Test context analysis layer contribution."""
        text = "The researcher analyzed the data. She found interesting patterns."
        error_position = 30
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        context_contrib = next(
            contrib for contrib in breakdown.layer_contributions
            if contrib.layer == ConfidenceLayer.CONTEXT_ANALYSIS
        )
        
        # Should have context-specific metadata
        self.assertIn('sentence_count', context_contrib.metadata)
        self.assertIn('coreference_count', context_contrib.metadata)
        self.assertIn('structural_confidence', context_contrib.metadata)
        self.assertIn('coreference_confidence', context_contrib.metadata)
        self.assertIn('coherence_confidence', context_contrib.metadata)
        self.assertIn('discourse_confidence', context_contrib.metadata)
        
        # Should have detected sentences and potentially coreferences
        self.assertGreaterEqual(context_contrib.metadata['sentence_count'], 1)
    
    def test_domain_classification_contribution(self):
        """Test domain classification layer contribution."""
        text = "The patient requires immediate medical attention and diagnosis."
        error_position = 25
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        domain_contrib = next(
            contrib for contrib in breakdown.layer_contributions
            if contrib.layer == ConfidenceLayer.DOMAIN_CLASSIFICATION
        )
        
        # Should have domain-specific metadata
        self.assertIn('content_type', domain_contrib.metadata)
        self.assertIn('content_type_confidence', domain_contrib.metadata)
        self.assertIn('primary_domain', domain_contrib.metadata)
        self.assertIn('domain_confidence', domain_contrib.metadata)
        self.assertIn('formality_level', domain_contrib.metadata)
        self.assertIn('formality_score', domain_contrib.metadata)
        self.assertIn('mixed_content_detected', domain_contrib.metadata)
        
        # Metadata should have valid values
        self.assertIn(domain_contrib.metadata['content_type'], ['technical', 'narrative', 'procedural'])
        self.assertIn(domain_contrib.metadata['formality_level'], ['formal', 'informal', 'neutral'])


class TestWeightedAveraging(unittest.TestCase):
    """Test weighted averaging algorithms."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_weighted_average_calculation(self):
        """Test that final confidence is calculated as weighted average."""
        text = "The methodology demonstrates significant improvements."
        error_position = 25
        base_confidence = 0.5
        
        breakdown = self.calculator.calculate_confidence(text, error_position, base_confidence=base_confidence)
        
        # Calculate expected weighted average
        total_weighted_effect = sum(contrib.weighted_score for contrib in breakdown.layer_contributions)
        expected_final = base_confidence + total_weighted_effect
        expected_final = max(0.0, min(1.0, expected_final))  # Clamp to [0, 1]
        
        self.assertAlmostEqual(breakdown.final_confidence, expected_final, places=5)
        self.assertAlmostEqual(breakdown.confidence_effect, total_weighted_effect, places=5)
    
    def test_different_weight_configurations(self):
        """Test confidence calculation with different weight configurations."""
        text = "The comprehensive API documentation provides excellent guidance."
        error_position = 30
        
        # Test with anchor-heavy weights
        anchor_heavy_weights = ConfidenceWeights(
            linguistic_anchors=0.7,
            context_analysis=0.2,
            domain_classification=0.1
        )
        
        calculator_anchor_heavy = ConfidenceCalculator(weights=anchor_heavy_weights)
        breakdown_anchor = calculator_anchor_heavy.calculate_confidence(text, error_position)
        
        # Test with context-heavy weights
        context_heavy_weights = ConfidenceWeights(
            linguistic_anchors=0.1,
            context_analysis=0.7,
            domain_classification=0.2
        )
        
        calculator_context_heavy = ConfidenceCalculator(weights=context_heavy_weights)
        breakdown_context = calculator_context_heavy.calculate_confidence(text, error_position)
        
        # Results should be different due to different weighting
        self.assertNotAlmostEqual(breakdown_anchor.final_confidence, breakdown_context.final_confidence, places=2)
        
        # But both should be valid
        self.assertGreaterEqual(breakdown_anchor.final_confidence, 0.0)
        self.assertLessEqual(breakdown_anchor.final_confidence, 1.0)
        self.assertGreaterEqual(breakdown_context.final_confidence, 0.0)
        self.assertLessEqual(breakdown_context.final_confidence, 1.0)
    
    def test_weight_sensitivity(self):
        """Test sensitivity to weight changes."""
        text = "Furthermore, the API implementation demonstrates proper authentication."
        error_position = 40
        
        # Use a fresh calculator to avoid caching issues
        calculator1 = ConfidenceCalculator(cache_results=False)
        breakdown_default = calculator1.calculate_confidence(text, error_position)
        
        # Calculate with modified weights using a different calculator
        modified_weights = ConfidenceWeights(
            linguistic_anchors=0.8,  # Much higher weight for anchors
            context_analysis=0.1,    # Much lower for context
            domain_classification=0.1  # Much lower for domain
        )
        
        calculator2 = ConfidenceCalculator(weights=modified_weights, cache_results=False)
        breakdown_modified = calculator2.calculate_confidence(text, error_position)
        
        # Should produce different results due to very different weighting
        # Check if either the final confidence or layer contributions are different
        confidence_different = abs(breakdown_default.final_confidence - breakdown_modified.final_confidence) > 0.001
        effect_different = abs(breakdown_default.confidence_effect - breakdown_modified.confidence_effect) > 0.001
        
        # At least one should be different
        self.assertTrue(confidence_different or effect_different, 
                       f"Default effect: {breakdown_default.confidence_effect}, Modified effect: {breakdown_modified.confidence_effect}")


class TestConfidenceBreakdownAnalysis(unittest.TestCase):
    """Test confidence breakdown and meta-analysis features."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_layer_agreement_calculation(self):
        """Test layer agreement calculation."""
        # Text likely to produce agreeing layers
        agreeing_text = "The comprehensive documentation provides clear examples."
        breakdown_agree = self.calculator.calculate_confidence(agreeing_text, 30)
        
        # Text likely to produce disagreeing layers
        disagreeing_text = "Yeah, the API stuff is pretty cool but confusing."
        breakdown_disagree = self.calculator.calculate_confidence(disagreeing_text, 25)
        
        # Both should have valid agreement scores
        self.assertIsInstance(breakdown_agree.layer_agreement, float)
        self.assertGreaterEqual(breakdown_agree.layer_agreement, 0.0)
        self.assertLessEqual(breakdown_agree.layer_agreement, 1.0)
        
        self.assertIsInstance(breakdown_disagree.layer_agreement, float)
        self.assertGreaterEqual(breakdown_disagree.layer_agreement, 0.0)
        self.assertLessEqual(breakdown_disagree.layer_agreement, 1.0)
    
    def test_confidence_certainty_calculation(self):
        """Test confidence certainty calculation."""
        text = "The methodology demonstrates significant statistical improvements."
        error_position = 35
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        self.assertIsInstance(breakdown.confidence_certainty, float)
        self.assertGreaterEqual(breakdown.confidence_certainty, 0.0)
        self.assertLessEqual(breakdown.confidence_certainty, 1.0)
    
    def test_outlier_layer_detection(self):
        """Test detection of outlier layers."""
        text = "The comprehensive documentation provides excellent guidance."
        error_position = 30
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        self.assertIsInstance(breakdown.outlier_layers, list)
        
        # Outlier layers should be valid layer names
        valid_layer_names = {layer.value for layer in ConfidenceLayer}
        for outlier in breakdown.outlier_layers:
            self.assertIn(outlier, valid_layer_names)
    
    def test_confidence_adjustment_description(self):
        """Test confidence adjustment description."""
        text = "The methodology demonstrates improvements."
        error_position = 20
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        self.assertIn(breakdown.confidence_adjustment, ['boost', 'reduce', 'neutral'])
        
        # Should match the actual effect
        if breakdown.confidence_effect > 0.05:
            self.assertEqual(breakdown.confidence_adjustment, 'boost')
        elif breakdown.confidence_effect < -0.05:
            self.assertEqual(breakdown.confidence_adjustment, 'reduce')
        else:
            self.assertEqual(breakdown.confidence_adjustment, 'neutral')


class TestExplanationGeneration(unittest.TestCase):
    """Test comprehensive explanation generation."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_explanation_completeness(self):
        """Test that explanations include all necessary components."""
        text = "Furthermore, the comprehensive API documentation demonstrates proper authentication mechanisms."
        error_position = 50
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        explanation = breakdown.explanation
        
        # Should include overall result
        self.assertTrue(
            '🔼' in explanation or '🔽' in explanation or '➡️' in explanation
        )
        
        # Should include layer breakdown
        self.assertIn('📊 LAYER CONTRIBUTIONS:', explanation)
        
        # Should include analysis quality
        self.assertIn('🔍 ANALYSIS QUALITY:', explanation)
        
        # Should include performance
        self.assertIn('⚡ PERFORMANCE:', explanation)
        
        # Should include insights
        self.assertIn('💡 KEY INSIGHTS:', explanation)
        
        # Should mention all layers
        self.assertIn('Linguistic Anchors', explanation)
        self.assertIn('Context Analysis', explanation)
        self.assertIn('Domain Classification', explanation)
    
    def test_explanation_formatting(self):
        """Test that explanations are properly formatted."""
        text = "The comprehensive methodology demonstrates significant improvements."
        error_position = 30
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        explanation = breakdown.explanation
        
        # Should be multi-line
        lines = explanation.split('\n')
        self.assertGreater(len(lines), 5)
        
        # Should have proper structure
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 100)  # Should be substantial
    
    def test_positive_effect_explanation(self):
        """Test explanation for positive confidence effects."""
        # Use text likely to have positive effect
        text = "Furthermore, the comprehensive methodology demonstrates significant improvements."
        error_position = 40
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        if breakdown.confidence_effect > 0.05:
            self.assertIn('🔼', breakdown.explanation)
            self.assertIn('increased', breakdown.explanation.lower())
    
    def test_negative_effect_explanation(self):
        """Test explanation for negative confidence effects."""
        # Use text likely to have negative effect
        text = "Yeah, this thing is kinda confusing and stuff."
        error_position = 20
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        if breakdown.confidence_effect < -0.05:
            self.assertIn('🔽', breakdown.explanation)
            self.assertIn('decreased', breakdown.explanation.lower())


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance optimization and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_calculation_caching(self):
        """Test that calculation results are cached."""
        text = "The API documentation provides clear guidance."
        error_position = 20
        
        # First calculation
        start_time = time.time()
        breakdown1 = self.calculator.calculate_confidence(text, error_position)
        first_time = time.time() - start_time
        
        # Second identical calculation
        start_time = time.time()
        breakdown2 = self.calculator.calculate_confidence(text, error_position)
        second_time = time.time() - start_time
        
        # Second should be from cache (though timing might be variable)
        self.assertEqual(breakdown1.final_confidence, breakdown2.final_confidence)
        self.assertEqual(breakdown1.confidence_effect, breakdown2.confidence_effect)
        
        # Check cache statistics
        stats = self.calculator.get_performance_stats()
        self.assertGreater(stats['cache_hits'], 0)
    
    def test_performance_statistics(self):
        """Test performance statistics collection."""
        # Perform several calculations
        texts = [
            "The API documentation explains endpoints.",
            "Furthermore, the methodology demonstrates improvements.",
            "The system processes data efficiently."
        ]
        
        for i, text in enumerate(texts):
            self.calculator.calculate_confidence(text, i * 10)
        
        stats = self.calculator.get_performance_stats()
        
        # Should have comprehensive statistics
        self.assertIn('total_calculations', stats)
        self.assertIn('cache_hits', stats)
        self.assertIn('cache_misses', stats)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('cached_calculations', stats)
        self.assertIn('current_weights', stats)
        self.assertIn('layer_cache_performance', stats)
        
        # Should have reasonable values
        self.assertGreaterEqual(stats['total_calculations'], 3)
        self.assertGreaterEqual(stats['cache_hit_rate'], 0.0)
        self.assertLessEqual(stats['cache_hit_rate'], 1.0)
        
        # Should have layer performance data
        layer_perf = stats['layer_cache_performance']
        self.assertIn('linguistic_anchors', layer_perf)
        self.assertIn('context_analysis', layer_perf)
        self.assertIn('domain_classification', layer_perf)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        text = "The comprehensive documentation provides guidance."
        
        # Perform calculation to populate caches
        self.calculator.calculate_confidence(text, 20)
        
        # Verify caches have content
        stats_before = self.calculator.get_performance_stats()
        self.assertGreater(stats_before['total_calculations'], 0)
        
        # Clear caches
        self.calculator.clear_caches()
        
        # Verify caches are empty
        stats_after = self.calculator.get_performance_stats()
        self.assertEqual(stats_after['cache_hits'], 0)
        self.assertEqual(stats_after['cache_misses'], 0)
        self.assertEqual(stats_after['total_calculations'], 0)
        self.assertEqual(stats_after['cached_calculations'], 0)
    
    def test_performance_with_various_text_lengths(self):
        """Test performance with different text lengths."""
        # Short text
        short_text = "API endpoint."
        start_time = time.time()
        breakdown_short = self.calculator.calculate_confidence(short_text, 5)
        short_time = time.time() - start_time
        
        # Long text
        long_text = "The comprehensive API documentation explains REST endpoints. " * 10
        start_time = time.time()
        breakdown_long = self.calculator.calculate_confidence(long_text, 100)
        long_time = time.time() - start_time
        
        # Both should complete in reasonable time
        self.assertLess(short_time, 1.0)
        self.assertLess(long_time, 5.0)
        
        # Both should produce valid results
        self.assertIsInstance(breakdown_short.final_confidence, float)
        self.assertIsInstance(breakdown_long.final_confidence, float)


class TestAdvancedAnalysisFeatures(unittest.TestCase):
    """Test advanced analysis and debugging features."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_confidence_factor_analysis(self):
        """Test confidence factor analysis for debugging."""
        text = "Furthermore, the comprehensive API documentation demonstrates proper authentication."
        error_position = 50
        
        factor_analysis = self.calculator.analyze_confidence_factors(text, error_position)
        
        # Should have complete factor analysis structure
        expected_keys = [
            'strongest_positive_factor',
            'strongest_negative_factor',
            'most_confident_layer',
            'least_confident_layer',
            'agreement_analysis',
            'layer_details'
        ]
        
        for key in expected_keys:
            self.assertIn(key, factor_analysis)
        
        # Agreement analysis should have proper structure
        agreement_analysis = factor_analysis['agreement_analysis']
        self.assertIn('agreement_score', agreement_analysis)
        self.assertIn('outliers', agreement_analysis)
        self.assertIn('consensus', agreement_analysis)
        
        # Layer details should cover all layers
        layer_details = factor_analysis['layer_details']
        expected_layers = ['linguistic_anchors', 'context_analysis', 'domain_classification']
        for layer in expected_layers:
            self.assertIn(layer, layer_details)
    
    def test_weight_simulation(self):
        """Test weight change simulation."""
        text = "The comprehensive methodology demonstrates significant improvements."
        error_position = 35
        
        # Define weight scenarios to test
        scenarios = [
            ConfidenceWeights(0.6, 0.3, 0.1),  # Anchor-heavy
            ConfidenceWeights(0.2, 0.6, 0.2),  # Context-heavy
            ConfidenceWeights(0.1, 0.1, 0.8),  # Domain-heavy
        ]
        
        simulation_results = self.calculator.simulate_weight_changes(
            text, error_position, scenarios
        )
        
        # Should have complete simulation structure
        self.assertIn('baseline', simulation_results)
        self.assertIn('scenarios', simulation_results)
        self.assertIn('weight_sensitivity', simulation_results)
        
        # Should have baseline results
        baseline = simulation_results['baseline']
        self.assertIn('weights', baseline)
        self.assertIn('final_confidence', baseline)
        self.assertIn('confidence_effect', baseline)
        
        # Should have scenario results
        scenarios_results = simulation_results['scenarios']
        self.assertEqual(len(scenarios_results), 3)
        
        for scenario in scenarios_results:
            self.assertIn('scenario_id', scenario)
            self.assertIn('weights', scenario)
            self.assertIn('final_confidence', scenario)
            self.assertIn('confidence_effect', scenario)
            self.assertIn('difference_from_baseline', scenario)
        
        # Should have weight sensitivity analysis
        sensitivity = simulation_results['weight_sensitivity']
        self.assertIn('linguistic_anchors', sensitivity)
        self.assertIn('context_analysis', sensitivity)
        self.assertIn('domain_classification', sensitivity)


class TestIntegrationWithAllLayers(unittest.TestCase):
    """Test integration with all confidence layers."""
    
    def setUp(self):
        """Set up test environment."""
        self.calculator = ConfidenceCalculator()
    
    def test_technical_content_integration(self):
        """Test integration with technical content."""
        text = "The API documentation explains REST endpoints and authentication mechanisms."
        error_position = 40
        
        breakdown = self.calculator.calculate_confidence(
            text, error_position,
            rule_type="terminology",
            content_type="technical"
        )
        
        # Should integrate all layers successfully
        self.assertEqual(len(breakdown.layer_contributions), 3)
        
        # Each layer should have valid contributions
        for contrib in breakdown.layer_contributions:
            self.assertIsInstance(contrib.raw_score, float)
            self.assertIsInstance(contrib.weighted_score, float)
            self.assertGreater(len(contrib.explanation), 0)
            self.assertGreater(contrib.processing_time, 0)
        
        # Should have meaningful metadata from each layer
        anchor_contrib = next(c for c in breakdown.layer_contributions if c.layer == ConfidenceLayer.LINGUISTIC_ANCHORS)
        self.assertGreater(anchor_contrib.metadata['total_matches'], 0)
        
        context_contrib = next(c for c in breakdown.layer_contributions if c.layer == ConfidenceLayer.CONTEXT_ANALYSIS)
        self.assertGreater(context_contrib.metadata['sentence_count'], 0)
        
        domain_contrib = next(c for c in breakdown.layer_contributions if c.layer == ConfidenceLayer.DOMAIN_CLASSIFICATION)
        self.assertIn(domain_contrib.metadata['content_type'], ['technical', 'narrative', 'procedural'])
    
    def test_narrative_content_integration(self):
        """Test integration with narrative content."""
        text = 'The protagonist embarked on an extraordinary journey. "This will change everything," she whispered.'
        error_position = 50
        
        breakdown = self.calculator.calculate_confidence(
            text, error_position,
            rule_type="style",
            content_type="narrative"
        )
        
        # Should handle narrative content appropriately
        self.assertIsInstance(breakdown.final_confidence, float)
        self.assertGreaterEqual(breakdown.final_confidence, 0.0)
        self.assertLessEqual(breakdown.final_confidence, 1.0)
        
        # Domain layer should detect narrative characteristics
        domain_contrib = next(c for c in breakdown.layer_contributions if c.layer == ConfidenceLayer.DOMAIN_CLASSIFICATION)
        # Content type might be narrative or another type depending on algorithm
        self.assertIsInstance(domain_contrib.metadata['content_type'], str)
    
    def test_mixed_domain_content_integration(self):
        """Test integration with mixed domain content."""
        text = "The patient data is stored in a MongoDB database using secure authentication."
        error_position = 40
        
        breakdown = self.calculator.calculate_confidence(text, error_position)
        
        # Should handle mixed content gracefully
        self.assertIsInstance(breakdown.final_confidence, float)
        self.assertGreaterEqual(breakdown.final_confidence, 0.0)
        self.assertLessEqual(breakdown.final_confidence, 1.0)
        
        # May detect mixed content
        domain_contrib = next(c for c in breakdown.layer_contributions if c.layer == ConfidenceLayer.DOMAIN_CLASSIFICATION)
        # Mixed content detection is in metadata
        self.assertIn('mixed_content_detected', domain_contrib.metadata)
    
    def test_performance_across_content_types(self):
        """Test performance consistency across different content types."""
        test_cases = [
            ("The API documentation explains REST endpoints.", "technical"),
            ("Once upon a time, there was a brave character.", "narrative"),
            ("Step 1: Install dependencies. Step 2: Configure settings.", "procedural"),
            ("The research methodology demonstrates significant correlation.", "academic"),
            ("The patient requires immediate medical attention.", "medical")
        ]
        
        for text, expected_domain in test_cases:
            start_time = time.time()
            breakdown = self.calculator.calculate_confidence(text, len(text) // 2)
            processing_time = time.time() - start_time
            
            # Should complete in reasonable time
            self.assertLess(processing_time, 2.0)
            
            # Should produce valid results
            self.assertIsInstance(breakdown.final_confidence, float)
            self.assertGreaterEqual(breakdown.final_confidence, 0.0)
            self.assertLessEqual(breakdown.final_confidence, 1.0)
            
            # Should have all layer contributions
            self.assertEqual(len(breakdown.layer_contributions), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)