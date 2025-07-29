#!/usr/bin/env python3

from style_analyzer.core_analyzer import StyleAnalyzer

def test_exact_content():
    """Test with exact content user mentioned seeing issues with"""
    
    # Test different variations of NOTE content
    test_cases = [
        # Case 1: Standalone NOTE line (might be treated as paragraph)
        "NOTE: This is just a sanity check for the final deployment phase.",
        
        # Case 2: User's full content  
        "NOTE: This is just a sanity check for the final deployment phase. You must whitelist the new IP addresses before continuing. The process is fast, it completes in under a minute.",
        
        # Case 3: As part of a paragraph (might trigger different parsing)
        "When I test this asciidoctor paragraph, even though it says note. I can write \"NOTE:\" like this\n\nNOTE: This is just a sanity check for the final deployment phase.",
        
        # Case 4: Mixed content that might confuse the parser
        "This is a regular paragraph.\n\nNOTE: This is just a sanity check for the final deployment phase."
    ]
    
    for i, content in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST CASE {i}")
        print(f"{'='*60}")
        print(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        print()
        
        try:
            analyzer = StyleAnalyzer()
            results = analyzer.analyze(content, format_hint='asciidoc')
            
            all_errors = results.get('errors', [])
            
            # Look specifically for NOTE-related errors
            note_abbreviation_errors = [e for e in all_errors if 'NOTE' in e.get('message', '') and 'abbreviation' in e.get('message', '').lower()]
            colon_errors = [e for e in all_errors if 'colon' in e.get('message', '').lower()]
            
            print(f"Total errors: {len(all_errors)}")
            print(f"NOTE abbreviation errors: {len(note_abbreviation_errors)}")  
            print(f"Colon errors: {len(colon_errors)}")
            
            if note_abbreviation_errors:
                print("\n🚨 NOTE ABBREVIATION ERRORS FOUND:")
                for error in note_abbreviation_errors:
                    print(f"  - {error['message']}")
                    print(f"    Context: {error.get('structural_context', {}).get('block_type', 'unknown')}")
            
            if colon_errors:
                print("\n🚨 COLON ERRORS FOUND:")
                for error in colon_errors:
                    print(f"  - {error['message']}")
                    print(f"    Context: {error.get('structural_context', {}).get('block_type', 'unknown')}")
            
            # Show context of all errors
            if all_errors:
                print(f"\nAll error contexts:")
                for error in all_errors:
                    block_type = error.get('structural_context', {}).get('block_type', 'unknown')
                    print(f"  - {error.get('type', 'unknown')}: {block_type}")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_exact_content() 