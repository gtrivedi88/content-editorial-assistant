#!/usr/bin/env python3
"""Debug failing language and grammar rules to identify root causes."""

import sys
sys.path.insert(0, '/home/gtrivedi/Documents/GitHub/style-guide-ai')

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    print("❌ SpaCy not available")
    exit(1)

from rules.language_and_grammar.verbs_rule import VerbsRule
from rules.language_and_grammar.plurals_rule import PluralsRule
from rules.language_and_grammar.prepositions_rule import PrepositionsRule
from rules.language_and_grammar.abbreviations_rule import AbbreviationsRule
from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule
from rules.language_and_grammar.inclusive_language_rule import InclusiveLanguageRule

def debug_rule(rule_name, rule, test_text, context, should_detect, description):
    """Debug a specific rule with detailed output."""
    print(f"\n🔍 DEBUGGING: {rule_name.upper()}")
    print(f"   Text: '{test_text}'")
    print(f"   Expected: {'Detection' if should_detect else 'No detection'}")
    print(f"   Description: {description}")
    
    try:
        # Get detailed analysis
        errors = rule.analyze(test_text, [test_text], nlp, context)
        detected = len(errors) > 0
        
        print(f"   Actual: {'Detection' if detected else 'No detection'}")
        
        if errors:
            print(f"   Found {len(errors)} error(s):")
            for i, error in enumerate(errors, 1):
                flagged = error.get('flagged_text', error.get('text', 'N/A'))
                score = error.get('evidence_score', 'N/A')
                message = error.get('message', 'N/A')
                print(f"     {i}. '{flagged}' (score: {score})")
                print(f"        Message: {message}")
        else:
            print("   No errors found")
            
        # Check if it matches expectation
        if detected == should_detect:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL - Investigating...")
            
            # For debugging, let's analyze the text structure
            doc = nlp(test_text)
            print(f"   📊 Text analysis:")
            for token in doc:
                print(f"     '{token.text}' -> {token.pos_} ({token.lemma_})")
                
    except Exception as e:
        print(f"   💥 ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("🎯 DEBUGGING FAILED LANGUAGE & GRAMMAR RULES")
    print("=" * 60)
    
    # Test each failing rule
    failing_tests = [
        {
            "rule_name": "verbs",
            "rule": VerbsRule(),
            "text": "Login to the system and signup for notifications.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "description": "Should detect 'Login' and 'signup' as improper verb forms"
        },
        {
            "rule_name": "plurals", 
            "rule": PluralsRule(),
            "text": "These datas and informations are processed by multiple processers.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "description": "Should detect 'datas', 'informations', 'processers' as incorrect plurals"
        },
        {
            "rule_name": "prepositions",
            "rule": PrepositionsRule(),
            "text": "Click in the button to connect at the server.",
            "context": {"content_type": "tutorial", "audience": "user"},
            "should_detect": True,
            "description": "Should detect 'Click in' and 'connect at' as incorrect prepositions"
        },
        {
            "rule_name": "abbreviations",
            "rule": AbbreviationsRule(),
            "text": "The API uses JSON to send data via HTTP and HTTPS protocols.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": True,
            "description": "Should detect unexpanded abbreviations on first use"
        },
        {
            "rule_name": "anthropomorphism",
            "rule": AnthropomorphismRule(),
            "text": "The system detects that the user attempts to delete files, so it displays a warning.",
            "context": {"content_type": "technical", "audience": "developer"},
            "should_detect": False,
            "description": "Should NOT detect 'detects' as anthropomorphic (false positive)"
        },
        {
            "rule_name": "inclusive_language",
            "rule": InclusiveLanguageRule(),
            "text": "This is a simple solution that even a dummy user can understand.",
            "context": {"content_type": "documentation", "audience": "user"},
            "should_detect": True,
            "description": "Should detect 'dummy' as non-inclusive language"
        }
    ]
    
    for test in failing_tests:
        debug_rule(
            test["rule_name"],
            test["rule"],
            test["text"],
            test["context"],
            test["should_detect"],
            test["description"]
        )
    
    print(f"\n{'=' * 60}")
    print("🔧 DEBUG COMPLETE - Root causes identified above")

if __name__ == "__main__":
    main()
