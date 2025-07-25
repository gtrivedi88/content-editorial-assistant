#!/usr/bin/env python3
"""
Debug script to test paragraph detection in AsciiDoc parsing.
This will help understand why content immediately following headings isn't detected as paragraphs.
"""
import json
from structural_parsing.asciidoc.parser import AsciiDocParser

def debug_parsing():
    parser = AsciiDocParser()
    
    # Test case 1: Without blank line after heading
    content_no_blank = """= Integration with {ocp-brand-name}
{product} is fully integrated with {ocp-brand-name}, offering:

* Operators to manage application lifecycle."""
    
    # Test case 2: With blank line after heading  
    content_with_blank = """= Integration with {ocp-brand-name}

{product} is fully integrated with {ocp-brand-name}, offering:

* Operators to manage application lifecycle."""
    
    print("=" * 80)
    print("DEBUGGING PARAGRAPH DETECTION")
    print("=" * 80)
    
    # Parse both cases
    print("\n1. PARSING WITHOUT BLANK LINE AFTER HEADING:")
    print("-" * 50)
    result1 = parser.parse(content_no_blank, "test_no_blank.adoc")
    if result1.success:
        print_blocks(result1.document.blocks, level=0)
    else:
        print(f"Parse error: {result1.errors}")
    
    print("\n2. PARSING WITH BLANK LINE AFTER HEADING:")
    print("-" * 50)
    result2 = parser.parse(content_with_blank, "test_with_blank.adoc")
    if result2.success:
        print_blocks(result2.document.blocks, level=0)
    else:
        print(f"Parse error: {result2.errors}")

    # Let's also check the raw AST from Ruby
    print("\n3. RAW AST FROM RUBY (without blank line):")
    print("-" * 50)
    ruby_result1 = parser.ruby_client.run(content_no_blank, "test_no_blank.adoc")
    print(json.dumps(ruby_result1.get('data', {}), indent=2))
    
    print("\n4. RAW AST FROM RUBY (with blank line):")
    print("-" * 50)
    ruby_result2 = parser.ruby_client.run(content_with_blank, "test_with_blank.adoc")
    print(json.dumps(ruby_result2.get('data', {}), indent=2))

def print_blocks(blocks, level=0):
    """Print block structure in a readable format."""
    indent = "  " * level
    for i, block in enumerate(blocks):
        print(f"{indent}Block {i+1}:")
        print(f"{indent}  Type: {block.block_type.value}")
        print(f"{indent}  Content: '{block.content}'")
        print(f"{indent}  Raw: '{block.raw_content}'")
        print(f"{indent}  Line: {block.start_line}")
        if block.children:
            print(f"{indent}  Children:")
            print_blocks(block.children, level + 2)
        print()

if __name__ == "__main__":
    debug_parsing() 