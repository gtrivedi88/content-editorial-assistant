"""
Comprehensive test suite for punctuation directory enhanced validation.
Tests all rules in the punctuation directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.punctuation.commas_rule import CommasRule
from rules.punctuation.quotation_marks_rule import QuotationMarksRule
from rules.punctuation.colons_rule import ColonsRule
from rules.punctuation.ellipses_rule import EllipsesRule
from rules.punctuation.periods_rule import PeriodsRule
from rules.punctuation.semicolons_rule import SemicolonsRule
from rules.punctuation.exclamation_points_rule import ExclamationPointsRule
from rules.punctuation.parentheses_rule import ParenthesesRule
from rules.punctuation.dashes_rule import DashesRule
from rules.punctuation.slashes_rule import SlashesRule
from rules.punctuation.punctuation_and_symbols_rule import PunctuationAndSymbolsRule
from rules.punctuation.hyphens_rule import HyphensRule

class TestPunctuationEnhancedValidation(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures and load SpaCy if available."""
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical', 
            'domain': 'software'
        }
        
        # Try to load spaCy model
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except (ImportError, OSError):
            # Create a mock NLP object for basic testing
            self.nlp = None
            print("Warning: SpaCy not available, using mock NLP for basic testing")

    def test_commas_rule_enhanced_validation(self):
        """Test CommasRule with enhanced validation parameters."""
        rule = CommasRule()
        
        # Test text with comma issues
        test_text = "Please install the software, configure the settings and restart the system. The database is running, the server is active. When installing the software follow these steps."
        test_sentences = [
            "Please install the software, configure the settings and restart the system.",
            "The database is running, the server is active.",
            "When installing the software follow these steps."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Missing serial (Oxford) comma",
                    "Potential comma splice",
                    "Missing comma after an introductory"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['medium', 'high'])
        else:
            print("Skipping detailed commas rule test - SpaCy not available")

    def test_quotation_marks_rule_enhanced_validation(self):
        """Test QuotationMarksRule with enhanced validation parameters."""
        rule = QuotationMarksRule()
        
        # Test text with quotation mark issues
        test_text = 'The system displayed "error". Use "quotes" for emphasis when needed.'
        test_sentences = [
            'The system displayed "error".',
            'Use "quotes" for emphasis when needed.'
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Punctuation placement with quotation mark",
                    "Quotation marks should not be used for emphasis"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['low', 'medium'])
        else:
            print("Skipping detailed quotation marks rule test - SpaCy not available")

    def test_colons_rule_enhanced_validation(self):
        """Test ColonsRule with enhanced validation parameters."""
        rule = ColonsRule()
        
        # Test text with colon issues
        test_text = "To install: download the software. The following: will be installed."
        test_sentences = [
            "To install: download the software.",
            "The following: will be installed."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Incorrect colon usage", error['message'])
                self.assertEqual(error['severity'], 'high')
        else:
            print("Skipping detailed colons rule test - SpaCy not available")

    def test_ellipses_rule_enhanced_validation(self):
        """Test EllipsesRule with enhanced validation parameters."""
        rule = EllipsesRule()
        
        # Test text with ellipses
        test_text = "The process takes time... and then completes. The system will continue…"
        test_sentences = [
            "The process takes time... and then completes.",
            "The system will continue…"
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find ellipses usage
            self.assertGreater(len(errors), 0, "Should detect ellipses usage")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Avoid using ellipses", error['message'])
                self.assertEqual(error['severity'], 'low')
        else:
            print("Skipping detailed ellipses rule test - SpaCy not available")

    def test_simple_punctuation_rules_enhanced_validation(self):
        """Test simple punctuation rules with enhanced validation parameters."""
        if not self.nlp:
            self.skipTest("SpaCy not available for punctuation testing")
            
        # Test different punctuation issues
        test_cases = [
            (PeriodsRule(), "The U.S.A. is a country.", "periods within uppercase abbreviations"),
            (SemicolonsRule(), "This is correct; however, this is not ideal.", "semicolons in technical writing"),
            (ExclamationPointsRule(), "This is amazing! Please check it.", "exclamation points"),
            (DashesRule(), "The system—when properly configured—works well.", "em dashes"),
            (SlashesRule(), "Use the CD/DVD drive for installation.", "slashes for and/or"),
            (PunctuationAndSymbolsRule(), "Configure the system & verify the settings.", "symbols in general text"),
            (HyphensRule(), "Use multi-threaded processing for better performance.", "hyphenation with prefixes")
        ]
        
        total_errors = 0
        enhanced_errors = 0
        
        for rule, test_text, description in test_cases:
            try:
                errors = rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.test_context)
                total_errors += len(errors)
                
                for error in errors:
                    self._verify_enhanced_error_structure(error)
                    if error.get('enhanced_validation_available', False):
                        enhanced_errors += 1
                        
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed for {description}: {e}")
        
        if total_errors > 0:
            enhancement_rate = (enhanced_errors / total_errors) * 100
            print(f"Simple punctuation rules enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")

    def test_parentheses_rule_enhanced_validation(self):
        """Test ParenthesesRule with enhanced validation parameters."""
        rule = ParenthesesRule()
        
        # Test text with parentheses punctuation issues
        test_text = "The system works well (as expected.) The configuration is complete (successfully)."
        test_sentences = [
            "The system works well (as expected.)",
            "The configuration is complete (successfully)."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("period should be placed outside the parentheses", error['message'])
                self.assertEqual(error['severity'], 'low')
        else:
            print("Skipping detailed parentheses rule test - SpaCy not available")

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [
            CommasRule(), QuotationMarksRule(), ColonsRule(), EllipsesRule(),
            PeriodsRule(), SemicolonsRule(), ExclamationPointsRule(), ParenthesesRule(),
            DashesRule(), SlashesRule(), PunctuationAndSymbolsRule(), HyphensRule()
        ]
        test_text = "Test text for basic functionality."
        test_sentences = ["Test text for basic functionality."]
        
        for rule in rules:
            try:
                # Test with no NLP (should return empty list)
                errors = rule.analyze(test_text, test_sentences, nlp=None, context=self.test_context)
                self.assertIsInstance(errors, list)
                
                # Test with NLP if available
                if self.nlp:
                    errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                    self.assertIsInstance(errors, list)
                    
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed basic functionality test: {e}")

    def test_enhanced_validation_backward_compatibility(self):
        """Test that rules work with old calling patterns (backward compatibility)."""
        rules = [
            CommasRule(), QuotationMarksRule(), EllipsesRule(), ExclamationPointsRule()
        ]
        test_text = "Test text."
        test_sentences = ["Test text."]
        
        for rule in rules:
            try:
                # Test old calling pattern without context
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp)
                self.assertIsInstance(errors, list)
                
                # Test old calling pattern with positional arguments
                errors = rule.analyze(test_text, test_sentences)
                self.assertIsInstance(errors, list)
                
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed backward compatibility test: {e}")

    def test_enhanced_validation_performance(self):
        """Test that enhanced validation doesn't significantly impact performance."""
        import time
        
        rule = CommasRule()  # Test with the most complex rule
        test_text = "Please install, configure, and test the software. When done, restart the system."
        test_sentences = [
            "Please install, configure, and test the software.",
            "When done, restart the system."
        ]
        
        if self.nlp:
            # Measure performance
            start_time = time.time()
            for _ in range(10):  # Run multiple times for average
                rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            # Should be under 100ms per analysis as per the implementation guide
            self.assertLess(avg_time, 0.1, f"Analysis took {avg_time:.3f}s, should be under 0.1s")

    def test_comprehensive_punctuation_scenarios(self):
        """Test complex punctuation scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        # Complex text with multiple punctuation issues
        test_text = """
        Please install the software, configure settings and restart! The system works... 
        To begin: follow these steps. Use "admin" mode for setup. The U.S.A. server
        is running; everything looks good. Use the CD/DVD drive & check the multi-user settings.
        The process (when complete.) will notify you—assuming everything works.
        """
        
        test_sentences = [s.strip() for s in test_text.strip().split('.') if s.strip()]
        
        rules = [
            CommasRule(), QuotationMarksRule(), ColonsRule(), EllipsesRule(),
            PeriodsRule(), SemicolonsRule(), ExclamationPointsRule(), ParenthesesRule(),
            DashesRule(), SlashesRule(), PunctuationAndSymbolsRule(), HyphensRule()
        ]
        
        total_errors = 0
        enhanced_errors = 0
        
        for rule in rules:
            try:
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                total_errors += len(errors)
                
                for error in errors:
                    self._verify_enhanced_error_structure(error)
                    if error.get('enhanced_validation_available', False):
                        enhanced_errors += 1
                        
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed comprehensive test: {e}")
        
        if total_errors > 0:
            enhancement_rate = (enhanced_errors / total_errors) * 100
            print(f"Comprehensive test enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")
            # Should have good enhancement coverage
            self.assertGreater(enhancement_rate, 0, "Should have some enhanced validation coverage")

    def test_domain_specific_validation(self):
        """Test that enhanced validation works with different domain contexts."""
        if not self.nlp:
            self.skipTest("SpaCy not available for domain testing")
            
        rule = ExclamationPointsRule()
        test_text = "This is amazing! The system works perfectly!"
        test_sentences = ["This is amazing!", "The system works perfectly!"]
        
        # Test different domain contexts
        contexts = [
            {'domain': 'software', 'content_type': 'technical'},
            {'domain': 'documentation', 'content_type': 'user_guide'},
            {'domain': 'general', 'content_type': 'instructions'}
        ]
        
        for context in contexts:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                # Enhanced validation should be available regardless of domain
                self.assertIn('enhanced_validation_available', error)

    def _verify_enhanced_error_structure(self, error):
        """Verify that an error has the enhanced validation structure."""
        # Verify basic required fields
        required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
        for field in required_fields:
            self.assertIn(field, error, f"Error missing required field: {field}")
        
        # Verify enhanced validation fields
        self.assertIn('enhanced_validation_available', error)
        
        if error.get('enhanced_validation_available', False):
            # If enhanced validation is available, check for confidence score
            if 'confidence_score' in error:
                confidence = error['confidence_score']
                self.assertIsInstance(confidence, (int, float))
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
        
        # Verify data types
        self.assertIsInstance(error['message'], str)
        self.assertIsInstance(error['suggestions'], list)
        self.assertIsInstance(error['sentence'], str)
        self.assertIsInstance(error['sentence_index'], int)
        self.assertIn(error['severity'], ['low', 'medium', 'high'])
        
        # Verify JSON serializability
        try:
            import json
            json.dumps(error)
        except TypeError as e:
            self.fail(f"Error is not JSON serializable: {e}")

if __name__ == '__main__':
    unittest.main()