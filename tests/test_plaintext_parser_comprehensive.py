"""
Comprehensive test suite for Plain Text structural parser.

This test suite aggressively tests all aspects of the plain text parser
to ensure production readiness, matching the testing level of AsciiDoc and Markdown parsers.
"""

import unittest
from typing import List, Optional
import tempfile
import os

from structural_parsing.plaintext.parser import PlainTextParser
from structural_parsing.plaintext.types import (
    PlainTextDocument, 
    PlainTextBlock, 
    PlainTextBlockType,
    PlainTextParseResult
)
from structural_parsing import StructuralParserFactory, FormatDetector


class TestPlainTextParserBasics(unittest.TestCase):
    """Test basic plain text parsing functionality."""

    def setUp(self):
        self.parser = PlainTextParser()

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
        self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
        self.assertEqual(block.content, content)
        self.assertEqual(block.start_line, 1)

    def test_multiple_paragraphs(self):
        """Test parsing multiple paragraphs separated by blank lines."""
        content = """First paragraph.

Second paragraph.

Third paragraph."""
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        expected_content = ["First paragraph.", "Second paragraph.", "Third paragraph."]
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
            self.assertEqual(block.content, expected_content[i])

    def test_paragraph_with_line_breaks(self):
        """Test paragraph with internal line breaks (no blank lines)."""
        content = """This is a paragraph
with multiple lines
but no blank lines."""
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
        self.assertEqual(block.content, content)

    def test_mixed_paragraph_styles(self):
        """Test mixed single-line and multi-line paragraphs."""
        content = """Single line paragraph.

Multi-line paragraph
spanning several lines
with no breaks.

Another single line."""
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        self.assertEqual(result.document.blocks[0].content, "Single line paragraph.")
        self.assertIn("Multi-line paragraph", result.document.blocks[1].content)
        self.assertEqual(result.document.blocks[2].content, "Another single line.")


class TestPlainTextEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.parser = PlainTextParser()

    def test_whitespace_only_document(self):
        """Test document with only whitespace."""
        content = "   \n\n  \t\n   "
        result = self.parser.parse(content)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 0)

    def test_none_content(self):
        """Test None content handling."""
        result = self.parser.parse(None)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 0)

    def test_very_long_lines(self):
        """Test very long lines."""
        long_line = "A" * 10000
        content = f"First paragraph.\n\n{long_line}\n\nLast paragraph."
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        self.assertEqual(result.document.blocks[1].content, long_line)

    def test_mixed_line_endings(self):
        """Test mixed line endings (\\n, \\r\\n, \\r)."""
        content = "Paragraph 1\n\nParagraph 2\r\n\r\nParagraph 3\r\rParagraph 4"
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 4)

    def test_unicode_content(self):
        """Test unicode content handling."""
        content = """English paragraph.

中文段落测试。

Ελληνικό κείμενο.

العربية النص.

🎉 Emoji paragraph! 🚀"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 5)
        
        # Verify unicode content is preserved
        self.assertIn("中文段落测试", result.document.blocks[1].content)
        self.assertIn("Ελληνικό κείμενο", result.document.blocks[2].content)
        self.assertIn("العربية النص", result.document.blocks[3].content)
        self.assertIn("🎉", result.document.blocks[4].content)

    def test_special_characters(self):
        """Test special characters that might confuse parsers."""
        content = """Paragraph with & < > " ' characters.

Symbols: @ # $ % ^ & * ( ) { } [ ] | \\ / ? ! ~

Code-like text: function() { return "test"; }"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        # Verify special characters are preserved
        self.assertIn("&", result.document.blocks[0].content)
        self.assertIn("@", result.document.blocks[1].content)
        self.assertIn("function()", result.document.blocks[2].content)

    def test_markdown_like_content(self):
        """Test content that looks like markdown but should be treated as plain text."""
        content = """# This looks like a heading

*This looks like bold*

- This looks like a list
- Another list item

```
This looks like code
```

But it's all plain text!"""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # All should be treated as paragraphs
        for block in result.document.blocks:
            self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
        
        # Content should be preserved as-is
        self.assertIn("# This looks like a heading", result.document.blocks[0].content)
        self.assertIn("*This looks like bold*", result.document.blocks[1].content)

    def test_excessive_blank_lines(self):
        """Test handling of excessive blank lines."""
        content = """Paragraph 1.




Paragraph 2.




Paragraph 3."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        expected_content = ["Paragraph 1.", "Paragraph 2.", "Paragraph 3."]
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.content, expected_content[i])


class TestPlainTextLineBased(unittest.TestCase):
    """Test line-based parsing mode."""

    def setUp(self):
        self.parser = PlainTextParser()

    def test_parse_as_lines_simple(self):
        """Test line-based parsing with simple content."""
        content = """Line 1
Line 2
Line 3"""
        result = self.parser.parse_as_lines(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        expected_lines = ["Line 1", "Line 2", "Line 3"]
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
            self.assertEqual(block.content, expected_lines[i])

    def test_parse_as_lines_with_empty_lines(self):
        """Test line-based parsing with empty lines."""
        content = """Line 1

Line 3

Line 5"""
        result = self.parser.parse_as_lines(content)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        expected_lines = ["Line 1", "Line 3", "Line 5"]
        for i, block in enumerate(result.document.blocks):
            self.assertEqual(block.content, expected_lines[i])

    def test_parse_as_lines_performance(self):
        """Test line-based parsing performance with many lines."""
        lines = [f"Line {i}" for i in range(1000)]
        content = "\n".join(lines)
        
        import time
        start_time = time.time()
        result = self.parser.parse_as_lines(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1000)
        self.assertLess(parse_time, 1.0, f"Line parsing took too long: {parse_time:.2f}s")


class TestPlainTextCompatibility(unittest.TestCase):
    """Test compatibility with style analysis system."""

    def setUp(self):
        self.parser = PlainTextParser()

    def test_skip_analysis_flags(self):
        """Test that appropriate blocks are flagged to skip analysis."""
        content = """Normal paragraph for analysis.

Another paragraph for analysis."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # All paragraph blocks should NOT skip analysis
        for block in result.document.blocks:
            if block.block_type == PlainTextBlockType.PARAGRAPH:
                self.assertFalse(block.should_skip_analysis())

    def test_text_content_extraction(self):
        """Test text content extraction for analysis."""
        content = """This is a test paragraph.

Another paragraph with   extra   spaces."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Test text extraction
        for block in result.document.blocks:
            text_content = block.get_text_content()
            self.assertIsInstance(text_content, str)
            self.assertGreater(len(text_content.strip()), 0)

    def test_context_info_generation(self):
        """Test context info generation for rules."""
        content = """Paragraph 1.

Paragraph 2."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Test context info for blocks
        for block in result.document.blocks:
            context = block.get_context_info()
            
            self.assertIn('block_type', context)
            self.assertIn('level', context)
            self.assertIn('contains_inline_formatting', context)
            
            # Verify values
            self.assertEqual(context['block_type'], block.block_type.value)
            self.assertIsInstance(context['level'], int)
            self.assertFalse(context['contains_inline_formatting'])  # Plain text has no formatting

    def test_inline_formatting_detection(self):
        """Test inline formatting detection (should always be False for plain text)."""
        content = """Text with *asterisks* and _underscores_.

Text with **double** and __double__ formatting."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Plain text should never have inline formatting detected
        for block in result.document.blocks:
            self.assertFalse(block.has_inline_formatting())

    def test_serialization_to_dict(self):
        """Test serialization to dictionary."""
        content = """Test paragraph."""
        
        result = self.parser.parse(content)
        self.assertTrue(result.success)
        
        # Test serialization
        for block in result.document.blocks:
            block_dict = block.to_dict()
            
            # Required fields
            required_fields = ['block_type', 'content', 'level', 
                             'should_skip_analysis', 'errors', 'children']
            for field in required_fields:
                self.assertIn(field, block_dict)
            
            # Verify data types
            self.assertIsInstance(block_dict['block_type'], str)
            self.assertIsInstance(block_dict['content'], str)
            self.assertIsInstance(block_dict['level'], int)
            self.assertIsInstance(block_dict['should_skip_analysis'], bool)
            self.assertIsInstance(block_dict['errors'], list)
            self.assertIsInstance(block_dict['children'], list)


class TestPlainTextPerformance(unittest.TestCase):
    """Performance tests for plain text parser."""

    def setUp(self):
        self.parser = PlainTextParser()

    def test_large_document_performance(self):
        """Test performance with large documents."""
        import time
        
        # Create a large document
        large_content = []
        for i in range(1000):
            large_content.append(f"Paragraph {i} with some content.")
            large_content.append("")  # Add blank line separator
        
        content = "\n".join(large_content)
        
        # Measure parse time
        start_time = time.time()
        result = self.parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # Should parse successfully
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 900)
        
        # Performance assertion (should parse quickly)
        self.assertLess(parse_time, 1.0, 
                       f"Parsing took too long: {parse_time:.2f}s")
        
        print(f"Large document ({len(content)} chars) parsed in {parse_time:.3f}s")

    def test_very_long_paragraph_performance(self):
        """Test performance with very long single paragraph."""
        import time
        
        # Create a very long paragraph
        long_content = "This is a very long paragraph. " * 10000
        
        start_time = time.time()
        result = self.parser.parse(long_content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 1)
        self.assertLess(parse_time, 1.0, 
                       f"Long paragraph parsing took too long: {parse_time:.2f}s")

    def test_many_paragraphs_performance(self):
        """Test performance with many small paragraphs."""
        import time
        
        # Create many small paragraphs
        paragraphs = []
        for i in range(5000):
            paragraphs.append(f"Para {i}.")
            paragraphs.append("")
        
        content = "\n".join(paragraphs)
        
        start_time = time.time()
        result = self.parser.parse(content)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.document.blocks), 4000)
        self.assertLess(parse_time, 2.0, 
                       f"Many paragraphs parsing took too long: {parse_time:.2f}s")


class TestPlainTextParserInfo(unittest.TestCase):
    """Test parser information and metadata."""

    def setUp(self):
        self.parser = PlainTextParser()

    def test_parser_info(self):
        """Test parser information retrieval."""
        info = self.parser.get_parsing_info()
        
        self.assertIsInstance(info, dict)
        self.assertIn('parser_type', info)
        self.assertIn('default_mode', info)
        self.assertIn('available_modes', info)
        self.assertIn('description', info)
        
        self.assertEqual(info['parser_type'], 'plain_text')
        self.assertIn('paragraph_based', info['available_modes'])
        self.assertIn('line_based', info['available_modes'])


if __name__ == '__main__':
    unittest.main()
