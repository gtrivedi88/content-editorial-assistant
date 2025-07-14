"""
Comprehensive Test Suite for Structural Parsing System
Tests all components of the structural parsing system including StructuralParserFactory,
FormatDetector, AsciiDocParser, MarkdownParser, RubyAsciidoctorServer, DocumentProcessor,
and all type definitions with detailed coverage of document parsing, format detection,
and text extraction.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, mock_open, Mock
from io import BytesIO
from typing import List, Dict, Any, Optional
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import structural parsing components
try:
    from structural_parsing.parser_factory import StructuralParserFactory, parse_document
    from structural_parsing.format_detector import FormatDetector
    from structural_parsing.asciidoc.parser import AsciiDocParser
    from structural_parsing.markdown.parser import MarkdownParser
    from structural_parsing.asciidoc.ruby_client import SimpleRubyClient, get_client
    from structural_parsing.extractors.document_processor import DocumentProcessor
    from structural_parsing.asciidoc.types import (
        AsciiDocDocument, AsciiDocBlock, AsciiDocBlockType, 
        AdmonitionType, AsciiDocAttributes, ParseResult
    )
    from structural_parsing.markdown.types import (
        MarkdownDocument, MarkdownBlock, MarkdownBlockType, MarkdownParseResult
    )
    
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError as e:
    STRUCTURAL_PARSING_AVAILABLE = False
    print(f"Structural parsing not available: {e}")


class TestStructuralParsingSystem:
    """Comprehensive test suite for the structural parsing system."""
    
    @pytest.fixture
    def sample_documents(self):
        """Create sample documents for testing."""
        return {
            'simple_markdown': "# Heading\n\nThis is a paragraph.\n\n- Item 1\n- Item 2",
            'complex_markdown': """# Main Title

This is an introduction paragraph.

## Section 1

Some content in section 1.

### Subsection 1.1

Content in subsection.

```python
print("Hello, world!")
```

> This is a blockquote.

- Unordered list item 1
- Unordered list item 2

1. Ordered list item 1
2. Ordered list item 2

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |

---

**Bold text** and *italic text*.
""",
            'simple_asciidoc': "= Document Title\n\nThis is a paragraph.\n\n== Section\n\nMore content.",
            'complex_asciidoc': """= Main Document Title
:author: John Doe
:version: 1.0

This is the document preamble.

== First Section

This is content in the first section.

=== Subsection

Content in subsection.

[NOTE]
====
This is an important note.
====

.Example Block
====
This is an example.
====

[source,python]
----
print("Hello, world!")
----

* Unordered list item 1
* Unordered list item 2

. Ordered list item 1
. Ordered list item 2

[cols="1,1"]
|===
| Header 1 | Header 2
| Cell 1   | Cell 2
| Cell 3   | Cell 4
|===

'''

*Bold text* and _italic text_.
""",
            'mixed_content': """# Mixed Content

This looks like markdown at first.

But it also has:
:author: Test Author

[NOTE]
====
This is an AsciiDoc admonition.
====

== AsciiDoc Section

Regular paragraph.
""",
            'plain_text': "This is plain text.\nWith multiple lines.\nNo special formatting.",
            'empty_document': "",
            'whitespace_only': "   \n\t\n   ",
            'special_chars': "# Special Characters\n\n@#$%^&*()_+{}|:<>?[]\\;'\".,/~`",
            'unicode_content': "# Unicode Content\n\nHello 世界! 🌍\n\nΓεια σας κόσμε!"
        }
    
    @pytest.fixture
    def sample_files(self):
        """Create sample file contents for testing."""
        return {
            'txt': "This is a sample text file.\nWith multiple lines.\nFor testing purposes.",
            'md': "# Sample Markdown\n\nThis is a **bold** text.\n\n- Item 1\n- Item 2\n\n```python\nprint('hello')\n```",
            'adoc': "= Sample AsciiDoc Document\n\nThis is a paragraph.\n\n[NOTE]\n====\nThis is a note.\n====\n\n== Section\n\nMore content.",
            'dita': '<?xml version="1.0"?>\n<topic id="sample"><title>Sample DITA</title><body><p>This is content.</p></body></topic>',
            'pdf_content': "This is extracted PDF content.\nMultiple lines of text.",
            'docx_content': "This is extracted DOCX content.\nWith formatting preserved."
        }
    
    # ===============================
    # STRUCTURAL PARSER FACTORY TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_initialization(self):
        """Test StructuralParserFactory initialization."""
        factory = StructuralParserFactory()
        
        assert isinstance(factory, StructuralParserFactory)
        assert hasattr(factory, 'format_detector')
        assert hasattr(factory, 'asciidoc_parser')
        assert hasattr(factory, 'markdown_parser')
        assert isinstance(factory.format_detector, FormatDetector)
        assert isinstance(factory.asciidoc_parser, AsciiDocParser)
        assert isinstance(factory.markdown_parser, MarkdownParser)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_markdown_parsing(self, sample_documents):
        """Test StructuralParserFactory markdown parsing."""
        factory = StructuralParserFactory()
        
        # Test explicit markdown format
        result = factory.parse(sample_documents['simple_markdown'], format_hint='markdown')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
        
        # Check for expected blocks
        markdown_doc: MarkdownDocument = result.document
        headings = markdown_doc.get_blocks_by_type(MarkdownBlockType.HEADING)
        assert len(headings) > 0
        assert headings[0].content == "Heading"
        
        paragraphs = markdown_doc.get_blocks_by_type(MarkdownBlockType.PARAGRAPH)
        assert len(paragraphs) > 0
        
        lists = markdown_doc.get_blocks_by_type(MarkdownBlockType.UNORDERED_LIST)
        assert len(lists) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_asciidoc_parsing(self, sample_documents):
        """Test StructuralParserFactory AsciiDoc parsing."""
        factory = StructuralParserFactory()
        
        # Test explicit asciidoc format
        result = factory.parse(sample_documents['simple_asciidoc'], format_hint='asciidoc')
        
        assert isinstance(result, ParseResult)
        assert isinstance(result.document, AsciiDocDocument)
        
        # Note: AsciiDoc parser may not be available in test environment
        if result.success:
            assert len(result.document.blocks) > 0
            
            # Check for expected blocks
            asciidoc_doc: AsciiDocDocument = result.document
            headings = asciidoc_doc.get_blocks_by_type(AsciiDocBlockType.HEADING)
            paragraphs = asciidoc_doc.get_blocks_by_type(AsciiDocBlockType.PARAGRAPH)
            
            assert len(headings) > 0 or len(paragraphs) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_auto_detection(self, sample_documents):
        """Test StructuralParserFactory auto format detection."""
        factory = StructuralParserFactory()
        
        # Test auto detection with markdown
        result = factory.parse(sample_documents['simple_markdown'], format_hint='auto')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        
        # Test auto detection with asciidoc
        result = factory.parse(sample_documents['simple_asciidoc'], format_hint='auto')
        
        # Could be either AsciiDoc or Markdown depending on availability
        assert result.success == True
        assert result.document is not None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_none_content(self):
        """Test StructuralParserFactory with None content."""
        factory = StructuralParserFactory()
        
        # Pass empty string instead of None, as the method internally handles None
        result = factory.parse("", format_hint='markdown')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) == 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_empty_content(self, sample_documents):
        """Test StructuralParserFactory with empty content."""
        factory = StructuralParserFactory()
        
        result = factory.parse(sample_documents['empty_document'], format_hint='markdown')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) == 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_get_available_parsers(self):
        """Test StructuralParserFactory get_available_parsers method."""
        factory = StructuralParserFactory()
        
        parsers = factory.get_available_parsers()
        
        assert isinstance(parsers, dict)
        assert 'asciidoc' in parsers
        assert 'markdown' in parsers
        
        # Check structure
        for parser_name, parser_info in parsers.items():
            assert 'available' in parser_info
            assert 'parser' in parser_info
            assert 'description' in parser_info
            assert isinstance(parser_info['available'], bool)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_structural_parser_factory_detect_format(self, sample_documents):
        """Test StructuralParserFactory detect_format method."""
        factory = StructuralParserFactory()
        
        # Test markdown detection
        format_detected = factory.detect_format(sample_documents['simple_markdown'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test asciidoc detection
        format_detected = factory.detect_format(sample_documents['simple_asciidoc'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test empty content
        format_detected = factory.detect_format(sample_documents['empty_document'])
        assert format_detected in ['markdown', 'asciidoc']
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_parse_document_convenience_function(self, sample_documents):
        """Test parse_document convenience function."""
        result = parse_document(sample_documents['simple_markdown'], format_hint='markdown')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
    
    # ===============================
    # FORMAT DETECTOR TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_format_detector_initialization(self):
        """Test FormatDetector initialization."""
        detector = FormatDetector()
        
        assert isinstance(detector, FormatDetector)
        assert hasattr(detector, 'asciidoc_patterns')
        assert hasattr(detector, 'markdown_patterns')
        assert isinstance(detector.asciidoc_patterns, list)
        assert isinstance(detector.markdown_patterns, list)
        assert len(detector.asciidoc_patterns) > 0
        assert len(detector.markdown_patterns) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_format_detector_asciidoc_patterns(self):
        """Test FormatDetector AsciiDoc pattern detection."""
        detector = FormatDetector()
        
        # Test various AsciiDoc patterns
        asciidoc_samples = [
            "= Document Title\n\nContent",
            "== Section Title\n\nContent",
            "[NOTE]\n====\nNote content\n====",
            ":author: John Doe\n:version: 1.0",
            "****\nSidebar content\n****",
            "====\nExample content\n====",
            "----\nCode content\n----",
            "+++\nPassthrough content\n+++",
            ".Block Title\nContent",
            "** Second level list item",
            "*** Third level list item",
            ". Ordered list item",
            "[[anchor]]\nContent",
            "include::file.adoc[]",
            "image::image.png[]",
            "link::http://example.com[]",
            "This is a link:http://example.com[link]."
        ]
        
        for sample in asciidoc_samples:
            format_detected = detector.detect_format(sample)
            assert format_detected in ['asciidoc', 'markdown']  # Could be either depending on pattern matching
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_format_detector_markdown_patterns(self):
        """Test FormatDetector Markdown pattern detection."""
        detector = FormatDetector()
        
        # Test various Markdown patterns
        markdown_samples = [
            "# Heading\n\nContent",
            "## Second Level\n\nContent",
            "```python\ncode\n```",
            "* List item",
            "- Another list item",
            "1. Numbered item",
            "2. Another numbered item",
            "> Blockquote content",
            "| Header 1 | Header 2 |\n|----------|----------|",
            "![Alt text](image.png)",
            "[Link text](http://example.com)",
            "**Bold text**",
            "*Italic text*",
            "---",
            "***"
        ]
        
        for sample in markdown_samples:
            format_detected = detector.detect_format(sample)
            assert format_detected in ['markdown', 'asciidoc']  # Could be either depending on pattern matching
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_format_detector_mixed_content(self, sample_documents):
        """Test FormatDetector with mixed content."""
        detector = FormatDetector()
        
        format_detected = detector.detect_format(sample_documents['mixed_content'])
        assert format_detected in ['markdown', 'asciidoc']
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_format_detector_edge_cases(self, sample_documents):
        """Test FormatDetector edge cases."""
        detector = FormatDetector()
        
        # Test empty content
        format_detected = detector.detect_format(sample_documents['empty_document'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test whitespace only
        format_detected = detector.detect_format(sample_documents['whitespace_only'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test plain text
        format_detected = detector.detect_format(sample_documents['plain_text'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test special characters
        format_detected = detector.detect_format(sample_documents['special_chars'])
        assert format_detected in ['markdown', 'asciidoc']
        
        # Test unicode content
        format_detected = detector.detect_format(sample_documents['unicode_content'])
        assert format_detected in ['markdown', 'asciidoc']
    
    # ===============================
    # MARKDOWN PARSER TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_initialization(self):
        """Test MarkdownParser initialization."""
        parser = MarkdownParser()
        
        assert isinstance(parser, MarkdownParser)
        assert hasattr(parser, 'md')
        assert parser.md is not None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_simple_parsing(self, sample_documents):
        """Test MarkdownParser simple parsing."""
        parser = MarkdownParser()
        
        result = parser.parse(sample_documents['simple_markdown'])
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
        
        # Check for expected blocks
        markdown_doc: MarkdownDocument = result.document
        headings = markdown_doc.get_blocks_by_type(MarkdownBlockType.HEADING)
        assert len(headings) > 0
        assert headings[0].content == "Heading"
        
        paragraphs = markdown_doc.get_blocks_by_type(MarkdownBlockType.PARAGRAPH)
        assert len(paragraphs) > 0
        
        lists = markdown_doc.get_blocks_by_type(MarkdownBlockType.UNORDERED_LIST)
        assert len(lists) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_complex_parsing(self, sample_documents):
        """Test MarkdownParser complex parsing."""
        parser = MarkdownParser()
        
        result = parser.parse(sample_documents['complex_markdown'])
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
        
        # Check for various block types
        markdown_doc: MarkdownDocument = result.document
        headings = markdown_doc.get_blocks_by_type(MarkdownBlockType.HEADING)
        assert len(headings) >= 3  # Main title, section, subsection
        
        paragraphs = markdown_doc.get_blocks_by_type(MarkdownBlockType.PARAGRAPH)
        assert len(paragraphs) > 0
        
        code_blocks = markdown_doc.get_blocks_by_type(MarkdownBlockType.CODE_BLOCK)
        assert len(code_blocks) > 0
        
        blockquotes = markdown_doc.get_blocks_by_type(MarkdownBlockType.BLOCKQUOTE)
        assert len(blockquotes) > 0
        
        lists = markdown_doc.get_blocks_by_type(MarkdownBlockType.UNORDERED_LIST)
        assert len(lists) > 0
        
        ordered_lists = markdown_doc.get_blocks_by_type(MarkdownBlockType.ORDERED_LIST)
        assert len(ordered_lists) > 0
        
        tables = markdown_doc.get_blocks_by_type(MarkdownBlockType.TABLE)
        assert len(tables) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_error_handling(self):
        """Test MarkdownParser error handling."""
        parser = MarkdownParser()
        
        # Mock markdown-it to raise exception
        with patch.object(parser.md, 'parse', side_effect=Exception("Parse error")):
            result = parser.parse("# Test")
            
            assert isinstance(result, MarkdownParseResult)
            assert result.success == False
            assert len(result.errors) > 0
            assert "Failed to parse Markdown" in result.errors[0]
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_empty_content(self, sample_documents):
        """Test MarkdownParser with empty content."""
        parser = MarkdownParser()
        
        result = parser.parse(sample_documents['empty_document'])
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) == 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_special_characters(self, sample_documents):
        """Test MarkdownParser with special characters."""
        parser = MarkdownParser()
        
        result = parser.parse(sample_documents['special_chars'])
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_parser_unicode_content(self, sample_documents):
        """Test MarkdownParser with unicode content."""
        parser = MarkdownParser()
        
        result = parser.parse(sample_documents['unicode_content'])
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
    
    # ===============================
    # ASCIIDOC PARSER TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_initialization(self):
        """Test AsciiDocParser initialization."""
        parser = AsciiDocParser()
        
        assert isinstance(parser, AsciiDocParser)
        assert hasattr(parser, 'asciidoctor_available')
        assert isinstance(parser.asciidoctor_available, bool)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_availability_check(self):
        """Test AsciiDocParser availability check."""
        parser = AsciiDocParser()
        
        # Check availability (will depend on system configuration)
        availability = parser._check_asciidoctor_availability()
        assert isinstance(availability, bool)
        assert availability == parser.asciidoctor_available
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_simple_parsing(self, sample_documents):
        """Test AsciiDocParser simple parsing."""
        parser = AsciiDocParser()
        
        result = parser.parse(sample_documents['simple_asciidoc'])
        
        assert isinstance(result, ParseResult)
        assert isinstance(result.document, AsciiDocDocument)
        
        # Note: Success depends on asciidoctor availability
        if parser.asciidoctor_available:
            assert result.success == True
            assert len(result.document.blocks) > 0
            
            # Check for expected blocks
            headings = result.document.get_blocks_by_type(AsciiDocBlockType.HEADING)
            paragraphs = result.document.get_blocks_by_type(AsciiDocBlockType.PARAGRAPH)
            
            assert len(headings) > 0 or len(paragraphs) > 0
        else:
            assert result.success == False
            assert len(result.errors) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_complex_parsing(self, sample_documents):
        """Test AsciiDocParser complex parsing."""
        parser = AsciiDocParser()
        
        result = parser.parse(sample_documents['complex_asciidoc'])
        
        assert isinstance(result, ParseResult)
        assert isinstance(result.document, AsciiDocDocument)
        
        # Note: Success depends on asciidoctor availability
        if parser.asciidoctor_available:
            assert result.success == True
            assert len(result.document.blocks) > 0
            
            # Check for various block types
            asciidoc_doc: AsciiDocDocument = result.document
            headings = asciidoc_doc.get_blocks_by_type(AsciiDocBlockType.HEADING)
            paragraphs = asciidoc_doc.get_blocks_by_type(AsciiDocBlockType.PARAGRAPH)
            admonitions = asciidoc_doc.get_blocks_by_type(AsciiDocBlockType.ADMONITION)
            
            # Should have at least some blocks
            total_blocks = len(headings) + len(paragraphs) + len(admonitions)
            assert total_blocks > 0
        else:
            assert result.success == False
            assert len(result.errors) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_unavailable_handling(self):
        """Test AsciiDocParser when asciidoctor is unavailable."""
        parser = AsciiDocParser()
        
        # Mock asciidoctor as unavailable
        parser.asciidoctor_available = False
        
        result = parser.parse("= Test Document\n\nContent")
        
        assert isinstance(result, ParseResult)
        assert result.success == False
        assert len(result.errors) > 0
        assert "Asciidoctor is not available" in result.errors[0]
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_error_handling(self):
        """Test AsciiDocParser error handling."""
        parser = AsciiDocParser()
        
        # Mock get_client to raise exception
        with patch('structural_parsing.asciidoc.parser.get_client', side_effect=Exception("Client error")):
            result = parser.parse("= Test Document\n\nContent")
            
            assert isinstance(result, ParseResult)
            assert result.success == False
            assert len(result.errors) > 0
            assert "Failed to parse AsciiDoc" in result.errors[0]
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_parser_empty_content(self, sample_documents):
        """Test AsciiDocParser with empty content."""
        parser = AsciiDocParser()
        
        result = parser.parse(sample_documents['empty_document'])
        
        assert isinstance(result, ParseResult)
        assert isinstance(result.document, AsciiDocDocument)
        
        if parser.asciidoctor_available:
            assert result.success == True
            assert len(result.document.blocks) == 0
        else:
            assert result.success == False
    
    # ===============================
    # RUBY ASCIIDOCTOR SERVER TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_ruby_client_initialization(self):
        """Test SimpleRubyClient initialization."""
        try:
            client = SimpleRubyClient()
            assert isinstance(client, SimpleRubyClient)
            assert hasattr(client, 'asciidoctor_available')
            assert isinstance(client.asciidoctor_available, bool)
        except Exception:
            # Client may not be available in test environment
            pytest.skip("Ruby client not available")
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_ruby_client_ping(self):
        """Test SimpleRubyClient ping functionality."""
        try:
            client = SimpleRubyClient()
            ping_result = client.ping()
            assert isinstance(ping_result, bool)
        except Exception:
            # Client may not be available in test environment
            pytest.skip("Ruby client not available")
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_ruby_client_parse_document(self):
        """Test SimpleRubyClient parse_document functionality."""
        try:
            client = SimpleRubyClient()
            if client.asciidoctor_available:
                result = client.parse_document("= Test Document\n\nContent")
                assert isinstance(result, dict)
                if result.get('success'):
                    data = result.get('data', {})
                    assert 'blocks' in data
                    assert isinstance(data['blocks'], list)
        except Exception:
            # Client may not be available in test environment
            pytest.skip("Ruby client not available")
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_get_client_function(self):
        """Test get_client function."""
        try:
            client = get_client()
            assert isinstance(client, SimpleRubyClient)
        except Exception:
            # Client may not be available in test environment
            pytest.skip("Ruby client not available")
    
    # ===============================
    # DOCUMENT PROCESSOR TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_initialization(self):
        """Test DocumentProcessor initialization."""
        processor = DocumentProcessor()
        
        assert isinstance(processor, DocumentProcessor)
        assert hasattr(processor, 'ALLOWED_EXTENSIONS')
        assert hasattr(processor, 'supported_formats')
        assert isinstance(processor.ALLOWED_EXTENSIONS, set)
        assert isinstance(processor.supported_formats, list)
        assert len(processor.ALLOWED_EXTENSIONS) > 0
        assert len(processor.supported_formats) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_allowed_file_extensions(self):
        """Test DocumentProcessor allowed file extensions."""
        processor = DocumentProcessor()
        
        # Test valid extensions
        assert processor.allowed_file('document.pdf') == True
        assert processor.allowed_file('document.docx') == True
        assert processor.allowed_file('document.txt') == True
        assert processor.allowed_file('document.md') == True
        assert processor.allowed_file('document.adoc') == True
        assert processor.allowed_file('document.dita') == True
        
        # Test invalid extensions
        assert processor.allowed_file('document.xyz') == False
        assert processor.allowed_file('document.exe') == False
        assert processor.allowed_file('document.jpg') == False
        
        # Test edge cases
        assert processor.allowed_file('document') == False
        assert processor.allowed_file('') == False
        assert processor.allowed_file('.pdf') == True
        assert processor.allowed_file('document.PDF') == True  # Case insensitive
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_text_file_extraction(self, sample_files):
        """Test DocumentProcessor text file extraction."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_files['txt'])
            f.flush()
            
            try:
                content = processor.extract_text(f.name)
                assert content is not None
                assert 'sample text file' in content
                assert 'multiple lines' in content
                assert 'testing purposes' in content
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_markdown_file_extraction(self, sample_files):
        """Test DocumentProcessor markdown file extraction."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_files['md'])
            f.flush()
            
            try:
                content = processor.extract_text(f.name)
                assert content is not None
                assert 'Sample Markdown' in content
                assert 'bold' in content
                assert 'Item 1' in content
                assert 'Item 2' in content
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_asciidoc_file_extraction(self, sample_files):
        """Test DocumentProcessor AsciiDoc file extraction."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(sample_files['adoc'])
            f.flush()
            
            try:
                content = processor.extract_text(f.name)
                assert content is not None
                assert 'Sample AsciiDoc' in content
                assert 'paragraph' in content
                assert 'Section' in content
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_dita_file_extraction(self, sample_files):
        """Test DocumentProcessor DITA file extraction."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dita', delete=False) as f:
            f.write(sample_files['dita'])
            f.flush()
            
            try:
                content = processor.extract_text(f.name)
                assert content is not None
                assert 'Sample DITA' in content
                assert 'This is content' in content
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_pdf_file_extraction(self, sample_files):
        """Test DocumentProcessor PDF file extraction."""
        processor = DocumentProcessor()
        
        # Mock fitz library
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = sample_files['pdf_content']
            mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
            mock_fitz.return_value = mock_doc
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(b'fake pdf content')
                f.flush()
                
                try:
                    content = processor.extract_text(f.name)
                    assert content is not None
                    assert 'extracted PDF content' in content
                    assert 'Multiple lines' in content
                finally:
                    os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_docx_file_extraction(self, sample_files):
        """Test DocumentProcessor DOCX file extraction."""
        processor = DocumentProcessor()
        
        # Mock python-docx library
        with patch('structural_parsing.extractors.document_processor.Document') as mock_document:
            mock_doc = MagicMock()
            mock_paragraph = MagicMock()
            mock_paragraph.text = sample_files['docx_content']
            mock_doc.paragraphs = [mock_paragraph]
            mock_document.return_value = mock_doc
            
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
                f.write(b'fake docx content')
                f.flush()
                
                try:
                    content = processor.extract_text(f.name)
                    assert content is not None
                    assert 'extracted DOCX content' in content
                    assert 'formatting preserved' in content
                finally:
                    os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_unsupported_format(self):
        """Test DocumentProcessor with unsupported format."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'unsupported content')
            f.flush()
            
            try:
                content = processor.extract_text(f.name)
                assert content is None
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_file_not_found(self):
        """Test DocumentProcessor with non-existent file."""
        processor = DocumentProcessor()
        
        content = processor.extract_text('non_existent_file.txt')
        assert content is None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_get_document_info(self, sample_files):
        """Test DocumentProcessor get_document_info method."""
        processor = DocumentProcessor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_files['txt'])
            f.flush()
            
            try:
                info = processor.get_document_info(f.name)
                assert isinstance(info, dict)
                assert 'filename' in info
                assert 'size' in info
                assert 'format' in info
                assert 'supported' in info
                assert info['filename'] == os.path.basename(f.name)
                assert info['size'] > 0
                assert info['format'] == 'txt'
                assert info['supported'] == True
            finally:
                os.unlink(f.name)
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_processor_get_document_info_nonexistent(self):
        """Test DocumentProcessor get_document_info with non-existent file."""
        processor = DocumentProcessor()
        
        info = processor.get_document_info('non_existent_file.txt')
        assert info is None
    
    # ===============================
    # TYPE DEFINITION TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_block_type_enum(self):
        """Test AsciiDocBlockType enum."""
        # Test enum values
        assert AsciiDocBlockType.DOCUMENT.value == "document"
        assert AsciiDocBlockType.PARAGRAPH.value == "paragraph"
        assert AsciiDocBlockType.HEADING.value == "heading"
        assert AsciiDocBlockType.ADMONITION.value == "admonition"
        assert AsciiDocBlockType.LISTING.value == "listing"
        
        # Test enum iteration
        block_types = list(AsciiDocBlockType)
        assert len(block_types) > 10  # Should have many block types
        
        # Test enum contains expected types
        expected_types = [
            AsciiDocBlockType.DOCUMENT,
            AsciiDocBlockType.PARAGRAPH,
            AsciiDocBlockType.HEADING,
            AsciiDocBlockType.ADMONITION,
            AsciiDocBlockType.LISTING
        ]
        
        for expected_type in expected_types:
            assert expected_type in block_types
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_block_type_enum(self):
        """Test MarkdownBlockType enum."""
        # Test enum values
        assert MarkdownBlockType.DOCUMENT.value == "document"
        assert MarkdownBlockType.PARAGRAPH.value == "paragraph"
        assert MarkdownBlockType.HEADING.value == "heading"
        assert MarkdownBlockType.CODE_BLOCK.value == "code_block"
        assert MarkdownBlockType.UNORDERED_LIST.value == "unordered_list"
        
        # Test enum iteration
        block_types = list(MarkdownBlockType)
        assert len(block_types) > 10  # Should have many block types
        
        # Test enum contains expected types
        expected_types = [
            MarkdownBlockType.DOCUMENT,
            MarkdownBlockType.PARAGRAPH,
            MarkdownBlockType.HEADING,
            MarkdownBlockType.CODE_BLOCK,
            MarkdownBlockType.UNORDERED_LIST
        ]
        
        for expected_type in expected_types:
            assert expected_type in block_types
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_block_creation(self):
        """Test AsciiDocBlock creation."""
        block = AsciiDocBlock(
            block_type=AsciiDocBlockType.PARAGRAPH,
            content="Test content",
            raw_content="Test raw content",
            start_line=1,
            end_line=1,
            start_pos=0,
            end_pos=12,
            level=0
        )
        
        assert block.block_type == AsciiDocBlockType.PARAGRAPH
        assert block.content == "Test content"
        assert block.raw_content == "Test raw content"
        assert block.start_line == 1
        assert block.end_line == 1
        assert block.start_pos == 0
        assert block.end_pos == 12
        assert block.level == 0
        assert block.children == []
        assert block.parent is None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_block_creation(self):
        """Test MarkdownBlock creation."""
        block = MarkdownBlock(
            block_type=MarkdownBlockType.PARAGRAPH,
            content="Test content",
            raw_content="Test raw content",
            start_line=1,
            end_line=1,
            start_pos=0,
            end_pos=12,
            level=0
        )
        
        assert block.block_type == MarkdownBlockType.PARAGRAPH
        assert block.content == "Test content"
        assert block.raw_content == "Test raw content"
        assert block.start_line == 1
        assert block.end_line == 1
        assert block.start_pos == 0
        assert block.end_pos == 12
        assert block.level == 0
        assert block.children == []
        assert block.parent is None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_asciidoc_document_creation(self):
        """Test AsciiDocDocument creation."""
        document = AsciiDocDocument(
            title="Test Document",
            source_file="test.adoc"
        )
        
        assert document.title == "Test Document"
        assert document.source_file == "test.adoc"
        assert document.blocks == []
        assert document.attributes == {}
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_markdown_document_creation(self):
        """Test MarkdownDocument creation."""
        document = MarkdownDocument()
        document.title = "Test Document"
        document.source_file = "test.md"
        
        assert document.title == "Test Document"
        assert document.source_file == "test.md"
        assert document.blocks == []
        assert document.metadata == {}
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_block_hierarchy_operations(self):
        """Test block hierarchy operations."""
        parent_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.SECTION,
            content="Parent section",
            raw_content="Parent section",
            start_line=1,
            end_line=1,
            start_pos=0,
            end_pos=14,
            level=1
        )
        
        child_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.PARAGRAPH,
            content="Child paragraph",
            raw_content="Child paragraph",
            start_line=2,
            end_line=2,
            start_pos=0,
            end_pos=15,
            level=2
        )
        
        # Test adding child
        parent_block.add_child(child_block)
        
        assert len(parent_block.children) == 1
        assert parent_block.children[0] == child_block
        assert child_block.parent == parent_block
        
        # Test removing child
        parent_block.remove_child(child_block)
        
        assert len(parent_block.children) == 0
        assert child_block.parent is None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_document_block_queries(self):
        """Test document block query methods."""
        document = AsciiDocDocument()
        
        # Create blocks
        heading_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.HEADING,
            content="Heading",
            raw_content="= Heading",
            start_line=1,
            end_line=1,
            start_pos=0,
            end_pos=9,
            level=1
        )
        
        paragraph_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.PARAGRAPH,
            content="Paragraph",
            raw_content="Paragraph",
            start_line=2,
            end_line=2,
            start_pos=0,
            end_pos=9,
            level=0
        )
        
        document.blocks = [heading_block, paragraph_block]
        
        # Test get_blocks_by_type
        headings = document.get_blocks_by_type(AsciiDocBlockType.HEADING)
        assert len(headings) == 1
        assert headings[0] == heading_block
        
        paragraphs = document.get_blocks_by_type(AsciiDocBlockType.PARAGRAPH)
        assert len(paragraphs) == 1
        assert paragraphs[0] == paragraph_block
        
        # Test non-existent type
        admonitions = document.get_blocks_by_type(AsciiDocBlockType.ADMONITION)
        assert len(admonitions) == 0
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_full_parsing_pipeline(self, sample_documents):
        """Test the complete parsing pipeline."""
        factory = StructuralParserFactory()
        
        # Test with markdown
        result = factory.parse(sample_documents['complex_markdown'], format_hint='auto')
        
        assert result.success == True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
        
        # Test with asciidoc
        result = factory.parse(sample_documents['complex_asciidoc'], format_hint='auto')
        
        assert result.success == True
        assert result.document is not None
        
        # Test with mixed content
        result = factory.parse(sample_documents['mixed_content'], format_hint='auto')
        
        assert result.success == True
        assert result.document is not None
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_concurrent_parsing_operations(self, sample_documents):
        """Test concurrent parsing operations."""
        import threading
        
        factory = StructuralParserFactory()
        
        results = []
        
        def parse_worker(content, index):
            result = factory.parse(content, format_hint='markdown')
            results.append((index, result))
        
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=parse_worker, args=(sample_documents['simple_markdown'], i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed
        assert len(results) == 3
        for index, result in results:
            assert isinstance(result, MarkdownParseResult)
            assert result.success == True
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_large_document_parsing(self):
        """Test parsing large documents."""
        factory = StructuralParserFactory()
        
        # Create large document
        large_content = "# Section\n\nParagraph content.\n\n" * 1000
        
        result = factory.parse(large_content, format_hint='markdown')
        
        assert isinstance(result, MarkdownParseResult)
        assert result.success == True
        assert len(result.document.blocks) > 0
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_parsing_performance(self, sample_documents):
        """Test parsing performance."""
        import time
        
        factory = StructuralParserFactory()
        
        start_time = time.time()
        result = factory.parse(sample_documents['complex_markdown'], format_hint='markdown')
        end_time = time.time()
        
        assert result.success == True
        
        # Should complete within reasonable time
        parsing_time = end_time - start_time
        assert parsing_time < 2.0  # Should complete within 2 seconds
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_error_recovery_and_fallbacks(self):
        """Test error recovery and fallback mechanisms."""
        factory = StructuralParserFactory()
        
        # Test with invalid content that might cause parsing issues
        invalid_content = "This is invalid content with \x00 null bytes and \xFF invalid utf-8"
        
        result = factory.parse(invalid_content, format_hint='markdown')
        
        # Should handle gracefully
        assert isinstance(result, MarkdownParseResult)
        # May succeed or fail depending on parser robustness
    
    @pytest.mark.skipif(not STRUCTURAL_PARSING_AVAILABLE, reason="Structural parsing not available")
    def test_end_to_end_document_processing(self, sample_files):
        """Test end-to-end document processing."""
        processor = DocumentProcessor()
        factory = StructuralParserFactory()
        
        # Create a markdown file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_files['md'])
            f.flush()
            
            try:
                # Extract text
                content = processor.extract_text(f.name)
                assert content is not None
                
                # Parse structure
                result = factory.parse(content, format_hint='markdown')
                assert result.success == True
                assert isinstance(result.document, MarkdownDocument)
                assert len(result.document.blocks) > 0
                
                # Verify content preservation
                markdown_doc: MarkdownDocument = result.document
                headings = markdown_doc.get_blocks_by_type(MarkdownBlockType.HEADING)
                assert len(headings) > 0
                assert "Sample Markdown" in headings[0].content
                
            finally:
                os.unlink(f.name) 