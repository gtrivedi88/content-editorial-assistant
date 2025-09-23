"""
Comprehensive test suite for Markdown structural parser.

This test suite aggressively tests all aspects of the markdown parser
to ensure production readiness, similar to the asciidoc parser testing.
"""

import unittest
from typing import List, Optional
import tempfile
import os

from structural_parsing.markdown.parser import MarkdownParser
from structural_parsing.markdown.types import (
    MarkdownDocument, 
    MarkdownBlock, 
    MarkdownBlockType,
    MarkdownParseResult
)
from structural_parsing import StructuralParserFactory, FormatDetector


class TestMarkdownParserBasics(unittest.TestCase):
    """Test basic markdown parsing functionality."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_empty_document(self):
        """Test parsing empty document."""
        result = self.parser.parse("")
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 0)

    def test_simple_paragraph(self):
        """Test parsing simple paragraph."""
        content = "This is a simple paragraph."
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.PARAGRAPH)
        self.assertEqual(block.content, content)
        self.assertEqual(block.start_line, 1)

    def test_multiple_paragraphs(self):
        """Test parsing multiple paragraphs."""
        content = """First paragraph.

Second paragraph.

Third paragraph."""
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.block_type, MarkdownBlockType.PARAGRAPH)
            expected_content = ["First paragraph.", "Second paragraph.", "Third paragraph."][i]
            self.assertEqual(block.content, expected_content)


class TestMarkdownHeadings(unittest.TestCase):
    """Test markdown heading parsing."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_all_heading_levels(self):
        """Test all heading levels (H1-H6)."""
        content = """# Heading 1
## Heading 2  
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 6)
        
        expected_levels = [1, 2, 3, 4, 5, 6]
        expected_content = ["Heading 1", "Heading 2", "Heading 3", 
                          "Heading 4", "Heading 5", "Heading 6"]
        
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.block_type, MarkdownBlockType.HEADING)
            self.assertEqual(block.level, expected_levels[i])
            self.assertEqual(block.content, expected_content[i])

    def test_heading_with_trailing_spaces(self):
        """Test headings with trailing spaces and hashes."""
        content = """# Heading with trailing spaces   
## Heading with trailing hashes ##  
### Heading mixed ###   """
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        # Content should be cleaned of trailing spaces/hashes
        expected_content = ["Heading with trailing spaces", 
                          "Heading with trailing hashes", "Heading mixed"]
        
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.block_type, MarkdownBlockType.HEADING)
            self.assertEqual(block.content, expected_content[i])


class TestMarkdownLists(unittest.TestCase):
    """Test markdown list parsing."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_simple_unordered_list(self):
        """Test simple unordered list."""
        content = """- First item
- Second item
- Third item"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Should have one list block with multiple list items
        self.assertEqual(len(result.document.blocks), 1)
        list_block = result.document.blocks[0]
        self.assertEqual(list_block.block_type, MarkdownBlockType.UNORDERED_LIST)
        self.assertEqual(len(list_block.children), 3)
        
        expected_items = ["First item", "Second item", "Third item"]
        for i, item in enumerate(list_block.children):
            self.assertEqual(item.block_type, MarkdownBlockType.LIST_ITEM)

    def test_simple_ordered_list(self):
        """Test simple ordered list."""
        content = """1. First item
2. Second item  
3. Third item"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        self.assertEqual(len(result.document.blocks), 1)
        list_block = result.document.blocks[0]
        self.assertEqual(list_block.block_type, MarkdownBlockType.ORDERED_LIST)
        self.assertEqual(len(list_block.children), 3)

    def test_nested_lists(self):
        """Test nested lists."""
        content = """- Top level item 1
  - Nested item 1
  - Nested item 2
- Top level item 2
  1. Nested ordered item
  2. Another nested ordered item"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # This tests complex nesting which might be challenging
        self.assertGreaterEqual(len(result.document.blocks), 1)

    def test_mixed_list_markers(self):
        """Test lists with different markers (*, -, +)."""
        content = """* Item with asterisk
- Item with dash
+ Item with plus"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Different markers create separate lists (per CommonMark spec)
        self.assertEqual(len(result.document.blocks), 3)
        for block in result.document.blocks:
            self.assertEqual(block.block_type, MarkdownBlockType.UNORDERED_LIST)
            self.assertEqual(len(block.children), 1)
            self.assertEqual(block.children[0].block_type, MarkdownBlockType.LIST_ITEM)


class TestMarkdownCodeBlocks(unittest.TestCase):
    """Test markdown code block parsing."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_fenced_code_block(self):
        """Test fenced code blocks."""
        content = """```python
def hello_world():
    print("Hello, World!")
    return True
```"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.CODE_BLOCK)
        self.assertIn("def hello_world", block.content)
        self.assertIn("Hello, World!", block.content)
        # Should skip code blocks in analysis
        self.assertTrue(block.should_skip_analysis())

    def test_fenced_code_block_no_language(self):
        """Test fenced code block without language specification."""
        content = """```
Some code without language
var x = 1;
```"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.CODE_BLOCK)
        self.assertIn("Some code without language", block.content)

    def test_indented_code_block(self):
        """Test indented code blocks."""
        content = """Here is some code:

    def function():
        return "indented code"
    
    print("test")

Back to regular text."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Should have paragraph, code block, paragraph
        self.assertGreaterEqual(len(result.document.blocks), 2)

    def test_inline_code(self):
        """Test inline code within paragraphs."""
        content = "Use the `print()` function to output text."
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.PARAGRAPH)
        self.assertIn("print()", block.content)


class TestMarkdownQuotes(unittest.TestCase):
    """Test markdown blockquote parsing."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_simple_blockquote(self):
        """Test simple blockquote."""
        content = "> This is a blockquote."
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.BLOCKQUOTE)
        self.assertEqual(block.content, "This is a blockquote.")

    def test_multiline_blockquote(self):
        """Test multiline blockquote."""
        content = """> This is a multiline
> blockquote that spans
> several lines."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, MarkdownBlockType.BLOCKQUOTE)

    def test_nested_blockquote(self):
        """Test nested blockquotes."""
        content = """> Level 1 quote
>> Level 2 quote  
>>> Level 3 quote"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.document.blocks), 1)


class TestMarkdownTables(unittest.TestCase):
    """Test markdown table parsing."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_simple_table(self):
        """Test simple table parsing."""
        content = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Row 1 Col 1 | Row 1 Col 2 | Row 1 Col 3 |
| Row 2 Col 1 | Row 2 Col 2 | Row 2 Col 3 |"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Should have table structure
        self.assertGreaterEqual(len(result.document.blocks), 1)
        # Look for table blocks in the results
        table_blocks = [b for b in result.document.blocks if b.block_type == MarkdownBlockType.TABLE]
        self.assertGreaterEqual(len(table_blocks), 1)

    def test_table_with_alignment(self):
        """Test table with column alignment."""
        content = """| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.document.blocks), 1)

    def test_table_with_missing_cells(self):
        """Test table with missing cells."""
        content = """| Header 1 | Header 2 |
|----------|----------|
| Complete | Complete |
| Missing  |          |
|          | Missing  |"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Should still parse successfully
        self.assertGreaterEqual(len(result.document.blocks), 1)


class TestMarkdownMixedContent(unittest.TestCase):
    """Test complex mixed content scenarios."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_comprehensive_document(self):
        """Test a comprehensive document with all elements."""
        content = """# Main Title

This is an introduction paragraph with some **bold text** and *italic text*.

## Section 1

Here's a paragraph before a list:

- First list item with `inline code`
- Second item
  - Nested item
  - Another nested item

### Subsection

> This is a blockquote with some important information.
> It spans multiple lines.

Here's a code block:

```python
def example_function():
    return "Hello, World!"
```

## Section 2 with Table

| Feature | Status | Notes |
|---------|--------|-------|
| Parser | ✅ Done | Works well |
| Tests | 🚧 In Progress | Almost there |

### Final Notes

1. First point
2. Second point  
3. Third point

---

That's all!"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 10)
        
        # Check that we have various block types
        block_types = [block.block_type for block in result.document.blocks]
        
        # Should have headings
        self.assertIn(MarkdownBlockType.HEADING, block_types)
        # Should have paragraphs
        self.assertIn(MarkdownBlockType.PARAGRAPH, block_types)
        # Should have lists
        self.assertIn(MarkdownBlockType.UNORDERED_LIST, block_types)
        # Should have blockquotes
        self.assertIn(MarkdownBlockType.BLOCKQUOTE, block_types)
        # Should have code blocks
        self.assertIn(MarkdownBlockType.CODE_BLOCK, block_types)

    def test_document_with_html_blocks(self):
        """Test document with HTML blocks."""
        content = """# Title

<div class="special">
This is HTML content
</div>

Regular paragraph after HTML."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreater(len(result.document.blocks), 1)

    def test_document_with_horizontal_rules(self):
        """Test document with horizontal rules."""
        content = """Section 1

---

Section 2

***

Section 3

___

Final section"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreater(len(result.document.blocks), 3)
        
        # Should have horizontal rule blocks
        hr_blocks = [b for b in result.document.blocks 
                    if b.block_type == MarkdownBlockType.HORIZONTAL_RULE]
        self.assertGreaterEqual(len(hr_blocks), 1)


class TestMarkdownEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.parser = MarkdownParser()

    def test_whitespace_only_document(self):
        """Test document with only whitespace."""
        content = "   \n\n  \t\n   "
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        # Should handle gracefully
        self.assertIsNotNone(result.document)

    def test_very_long_lines(self):
        """Test very long lines."""
        long_line = "A" * 10000
        content = f"# Title\n\n{long_line}\n\nEnd."
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreater(len(result.document.blocks), 1)

    def test_malformed_headings(self):
        """Test malformed heading syntax."""
        content = """#No space after hash
# Proper heading
####### Too many hashes
# Another proper heading"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        # Should handle gracefully, some may be treated as paragraphs
        self.assertGreater(len(result.document.blocks), 1)

    def test_unclosed_code_blocks(self):
        """Test unclosed code blocks."""
        content = """```python
def function():
    return "no closing fence"

This should still be parsed."""
        
        result = self.parser.parse(content)
        # Should still succeed, markdown-it handles this
        self.assertTrue(result.success)

    def test_deeply_nested_structures(self):
        """Test deeply nested list structures."""
        content = """- Level 1
  - Level 2
    - Level 3
      - Level 4
        - Level 5
          - Level 6"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreaterEqual(len(result.document.blocks), 1)

    def test_mixed_line_endings(self):
        """Test mixed line endings (\\n, \\r\\n)."""
        content = "Line 1\nLine 2\r\nLine 3\nLine 4"
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)

    def test_unicode_content(self):
        """Test unicode content handling."""
        content = """# Título with àccènts

测试中文内容 with émojis 🎉

- 日本語 item
- العربية item  
- Ελληνικά item

```python
# Comment with unicode: café naïve résumé
def 函数名():
    return "🚀"
```"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertGreater(len(result.document.blocks), 1)
        
        # Verify unicode content is preserved
        heading = result.document.blocks[0]
        self.assertIn("Título", heading.content)


if __name__ == '__main__':
    unittest.main()
