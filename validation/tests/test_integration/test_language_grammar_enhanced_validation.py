"""
Comprehensive test suite for language_and_grammar directory enhanced validation.
Tests all rules in the language_and_grammar directory with Level 2 enhanced error creation.
"""

import unittest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import test utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import all language_and_grammar rules
from rules.base_rule import ENHANCED_VALIDATION_AVAILABLE

# Import availability checks for individual rules
rule_availability = {}
language_grammar_rules = [
    ('abbreviations_rule', 'AbbreviationsRule'),
    ('adverbs_only_rule', 'AdverbsOnlyRule'),
    ('anthropomorphism_rule', 'AnthropomorphismRule'),
    ('articles_rule', 'ArticlesRule'),
    ('capitalization_rule', 'CapitalizationRule'),
    ('conjunctions_rule', 'ConjunctionsRule'),
    ('contractions_rule', 'ContractionsRule'),
    ('inclusive_language_rule', 'InclusiveLanguageRule'),
    ('plurals_rule', 'PluralsRule'),
    ('possessives_rule', 'PossessivesRule'),
    ('prefixes_rule', 'PrefixesRule'),
    ('prepositions_rule', 'PrepositionsRule'),
    ('pronouns_rule', 'PronounsRule'),
    ('spelling_rule', 'SpellingRule'),
    ('terminology_rule', 'TerminologyRule'),
    ('verbs_rule', 'VerbsRule')  # Already enhanced in Step 17
]

# Import rules with availability tracking
for rule_module, rule_class in language_grammar_rules:
    try:
        module = __import__(f'rules.language_and_grammar.{rule_module}', fromlist=[rule_class])
        globals()[rule_class] = getattr(module, rule_class)
        rule_availability[rule_class] = True
    except ImportError:
        rule_availability[rule_class] = False


class TestLanguageGrammarEnhancedValidation(unittest.TestCase):
    """Test enhanced validation for all language_and_grammar rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Test data designed to trigger language and grammar rules
        self.test_text = """The sophisticated methodology can't facilitate comprehension effectively. 
        The analysis includes i.e. morphological features and e.g. syntactic structures.
        The data is analysed using colour-based visualization techniques.
        The systems thinks and believes the user will understand.
        The user's API properties need to be configured.
        The report contain only three word(s) analysis.
        A apple and a university was selected for testing.
        The system's methodology is very complex, containing many prepositions in the sentence structure analysis.
        The non-standard terms like blacklist should be avoided.
        The System should be Capitalized when referring to specific components.
        He will configure the system to ensure his preferences are applied.
        This is a overly-complex sentence containing numerous grammatical challenges, and it demonstrates various issues, but it continues with multiple clauses that make it difficult to read.
        """
        
        self.test_sentences = [
            "The sophisticated methodology can't facilitate comprehension effectively.",
            "The analysis includes i.e. morphological features and e.g. syntactic structures.",
            "The data is analysed using colour-based visualization techniques.",
            "The systems thinks and believes the user will understand.",
            "The user's API properties need to be configured.",
            "The report contain only three word(s) analysis.",
            "A apple and a university was selected for testing.",
            "The system's methodology is very complex, containing many prepositions in the sentence structure analysis.",
            "The non-standard terms like blacklist should be avoided.",
            "The System should be Capitalized when referring to specific components.",
            "He will configure the system to ensure his preferences are applied.",
            "This is a overly-complex sentence containing numerous grammatical challenges, and it demonstrates various issues, but it continues with multiple clauses that make it difficult to read."
        ]
        
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'software',
            'audience': 'developers',
            'medium': 'documentation',
            'document_title': 'Technical Writing Guidelines'
        }
        
        # Load spaCy model for testing
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except:
            self.nlp = None
    
    @unittest.skipIf(not rule_availability.get('ContractionsRule', False), "ContractionsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_contractions_rule_enhanced_validation(self):
        """Test ContractionsRule with enhanced validation."""
        rule = ContractionsRule()
        
        # Test with contractions
        contraction_text = "The system can't handle the user's requests, but it'll try."
        contraction_sentences = ["The system can't handle the user's requests, but it'll try."]
        
        errors = rule.analyze(contraction_text, contraction_sentences, nlp=self.nlp, context=self.test_context)
        
        # Verify errors were created
        self.assertGreater(len(errors), 0, "Expected errors for contractions")
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'contractions')
            self.assertIn('contraction', error['message'].lower())
    
    @unittest.skipIf(not rule_availability.get('AbbreviationsRule', False), "AbbreviationsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_abbreviations_rule_enhanced_validation(self):
        """Test AbbreviationsRule with enhanced validation."""
        rule = AbbreviationsRule()
        
        # Test with Latin abbreviations and undefined abbreviations
        abbrev_text = "The analysis includes i.e. morphological features and e.g. syntactic structures. The API configuration was updated."
        abbrev_sentences = ["The analysis includes i.e. morphological features and e.g. syntactic structures.", "The API configuration was updated."]
        
        errors = rule.analyze(abbrev_text, abbrev_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'abbreviations')
    
    @unittest.skipIf(not rule_availability.get('SpellingRule', False), "SpellingRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_spelling_rule_enhanced_validation(self):
        """Test SpellingRule with enhanced validation."""
        rule = SpellingRule()
        
        # Test with British spellings
        spelling_text = "The data is analysed using colour-based visualization techniques."
        spelling_sentences = ["The data is analysed using colour-based visualization techniques."]
        
        errors = rule.analyze(spelling_text, spelling_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'spelling')
            self.assertIn('spelling', error['message'].lower())
    
    @unittest.skipIf(not rule_availability.get('AnthropomorphismRule', False), "AnthropomorphismRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_anthropomorphism_rule_enhanced_validation(self):
        """Test AnthropomorphismRule with enhanced validation."""
        rule = AnthropomorphismRule()
        
        # Test with anthropomorphic language
        anthro_text = "The system thinks and believes the user will understand."
        anthro_sentences = ["The system thinks and believes the user will understand."]
        
        errors = rule.analyze(anthro_text, anthro_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'anthropomorphism')
            self.assertIn('anthropomorphism', error['message'].lower())
    
    @unittest.skipIf(not rule_availability.get('PossessivesRule', False), "PossessivesRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_possessives_rule_enhanced_validation(self):
        """Test PossessivesRule with enhanced validation."""
        rule = PossessivesRule()
        
        # Test with possessive on abbreviation
        possessive_text = "The API's properties need to be configured."
        possessive_sentences = ["The API's properties need to be configured."]
        
        errors = rule.analyze(possessive_text, possessive_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'possessives')
    
    @unittest.skipIf(not rule_availability.get('PluralsRule', False), "PluralsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_plurals_rule_enhanced_validation(self):
        """Test PluralsRule with enhanced validation."""
        rule = PluralsRule()
        
        # Test with (s) pattern
        plurals_text = "The report contains word(s) analysis."
        plurals_sentences = ["The report contains word(s) analysis."]
        
        errors = rule.analyze(plurals_text, plurals_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'plurals')
    
    @unittest.skipIf(not rule_availability.get('ArticlesRule', False), "ArticlesRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_articles_rule_enhanced_validation(self):
        """Test ArticlesRule with enhanced validation."""
        rule = ArticlesRule()
        
        # Test with incorrect article usage
        articles_text = "A apple and a university was selected for testing."
        articles_sentences = ["A apple and a university was selected for testing."]
        
        errors = rule.analyze(articles_text, articles_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'articles')
    
    @unittest.skipIf(not rule_availability.get('InclusiveLanguageRule', False), "InclusiveLanguageRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_inclusive_language_rule_enhanced_validation(self):
        """Test InclusiveLanguageRule with enhanced validation."""
        rule = InclusiveLanguageRule()
        
        # Test with non-inclusive terms
        inclusive_text = "The blacklist contains blocked items."
        inclusive_sentences = ["The blacklist contains blocked items."]
        
        errors = rule.analyze(inclusive_text, inclusive_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'inclusive_language')
    
    @unittest.skipIf(not rule_availability.get('PronounsRule', False), "PronounsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_pronouns_rule_enhanced_validation(self):
        """Test PronounsRule with enhanced validation."""
        rule = PronounsRule()
        
        # Test with gender-specific pronouns
        pronouns_text = "He will configure the system to ensure his preferences are applied."
        pronouns_sentences = ["He will configure the system to ensure his preferences are applied."]
        
        errors = rule.analyze(pronouns_text, pronouns_sentences, nlp=self.nlp, context=self.test_context)
        
        # Check enhanced validation fields
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'pronouns')
    
    def test_enhanced_validation_performance_language_grammar(self):
        """Test performance impact of enhanced validation in language_grammar rules."""
        if not self.nlp:
            self.skipTest("SpaCy not available for performance testing")
        
        # Test with multiple rules
        test_rules = []
        for rule_class in ['ContractionsRule', 'AbbreviationsRule', 'SpellingRule', 
                          'AnthropomorphismRule', 'PluralsRule']:
            if rule_availability.get(rule_class, False):
                test_rules.append((rule_class, globals()[rule_class]))
        
        performance_results = {}
        
        for rule_name, rule_class in test_rules:
            rule = rule_class()
            
            # Measure performance with enhanced validation
            start_time = time.time()
            for _ in range(3):  # Multiple iterations for average
                errors = rule.analyze(self.test_text, self.test_sentences, 
                                    nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 3
            performance_results[rule_name] = {
                'avg_time': avg_time,
                'errors_found': len(errors) if 'errors' in locals() else 0
            }
        
        # Verify performance is reasonable (less than 100ms per rule for complex grammar rules)
        for rule_name, results in performance_results.items():
            with self.subTest(rule=rule_name):
                self.assertLess(results['avg_time'], 0.1, 
                              f"{rule_name} too slow: {results['avg_time']:.4f}s")
                print(f"{rule_name}: {results['avg_time']*1000:.1f}ms, "
                      f"{results['errors_found']} errors")
    
    def test_language_grammar_error_serialization(self):
        """Test that all language_grammar errors are properly serializable."""
        import json
        
        # Test with all available rules
        all_errors = []
        
        # Test a few key rules with targeted inputs
        test_cases = [
            ('ContractionsRule', "can't", ["can't"]),
            ('SpellingRule', "colour", ["colour"]),
            ('InclusiveLanguageRule', "blacklist", ["blacklist"])
        ]
        
        for rule_class_name, test_text, test_sentences in test_cases:
            if rule_availability.get(rule_class_name, False):
                rule_class = globals()[rule_class_name]
                rule = rule_class()
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                all_errors.extend(errors)
        
        # Test JSON serialization
        try:
            json_str = json.dumps(all_errors, indent=2)
            deserialized = json.loads(json_str)
            
            self.assertEqual(len(all_errors), len(deserialized))
            print(f"Successfully serialized {len(all_errors)} language_grammar errors")
            
        except (TypeError, ValueError) as e:
            self.fail(f"Serialization failed: {e}")
    
    def test_backward_compatibility_language_grammar(self):
        """Test that enhanced rules maintain backward compatibility."""
        # Test that rules work without text and context parameters
        if rule_availability.get('SpellingRule', False):
            rule = SpellingRule()
            
            # Old style call (without enhanced parameters)
            try:
                errors_old = rule.analyze("colour", ["colour"])
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


class TestLanguageGrammarDirectoryIntegration(unittest.TestCase):
    """Test complete integration of the language_grammar directory."""
    
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
    
    def test_all_language_grammar_rules_integration(self):
        """Test that all language_grammar rules work together."""
        from rules import RulesRegistry
        
        # Create registry and get language/grammar rules
        registry = RulesRegistry()
        
        # Filter for language_grammar rules
        language_grammar_rules = {
            name: rule for name, rule in registry.rules.items() 
            if any(keyword in name.lower() for keyword in 
                  ['contraction', 'abbreviation', 'spelling', 'anthropomorphism', 
                   'plural', 'article', 'inclusive', 'pronoun', 'verb', 
                   'capitalization', 'conjunction', 'preposition', 'possessive',
                   'adverb', 'prefix', 'terminology'])
        }
        
        print(f"Found {len(language_grammar_rules)} language_grammar rules: {list(language_grammar_rules.keys())}")
        
        # Test text that should trigger multiple language/grammar rules
        test_text = """The sophisticated API's can't facilitate comprehensive data colour analysis.
        The systems thinks the user's won't understand i.e. complex terminology like blacklist.
        A apple was selected, but it's properties aren't analysed correctly.
        He believes the overly-complex sentence containing numerous prepositions in the system analysis won't work."""
        
        test_sentences = [
            "The sophisticated API's can't facilitate comprehensive data colour analysis.",
            "The systems thinks the user's won't understand i.e. complex terminology like blacklist.",
            "A apple was selected, but it's properties aren't analysed correctly.",
            "He believes the overly-complex sentence containing numerous prepositions in the system analysis won't work."
        ]
        
        # Run analysis
        all_errors = registry.analyze_with_context_aware_rules(
            test_text, test_sentences, nlp=self.nlp, context=self.test_context)
        
        # Filter for language/grammar errors
        language_errors = [
            error for error in all_errors 
            if any(keyword in error['type'].lower() for keyword in 
                  ['contraction', 'abbreviation', 'spelling', 'anthropomorphism', 
                   'plural', 'article', 'inclusive', 'pronoun', 'verb',
                   'capitalization', 'conjunction', 'preposition', 'possessive',
                   'adverb', 'prefix', 'terminology'])
        ]
        
        print(f"Found {len(language_errors)} language_grammar errors out of {len(all_errors)} total")
        
        # Verify enhanced validation in language/grammar errors
        enhanced_count = 0
        confidence_scores = []
        
        for error in language_errors:
            if error.get('enhanced_validation_available', False):
                enhanced_count += 1
                if 'confidence_score' in error:
                    confidence_scores.append(error['confidence_score'])
        
        if language_errors:
            print(f"Enhanced validation: {enhanced_count}/{len(language_errors)} errors")
            if confidence_scores:
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                print(f"Average confidence: {avg_confidence:.3f}")
        
        # Verify all errors are properly structured
        for error in language_errors:
            self.assertIn('type', error)
            self.assertIn('enhanced_validation_available', error)


if __name__ == '__main__':
    # Configure test runner for comprehensive output
    unittest.main(verbosity=2, buffer=True)