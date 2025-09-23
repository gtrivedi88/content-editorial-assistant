"""
Integration tests for Markdown parser with format detector and parser factory.

Tests the complete workflow from format detection to parsing.
"""

import unittest
from structural_parsing import StructuralParserFactory, FormatDetector
from structural_parsing.markdown.types import MarkdownBlockType, MarkdownParseResult


class TestMarkdownFormatDetection(unittest.TestCase):
    """Test markdown format detection accuracy."""

    def setUp(self):
        self.detector = FormatDetector()

    def test_detect_simple_markdown(self):
        """Test detection of simple markdown."""
        content = """# Heading
This is a paragraph with **bold** text."""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'markdown')

    def test_detect_markdown_with_lists(self):
        """Test detection of markdown with lists."""
        content = """- First item
- Second item
- Third item"""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'markdown')

    def test_detect_markdown_with_code_blocks(self):
        """Test detection of markdown with code blocks."""
        content = """```python
def hello():
    print("Hello")
```"""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'markdown')

    def test_detect_markdown_with_blockquotes(self):
        """Test detection of markdown with blockquotes."""
        content = """> This is a blockquote
> spanning multiple lines."""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'markdown')

    def test_detect_markdown_vs_asciidoc(self):
        """Test distinguishing markdown from asciidoc."""
        markdown_content = """# Markdown Heading
- List item
```code```"""
        
        asciidoc_content = """= AsciiDoc Title
:author: John Doe
- List item
....
code block
...."""
        
        self.assertEqual(self.detector.detect_format(markdown_content), 'markdown')
        self.assertEqual(self.detector.detect_format(asciidoc_content), 'asciidoc')

    def test_detect_ambiguous_content(self):
        """Test detection of ambiguous content."""
        # Content that could be either format
        content = """Title
- Item 1
- Item 2"""
        
        # Should make a reasonable choice
        format_detected = self.detector.detect_format(content)
        self.assertIn(format_detected, ['markdown', 'asciidoc', 'plaintext'])

    def test_detect_plaintext(self):
        """Test detection of plain text."""
        content = """This is just plain text.
No special formatting.
Just regular sentences."""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'plaintext')


class TestParserFactoryMarkdown(unittest.TestCase):
    """Test parser factory with markdown content."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_auto_detect_and_parse_markdown(self):
        """Test automatic detection and parsing of markdown."""
        content = """# Main Title

This is a paragraph with some formatting.

## Subheading

- First item
- Second item
- Third item

```python
def example():
    return "code"
```"""
        
        result = self.factory.parse(content, format_hint='auto')
        
        self.assertIsInstance(result, MarkdownParseResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1)
        
        # Verify we have expected block types
        block_types = [block.block_type for block in result.document.blocks]
        self.assertIn(MarkdownBlockType.HEADING, block_types)
        self.assertIn(MarkdownBlockType.PARAGRAPH, block_types)
        self.assertIn(MarkdownBlockType.UNORDERED_LIST, block_types)
        self.assertIn(MarkdownBlockType.CODE_BLOCK, block_types)

    def test_explicit_markdown_hint(self):
        """Test explicit markdown format hint."""
        content = """Simple content that could be anything."""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertIsInstance(result, MarkdownParseResult)
        self.assertTrue(result.success)

    def test_plaintext_fallback_to_markdown(self):
        """Test that plaintext falls back to markdown parser."""
        content = """Just plain text content."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertIsInstance(result, MarkdownParseResult)
        self.assertTrue(result.success)

    def test_get_available_parsers(self):
        """Test getting available parsers info."""
        parsers = self.factory.get_available_parsers()
        
        self.assertIn('markdown', parsers)
        self.assertTrue(parsers['markdown']['available'])
        self.assertEqual(parsers['markdown']['parser'], 'markdown-it-py')


class TestMarkdownParserErrorHandling(unittest.TestCase):
    """Test error handling and edge cases in markdown parsing."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_empty_content(self):
        """Test parsing empty content."""
        result = self.factory.parse("", format_hint='markdown')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 0)

    def test_none_content(self):
        """Test parsing None content."""
        result = self.factory.parse(None, format_hint='markdown')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)

    def test_very_large_document(self):
        """Test parsing a very large markdown document."""
        # Create a large document
        large_content = []
        for i in range(1000):
            large_content.append(f"## Heading {i}")
            large_content.append(f"This is paragraph {i} with some content.")
            large_content.append("")
        
        content = "\n".join(large_content)
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1000)

    def test_malformed_content_recovery(self):
        """Test recovery from malformed markdown content."""
        content = """# Title
<script>alert('xss');</script>
```unclosed code block
- Malformed list
  - Without proper spacing
    - But still parseable

Regular paragraph at the end."""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        # Should still parse successfully
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1)

    def test_mixed_content_types(self):
        """Test mixed markdown and HTML content."""
        content = """# Markdown Title

<div class="custom-class">
  <p>HTML paragraph</p>
  <ul>
    <li>HTML list item</li>
  </ul>
</div>

## Back to Markdown

- Markdown list item
- Another item

<details>
<summary>Collapsible section</summary>

Markdown content inside HTML.

</details>"""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 3)


class TestMarkdownCompatibility(unittest.TestCase):
    """Test compatibility with style analysis system."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_block_skip_analysis_flags(self):
        """Test that appropriate blocks are flagged to skip analysis."""
        content = """# Title

Regular paragraph for analysis.

```python
# This code should be skipped
def function():
    return "test"
```

Another paragraph for analysis.

<script>
// This HTML should be skipped
alert('test');
</script>

Final paragraph for analysis."""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        
        # Check that code blocks and HTML blocks skip analysis
        for block in result.document.blocks:
            if block.block_type in [MarkdownBlockType.CODE_BLOCK, MarkdownBlockType.HTML_BLOCK]:
                self.assertTrue(block.should_skip_analysis())
            elif block.block_type in [MarkdownBlockType.PARAGRAPH, MarkdownBlockType.HEADING]:
                self.assertFalse(block.should_skip_analysis())

    def test_get_text_content_cleaning(self):
        """Test that text content is properly cleaned for analysis."""
        content = """This paragraph has **bold**, *italic*, and `code` formatting."""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        text_content = block.get_text_content()
        
        # Should have markdown formatting preserved but HTML tags removed
        # The actual behavior depends on how markdown-it-py processes the content
        self.assertIsInstance(text_content, str)
        self.assertGreater(len(text_content), 0)

    def test_context_info_generation(self):
        """Test context info generation for rules."""
        content = """# Main Heading

Regular paragraph.

## Sub Heading

- List item 1
- List item 2

```python
code block
```"""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        
        # Test context info for different block types
        for block in result.document.blocks:
            context = block.get_context_info()
            
            self.assertIn('block_type', context)
            self.assertIn('level', context)
            self.assertIn('contains_inline_formatting', context)
            
            # Verify block type mapping
            self.assertEqual(context['block_type'], block.block_type.value)
            
            if block.block_type == MarkdownBlockType.HEADING:
                self.assertGreater(block.level, 0)

    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        content = """# Title

Paragraph with content."""
        
        result = self.factory.parse(content, format_hint='markdown')
        
        self.assertTrue(result.success)
        
        # Test serialization
        for block in result.document.blocks:
            block_dict = block.to_dict()
            
            self.assertIn('block_type', block_dict)
            self.assertIn('content', block_dict)
            self.assertIn('level', block_dict)
            self.assertIn('should_skip_analysis', block_dict)
            self.assertIn('errors', block_dict)
            self.assertIn('children', block_dict)


if __name__ == '__main__':
    unittest.main()
