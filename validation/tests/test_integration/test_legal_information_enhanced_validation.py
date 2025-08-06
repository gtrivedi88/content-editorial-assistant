"""
Comprehensive test suite for legal_information directory enhanced validation.
Tests all rules in the legal_information directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.legal_information.claims_rule import ClaimsRule
from rules.legal_information.company_names_rule import CompanyNamesRule
from rules.legal_information.personal_information_rule import PersonalInformationRule

class TestLegalInformationEnhancedValidation(unittest.TestCase):
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

    def test_claims_rule_enhanced_validation(self):
        """Test ClaimsRule with enhanced validation parameters."""
        rule = ClaimsRule()
        
        # Test text with multiple claim words
        test_text = "This solution is secure and provides an easy setup process. It's a best practice approach that offers effortless configuration."
        test_sentences = [
            "This solution is secure and provides an easy setup process.",
            "It's a best practice approach that offers effortless configuration."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find multiple claim words
            self.assertGreater(len(errors), 0, "Should detect claim words in the test text")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("makes a subjective or unsupported claim", error['message'])
                self.assertEqual(error['severity'], 'high')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
        else:
            print("Skipping detailed claims rule test - SpaCy not available")

    def test_company_names_rule_enhanced_validation(self):
        """Test CompanyNamesRule with enhanced validation parameters."""
        rule = CompanyNamesRule()
        
        # Test text with company names that might need legal suffixes
        test_text = "Oracle provides database solutions and Microsoft develops software products. Red Hat offers enterprise solutions."
        test_sentences = [
            "Oracle provides database solutions and Microsoft develops software products.",
            "Red Hat offers enterprise solutions."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # May or may not find errors depending on NLP entity recognition
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("should be written with its full legal name", error['message'])
                self.assertEqual(error['severity'], 'low')
                self.assertIsInstance(error['suggestions'], list)
        else:
            print("Skipping detailed company names rule test - SpaCy not available")

    def test_personal_information_rule_enhanced_validation(self):
        """Test PersonalInformationRule with enhanced validation parameters."""
        rule = PersonalInformationRule()
        
        # Test text with problematic personal information terms
        test_text = "Please enter your first name and last name in the form. The Christian name field is required."
        test_sentences = [
            "Please enter your first name and last name in the form.",
            "The Christian name field is required."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find multiple problematic terms
            self.assertGreater(len(errors), 0, "Should detect problematic personal information terms")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Use a more globally understood term", error['message'])
                self.assertEqual(error['severity'], 'medium')
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0)
                
                # Check for span information
                self.assertIn('span', error)
                self.assertIn('flagged_text', error)
        else:
            print("Skipping detailed personal information rule test - SpaCy not available")

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [ClaimsRule(), CompanyNamesRule(), PersonalInformationRule()]
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
        rules = [ClaimsRule(), CompanyNamesRule(), PersonalInformationRule()]
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
        
        rule = ClaimsRule()  # Test with the most complex rule
        test_text = "This is a secure and easy solution that follows best practice guidelines."
        test_sentences = ["This is a secure and easy solution that follows best practice guidelines."]
        
        if self.nlp:
            # Measure performance
            start_time = time.time()
            for _ in range(10):  # Run multiple times for average
                rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            # Should be under 100ms per analysis as per the implementation guide
            self.assertLess(avg_time, 0.1, f"Analysis took {avg_time:.3f}s, should be under 0.1s")

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

    def test_contextual_suggestions_quality(self):
        """Test that contextual suggestions are meaningful and helpful."""
        if not self.nlp:
            self.skipTest("SpaCy not available for contextual testing")
            
        rule = ClaimsRule()
        
        # Test different contexts
        test_cases = [
            {
                'text': "This process is easy to follow.",
                'expected_suggestion_keywords': ['straightforward', 'simple']
            },
            {
                'text': "The system is secure and reliable.",
                'expected_suggestion_keywords': ['security-enhanced', 'encrypted']
            },
            {
                'text': "This is the best practice approach.",
                'expected_suggestion_keywords': ['recommended', 'standard']
            }
        ]
        
        for test_case in test_cases:
            errors = rule.analyze(test_case['text'], [test_case['text']], nlp=self.nlp, context=self.test_context)
            
            if errors:  # If the rule found errors
                for error in errors:
                    suggestions_text = ' '.join(error['suggestions']).lower()
                    # Check if any expected keywords appear in suggestions
                    found_keyword = any(keyword in suggestions_text for keyword in test_case['expected_suggestion_keywords'])
                    self.assertTrue(found_keyword, 
                                  f"Expected contextual suggestions not found for '{test_case['text']}'. "
                                  f"Got: {error['suggestions']}")

if __name__ == '__main__':
    unittest.main()