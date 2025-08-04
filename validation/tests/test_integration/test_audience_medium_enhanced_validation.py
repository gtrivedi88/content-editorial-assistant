"""
Comprehensive test suite for audience_and_medium directory enhanced validation.
Tests all rules in the audience_and_medium directory with Level 2 enhanced error creation.
"""

import unittest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import test utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import all audience_and_medium rules
from rules.base_rule import ENHANCED_VALIDATION_AVAILABLE

try:
    from rules.audience_and_medium.llm_consumability_rule import LLMConsumabilityRule
    LLM_CONSUMABILITY_AVAILABLE = True
except ImportError:
    LLM_CONSUMABILITY_AVAILABLE = False

try:
    from rules.audience_and_medium.conversational_style_rule import ConversationalStyleRule
    CONVERSATIONAL_STYLE_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_STYLE_AVAILABLE = False

try:
    from rules.audience_and_medium.global_audiences_rule import GlobalAudiencesRule
    GLOBAL_AUDIENCES_AVAILABLE = True
except ImportError:
    GLOBAL_AUDIENCES_AVAILABLE = False

try:
    from rules.audience_and_medium.tone_rule import ToneRule
    TONE_RULE_AVAILABLE = True
except ImportError:
    TONE_RULE_AVAILABLE = False

try:
    from rules.audience_and_medium.base_audience_rule import BaseAudienceRule
    BASE_AUDIENCE_AVAILABLE = True
except ImportError:
    BASE_AUDIENCE_AVAILABLE = False


class TestAudienceMediumEnhancedValidation(unittest.TestCase):
    """Test enhanced validation for all audience_and_medium rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Test data designed to trigger audience/medium rules
        self.test_text = "The sophisticated methodology facilitates comprehension. " \
                        "Users can't really understand this complex interface design. " \
                        "This is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long sentence that definitely exceeds normal length limits."
        
        self.test_sentences = [
            "The sophisticated methodology facilitates comprehension.",
            "Users can't really understand this complex interface design.",
            "This is a very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very very long sentence that definitely exceeds normal length limits."
        ]
        
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'software',
            'audience': 'general',
            'medium': 'web',
            'document_title': 'User Interface Guidelines'
        }
        
        # Load spaCy model for testing
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    @unittest.skipIf(not LLM_CONSUMABILITY_AVAILABLE, "LLMConsumabilityRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_llm_consumability_rule_enhanced_validation(self):
        """Test LLMConsumabilityRule with enhanced validation."""
        rule = LLMConsumabilityRule()
        
        # Test with short sentences to trigger the rule
        short_text = "Hi. Yes. No. OK."
        short_sentences = ["Hi.", "Yes.", "No.", "OK."]
        
        errors = rule.analyze(short_text, short_sentences, nlp=self.nlp, context=self.test_context)
        
        # Verify errors were created
        self.assertGreater(len(errors), 0, "Expected errors for very short sentences")
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'llm_consumability')
            self.assertIn('short sentences', error['message'].lower())
    
    @unittest.skipIf(not CONVERSATIONAL_STYLE_AVAILABLE, "ConversationalStyleRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_conversational_style_rule_enhanced_validation(self):
        """Test ConversationalStyleRule with enhanced validation."""
        rule = ConversationalStyleRule()
        
        # Test with formal language to trigger the rule
        formal_text = "The methodology facilitates comprehensive understanding."
        formal_sentences = ["The methodology facilitates comprehensive understanding."]
        
        errors = rule.analyze(formal_text, formal_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'conversational_style')
            self.assertIn('formal', error['message'].lower())
    
    @unittest.skipIf(not GLOBAL_AUDIENCES_AVAILABLE, "GlobalAudiencesRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_global_audiences_rule_enhanced_validation(self):
        """Test GlobalAudiencesRule with enhanced validation."""
        rule = GlobalAudiencesRule()
        
        # Test with negative construction and long sentence
        negative_text = "This approach is not different from traditional methods. " + \
                       " ".join(["word"] * 35)  # Create a sentence with 35+ words
        negative_sentences = [negative_text]
        
        errors = rule.analyze(negative_text, negative_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'global_audiences')
            # Should catch either negative construction or long sentence
            self.assertTrue(
                'negative' in error['message'].lower() or 
                'long' in error['message'].lower(),
                f"Expected negative or length message, got: {error['message']}"
            )
    
    @unittest.skipIf(not TONE_RULE_AVAILABLE, "ToneRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available") 
    def test_tone_rule_enhanced_validation(self):
        """Test ToneRule with enhanced validation."""
        rule = ToneRule()
        
        # Test with informal phrases
        informal_text = "Let's get the ball rolling on this project."
        informal_sentences = ["Let's get the ball rolling on this project."]
        
        errors = rule.analyze(informal_text, informal_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'tone')
            self.assertIn('informal', error['message'].lower())
    
    @unittest.skipIf(not BASE_AUDIENCE_AVAILABLE, "BaseAudienceRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_base_audience_rule_enhanced_validation(self):
        """Test BaseAudienceRule helper methods with enhanced validation."""
        # Create a concrete implementation to test the base methods
        class TestAudienceRule(BaseAudienceRule):
            def _get_rule_type(self):
                return 'test_audience'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                errors = []
                if nlp:
                    for i, sentence in enumerate(sentences):
                        doc = nlp(sentence)
                        # Test the base analysis methods with enhanced parameters
                        errors.extend(self._analyze_conversational_appropriateness(
                            doc, sentence, i, text=text, context=context))
                        errors.extend(self._analyze_global_accessibility(
                            doc, sentence, i, text=text, context=context))
                        errors.extend(self._analyze_professional_tone(
                            doc, sentence, i, text=text, context=context))
                return errors
        
        rule = TestAudienceRule()
        
        # Test with complex formal language
        complex_text = "The sophisticated methodology facilitates comprehensive understanding through innovative approaches."
        complex_sentences = [complex_text]
        
        errors = rule.analyze(complex_text, complex_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields for any errors found
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'test_audience')
    
    def test_enhanced_validation_performance_audience_medium(self):
        """Test performance impact of enhanced validation in audience_medium rules."""
        if not self.nlp:
            self.skipTest("SpaCy not available for performance testing")
        
        # Test with multiple rules
        test_rules = []
        if LLM_CONSUMABILITY_AVAILABLE:
            test_rules.append(('LLMConsumabilityRule', LLMConsumabilityRule))
        if CONVERSATIONAL_STYLE_AVAILABLE:
            test_rules.append(('ConversationalStyleRule', ConversationalStyleRule))
        if GLOBAL_AUDIENCES_AVAILABLE:
            test_rules.append(('GlobalAudiencesRule', GlobalAudiencesRule))
        if TONE_RULE_AVAILABLE:
            test_rules.append(('ToneRule', ToneRule))
        
        performance_results = {}
        
        for rule_name, rule_class in test_rules:
            rule = rule_class()
            
            # Measure performance with enhanced validation
            start_time = time.time()
            for _ in range(5):  # Multiple iterations for average
                errors = rule.analyze(self.test_text, self.test_sentences, 
                                    nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 5
            performance_results[rule_name] = {
                'avg_time': avg_time,
                'errors_found': len(errors) if 'errors' in locals() else 0
            }
        
        # Verify performance is reasonable (less than 50ms per rule)
        for rule_name, results in performance_results.items():
            with self.subTest(rule=rule_name):
                self.assertLess(results['avg_time'], 0.05, 
                              f"{rule_name} too slow: {results['avg_time']:.4f}s")
                print(f"{rule_name}: {results['avg_time']*1000:.1f}ms, "
                      f"{results['errors_found']} errors")
    
    def test_audience_medium_error_serialization(self):
        """Test that all audience_medium errors are properly serializable."""
        import json
        
        # Test with all available rules
        all_errors = []
        
        if LLM_CONSUMABILITY_AVAILABLE:
            rule = LLMConsumabilityRule()
            errors = rule.analyze("Hi.", ["Hi."], nlp=self.nlp, context=self.test_context)
            all_errors.extend(errors)
        
        if CONVERSATIONAL_STYLE_AVAILABLE:
            rule = ConversationalStyleRule()
            errors = rule.analyze("The methodology facilitates understanding.", 
                                ["The methodology facilitates understanding."], 
                                nlp=self.nlp, context=self.test_context)
            all_errors.extend(errors)
        
        # Test JSON serialization
        try:
            json_str = json.dumps(all_errors, indent=2)
            deserialized = json.loads(json_str)
            
            self.assertEqual(len(all_errors), len(deserialized))
            print(f"Successfully serialized {len(all_errors)} audience_medium errors")
            
        except (TypeError, ValueError) as e:
            self.fail(f"Serialization failed: {e}")
    
    def test_backward_compatibility_audience_medium(self):
        """Test that enhanced rules maintain backward compatibility."""
        # Test that rules work without text and context parameters
        if CONVERSATIONAL_STYLE_AVAILABLE:
            rule = ConversationalStyleRule()
            
            # Old style call (without enhanced parameters)
            try:
                errors_old = rule.analyze("The methodology facilitates understanding.", 
                                        ["The methodology facilitates understanding."])
                # Should not crash and should return some structure
                self.assertIsInstance(errors_old, list)
                print(f"Backward compatibility test passed: {len(errors_old)} errors")
                
            except Exception as e:
                self.fail(f"Backward compatibility failed: {e}")
    
    def _verify_enhanced_error_structure(self, error):
        """Verify that an error has the enhanced validation structure."""
        # Basic required fields
        required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
        for field in required_fields:
            self.assertIn(field, error, f"Missing required field: {field}")
        
        # Enhanced validation fields
        self.assertIn('enhanced_validation_available', error)
        
        # If enhanced validation is available and working, check for enhanced fields
        if error.get('enhanced_validation_available', False):
            if 'confidence_score' in error:
                confidence = error['confidence_score']
                self.assertIsInstance(confidence, (int, float))
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)


class TestAudienceMediumDirectoryIntegration(unittest.TestCase):
    """Test complete integration of the audience_medium directory."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_context = {
            'block_type': 'paragraph', 
            'content_type': 'technical',
            'domain': 'software'
        }
        
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    def test_all_audience_medium_rules_integration(self):
        """Test that all audience_medium rules work together."""
        from rules import RulesRegistry
        
        # Create registry and get audience/medium rules
        registry = RulesRegistry()
        
        # Filter for audience_medium rules
        audience_medium_rules = {
            name: rule for name, rule in registry.rules.items() 
            if any(keyword in name.lower() for keyword in 
                  ['conversational', 'tone', 'global', 'llm', 'audience'])
        }
        
        print(f"Found {len(audience_medium_rules)} audience_medium rules: {list(audience_medium_rules.keys())}")
        
        # Test text that should trigger multiple audience/medium rules
        test_text = "The sophisticated methodology can't really facilitate comprehensive understanding. " \
                   "Let's get the ball rolling on this project with some really complex technical jargon."
        
        test_sentences = [
            "The sophisticated methodology can't really facilitate comprehensive understanding.",
            "Let's get the ball rolling on this project with some really complex technical jargon."
        ]
        
        # Run analysis
        all_errors = registry.analyze_with_context_aware_rules(
            test_text, test_sentences, nlp=self.nlp, context=self.test_context)
        
        # Filter for audience/medium errors
        audience_errors = [
            error for error in all_errors 
            if any(keyword in error['type'].lower() for keyword in 
                  ['conversational', 'tone', 'global', 'llm', 'audience'])
        ]
        
        print(f"Found {len(audience_errors)} audience_medium errors out of {len(all_errors)} total")
        
        # Verify enhanced validation in audience/medium errors
        enhanced_count = 0
        confidence_scores = []
        
        for error in audience_errors:
            if error.get('enhanced_validation_available', False):
                enhanced_count += 1
                if 'confidence_score' in error:
                    confidence_scores.append(error['confidence_score'])
        
        if audience_errors:
            print(f"Enhanced validation: {enhanced_count}/{len(audience_errors)} errors")
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                print(f"Average confidence: {avg_confidence:.3f}")
        
        # Verify all errors are properly structured
        for error in audience_errors:
            self.assertIn('type', error)
            self.assertIn('enhanced_validation_available', error)


if __name__ == '__main__':
    # Configure test runner for comprehensive output
    unittest.main(verbosity=2, buffer=True)