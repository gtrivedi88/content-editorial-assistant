#!/usr/bin/env python3
"""
Debug failing plurals test cases to understand the rule behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import spacy
from rules.language_and_grammar.plurals_rule import PluralsRule

def debug_test_case(text, context, rule, nlp):
    """Debug a specific test case to understand linguistic analysis."""
    print(f"🔍 DEBUGGING: \"{text}\"")
    print(f"📋 Context: {context}")
    
    sentences = [text]
    errors = rule.analyze(text, sentences, nlp, context)
    
    if errors:
        print(f"🚨 Found {len(errors)} errors:")
        for i, error in enumerate(errors):
            print(f"  {i+1}. Message: {error.get('message', 'No message')}")
            print(f"     Evidence: {error.get('evidence_score', 'No evidence')}")
            print(f"     Flagged: '{error.get('flagged_text', 'Unknown')}'")
            print(f"     Span: {error.get('span', 'No span')}")
    else:
        print("✅ No errors found")
        
        # Debug why not detected - check potential issues
        doc = nlp(text)
        print("🔍 Checking potential issues manually:")
        
        # Check for (s) patterns
        import re
        s_pattern = re.findall(r'\b\w+\(s\)', text)
        if s_pattern:
            print(f"  Found (s) patterns: {s_pattern}")
        
        # Check for plural adjectives
        potential_issues = rule._find_potential_issues(doc, text)
        if potential_issues:
            print(f"  Found {len(potential_issues)} potential issues:")
            for issue in potential_issues:
                print(f"    Type: {issue['type']}, Text: '{issue['flagged_text']}'")
                # Calculate evidence manually
                evidence = rule._calculate_plurals_evidence(issue, doc, text, context)
                print(f"    Evidence: {evidence:.3f}")
        else:
            print("  No potential issues found by _find_potential_issues")
    
    print()

def main():
    """Debug the failing test cases."""
    print("🐛 DEBUGGING PLURALS RULE FAILURES")
    print("=" * 50)
    
    nlp = spacy.load('en_core_web_sm')
    rule = PluralsRule()
    
    # Failed test cases to debug
    failing_cases = [
        {
            'text': 'The user(s) should complete the registration.',
            'context': {'content_type': 'procedural', 'audience': 'general', 'block_type': 'paragraph'},
            'issue': 'Should be flagged but was not detected'
        },
        {
            'text': 'The item(s) will be processed automatically.',
            'context': {'content_type': 'marketing', 'audience': 'general', 'block_type': 'paragraph'},
            'issue': 'Should be flagged but was not detected'
        },
        {
            'text': 'The systems administrator manages server infrastructure.',
            'context': {'content_type': 'technical', 'audience': 'developer', 'block_type': 'paragraph'},
            'issue': 'Should be flagged as plural adjective but was not detected'
        },
        {
            'text': 'Set the parameter(s) according to your requirements.',
            'context': {'content_type': 'academic', 'audience': 'expert', 'block_type': 'paragraph'},
            'issue': 'Should be flagged in academic context but was not'
        },
        {
            'text': 'Configure the settings(s) properly.',
            'context': {'content_type': 'technical', 'audience': 'developer'},
            'issue': 'Should detect (s) pattern but did not'
        },
        {
            'text': 'The users manual provides detailed instructions.',
            'context': {'content_type': 'technical', 'audience': 'developer'},
            'issue': 'Should detect plural adjective but did not'
        }
    ]
    
    for i, case in enumerate(failing_cases, 1):
        print(f"❌ Failed Case {i}: {case['issue']}")
        debug_test_case(case['text'], case['context'], rule, nlp)

if __name__ == "__main__":
    main()
