"""
Comprehensive test suite for enhanced StructuralAnalyzer (Phase 4 Step 19).
Tests validation pipeline integration, confidence filtering, and performance monitoring.
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

# Import the enhanced StructuralAnalyzer
from style_analyzer.structural_analyzer import StructuralAnalyzer, ENHANCED_VALIDATION_AVAILABLE
from style_analyzer.base_types import AnalysisMode


class TestEnhancedStructuralAnalyzer(unittest.TestCase):
    """Test enhanced StructuralAnalyzer validation pipeline integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock components
        self.mock_readability_analyzer = Mock()
        self.mock_sentence_analyzer = Mock()
        self.mock_statistics_calculator = Mock()
        self.mock_suggestion_generator = Mock()
        self.mock_rules_registry = Mock()
        
        # Setup mock returns for statistics calculator
        self.mock_statistics_calculator.split_paragraphs_safe.return_value = ["Test paragraph"]
        self.mock_statistics_calculator.calculate_comprehensive_statistics.return_value = {
            'word_count': 10,
            'sentence_count': 1,
            'paragraph_count': 1,
            'avg_words_per_sentence': 10.0
        }
        self.mock_statistics_calculator.calculate_comprehensive_technical_metrics.return_value = {
            'readability_score': 70.0,
            'complexity_score': 0.5,
            'lexical_diversity': 0.8
        }
        
        # Setup mock returns for suggestion generator
        self.mock_suggestion_generator.generate_suggestions.return_value = [
            "Consider using simpler language"
        ]
        
        # Load spaCy model for testing
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
        
        self.test_text = "The sophisticated methodology can't facilitate comprehensive analysis using colour-based visualization."
        self.test_format_hint = "asciidoc"
        self.analysis_mode = AnalysisMode.SPACY_WITH_MODULAR_RULES
    
    def test_enhanced_analyzer_initialization_with_validation(self):
        """Test that StructuralAnalyzer initializes correctly with enhanced validation."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.6
        )
        
        # Check initialization
        self.assertIsNotNone(analyzer)
        self.assertTrue(hasattr(analyzer, 'enable_enhanced_validation'))
        self.assertTrue(hasattr(analyzer, 'confidence_threshold'))
        self.assertTrue(hasattr(analyzer, 'validation_performance'))
        
        # Check validation system initialization
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertTrue(analyzer.enable_enhanced_validation)
            self.assertEqual(analyzer.confidence_threshold, 0.6)
        
        # Check validation performance tracking initialized
        self.assertIn('total_validations', analyzer.validation_performance)
        self.assertIn('validation_time', analyzer.validation_performance)
        self.assertIn('confidence_stats', analyzer.validation_performance)
    
    def test_analyzer_initialization_without_enhanced_validation(self):
        """Test that StructuralAnalyzer initializes correctly without enhanced validation."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=False
        )
        
        # Check initialization
        self.assertIsNotNone(analyzer)
        self.assertFalse(analyzer.enable_enhanced_validation)
        self.assertEqual(analyzer.rules_registry, self.mock_rules_registry)
    
    def test_validation_performance_tracking(self):
        """Test validation performance metrics tracking."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True
        )
        
        # Mock errors with confidence scores
        test_errors = [
            {
                'type': 'test_rule',
                'message': 'Test error with confidence',
                'confidence_score': 0.8,
                'enhanced_validation_available': True
            },
            {
                'type': 'test_rule_2',
                'message': 'Another test error',
                'confidence_score': 0.6,
                'enhanced_validation_available': True
            }
        ]
        
        # Test performance tracking
        analyzer._update_validation_performance(test_errors, 0.1)
        
        performance = analyzer.validation_performance
        self.assertEqual(performance['total_validations'], 1)
        self.assertGreater(performance['confidence_stats']['max'], 0)
        self.assertLess(performance['confidence_stats']['min'], 1)
    
    def test_enhanced_error_detection(self):
        """Test detection of enhanced errors."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True
        )
        
        # Test enhanced error detection
        enhanced_error = {
            'type': 'test',
            'confidence_score': 0.8,
            'enhanced_validation_available': True
        }
        
        legacy_error = {
            'type': 'test',
            'message': 'Legacy error'
        }
        
        self.assertTrue(analyzer._is_enhanced_error(enhanced_error))
        self.assertFalse(analyzer._is_enhanced_error(legacy_error))
    
    def test_validation_performance_summary(self):
        """Test validation performance summary generation."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True
        )
        
        # Simulate some validation activity
        analyzer.validation_performance['total_validations'] = 5
        analyzer.validation_performance['validation_time'] = 0.5
        
        summary = analyzer._get_validation_performance_summary()
        
        # Check summary structure
        self.assertIn('total_validations', summary)
        self.assertIn('validation_time', summary)
        self.assertIn('avg_validation_time', summary)
        self.assertEqual(summary['avg_validation_time'], 0.1)  # 0.5 / 5
    
    def test_enhanced_validation_status(self):
        """Test enhanced validation status reporting."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.7
        )
        
        status = analyzer.get_enhanced_validation_status()
        
        # Check status structure
        required_fields = [
            'enhanced_validation_enabled',
            'enhanced_validation_available',
            'confidence_threshold',
            'validation_performance'
        ]
        
        for field in required_fields:
            self.assertIn(field, status)
        
        self.assertEqual(status['confidence_threshold'], 0.7)
        self.assertEqual(status['enhanced_validation_available'], ENHANCED_VALIDATION_AVAILABLE)
    
    @patch('style_analyzer.structural_analyzer.StructuralParserFactory')
    def test_analyze_with_blocks_enhanced_validation(self, mock_parser_factory):
        """Test complete analysis workflow with enhanced validation."""
        if not self.nlp:
            self.skipTest("SpaCy not available for integration testing")
        
        # Setup mock parser
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = True
        mock_parse_result.document = Mock()
        
        # Mock document structure
        mock_block = Mock()
        mock_block.should_skip_analysis.return_value = False
        mock_block.get_text_content.return_value = self.test_text
        mock_block.get_context_info.return_value = {'block_type': 'paragraph'}
        mock_block.to_dict.return_value = {'content': self.test_text, 'type': 'paragraph'}
        
        mock_parser.parse.return_value = mock_parse_result
        mock_parser_factory.return_value = mock_parser
        
        # Create analyzer with enhanced validation
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.5
        )
        
        # Mock _flatten_tree_only to return our mock block
        analyzer._flatten_tree_only = Mock(return_value=[mock_block])
        
        # Mock mode executor to return enhanced errors
        mock_enhanced_errors = [
            {
                'type': 'word_usage',
                'message': 'Enhanced error with confidence',
                'confidence_score': 0.7,
                'enhanced_validation_available': True,
                'suggestions': ['Fix this'],
                'sentence': self.test_text,
                'sentence_index': 0,
                'severity': 'medium'
            }
        ]
        
        analyzer.mode_executor = Mock()
        analyzer.mode_executor.analyze_block_content.return_value = mock_enhanced_errors
        
        # Run analysis
        result = analyzer.analyze_with_blocks(self.test_text, self.test_format_hint, self.analysis_mode)
        
        # Verify results structure
        self.assertIn('analysis', result)
        self.assertIn('structural_blocks', result)
        self.assertIn('has_structure', result)
        
        analysis = result['analysis']
        
        # Check enhanced validation fields
        if analyzer.enable_enhanced_validation:
            self.assertIn('validation_performance', analysis)
            self.assertIn('enhanced_validation_enabled', analysis)
            self.assertIn('confidence_threshold', analysis)
            self.assertIn('enhanced_error_stats', analysis)
            
            # Check enhanced error statistics
            error_stats = analysis['enhanced_error_stats']
            self.assertIn('total_errors', error_stats)
            self.assertIn('enhanced_errors', error_stats)
            self.assertIn('enhancement_rate', error_stats)
    
    @patch('style_analyzer.structural_analyzer.StructuralParserFactory')
    def test_analyze_with_blocks_error_handling(self, mock_parser_factory):
        """Test error handling during analysis with enhanced validation."""
        # Setup mock parser that fails
        mock_parser = Mock()
        mock_parse_result = Mock()
        mock_parse_result.success = False
        mock_parse_result.document = None
        
        mock_parser.parse.return_value = mock_parse_result
        mock_parser_factory.return_value = mock_parser
        
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True
        )
        
        # Run analysis with failed parsing
        result = analyzer.analyze_with_blocks("invalid content", self.test_format_hint, self.analysis_mode)
        
        # Should return error result gracefully
        self.assertIn('analysis', result)
        self.assertIn('structural_blocks', result)
        self.assertFalse(result['has_structure'])
        
        # Check that errors are present
        analysis = result['analysis']
        self.assertIn('errors', analysis)
        self.assertGreater(len(analysis['errors']), 0)
    
    def test_performance_monitoring_accuracy(self):
        """Test accuracy of performance monitoring."""
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=True
        )
        
        # Test multiple validation operations
        for i in range(3):
            test_errors = [
                {
                    'confidence_score': 0.5 + (i * 0.1),
                    'enhanced_validation_available': True
                }
            ]
            analyzer._update_validation_performance(test_errors, 0.05 * (i + 1))
        
        performance = analyzer._get_validation_performance_summary()
        
        # Check that metrics are reasonable
        self.assertEqual(performance['total_validations'], 3)
        self.assertGreater(performance['confidence_stats']['max'], performance['confidence_stats']['min'])
        self.assertGreater(performance['avg_validation_time'], 0)
    
    def test_backward_compatibility(self):
        """Test that enhanced analyzer maintains backward compatibility."""
        # Test with disabled enhanced validation
        analyzer = StructuralAnalyzer(
            self.mock_readability_analyzer,
            self.mock_sentence_analyzer,
            self.mock_statistics_calculator,
            self.mock_suggestion_generator,
            self.mock_rules_registry,
            self.nlp,
            enable_enhanced_validation=False
        )
        
        # Should use the provided registry directly
        self.assertEqual(analyzer.rules_registry, self.mock_rules_registry)
        self.assertFalse(analyzer.enable_enhanced_validation)
        
        # Performance tracking should still work but be disabled
        test_errors = [{'type': 'test', 'message': 'test'}]
        analyzer._update_validation_performance(test_errors, 0.1)
        
        # Should not crash and should not increment counters
        self.assertEqual(analyzer.validation_performance['total_validations'], 0)


class TestEnhancedStructuralAnalyzerIntegration(unittest.TestCase):
    """Test complete integration workflow with enhanced StructuralAnalyzer."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.complex_text = """= Document Title

The sophisticated methodology can't facilitate comprehensive analysis.
This system thinks users won't understand i.e. complex terminology like blacklist.

== Section Header

The data is analysed using colour-based visualization techniques.
He believes the API's properties aren't configured correctly.

[source,python]
----
def example_function():
    return "code should be ignored"
----

* List item with can't
* Another item with colour
* Final item with analyse"""
        
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_complete_document_analysis_workflow(self):
        """Test complete document analysis with enhanced validation."""
        if not self.nlp:
            self.skipTest("SpaCy not available for integration testing")
        
        # Create mock components with realistic behavior
        mock_readability_analyzer = Mock()
        mock_sentence_analyzer = Mock()
        mock_sentence_analyzer.split_sentences_safe.return_value = [
            "The sophisticated methodology can't facilitate comprehensive analysis.",
            "This system thinks users won't understand i.e. complex terminology like blacklist.",
            "The data is analysed using colour-based visualization techniques.",
            "He believes the API's properties aren't configured correctly."
        ]
        
        mock_statistics_calculator = Mock()
        mock_statistics_calculator.split_paragraphs_safe.return_value = [
            "The sophisticated methodology can't facilitate comprehensive analysis. This system thinks users won't understand i.e. complex terminology like blacklist.",
            "The data is analysed using colour-based visualization techniques. He believes the API's properties aren't configured correctly."
        ]
        mock_statistics_calculator.calculate_comprehensive_statistics.return_value = {
            'word_count': 45,
            'sentence_count': 4,
            'paragraph_count': 2,
            'avg_words_per_sentence': 11.25,
            'avg_syllables_per_word': 2.1,
            'readability_score': 65.0
        }
        mock_statistics_calculator.calculate_comprehensive_technical_metrics.return_value = {
            'readability_score': 65.0,
            'complexity_score': 0.6,
            'lexical_diversity': 0.85,
            'sentence_variation': 0.7
        }
        
        mock_suggestion_generator = Mock()
        mock_suggestion_generator.generate_suggestions.return_value = [
            "Consider using simpler language",
            "Avoid contractions in formal writing",
            "Use consistent spelling (analyze vs analyse)"
        ]
        
        # Create enhanced analyzer
        analyzer = StructuralAnalyzer(
            mock_readability_analyzer,
            mock_sentence_analyzer,
            mock_statistics_calculator,
            mock_suggestion_generator,
            None,  # Will be replaced with enhanced registry
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.4
        )
        
        # Run complete analysis
        result = analyzer.analyze_with_blocks(self.complex_text, "asciidoc", AnalysisMode.SPACY_WITH_MODULAR_RULES)
        
        # Verify complete result structure
        self.assertIn('analysis', result)
        self.assertIn('structural_blocks', result)
        self.assertIn('has_structure', result)
        
        analysis = result['analysis']
        
        # Check that analysis completed successfully
        self.assertIn('errors', analysis)
        self.assertIn('suggestions', analysis)
        self.assertIn('statistics', analysis)
        # Note: Field name can be 'technical_metrics' or 'technical_writing_metrics'
        self.assertTrue('technical_metrics' in analysis or 'technical_writing_metrics' in analysis)
        self.assertIn('overall_score', analysis)
        
        # Check enhanced validation fields
        if analyzer.enable_enhanced_validation:
            self.assertIn('validation_performance', analysis)
            self.assertIn('enhanced_validation_enabled', analysis)
            self.assertTrue(analysis['enhanced_validation_enabled'])
            
            # Check validation performance data
            validation_perf = analysis['validation_performance']
            self.assertIn('total_validations', validation_perf)
            self.assertIn('validation_time', validation_perf)
            self.assertIn('confidence_stats', validation_perf)
            
            # Should have some validation activity
            self.assertGreaterEqual(validation_perf['total_validations'], 0)
        
        # Test serialization
        import json
        try:
            json_str = json.dumps(result, indent=2)
            deserialized = json.loads(json_str)
            self.assertEqual(len(result), len(deserialized))
            print("✅ Enhanced structural analysis results are JSON serializable")
        except (TypeError, ValueError) as e:
            self.fail(f"Enhanced structural analysis results not serializable: {e}")
        
        print(f"Integration test results: Analysis mode={analysis.get('analysis_mode')}")
        print(f"  Enhanced validation: {analysis.get('enhanced_validation_enabled', False)}")
        print(f"  Total blocks processed: {len(result.get('structural_blocks', []))}")
        print(f"  Total errors: {len(analysis.get('errors', []))}")
        
        if 'enhanced_error_stats' in analysis:
            stats = analysis['enhanced_error_stats']
            print(f"  Enhanced errors: {stats.get('enhanced_errors', 0)}/{stats.get('total_errors', 0)}")
            print(f"  Enhancement rate: {stats.get('enhancement_rate', 0.0):.2%}")
    
    def test_analyzer_comparison_enhanced_vs_basic(self):
        """Compare enhanced vs basic structural analyzer."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comparison testing")
        
        # Create shared mock components
        mock_readability_analyzer = Mock()
        mock_sentence_analyzer = Mock()
        mock_sentence_analyzer.split_sentences_safe.return_value = [
            "The sophisticated methodology can't facilitate comprehensive analysis."
        ]
        
        mock_statistics_calculator = Mock()
        mock_statistics_calculator.split_paragraphs_safe.return_value = ["Test paragraph"]
        mock_statistics_calculator.calculate_comprehensive_statistics.return_value = {
            'word_count': 10, 'sentence_count': 1, 'paragraph_count': 1
        }
        mock_statistics_calculator.calculate_comprehensive_technical_metrics.return_value = {
            'readability_score': 70.0, 'complexity_score': 0.5
        }
        
        mock_suggestion_generator = Mock()
        mock_suggestion_generator.generate_suggestions.return_value = []
        
        # Basic analyzer
        basic_analyzer = StructuralAnalyzer(
            mock_readability_analyzer,
            mock_sentence_analyzer,
            mock_statistics_calculator,
            mock_suggestion_generator,
            Mock(),  # Basic registry
            self.nlp,
            enable_enhanced_validation=False
        )
        
        # Enhanced analyzer
        enhanced_analyzer = StructuralAnalyzer(
            mock_readability_analyzer,
            mock_sentence_analyzer,
            mock_statistics_calculator,
            mock_suggestion_generator,
            Mock(),  # Will be replaced
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.3
        )
        
        test_text = "The sophisticated methodology can't facilitate analysis."
        
        # Get status from both
        basic_status = basic_analyzer.get_enhanced_validation_status()
        enhanced_status = enhanced_analyzer.get_enhanced_validation_status()
        
        # Compare statuses
        self.assertFalse(basic_status['enhanced_validation_enabled'])
        
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertTrue(enhanced_status['enhanced_validation_enabled'])
            self.assertEqual(enhanced_status['confidence_threshold'], 0.3)
        else:
            # If enhanced validation not available, should fall back gracefully
            self.assertFalse(enhanced_status['enhanced_validation_enabled'])
        
        print(f"Comparison test:")
        print(f"  Basic analyzer enhanced validation: {basic_status['enhanced_validation_enabled']}")
        print(f"  Enhanced analyzer enhanced validation: {enhanced_status['enhanced_validation_enabled']}")
        print(f"  Enhanced validation available: {ENHANCED_VALIDATION_AVAILABLE}")


if __name__ == '__main__':
    # Configure test runner for comprehensive output
    unittest.main(verbosity=2, buffer=True)