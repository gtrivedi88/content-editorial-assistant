"""
Comprehensive test suite for numbers_and_measurement directory enhanced validation.
Tests all rules in the numbers_and_measurement directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.numbers_and_measurement.units_of_measurement_rule import UnitsOfMeasurementRule
from rules.numbers_and_measurement.numbers_rule import NumbersRule
from rules.numbers_and_measurement.currency_rule import CurrencyRule
from rules.numbers_and_measurement.numerals_vs_words_rule import NumeralsVsWordsRule
from rules.numbers_and_measurement.dates_and_times_rule import DatesAndTimesRule

class TestNumbersAndMeasurementEnhancedValidation(unittest.TestCase):
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

    def test_units_of_measurement_rule_enhanced_validation(self):
        """Test UnitsOfMeasurementRule with enhanced validation parameters."""
        rule = UnitsOfMeasurementRule()
        
        # Test text with missing spaces between numbers and units
        test_text = "The server runs at 2.4GHz and has 16GB of RAM. The disk space is 500GB with transfer speeds of 100MHz."
        test_sentences = [
            "The server runs at 2.4GHz and has 16GB of RAM.",
            "The disk space is 500GB with transfer speeds of 100MHz."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find multiple unit formatting issues
            self.assertGreater(len(errors), 0, "Should detect missing spaces between numbers and units")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Missing space between number and unit", error['message'])
                self.assertEqual(error['severity'], 'medium')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
                
                # Check for span and flagged text
                self.assertIn('span', error)
                self.assertIn('flagged_text', error)
        else:
            print("Skipping detailed units rule test - SpaCy not available")

    def test_numbers_rule_enhanced_validation(self):
        """Test NumbersRule with enhanced validation parameters."""
        rule = NumbersRule()
        
        # Test text with number formatting issues
        test_text = "The system processes 50000 requests per second with a latency of .5 seconds. Memory usage is 12345 bytes."
        test_sentences = [
            "The system processes 50000 requests per second with a latency of .5 seconds.",
            "Memory usage is 12345 bytes."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find number formatting issues
            self.assertGreater(len(errors), 0, "Should detect number formatting issues")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Large numbers should use commas as thousands separators",
                    "Decimal values less than 1 should have a leading zero"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertEqual(error['severity'], 'medium')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed numbers rule test - SpaCy not available")

    def test_currency_rule_enhanced_validation(self):
        """Test CurrencyRule with enhanced validation parameters."""
        rule = CurrencyRule()
        
        # Test text with currency formatting issues
        test_text = "The software costs $500 for a basic license and $4M for enterprise. Premium support is €200 additional."
        test_sentences = [
            "The software costs $500 for a basic license and $4M for enterprise.",
            "Premium support is €200 additional."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find currency formatting issues
            self.assertGreater(len(errors), 0, "Should detect currency formatting issues")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "use the three-letter ISO currency code",
                    "Do not use letter abbreviations"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['medium', 'high'])
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed currency rule test - SpaCy not available")

    def test_numerals_vs_words_rule_enhanced_validation(self):
        """Test NumeralsVsWordsRule with enhanced validation parameters."""
        rule = NumeralsVsWordsRule()
        
        # Test text with inconsistent numeral/word usage
        test_text = "We have three servers and 5 databases. The system handles 2 requests at a time but can scale to eight concurrent connections."
        test_sentences = [
            "We have three servers and 5 databases.",
            "The system handles 2 requests at a time but can scale to eight concurrent connections."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # May find inconsistency errors
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Inconsistent use of numerals and words", error['message'])
                self.assertEqual(error['severity'], 'low')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed numerals vs words rule test - SpaCy not available")

    def test_dates_and_times_rule_enhanced_validation(self):
        """Test DatesAndTimesRule with enhanced validation parameters."""
        rule = DatesAndTimesRule()
        
        # Test text with date and time formatting issues
        test_text = "The system was deployed on 12/25/2023 and maintenance is scheduled for 3:30 p.m. The next update is on 01/15/2024 at 9:00 A.M."
        test_sentences = [
            "The system was deployed on 12/25/2023 and maintenance is scheduled for 3:30 p.m.",
            "The next update is on 01/15/2024 at 9:00 A.M."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find date and time formatting issues
            self.assertGreater(len(errors), 0, "Should detect date and time formatting issues")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Avoid all-numeric date formats",
                    "Use 'AM' or 'PM' (uppercase, no periods)"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['medium', 'high'])
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed dates and times rule test - SpaCy not available")

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [
            UnitsOfMeasurementRule(),
            NumbersRule(),
            CurrencyRule(),
            NumeralsVsWordsRule(),
            DatesAndTimesRule()
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
            UnitsOfMeasurementRule(),
            NumbersRule(),
            CurrencyRule(),
            NumeralsVsWordsRule(),
            DatesAndTimesRule()
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
        
        rule = NumbersRule()  # Test with a rule that has multiple patterns
        test_text = "The system handles 50000 requests with .5 second latency and costs $100."
        test_sentences = ["The system handles 50000 requests with .5 second latency and costs $100."]
        
        if self.nlp:
            # Measure performance
            start_time = time.time()
            for _ in range(10):  # Run multiple times for average
                rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            # Should be under 100ms per analysis as per the implementation guide
            self.assertLess(avg_time, 0.1, f"Analysis took {avg_time:.3f}s, should be under 0.1s")

    def test_domain_specific_validation(self):
        """Test that enhanced validation works with different domain contexts."""
        if not self.nlp:
            self.skipTest("SpaCy not available for domain testing")
            
        rule = CurrencyRule()
        test_text = "The system costs $500."
        test_sentences = ["The system costs $500."]
        
        # Test different domain contexts
        contexts = [
            {'domain': 'software', 'content_type': 'technical'},
            {'domain': 'finance', 'content_type': 'business'},
            {'domain': 'general', 'content_type': 'documentation'}
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

    def test_comprehensive_number_formatting_scenarios(self):
        """Test various number formatting scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        rules_and_texts = [
            (UnitsOfMeasurementRule(), "Server specs: 2.4GHz processor, 16GB RAM, 500GB storage"),
            (NumbersRule(), "Processing 10000 items with .75 accuracy and 25000 operations"),
            (CurrencyRule(), "Pricing: $99 basic, $5M enterprise, €150 support"),
            (NumeralsVsWordsRule(), "We have three servers, 5 databases, and two backups"),
            (DatesAndTimesRule(), "Deployed 12/25/2023 at 3:30 p.m., updated 01/15/2024 at 9:00 A.M.")
        ]
        
        total_errors = 0
        enhanced_errors = 0
        
        for rule, test_text in rules_and_texts:
            errors = rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.test_context)
            total_errors += len(errors)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                if error.get('enhanced_validation_available', False):
                    enhanced_errors += 1
        
        if total_errors > 0:
            enhancement_rate = (enhanced_errors / total_errors) * 100
            print(f"Enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")
            # Should have good enhancement coverage
            self.assertGreater(enhancement_rate, 0, "Should have some enhanced validation coverage")

if __name__ == '__main__':
    unittest.main()