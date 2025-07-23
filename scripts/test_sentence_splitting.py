#!/usr/bin/env python3
"""
Test script for verifying sentence splitting improvements.

This script tests the new NLTK-based sentence splitting against the old regex method
to verify improvements in handling edge cases.
"""

import sys
import os
import re

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import nltk
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("Downloading NLTK punkt_tab tokenizer...")
        try:
            nltk.download('punkt_tab', quiet=True)
        except:
            print("punkt_tab failed, trying punkt...")
            nltk.download('punkt', quiet=True)
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("WARNING: NLTK not available. Only testing fallback.")

def old_sentence_split(content: str):
    """Original regex-based sentence splitting (problematic)."""
    return re.split(r'(?<=[.!?])\s+', content.strip())

def new_sentence_split(content: str):
    """New robust sentence splitting with NLTK fallback."""
    if not content or not content.strip():
        return []
        
    content = content.strip()
    
    if NLTK_AVAILABLE:
        try:
            sentences = nltk.sent_tokenize(content)
            return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            print(f"NLTK failed: {e}. Using fallback.")
    
    # Improved regex fallback
    sentences = re.split(r'(?<![A-Z][a-z])\.\s+(?=[A-Z])|(?<=[.!?])\s+(?=[A-Z])', content)
    return [s.strip() for s in sentences if s.strip()]

def test_sentence_splitting():
    """Test cases for sentence splitting improvements."""
    
    test_cases = [
        # Basic cases (should work with both)
        {
            "text": "This is sentence one. This is sentence two.",
            "description": "Basic two sentences",
            "expected_count": 2
        },
        
        # Problematic cases for regex
        {
            "text": "Dr. Smith went to the U.S.A. for research. He found interesting results.",
            "description": "Abbreviations with periods",
            "expected_count": 2
        },
        {
            "text": "The version is 2.5.1. Download it from the website.",
            "description": "Version numbers",
            "expected_count": 2
        },
        {
            "text": "Configure the database. This step is critical for performance.",
            "description": "Pronoun reference (This)",
            "expected_count": 2
        },
        {
            "text": "What?! Really?! That's amazing!",
            "description": "Multiple punctuation",
            "expected_count": 3
        },
        {
            "text": "The API returns JSON. E.g., {'status': 'success'}.",
            "description": "Abbreviation e.g. with JSON",
            "expected_count": 2
        },
        {
            "text": "Visit https://example.com for more info. The site has documentation.",
            "description": "URLs in text",
            "expected_count": 2
        }
    ]
    
    print("=" * 60)
    print("SENTENCE SPLITTING TEST RESULTS")
    print("=" * 60)
    print(f"NLTK Available: {NLTK_AVAILABLE}")
    print()
    
    total_tests = len(test_cases)
    old_correct = 0
    new_correct = 0
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        description = test_case["description"]
        expected_count = test_case["expected_count"]
        
        print(f"Test {i}: {description}")
        print(f"Text: {text}")
        print()
        
        # Test old method
        old_sentences = old_sentence_split(text)
        old_count = len(old_sentences)
        old_pass = old_count == expected_count
        if old_pass:
            old_correct += 1
            
        # Test new method
        new_sentences = new_sentence_split(text)
        new_count = len(new_sentences)
        new_pass = new_count == expected_count
        if new_pass:
            new_correct += 1
        
        print(f"Expected sentences: {expected_count}")
        print(f"Old method: {old_count} {'✓' if old_pass else '✗'}")
        if old_sentences:
            for j, s in enumerate(old_sentences, 1):
                print(f"  {j}. '{s}'")
        
        print(f"New method: {new_count} {'✓' if new_pass else '✗'}")
        if new_sentences:
            for j, s in enumerate(new_sentences, 1):
                print(f"  {j}. '{s}'")
        
        if old_pass != new_pass:
            if new_pass:
                print("🎉 IMPROVEMENT: New method fixed this case!")
            else:
                print("⚠️  REGRESSION: New method broke this case!")
        
        print("-" * 40)
    
    print("\nSUMMARY:")
    print(f"Old method: {old_correct}/{total_tests} tests passed ({old_correct/total_tests*100:.1f}%)")
    print(f"New method: {new_correct}/{total_tests} tests passed ({new_correct/total_tests*100:.1f}%)")
    
    if new_correct > old_correct:
        print(f"🎉 IMPROVEMENT: {new_correct - old_correct} more tests passed!")
    elif new_correct < old_correct:
        print(f"⚠️  REGRESSION: {old_correct - new_correct} fewer tests passed!")
    else:
        print("📊 SAME: No change in test results")

def test_context_requiring_errors():
    """Test the context-requiring error detection."""
    from rewriter.assembly_line_rewriter import AssemblyLineRewriter
    from rewriter.generators import TextGenerator
    from rewriter.processors import TextProcessor
    from models import ModelManager
    
    # Create a minimal rewriter instance for testing
    model_manager = ModelManager()
    text_generator = TextGenerator(model_manager)
    text_processor = TextProcessor()
    rewriter = AssemblyLineRewriter(text_generator, text_processor)
    
    print("\n" + "=" * 60)
    print("CONTEXT-REQUIRING ERROR DETECTION TEST")
    print("=" * 60)
    
    test_errors = [
        {
            "type": "pronouns",
            "description": "Pronoun error - should require context"
        },
        {
            "type": "ambiguity", 
            "description": "Ambiguity error - should require context"
        },
        {
            "type": "word_usage",
            "description": "Word usage error - should NOT require context"
        },
        {
            "type": "spelling",
            "description": "Spelling error - should NOT require context"
        }
    ]
    
    for test_error in test_errors:
        error_type = test_error["type"]
        description = test_error["description"]
        
        needs_context = rewriter._sentence_needs_context([{"type": error_type}])
        expected = error_type in ["pronouns", "ambiguity", "missing_actor", "unclear_reference"]
        
        result = "✓" if needs_context == expected else "✗"
        print(f"{result} {description}")
        print(f"   Type: {error_type}, Needs context: {needs_context}, Expected: {expected}")
    
    print()

if __name__ == "__main__":
    test_sentence_splitting()
    test_context_requiring_errors()
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. ✅ NLTK sentence splitting implemented")
    print("2. ✅ Context-aware processing for pronouns implemented") 
    print("3. 📋 Test with real documents to verify improvements")
    print("4. 📋 Monitor for pronoun error frequency to validate approach")
    print("=" * 60) 