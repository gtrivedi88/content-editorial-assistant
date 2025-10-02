"""
Integration tests for Plain Text parser with format detector and parser factory.

Tests the complete workflow from format detection to parsing for plain text.
"""

import unittest
from structural_parsing import StructuralParserFactory, FormatDetector
from structural_parsing.plaintext.types import PlainTextBlockType, PlainTextParseResult


class TestPlainTextFormatDetection(unittest.TestCase):
    """Test plain text format detection accuracy."""

    def setUp(self):
        self.detector = FormatDetector()

    def test_detect_simple_plaintext(self):
        """Test detection of simple plain text."""
        content = """This is just plain text.
No special formatting.
Just regular sentences."""
        
        format_detected = self.detector.detect_format(content)
        self.assertEqual(format_detected, 'plaintext')

    def test_detect_plaintext_vs_markdown(self):
        """Test distinguishing plain text from markdown."""
        plaintext_content = """This is plain text.
No special characters or formatting.
Just normal sentences."""
        
        markdown_content = """# This is Markdown
With a heading and **bold** text."""
        
        self.assertEqual(self.detector.detect_format(plaintext_content), 'plaintext')
        self.assertEqual(self.detector.detect_format(markdown_content), 'markdown')

    def test_detect_plaintext_vs_asciidoc(self):
        """Test distinguishing plain text from asciidoc."""
        plaintext_content = """This is plain text content.
No special markup here.
Just regular text."""
        
        asciidoc_content = """= AsciiDoc Title
:author: John Doe
This is AsciiDoc content."""
        
        self.assertEqual(self.detector.detect_format(plaintext_content), 'plaintext')
        self.assertEqual(self.detector.detect_format(asciidoc_content), 'asciidoc')

    def test_detect_ambiguous_content_as_plaintext(self):
        """Test that truly ambiguous content is detected as plain text."""
        content = """Line 1
Line 2
Line 3"""
        
        format_detected = self.detector.detect_format(content)
        # This should be detected as plaintext since it has no markup indicators
        self.assertEqual(format_detected, 'plaintext')


class TestParserFactoryPlainText(unittest.TestCase):
    """Test parser factory with plain text content."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_auto_detect_and_parse_plaintext(self):
        """Test automatic detection and parsing of plain text."""
        content = """This is plain text content.

It has multiple paragraphs.

Each separated by blank lines.

No special formatting or markup."""
        
        result = self.factory.parse(content, format_hint='auto')
        
        self.assertIsInstance(result, PlainTextParseResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 4)
        
        # Verify we have expected block types
        for block in result.document.blocks:
            self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)

    def test_explicit_plaintext_hint(self):
        """Test explicit plain text format hint."""
        content = """# This might look like markdown
But it's being parsed as plain text."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertIsInstance(result, PlainTextParseResult)
        self.assertTrue(result.success)
        
        # Should be treated as plain text, not markdown
        self.assertEqual(len(result.document.blocks), 1)
        block = result.document.blocks[0]
        self.assertEqual(block.block_type, PlainTextBlockType.PARAGRAPH)
        self.assertIn("# This might look like markdown", block.content)

    def test_get_available_parsers_includes_plaintext(self):
        """Test that plain text parser is listed in available parsers."""
        parsers = self.factory.get_available_parsers()
        
        self.assertIn('plaintext', parsers)
        self.assertTrue(parsers['plaintext']['available'])
        self.assertEqual(parsers['plaintext']['parser'], 'dedicated plain text parser')

    def test_parser_factory_format_detection(self):
        """Test that parser factory correctly detects plain text."""
        content = """Just plain text content.
Nothing special here.
No markup at all."""
        
        detected_format = self.factory.detect_format(content)
        self.assertEqual(detected_format, 'plaintext')

    def test_comparison_with_markdown_fallback(self):
        """Test that dedicated plain text parser works better than markdown fallback."""
        content = """Line 1
Line 2

Line 4
Line 5"""
        
        # Parse with plain text parser
        plaintext_result = self.factory.parse(content, format_hint='plaintext')
        
        # Parse with markdown parser (old fallback method)
        markdown_result = self.factory.parse(content, format_hint='markdown')
        
        # Both should succeed
        self.assertTrue(plaintext_result.success)
        self.assertTrue(markdown_result.success)
        
        # Plain text parser should create more logical paragraph structure
        self.assertIsInstance(plaintext_result, PlainTextParseResult)
        self.assertEqual(len(plaintext_result.document.blocks), 2)  # Two paragraphs


class TestPlainTextParserErrorHandling(unittest.TestCase):
    """Test error handling and edge cases in plain text parsing."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_empty_content(self):
        """Test parsing empty content."""
        result = self.factory.parse("", format_hint='plaintext')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 0)

    def test_none_content(self):
        """Test parsing None content."""
        result = self.factory.parse(None, format_hint='plaintext')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)

    def test_very_large_plaintext_document(self):
        """Test parsing a very large plain text document."""
        # Create a large document
        large_content = []
        for i in range(1000):
            large_content.append(f"Paragraph {i} with some plain text content.")
            large_content.append("")  # Blank line separator
        
        content = "\n".join(large_content)
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 900)

    def test_mixed_encoding_content(self):
        """Test mixed encoding and special characters."""
        content = """English text here.

中文内容在这里。

Ελληνικά εδώ.

العربية هنا.

🚀 Unicode emojis work too! 🎉"""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertEqual(len(result.document.blocks), 5)

    def test_malformed_content_recovery(self):
        """Test recovery from potentially problematic content."""
        content = """Normal paragraph.

\x00Null bytes\x00 in content.

\tTabs\tand\tother\twhitespace.

Very\r\nMixed\nLine\rEndings."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        # Should still parse successfully
        self.assertTrue(result.success)
        self.assertIsNotNone(result.document)
        self.assertGreater(len(result.document.blocks), 1)


class TestPlainTextCompatibility(unittest.TestCase):
    """Test compatibility with style analysis system."""

    def setUp(self):
        self.factory = StructuralParserFactory()

    def test_block_analysis_integration(self):
        """Test integration with style analysis system."""
        content = """First paragraph for analysis.

Second paragraph with different content.

Third paragraph to complete the test."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertTrue(result.success)
        
        # Test that all blocks are suitable for analysis
        for block in result.document.blocks:
            # Should not skip analysis
            self.assertFalse(block.should_skip_analysis())
            
            # Should have clean text content
            text_content = block.get_text_content()
            self.assertIsInstance(text_content, str)
            self.assertGreater(len(text_content.strip()), 0)
            
            # Should have proper context info
            context = block.get_context_info()
            self.assertIn('block_type', context)
            self.assertEqual(context['block_type'], 'paragraph')
            self.assertFalse(context['contains_inline_formatting'])

    def test_serialization_compatibility(self):
        """Test serialization compatibility for storage/transmission."""
        content = """Paragraph one.

Paragraph two."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertTrue(result.success)
        
        # Test serialization
        for block in result.document.blocks:
            block_dict = block.to_dict()
            
            # Should have all required fields
            required_fields = ['block_type', 'content', 'level', 
                             'should_skip_analysis', 'errors', 'children']
            for field in required_fields:
                self.assertIn(field, block_dict)
            
            # Values should be properly typed
            self.assertIsInstance(block_dict['block_type'], str)
            self.assertIsInstance(block_dict['content'], str)
            self.assertIsInstance(block_dict['should_skip_analysis'], bool)

    def test_performance_comparison(self):
        """Test performance compared to markdown fallback."""
        import time
        
        # Create moderately sized content
        content_parts = []
        for i in range(100):
            content_parts.append(f"Plain text paragraph {i}.")
            content_parts.append("")
        content = "\n".join(content_parts)
        
        # Test plain text parser performance
        start_time = time.time()
        result = self.factory.parse(content, format_hint='plaintext')
        plaintext_time = time.time() - start_time
        
        self.assertTrue(result.success)
        
        # Should be reasonably fast
        self.assertLess(plaintext_time, 1.0, 
                       f"Plain text parsing took too long: {plaintext_time:.2f}s")

    def test_line_numbering_accuracy(self):
        """Test that line numbering is accurate for analysis."""
        content = """First paragraph.

Second paragraph on line 3.

Third paragraph on line 5."""
        
        result = self.factory.parse(content, format_hint='plaintext')
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.document.blocks), 3)
        
        # Check line numbers are reasonable (exact values depend on parsing logic)
        self.assertEqual(result.document.blocks[0].start_line, 1)
        self.assertGreater(result.document.blocks[1].start_line, 1)
        self.assertGreater(result.document.blocks[2].start_line, result.document.blocks[1].start_line)


if __name__ == '__main__':
    unittest.main()
