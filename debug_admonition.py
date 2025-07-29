#!/usr/bin/env python3

from structural_parsing.asciidoc.parser import AsciiDocParser

def debug_admonition_parsing():
    """Debug how the AsciiDoc parser handles admonition content"""
    
    # User's exact content
    content = """NOTE: This is just a sanity check for the final deployment phase. You must whitelist the new IP addresses before continuing. The process is fast, it completes in under a minute."""
    
    print("Admonition Parsing Debug")
    print("=" * 50)
    print(f"Content: {content}")
    print()
    
    try:
        parser = AsciiDocParser()
        result = parser.parse(content)
        
        print(f"Parse success: {result.success}")
        if not result.success:
            print(f"Parse errors: {result.errors}")
            return
        
        print(f"Document type: {result.document.block_type}")
        print(f"Number of blocks: {len(result.document.blocks)}")
        print()
        
        for i, block in enumerate(result.document.blocks):
            print(f"Block {i+1}:")
            print(f"  Type: {block.block_type}")
            print(f"  Content: '{block.content[:100]}{'...' if len(block.content) > 100 else ''}'")
            print(f"  Raw content: '{block.raw_content[:100]}{'...' if len(block.raw_content) > 100 else ''}'")
            print(f"  Admonition type: {block.admonition_type}")
            print(f"  Style: {block.style}")
            print(f"  Context info: {block.get_context_info()}")
            print()
            
    except Exception as e:
        print(f"Error during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_admonition_parsing() 