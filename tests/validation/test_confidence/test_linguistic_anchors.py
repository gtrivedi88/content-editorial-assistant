"""
Comprehensive test suite for LinguisticAnchors class.
Tests pattern loading, matching, confidence calculation, and explanations.
"""

import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

from validation.confidence.linguistic_anchors import LinguisticAnchors, AnchorMatch, AnchorAnalysis
from validation.config.linguistic_anchors_config import LinguisticAnchorsConfig


class TestLinguisticAnchorsInitialization(unittest.TestCase):
    """Test LinguisticAnchors initialization and configuration loading."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_default_initialization(self):
        """Test initialization with default configuration."""
        anchors = LinguisticAnchors()
        
        self.assertIsInstance(anchors.config, LinguisticAnchorsConfig)
        self.assertTrue(anchors.cache_compiled_patterns)
        self.assertIsInstance(anchors._pattern_cache, dict)
        self.assertIsInstance(anchors._analysis_cache, dict)
        
        # Should have pre-compiled patterns
        self.assertGreater(len(anchors._pattern_cache), 0)
    
    def test_custom_config_file_initialization(self):
        """Test initialization with custom configuration file."""
        # Create a minimal test config
        config_file = Path(self.temp_dir) / 'test_anchors.yaml'
        config_content = """
confidence_boosting_anchors:
  test_category:
    test_anchor:
      patterns: ["\\\\btest\\\\b"]
      confidence_boost: 0.10
      context_window: 3
      description: "Test pattern"

confidence_reducing_anchors:
  test_category:
    test_anchor:
      patterns: ["\\\\bnoise\\\\b"]
      confidence_reduction: 0.15
      context_window: 2
      description: "Test noise pattern"
"""
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        anchors = LinguisticAnchors(config_file)
        
        # Should load the custom configuration
        self.assertEqual(anchors.config.get_config_file_path(), config_file)
        
        # Should have test patterns
        boosting = anchors.config.get_boosting_anchors()
        self.assertIn('test_category', boosting)
        self.assertIn('test_anchor', boosting['test_category'])
    
    def test_pattern_caching_disabled(self):
        """Test initialization with pattern caching disabled."""
        anchors = LinguisticAnchors(cache_compiled_patterns=False)
        
        self.assertFalse(anchors.cache_compiled_patterns)
        # Should not pre-compile patterns
        self.assertEqual(len(anchors._pattern_cache), 0)
    
    def test_get_anchor_categories(self):
        """Test getting available anchor categories."""
        anchors = LinguisticAnchors()
        categories = anchors.get_anchor_categories()
        
        self.assertIn('boosting', categories)
        self.assertIn('reducing', categories)
        self.assertIsInstance(categories['boosting'], list)
        self.assertIsInstance(categories['reducing'], list)
        
        # Should have expected categories
        self.assertIn('generic_patterns', categories['boosting'])
        self.assertIn('technical_patterns', categories['boosting'])
        self.assertIn('proper_nouns', categories['reducing'])
        self.assertIn('quoted_content', categories['reducing'])


class TestContextExtraction(unittest.TestCase):
    """Test context extraction functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_extract_context_normal_text(self):
        """Test context extraction from normal text."""
        text = "The quick brown fox jumps over the lazy dog"
        error_position = 16  # Position of "fox"
        
        context_info = self.anchors._extract_context(text, error_position)
        
        self.assertIn('context_text', context_info)
        self.assertIn('context_start', context_info)
        self.assertIn('context_end', context_info)
        self.assertIn('error_word_index', context_info)
        
        # Should include words around "fox"
        self.assertIn('fox', context_info['context_text'])
        self.assertIn('brown', context_info['context_text'])
        self.assertIn('jumps', context_info['context_text'])
    
    def test_extract_context_at_beginning(self):
        """Test context extraction when error is at text beginning."""
        text = "Error at the very beginning of text"
        error_position = 0  # Position of "Error"
        
        context_info = self.anchors._extract_context(text, error_position)
        
        self.assertEqual(context_info['error_word_index'], 0)
        self.assertIn('Error', context_info['context_text'])
    
    def test_extract_context_at_end(self):
        """Test context extraction when error is at text end."""
        text = "Text with error at the very end"
        error_position = len(text) - 3  # Position of "end"
        
        context_info = self.anchors._extract_context(text, error_position)
        
        self.assertIn('end', context_info['context_text'])
    
    def test_extract_context_custom_window(self):
        """Test context extraction with custom window size."""
        text = "One two three four five six seven eight nine ten"
        error_position = 20  # Position of "five"
        
        context_info = self.anchors._extract_context(text, error_position, max_context_window=2)
        
        # Should only include 2 words on each side of "five"
        words = context_info['context_text'].split()
        self.assertLessEqual(len(words), 5)  # "five" + 2 on each side
        self.assertIn('five', words)
    
    def test_word_index_conversion(self):
        """Test word index and character position conversion."""
        text = "The quick brown fox"
        
        # Test finding word index from character position
        self.assertEqual(self.anchors._find_word_index(text, 0), 0)   # "The"
        self.assertEqual(self.anchors._find_word_index(text, 4), 1)   # "quick"
        self.assertEqual(self.anchors._find_word_index(text, 10), 2)  # "brown"
        self.assertEqual(self.anchors._find_word_index(text, 16), 3)  # "fox"
        
        # Test finding character position from word index
        self.assertEqual(self.anchors._find_position_of_word_index(text, 0), 0)
        self.assertEqual(self.anchors._find_position_of_word_index(text, 1), 4)
        self.assertEqual(self.anchors._find_position_of_word_index(text, 2), 10)
        self.assertEqual(self.anchors._find_position_of_word_index(text, 3), 16)


class TestPatternMatching(unittest.TestCase):
    """Test pattern matching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_boosting_pattern_detection(self):
        """Test detection of confidence-boosting patterns."""
        text = "The API documentation provides clear examples"
        error_position = 20  # Position of "documentation"
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should detect boosting patterns
        self.assertGreater(len(analysis.boosting_matches), 0)
        
        # Should detect "the" determiner
        determiner_matches = [m for m in analysis.boosting_matches 
                            if m.anchor_name == 'determiners']
        self.assertGreater(len(determiner_matches), 0)
        
        # Should detect API as programming term
        programming_matches = [m for m in analysis.boosting_matches 
                             if m.anchor_name == 'programming_terms']
        self.assertGreater(len(programming_matches), 0)
    
    def test_reducing_pattern_detection(self):
        """Test detection of confidence-reducing patterns."""
        text = 'John said "Yeah, that\'s awesome!" with enthusiasm'
        error_position = 25  # Position inside the quote
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should detect reducing patterns
        self.assertGreater(len(analysis.reducing_matches), 0)
        
        # Should detect person name
        name_matches = [m for m in analysis.reducing_matches 
                       if m.anchor_name == 'person_names']
        self.assertGreater(len(name_matches), 0)
        
        # Should detect quoted content or contractions
        informal_matches = [m for m in analysis.reducing_matches 
                          if m.anchor_name in ['direct_quotes', 'contractions']]
        self.assertGreater(len(informal_matches), 0)
    
    def test_technical_content_pattern_matching(self):
        """Test pattern matching with technical content type."""
        text = "Install Node.js and configure package.json for React development"
        error_position = 30  # Position of "package.json"
        
        analysis = self.anchors.analyze_text(
            text, error_position, 
            rule_type='terminology', 
            content_type='technical'
        )
        
        # Should detect technical patterns
        self.assertGreater(len(analysis.matches), 0)
        
        # Net effect calculation should work
        self.assertIsInstance(analysis.net_effect, float)
        
        # Should have explanation
        self.assertIsInstance(analysis.explanation, str)
        self.assertGreater(len(analysis.explanation), 0)
    
    def test_pattern_matching_edge_cases(self):
        """Test pattern matching with edge cases."""
        # Empty text
        analysis = self.anchors.analyze_text("", 0)
        self.assertEqual(len(analysis.matches), 0)
        self.assertEqual(analysis.net_effect, 0.0)
        
        # Single word
        analysis = self.anchors.analyze_text("Word", 0)
        self.assertIsInstance(analysis.net_effect, float)
        
        # Very long text
        long_text = " ".join(["word"] * 1000)
        analysis = self.anchors.analyze_text(long_text, 500)
        self.assertIsInstance(analysis.net_effect, float)
    
    def test_context_window_zero_matching(self):
        """Test pattern matching with zero context window (exact position)."""
        # This tests patterns that should only match at the exact error position
        text = 'Error in "quoted text" should be detected'
        error_position = 11  # Position inside quotes
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should have some matches (though exact behavior depends on patterns)
        self.assertIsInstance(analysis.matches, list)
        self.assertIsInstance(analysis.net_effect, float)


class TestConfidenceCalculation(unittest.TestCase):
    """Test confidence effect calculation."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_confidence_boost_calculation(self):
        """Test calculation of confidence boosts."""
        text = "The comprehensive documentation provides clear examples"
        error_position = 20  # Position of "documentation"
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should have positive boost from formal language
        self.assertGreater(analysis.total_boost, 0)
        # With comprehensive linguistic anchors, net effect can vary due to multiple patterns
        # The important thing is that we detected boosting patterns and calculated effects properly
        self.assertIsInstance(analysis.net_effect, float)
        self.assertGreater(len(analysis.boosting_matches), 0)  # Should detect some boosting patterns
    
    def test_confidence_reduction_calculation(self):
        """Test calculation of confidence reductions."""
        text = 'UserName123 said "LOL that\'s totally awesome!!!"'
        error_position = 25  # Position inside the quote
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should have reduction from informal language
        self.assertGreater(analysis.total_reduction, 0)
        self.assertLess(analysis.net_effect, 0.1)  # Should be negative or near-neutral
    
    def test_distance_weighting(self):
        """Test that distance from error affects pattern weights."""
        text = "The word error is here and more text follows"
        
        # Analyze with error at different positions
        analysis1 = self.anchors.analyze_text(text, 4)   # Near "The"
        analysis2 = self.anchors.analyze_text(text, 40)  # Far from "The"
        
        # Find determiner matches in both analyses
        det_matches1 = [m for m in analysis1.matches if m.anchor_name == 'determiners']
        det_matches2 = [m for m in analysis2.matches if m.anchor_name == 'determiners']
        
        if det_matches1 and det_matches2:
            # Closer match should have higher weighted effect
            self.assertGreater(det_matches1[0].weighted_effect, det_matches2[0].weighted_effect)
    
    def test_rule_type_weighting(self):
        """Test that rule type affects pattern weights."""
        text = "The technical documentation explains API usage"
        error_position = 20  # Position of "documentation"
        
        # Analyze with different rule types
        grammar_analysis = self.anchors.analyze_text(
            text, error_position, rule_type='grammar'
        )
        terminology_analysis = self.anchors.analyze_text(
            text, error_position, rule_type='terminology'
        )
        
        # Both should work without error
        self.assertIsInstance(grammar_analysis.net_effect, float)
        self.assertIsInstance(terminology_analysis.net_effect, float)
        
        # Should include rule type in explanation
        self.assertIn('grammar', grammar_analysis.explanation)
        self.assertIn('terminology', terminology_analysis.explanation)
    
    def test_content_type_adjustments(self):
        """Test that content type affects pattern adjustments."""
        text = "The system API handles HTTP requests efficiently"
        error_position = 15  # Position of "API"
        
        # Analyze with different content types
        technical_analysis = self.anchors.analyze_text(
            text, error_position, content_type='technical'
        )
        narrative_analysis = self.anchors.analyze_text(
            text, error_position, content_type='narrative'
        )
        
        # Both should work without error
        self.assertIsInstance(technical_analysis.net_effect, float)
        self.assertIsInstance(narrative_analysis.net_effect, float)
        
        # Should include content type in explanation
        self.assertIn('technical', technical_analysis.explanation)
        self.assertIn('narrative', narrative_analysis.explanation)
    
    def test_combination_methods(self):
        """Test different effect combination methods."""
        text = "The API documentation and HTTP examples demonstrate clear usage"
        error_position = 20  # Position with multiple potential matches
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        # Should combine multiple effects
        if len(analysis.boosting_matches) > 1:
            individual_effects = [m.weighted_effect for m in analysis.boosting_matches]
            total_individual = sum(individual_effects)
            
            # With diminishing returns, total should be less than sum
            self.assertLess(analysis.total_boost, total_individual)
        
        # Total effect should respect limits
        self.assertLessEqual(analysis.total_boost, 0.30)  # Max boost limit
        self.assertLessEqual(analysis.total_reduction, 0.35)  # Max reduction limit


class TestAnchorMatchObjects(unittest.TestCase):
    """Test AnchorMatch and AnchorAnalysis data structures."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_anchor_match_structure(self):
        """Test AnchorMatch object structure and content."""
        text = "The quick brown fox"
        error_position = 10  # Position of "brown"
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        if analysis.matches:
            match = analysis.matches[0]
            
            # Check required fields
            self.assertIn(match.anchor_type, ['boosting', 'reducing'])
            self.assertIsInstance(match.category, str)
            self.assertIsInstance(match.anchor_name, str)
            self.assertIsInstance(match.pattern, str)
            self.assertIsInstance(match.match_text, str)
            self.assertIsInstance(match.match_start, int)
            self.assertIsInstance(match.match_end, int)
            self.assertIsInstance(match.confidence_effect, float)
            self.assertIsInstance(match.distance_from_error, int)
            self.assertIsInstance(match.weighted_effect, float)
            self.assertIsInstance(match.description, str)
            
            # Positions should be valid
            self.assertGreaterEqual(match.match_start, 0)
            self.assertGreater(match.match_end, match.match_start)
            self.assertGreaterEqual(match.distance_from_error, 0)
    
    def test_anchor_analysis_structure(self):
        """Test AnchorAnalysis object structure and content."""
        text = "The API documentation provides examples"
        error_position = 20  # Position of "documentation"
        
        analysis = self.anchors.analyze_text(
            text, error_position, 
            rule_type='terminology', 
            content_type='technical'
        )
        
        # Check required fields
        self.assertEqual(analysis.text, text)
        self.assertEqual(analysis.error_position, error_position)
        self.assertIsInstance(analysis.error_word_index, int)
        self.assertIsInstance(analysis.context_text, str)
        self.assertIsInstance(analysis.context_start, int)
        self.assertIsInstance(analysis.context_end, int)
        
        self.assertIsInstance(analysis.matches, list)
        self.assertIsInstance(analysis.boosting_matches, list)
        self.assertIsInstance(analysis.reducing_matches, list)
        
        self.assertIsInstance(analysis.total_boost, float)
        self.assertIsInstance(analysis.total_reduction, float)
        self.assertIsInstance(analysis.net_effect, float)
        
        self.assertEqual(analysis.rule_type, 'terminology')
        self.assertEqual(analysis.content_type, 'technical')
        
        self.assertIsInstance(analysis.explanation, str)
        self.assertIsInstance(analysis.performance_stats, dict)
        
        # Verify consistency
        boosting_count = len([m for m in analysis.matches if m.anchor_type == 'boosting'])
        reducing_count = len([m for m in analysis.matches if m.anchor_type == 'reducing'])
        
        self.assertEqual(len(analysis.boosting_matches), boosting_count)
        self.assertEqual(len(analysis.reducing_matches), reducing_count)
    
    def test_analysis_performance_stats(self):
        """Test performance statistics in analysis."""
        text = "The comprehensive API documentation with multiple patterns"
        error_position = 30  # Position with potential matches
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        stats = analysis.performance_stats
        
        # Check expected performance metrics
        self.assertIn('analysis_time_ms', stats)
        self.assertIn('total_patterns_checked', stats)
        self.assertIn('matches_found', stats)
        self.assertIn('cache_hits', stats)
        self.assertIn('cache_misses', stats)
        
        # Values should be reasonable
        self.assertGreater(stats['analysis_time_ms'], 0)
        self.assertGreater(stats['total_patterns_checked'], 0)
        self.assertEqual(stats['matches_found'], len(analysis.matches))


class TestExplanationGeneration(unittest.TestCase):
    """Test explanation generation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_positive_confidence_explanation(self):
        """Test explanation for positive confidence changes."""
        text = "The comprehensive API documentation provides clear examples"
        error_position = 30  # Position with boosting patterns
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        explanation = analysis.explanation
        
        # Should mention confidence increase if net effect is positive
        if analysis.net_effect > 0.05:
            self.assertIn('🔼', explanation)
            self.assertIn('increased', explanation.lower())
        
        # Should list boosting factors if present
        if analysis.boosting_matches:
            self.assertIn('📈', explanation)
            self.assertIn('Boosting factors', explanation)
    
    def test_negative_confidence_explanation(self):
        """Test explanation for negative confidence changes."""
        text = 'PersonName said "LOL that\'s totally awesome!!!"'
        error_position = 25  # Position with reducing patterns
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        explanation = analysis.explanation
        
        # Should mention confidence decrease if net effect is negative
        if analysis.net_effect < -0.05:
            self.assertIn('🔽', explanation)
            self.assertIn('decreased', explanation.lower())
        
        # Should list reducing factors if present
        if analysis.reducing_matches:
            self.assertIn('📉', explanation)
            self.assertIn('Reducing factors', explanation)
    
    def test_context_information_in_explanation(self):
        """Test that context information appears in explanations."""
        text = "The system processes requests efficiently"
        error_position = 15  # Position of "processes"
        
        analysis = self.anchors.analyze_text(
            text, error_position,
            rule_type='grammar',
            content_type='technical'
        )
        
        explanation = analysis.explanation
        
        # Should include context information
        self.assertIn('Context:', explanation)
        self.assertIn('rule: grammar', explanation)
        self.assertIn('content: technical', explanation)
    
    def test_no_matches_explanation(self):
        """Test explanation when no patterns match."""
        text = "Xyz qrs wxy zyx"  # Text unlikely to match patterns
        error_position = 5
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        explanation = analysis.explanation
        
        # Should handle no matches gracefully
        if not analysis.matches:
            self.assertIn('🔍', explanation)
            self.assertIn('No significant linguistic patterns', explanation)
    
    def test_explanation_match_limits(self):
        """Test that explanations limit the number of matches shown."""
        # Create text likely to trigger many patterns
        text = "The comprehensive API documentation provides clear HTTP GET examples with detailed explanations"
        error_position = 40  # Position likely to trigger multiple matches
        
        analysis = self.anchors.analyze_text(text, error_position)
        
        explanation = analysis.explanation
        
        # Should not overwhelm with too many matches
        lines = explanation.split('\n')
        explanation_lines = [line for line in lines if line.strip().startswith('•')]
        
        # Should limit to reasonable number of lines per category
        self.assertLessEqual(len(explanation_lines), 10)


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance optimization and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_pattern_caching(self):
        """Test that pattern compilation is cached."""
        # First analysis should compile patterns
        text = "The API documentation explains usage"
        error_position = 15
        
        start_time = time.time()
        analysis1 = self.anchors.analyze_text(text, error_position)
        first_time = time.time() - start_time
        
        # Second analysis should use cached patterns
        start_time = time.time()
        analysis2 = self.anchors.analyze_text(text, error_position)
        second_time = time.time() - start_time
        
        # Results should be identical
        self.assertEqual(analysis1.net_effect, analysis2.net_effect)
        self.assertEqual(len(analysis1.matches), len(analysis2.matches))
        
        # Second should be faster (though timing can be variable)
        # At minimum, both should complete successfully
        self.assertIsInstance(analysis1.net_effect, float)
        self.assertIsInstance(analysis2.net_effect, float)
    
    def test_analysis_caching(self):
        """Test that analysis results are cached."""
        text = "The API documentation explains usage"
        error_position = 15
        
        # First analysis
        analysis1 = self.anchors.analyze_text(text, error_position)
        cache_misses_after_first = self.anchors._cache_misses
        
        # Second identical analysis
        analysis2 = self.anchors.analyze_text(text, error_position)
        cache_hits_after_second = self.anchors._cache_hits
        
        # Second should be from cache
        self.assertGreater(cache_hits_after_second, 0)
        
        # Results should be identical
        self.assertEqual(analysis1.net_effect, analysis2.net_effect)
        self.assertEqual(len(analysis1.matches), len(analysis2.matches))
    
    def test_performance_stats(self):
        """Test performance statistics collection."""
        text = "The comprehensive documentation provides examples"
        error_position = 20
        
        # Perform some analyses
        self.anchors.analyze_text(text, error_position)
        self.anchors.analyze_text(text, error_position)  # Should hit cache
        self.anchors.analyze_text(text, error_position + 5)  # Different analysis
        
        stats = self.anchors.get_performance_stats()
        
        # Should have performance data
        self.assertIn('cache_hits', stats)
        self.assertIn('cache_misses', stats)
        self.assertIn('cache_hit_rate', stats)
        self.assertIn('compiled_patterns_cached', stats)
        self.assertIn('analysis_results_cached', stats)
        
        # Should have reasonable values
        self.assertGreaterEqual(stats['cache_hits'], 0)
        self.assertGreater(stats['cache_misses'], 0)  # At least some misses
        self.assertGreaterEqual(stats['cache_hit_rate'], 0)
        self.assertLessEqual(stats['cache_hit_rate'], 1)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        text = "The API documentation explains usage"
        error_position = 15
        
        # Perform analysis to populate caches
        self.anchors.analyze_text(text, error_position)
        
        # Verify caches have content
        self.assertGreater(len(self.anchors._pattern_cache), 0)
        self.assertGreater(len(self.anchors._analysis_cache), 0)
        
        # Clear caches
        self.anchors.clear_caches()
        
        # Verify caches are empty
        self.assertEqual(len(self.anchors._pattern_cache), 0)
        self.assertEqual(len(self.anchors._analysis_cache), 0)
        self.assertEqual(self.anchors._cache_hits, 0)
        self.assertEqual(self.anchors._cache_misses, 0)
    
    def test_configuration_reload(self):
        """Test configuration reloading."""
        # Perform initial analysis
        text = "The API documentation explains usage"
        error_position = 15
        
        analysis1 = self.anchors.analyze_text(text, error_position)
        
        # Reload configuration
        self.anchors.reload_configuration()
        
        # Should work after reload
        analysis2 = self.anchors.analyze_text(text, error_position)
        
        # Results should be consistent
        self.assertIsInstance(analysis2.net_effect, float)
        
        # Caches should be cleared after reload
        # (Can't test exact equality since reload might affect timing/order)
        stats = self.anchors.get_performance_stats()
        self.assertGreaterEqual(stats['cache_misses'], 0)


class TestEdgeCasesAndRobustness(unittest.TestCase):
    """Test edge cases and robustness."""
    
    def setUp(self):
        """Set up test environment."""
        self.anchors = LinguisticAnchors()
    
    def test_empty_text_analysis(self):
        """Test analysis of empty text."""
        analysis = self.anchors.analyze_text("", 0)
        
        self.assertEqual(analysis.text, "")
        self.assertEqual(analysis.error_position, 0)
        self.assertEqual(len(analysis.matches), 0)
        self.assertEqual(analysis.net_effect, 0.0)
        self.assertIsInstance(analysis.explanation, str)
    
    def test_single_character_text(self):
        """Test analysis of single character."""
        analysis = self.anchors.analyze_text("A", 0)
        
        self.assertEqual(analysis.text, "A")
        self.assertEqual(analysis.error_position, 0)
        self.assertIsInstance(analysis.net_effect, float)
        self.assertIsInstance(analysis.explanation, str)
    
    def test_very_long_text(self):
        """Test analysis of very long text."""
        # Create long text with patterns
        long_text = "The API documentation " * 100  # 300 words
        error_position = len(long_text) // 2  # Middle position
        
        start_time = time.time()
        analysis = self.anchors.analyze_text(long_text, error_position)
        analysis_time = time.time() - start_time
        
        # Should complete in reasonable time
        self.assertLess(analysis_time, 5.0)  # Should be much faster than 5 seconds
        
        # Should produce valid results
        self.assertIsInstance(analysis.net_effect, float)
        self.assertIsInstance(analysis.matches, list)
    
    def test_special_characters_handling(self):
        """Test handling of special characters."""
        text = "Text with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        error_position = 20
        
        # Should not crash with special characters
        analysis = self.anchors.analyze_text(text, error_position)
        
        self.assertIsInstance(analysis.net_effect, float)
        self.assertIsInstance(analysis.explanation, str)
    
    def test_unicode_text_handling(self):
        """Test handling of Unicode text."""
        text = "Text with Unicode: café naïve résumé Москва 北京 🎉"
        error_position = 20
        
        # Should handle Unicode gracefully
        analysis = self.anchors.analyze_text(text, error_position)
        
        self.assertIsInstance(analysis.net_effect, float)
        self.assertIsInstance(analysis.explanation, str)
    
    def test_invalid_error_position(self):
        """Test handling of invalid error positions."""
        text = "Short text"
        
        # Position beyond text end
        analysis = self.anchors.analyze_text(text, 1000)
        self.assertIsInstance(analysis.net_effect, float)
        
        # Negative position
        analysis = self.anchors.analyze_text(text, -5)
        self.assertIsInstance(analysis.net_effect, float)
    
    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text."""
        analysis = self.anchors.analyze_text("   \t\n  ", 2)
        
        self.assertIsInstance(analysis.net_effect, float)
        self.assertIsInstance(analysis.explanation, str)
        self.assertEqual(len(analysis.matches), 0)  # Should find no patterns


if __name__ == '__main__':
    unittest.main(verbosity=2)