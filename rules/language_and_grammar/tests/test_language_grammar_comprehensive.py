#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing for Language & Grammar Rules
Tests all rules for production-grade functionality, evidence-based scoring, and context awareness.
"""

import sys
import os
sys.path.insert(0, '/home/gtrivedi/Documents/GitHub/style-guide-ai')

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    print("❌ SpaCy not available")
    exit(1)

# Import all language and grammar rules
from rules.language_and_grammar.terminology_rule import TerminologyRule
from rules.language_and_grammar.spelling_rule import SpellingRule
from rules.language_and_grammar.pronouns_rule import PronounsRule
from rules.language_and_grammar.prefixes_rule import PrefixesRule
from rules.language_and_grammar.contractions_rule import ContractionsRule
from rules.language_and_grammar.articles_rule import ArticlesRule
from rules.language_and_grammar.verbs_rule import VerbsRule
from rules.language_and_grammar.plurals_rule import PluralsRule
from rules.language_and_grammar.prepositions_rule import PrepositionsRule
from rules.language_and_grammar.abbreviations_rule import AbbreviationsRule
from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule
from rules.language_and_grammar.inclusive_language_rule import InclusiveLanguageRule

def test_language_grammar_comprehensive():
    """Comprehensive testing of language and grammar rules."""
    
    print("🎯 COMPREHENSIVE LANGUAGE & GRAMMAR RULES TEST")
    print("Testing all rules for evidence-based functionality and context awareness")
    print("=" * 85)
    
    # Initialize all rules
    rules = {
        "terminology": TerminologyRule(),
        "spelling": SpellingRule(), 
        "pronouns": PronounsRule(),
        "prefixes": PrefixesRule(),
        "contractions": ContractionsRule(),
        "articles": ArticlesRule(),
        "verbs": VerbsRule(),
        "plurals": PluralsRule(),
        "prepositions": PrepositionsRule(),
        "abbreviations": AbbreviationsRule(),
        "anthropomorphism": AnthropomorphismRule(),
        "inclusive_language": InclusiveLanguageRule()
    }
    
    # Comprehensive test scenarios covering critical functionality
    test_scenarios = [
        
        # === TERMINOLOGY RULE TESTS ===
        {
            "rule_name": "terminology",
            "category": "Terminology Standards",
            "content": "Check the infocenter for documentation about the dialog box.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["infocenter", "dialog box"],
            "description": "IBM terminology enforcement"
        },
        {
            "rule_name": "terminology", 
            "content": "Visit our website for user guides and tutorials.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct terminology usage"
        },
        
        # === SPELLING RULE TESTS ===
        {
            "rule_name": "spelling",
            "category": "US Spelling Standards",
            "content": "The colour scheme optimises system behaviour for organisations.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["colour", "optimises", "behaviour", "organisations"],
            "description": "British vs US spelling correction"
        },
        {
            "rule_name": "spelling",
            "content": "The color scheme optimizes system behavior for organizations.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct US spelling usage"
        },
        
        # === PRONOUNS RULE TESTS ===
        {
            "rule_name": "pronouns",
            "category": "Inclusive Language",
            "content": "When a user logs in, he should check his email first.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["he", "his"],
            "description": "Gendered pronoun usage in user instructions"
        },
        {
            "rule_name": "pronouns",
            "content": "When users log in, they should check their email first.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Gender-neutral pronoun usage"
        },
        
        # === PREFIXES RULE TESTS ===
        {
            "rule_name": "prefixes",
            "category": "Hyphenation Standards",
            "content": "The co-location of servers enables multi-user collaboration.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "expected_terms": ["co-location", "multi-user"],
            "description": "Unnecessary hyphenation in prefixes"
        },
        {
            "rule_name": "prefixes",
            "content": "The colocation of servers enables multiuser collaboration.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct closed-form prefix usage"
        },
        
        # === CONTRACTIONS RULE TESTS ===
        {
            "rule_name": "contractions",
            "category": "Professional Tone",
            "content": "Don't use this feature until you're sure it's configured properly.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["Don't", "you're", "it's"],
            "description": "Contractions in formal documentation"
        },
        {
            "rule_name": "contractions",
            "content": "Do not use this feature until you are sure it is configured properly.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Expanded forms in formal documentation"
        },
        
        # === ARTICLES RULE TESTS ===
        {
            "rule_name": "articles",
            "category": "Grammar Correctness", 
            "content": "Create a user account and an URL for the system.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["an URL"],
            "description": "Incorrect article usage (URL sounds like 'you')"
        },
        {
            "rule_name": "articles",
            "content": "Create a user account and a URL for the system.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct article usage"
        },
        
        # === VERBS RULE TESTS ===
        {
            "rule_name": "verbs",
            "category": "Clear Communication",
            "content": "Login to the system and signup for notifications.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["Login", "signup"],
            "description": "Noun forms used as verbs"
        },
        {
            "rule_name": "verbs",
            "content": "Log in to the system and sign up for notifications.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct verb forms"
        },
        
        # === PLURALS RULE TESTS ===
        {
            "rule_name": "plurals",
            "category": "Proper Pluralization",
            "content": "These datas and informations are processed by multiple processers.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "expected_terms": ["datas", "informations", "processers"],
            "description": "Incorrect plural forms"
        },
        {
            "rule_name": "plurals",
            "content": "This data and information are processed by multiple processors.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct plural forms"
        },
        
        # === PREPOSITIONS RULE TESTS ===
        {
            "rule_name": "prepositions",
            "category": "Idiomatic Usage",
            "content": "Click in the button to connect at the server.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["Click in", "connect at"],
            "description": "Incorrect preposition usage"
        },
        {
            "rule_name": "prepositions",
            "content": "Click on the button to connect to the server.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Correct preposition usage"
        },
        
        # === ABBREVIATIONS RULE TESTS ===
        {
            "rule_name": "abbreviations",
            "category": "Clarity Standards",
            "content": "The API uses JSON to send data via HTTP and HTTPS protocols.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "expected_terms": ["API", "JSON", "HTTP", "HTTPS"],
            "description": "Unexpanded abbreviations on first use"
        },
        {
            "rule_name": "abbreviations",
            "content": "The Application Programming Interface (API) uses JavaScript Object Notation (JSON).",
            "context": {"content_type": "technical", "audience": "beginner"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Properly expanded abbreviations"
        },
        
        # === ANTHROPOMORPHISM RULE TESTS ===
        {
            "rule_name": "anthropomorphism",
            "category": "Technical Clarity",
            "content": "The system thinks the user wants to delete files, so it decides to show a warning.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "expected_terms": ["thinks", "wants", "decides"],
            "description": "Anthropomorphic language in technical content"
        },
        {
            "rule_name": "anthropomorphism",
            "content": "The system detects that the user attempts to delete files, so it displays a warning.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Technical language without anthropomorphism"
        },
        
        # === INCLUSIVE LANGUAGE RULE TESTS ===
        {
            "rule_name": "inclusive_language",
            "category": "Inclusive Communication",
            "content": "This is a simple solution that even a dummy user can understand.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": True,
            "expected_terms": ["dummy"],
            "description": "Non-inclusive language in user documentation"
        },
        {
            "rule_name": "inclusive_language",
            "content": "This is a simple solution that any user can understand.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": False,
            "expected_terms": [],
            "description": "Inclusive language in user documentation"
        }
    ]
    
    # Execute tests
    passed = 0
    total = len(test_scenarios)
    failed_tests = []
    
    for i, test in enumerate(test_scenarios, 1):
        rule = rules[test["rule_name"]]
        
        print(f"\n🧪 Test {i}/{total}: {test['rule_name'].title()} - {test['description']}")
        print(f"   📝 Text: '{test['content']}'")
        print(f"   🎯 Context: {test['context']}")
        
        try:
            errors = rule.analyze(test['content'], [test['content']], nlp, test['context'])
            detected = len(errors) > 0
            
            expected = "Detection" if test['should_detect'] else "No detection"
            actual = "Detection" if detected else "No detection"
            
            if detected:
                flagged = [e.get('flagged_text', e.get('text', '')) for e in errors]
                scores = [f"{e.get('evidence_score', 0):.2f}" for e in errors]
                print(f"   🔍 Detected: {flagged} (scores: {scores})")
            else:
                print(f"   ✅ No issues detected")
            
            print(f"   Expected: {expected} | Actual: {actual}")
            
            if detected == test['should_detect']:
                print(f"   🏆 ✅ PASS")
                passed += 1
            else:
                print(f"   ❌ FAIL")
                failed_tests.append({
                    'test_num': i,
                    'rule': test['rule_name'],
                    'description': test['description'],
                    'expected': expected,
                    'actual': actual,
                    'content': test['content']
                })
                
        except Exception as e:
            print(f"   💥 ERROR: {str(e)}")
            failed_tests.append({
                'test_num': i,
                'rule': test['rule_name'],
                'description': test['description'],
                'error': str(e),
                'content': test['content']
            })
    
    # Final results
    success_rate = (passed / total) * 100
    print(f"\n{'=' * 85}")
    print(f"🎯 LANGUAGE & GRAMMAR TESTING: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if failed_tests:
        print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
        for fail in failed_tests:
            print(f"   • Test {fail['test_num']}: {fail['rule']} - {fail['description']}")
            if 'error' in fail:
                print(f"     Error: {fail['error']}")
            else:
                print(f"     Expected: {fail['expected']}, Got: {fail['actual']}")
    
    if success_rate >= 95:
        print("🏆 ✅ EXCELLENT PERFORMANCE! Language & Grammar rules are production-ready!")
    elif success_rate >= 85:
        print("✅ GOOD PERFORMANCE! Minor issues need attention.")
    else:
        print("❌ SIGNIFICANT ISSUES DETECTED! Major fixes required.")
    
    return success_rate, failed_tests

if __name__ == "__main__":
    test_language_grammar_comprehensive()
