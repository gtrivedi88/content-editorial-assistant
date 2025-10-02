"""
Comprehensive test suite for references directory enhanced validation.
Tests all rules in the references directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.references.names_and_titles_rule import NamesAndTitlesRule
from rules.references.product_versions_rule import ProductVersionsRule
from rules.references.geographic_locations_rule import GeographicLocationsRule
from rules.references.product_names_rule import ProductNamesRule
from rules.references.citations_rule import CitationsRule

class TestReferencesEnhancedValidation(unittest.TestCase):
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

    def test_names_and_titles_rule_enhanced_validation(self):
        """Test NamesAndTitlesRule with enhanced validation parameters."""
        rule = NamesAndTitlesRule()
        
        # Test text with title capitalization issues
        test_text = "Meet John Smith, ceo of the company. The manager will assist you."
        test_sentences = [
            "Meet John Smith, ceo of the company.",
            "The manager will assist you."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Professional title",
                    "should be capitalized when used with a name",
                    "should be lowercase"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed names and titles rule test - SpaCy not available")

    def test_product_versions_rule_enhanced_validation(self):
        """Test ProductVersionsRule with enhanced validation parameters."""
        rule = ProductVersionsRule()
        
        # Test text with version identifier issues
        test_text = "Download V2.1 of the software. Use Release 3.0 for better features."
        test_sentences = [
            "Download V2.1 of the software.",
            "Use Release 3.0 for better features."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find version identifier issues
            self.assertGreater(len(errors), 0, "Should detect version identifier usage")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Avoid using version identifiers", error['message'])
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed product versions rule test - SpaCy not available")

    def test_geographic_locations_rule_enhanced_validation(self):
        """Test GeographicLocationsRule with enhanced validation parameters."""
        rule = GeographicLocationsRule()
        
        # Test text with location capitalization issues
        test_text = "Visit new york and los angeles. The london office is open."
        test_sentences = [
            "Visit new york and los angeles.",
            "The london office is open."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Geographic location", error['message'])
                self.assertIn("incorrect capitalization", error['message'])
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed geographic locations rule test - SpaCy not available")

    def test_product_names_rule_enhanced_validation(self):
        """Test ProductNamesRule with enhanced validation parameters."""
        rule = ProductNamesRule()
        
        # Test text with product name issues (IBM missing)
        test_text = "Use Watson to build your AI applications. WebSphere is great for enterprise."
        test_sentences = [
            "Use Watson to build your AI applications.",
            "WebSphere is great for enterprise."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                if len(errors) > 0:
                    self.assertIn("should be preceded by 'IBM'", error['message'])
                    self.assertEqual(error['severity'], 'high')
        else:
            print("Skipping detailed product names rule test - SpaCy not available")

    def test_citations_rule_enhanced_validation(self):
        """Test CitationsRule with enhanced validation parameters."""
        rule = CitationsRule()
        
        # Test text with citation issues
        test_text = "Click here for more info. See Chapter 1 for details."
        test_sentences = [
            "Click here for more info.",
            "See Chapter 1 for details."
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find citation issues
            self.assertGreater(len(errors), 0, "Should detect citation issues")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Avoid using generic link text",
                    "should be lowercase in cross-references"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['medium', 'high'])
        else:
            print("Skipping detailed citations rule test - SpaCy not available")

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [
            NamesAndTitlesRule(), ProductVersionsRule(), GeographicLocationsRule(),
            ProductNamesRule(), CitationsRule()
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
            NamesAndTitlesRule(), ProductVersionsRule(), CitationsRule()
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
        
        rule = CitationsRule()  # Test with a representative rule
        test_text = "Click here for information. See Chapter 1 and go here for details."
        test_sentences = [
            "Click here for information.",
            "See Chapter 1 and go here for details."
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

    def test_comprehensive_references_scenarios(self):
        """Test complex reference scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        # Complex text with multiple reference issues
        test_text = """
        Visit new york for the conference. Meet John Smith, ceo of the company.
        Download V2.0 of Watson for your projects. Click here for installation guide.
        See Chapter 5 for more details. Use Release 3.1 for better performance.
        """
        
        test_sentences = [s.strip() for s in test_text.strip().split('.') if s.strip()]
        
        rules = [
            NamesAndTitlesRule(), ProductVersionsRule(), GeographicLocationsRule(),
            ProductNamesRule(), CitationsRule()
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
            
        rule = CitationsRule()
        test_text = "Click here to see more information about the product."
        test_sentences = ["Click here to see more information about the product."]
        
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

    def test_complex_reference_patterns(self):
        """Test complex reference patterns to ensure robust validation."""
        if not self.nlp:
            self.skipTest("SpaCy not available for complex pattern testing")
            
        # Test cases with varying complexity
        test_cases = [
            (NamesAndTitlesRule(), "Dr. jane smith, president of the organization", "title capitalization"),
            (ProductVersionsRule(), "Install V1.2.3 and Version 2.0", "version identifiers"),
            (GeographicLocationsRule(), "from new york to los angeles", "location capitalization"),
            (CitationsRule(), "go here and click here for details", "generic link text")
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
            print(f"Complex patterns enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")

    def test_json_serialization_compatibility(self):
        """Test that all errors are JSON serializable."""
        if not self.nlp:
            self.skipTest("SpaCy not available for JSON testing")
            
        import json
        
        rule = CitationsRule()
        test_text = "Click here for more information."
        test_sentences = ["Click here for more information."]
        
        errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
        
        for error in errors:
            try:
                json_str = json.dumps(error)
                self.assertIsInstance(json_str, str)
                # Verify it can be parsed back
                parsed = json.loads(json_str)
                self.assertIsInstance(parsed, dict)
            except (TypeError, ValueError) as e:
                self.fail(f"Error is not JSON serializable: {e}")

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