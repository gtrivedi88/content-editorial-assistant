#!/usr/bin/env python3

from style_analyzer.core_analyzer import StyleAnalyzer

def debug_admonition_pipeline():
    """Debug the full StyleAnalyzer pipeline with admonition content"""
    
    # User's exact content
    content = """NOTE: This is just a sanity check for the final deployment phase. You must whitelist the new IP addresses before continuing. The process is fast, it completes in under a minute."""
    
    print("Admonition Pipeline Debug")
    print("=" * 50)
    print(f"Content: {content}")
    print()
    
    try:
        analyzer = StyleAnalyzer()
        results = analyzer.analyze(content, format_hint='asciidoc')
        
        # Extract all errors
        all_errors = results.get('errors', [])
        print(f"Total errors found: {len(all_errors)}")
        
        # Look for abbreviation and colon errors
        abbreviation_errors = [e for e in all_errors if 'abbreviation' in e.get('message', '').lower()]
        colon_errors = [e for e in all_errors if 'colon' in e.get('message', '').lower()]
        
        print(f"Abbreviation errors: {len(abbreviation_errors)}")
        print(f"Colon errors: {len(colon_errors)}")
        
        if abbreviation_errors:
            print("\nAbbreviation errors:")
            for error in abbreviation_errors:
                print(f"  - {error['message']}")
                print(f"    Type: {error.get('type', 'unknown')}")
                print(f"    Context: {error.get('structural_context', 'No context')}")
        
        if colon_errors:
            print("\nColon errors:")
            for error in colon_errors:
                print(f"  - {error['message']}")
                print(f"    Type: {error.get('type', 'unknown')}")
                print(f"    Context: {error.get('structural_context', 'No context')}")
        
        # Show all errors for debugging
        if all_errors:
            print(f"\n=== ALL {len(all_errors)} ERRORS FOUND ===")
            for i, error in enumerate(all_errors, 1):
                print(f"{i}. {error.get('message', 'No message')}")
                print(f"   Type: {error.get('type', 'unknown')}")
                print(f"   Context: {error.get('structural_context', 'No context')}")
                print()
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_admonition_pipeline() 