"""
Comprehensive test suite for word_usage directory enhanced validation.
Tests all rules in the word_usage directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.word_usage.a_words_rule import AWordsRule
from rules.word_usage.b_words_rule import BWordsRule
from rules.word_usage.c_words_rule import CWordsRule
from rules.word_usage.k_words_rule import KWordsRule
from rules.word_usage.l_words_rule import LWordsRule
from rules.word_usage.q_words_rule import QWordsRule
from rules.word_usage.r_words_rule import RWordsRule
from rules.word_usage.s_words_rule import SWordsRule
from rules.word_usage.w_words_rule import WWordsRule
from rules.word_usage.x_words_rule import XWordsRule
from rules.word_usage.special_chars_rule import SpecialCharsRule

class TestWordUsageEnhancedValidation(unittest.TestCase):
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

    def test_a_words_rule_enhanced_validation(self):
        """Test AWordsRule with enhanced validation parameters."""
        rule = AWordsRule()
        
        # Test text with 'action' as a verb
        test_text = "Please action this request immediately. The system will action the command automatically."
        test_sentences = [
            "Please action this request immediately.",
            "The system will action the command automatically."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format for action as verb
                if "'action'" in error['message']:
                    self.assertIn("Do not use 'action' as a verb", error['message'])
                    self.assertEqual(error['severity'], 'medium')
                    self.assertIsInstance(error['suggestions'], list)
                    self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed a words rule test - SpaCy not available")

    def test_b_words_rule_enhanced_validation(self):
        """Test BWordsRule with enhanced validation parameters."""
        rule = BWordsRule()
        
        # Test text with backup/back up usage issues
        test_text = "I need to backup the database. The back up process is automated. This best practice ensures data safety."
        test_sentences = [
            "I need to backup the database.",
            "The back up process is automated.",
            "This best practice ensures data safety."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Incorrect verb form",
                    "Incorrect noun/adjective form",
                    "Review usage of the term"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['low', 'medium', 'high'])
        else:
            print("Skipping detailed b words rule test - SpaCy not available")

    def test_c_words_rule_enhanced_validation(self):
        """Test CWordsRule with enhanced validation parameters."""
        rule = CWordsRule()
        
        # Test text with C words that might trigger the rule
        test_text = "The system can check the configuration and confirm the settings."
        test_sentences = ["The system can check the configuration and confirm the settings."]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Review usage", error['message'])
                self.assertIsInstance(error['suggestions'], list)
        else:
            print("Skipping detailed c words rule test - SpaCy not available")

    def test_s_words_rule_enhanced_validation(self):
        """Test SWordsRule with enhanced validation parameters."""
        rule = SWordsRule()
        
        # Test text with setup/shutdown as verbs
        test_text = "Please setup the environment before you begin. The system will shutdown automatically at midnight."
        test_sentences = [
            "Please setup the environment before you begin.",
            "The system will shutdown automatically at midnight."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Incorrect verb form: 'setup' should be 'set up'",
                    "Incorrect verb form: 'shutdown' should be 'shut down'"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['medium', 'high'])
        else:
            print("Skipping detailed s words rule test - SpaCy not available")

    def test_special_chars_rule_enhanced_validation(self):
        """Test SpecialCharsRule with enhanced validation parameters."""
        rule = SpecialCharsRule()
        
        # Test text with # character usage
        test_text = "Use the # character to indicate numbers. The #hashtag is popular on social media."
        test_sentences = [
            "Use the # character to indicate numbers.",
            "The #hashtag is popular on social media."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Review usage of the term", error['message'])
                self.assertEqual(error['severity'], 'low')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed special chars rule test - SpaCy not available")

    def test_multiple_word_rules_enhanced_validation(self):
        """Test multiple word usage rules with enhanced validation parameters."""
        if not self.nlp:
            self.skipTest("SpaCy not available for multi-rule testing")
            
        rules_and_texts = [
            (KWordsRule(), "You can key in the password to access the system."),
            (LWordsRule(), "The application life cycle management is important."),
            (QWordsRule(), "Please add a quote from the documentation to support your argument."),
            (RWordsRule(), "The real time processing ensures low latency."),
            (WWordsRule(), "While the system is fast, it consumes a lot of memory."),
            (XWordsRule(), "The XML file contains configuration data.")
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

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [
            AWordsRule(), BWordsRule(), CWordsRule(), KWordsRule(),
            LWordsRule(), QWordsRule(), RWordsRule(), SWordsRule(),
            WWordsRule(), XWordsRule(), SpecialCharsRule()
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
            AWordsRule(), BWordsRule(), SWordsRule(), SpecialCharsRule()
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
        
        rule = BWordsRule()  # Test with a complex rule that has multiple patterns
        test_text = "Please backup the data and verify the best practice guidelines are followed."
        test_sentences = ["Please backup the data and verify the best practice guidelines are followed."]
        
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
            
        rule = BWordsRule()
        test_text = "This is considered a best practice in software development."
        test_sentences = ["This is considered a best practice in software development."]
        
        # Test different domain contexts
        contexts = [
            {'domain': 'software', 'content_type': 'technical'},
            {'domain': 'business', 'content_type': 'documentation'},
            {'domain': 'general', 'content_type': 'guidelines'}
        ]
        
        for context in contexts:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                # Enhanced validation should be available regardless of domain
                self.assertIn('enhanced_validation_available', error)

    def test_complex_word_usage_scenarios(self):
        """Test complex word usage scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        # Complex text with multiple word usage issues
        test_text = """
        Please action the backup process immediately. The setup should be completed before you shutdown the system.
        Use the # symbol carefully. I need a quote from the documentation. 
        While processing in real time, key in your credentials. The life cycle must be reviewed.
        This is a best practice approach.
        """
        
        test_sentences = [s.strip() for s in test_text.strip().split('.') if s.strip()]
        
        rules = [
            AWordsRule(), BWordsRule(), SWordsRule(), SpecialCharsRule(),
            QWordsRule(), RWordsRule(), WWordsRule(), KWordsRule(), LWordsRule()
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