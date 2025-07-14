"""
Comprehensive Test Suite for Document Processing
Tests document text extraction, format detection, and structural parsing for all supported formats.
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structural_parsing.extractors.document_processor import DocumentProcessor
from structural_parsing.format_detector import FormatDetector
from structural_parsing.parser_factory import StructuralParserFactory, parse_document
from structural_parsing.markdown.parser import MarkdownParser
from structural_parsing.asciidoc.parser import AsciiDocParser
from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlock, MarkdownBlockType
from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlock, AsciiDocBlockType


class TestDocumentProcessing:
    """Test suite for document processing functionality."""
    
    @pytest.fixture
    def document_processor(self):
        """Create a document processor instance."""
        return DocumentProcessor()
    
    @pytest.fixture
    def format_detector(self):
        """Create a format detector instance."""
        return FormatDetector()
    
    @pytest.fixture
    def parser_factory(self):
        """Create a parser factory instance."""
        return StructuralParserFactory()
    
    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing."""
        return {
            'txt': "This is a sample text file.\nWith multiple lines.\nFor testing purposes.",
            'md': "# Sample Markdown\n\nThis is a **bold** text.\n\n- Item 1\n- Item 2\n\n```python\nprint('hello')\n```",
            'adoc': "= Sample AsciiDoc Document\n\nThis is a paragraph.\n\n[NOTE]\n====\nThis is a note.\n====\n\n== Section\n\nMore content.",
            'dita': '<?xml version="1.0"?>\n<topic id="sample"><title>Sample DITA</title><body><p>This is content.</p></body></topic>',
            'pdf_content': "This is extracted PDF content.\nMultiple lines of text.",
            'docx_content': "This is extracted DOCX content.\nWith formatting preserved."
        }
    
    def test_document_processor_initialization(self, document_processor):
        """Test document processor initialization."""
        assert isinstance(document_processor, DocumentProcessor)
        assert hasattr(document_processor, 'ALLOWED_EXTENSIONS')
        assert hasattr(document_processor, 'supported_formats')
        assert len(document_processor.ALLOWED_EXTENSIONS) > 0
        assert len(document_processor.supported_formats) > 0
    
    def test_allowed_file_extensions(self, document_processor):
        """Test allowed file extension checking."""
        
        # Test valid extensions
        assert document_processor.allowed_file('document.pdf') is True
        assert document_processor.allowed_file('document.docx') is True
        assert document_processor.allowed_file('document.txt') is True
        assert document_processor.allowed_file('document.md') is True
        assert document_processor.allowed_file('document.adoc') is True
        assert document_processor.allowed_file('document.dita') is True
        
        # Test invalid extensions
        assert document_processor.allowed_file('document.xyz') is False
        assert document_processor.allowed_file('document.exe') is False
        assert document_processor.allowed_file('document.jpg') is False
        
        # Test edge cases
        assert document_processor.allowed_file('document') is False
        assert document_processor.allowed_file('') is False
        assert document_processor.allowed_file('.pdf') is True
        assert document_processor.allowed_file('document.PDF') is True  # Case insensitive
    
    def test_text_file_extraction(self, document_processor, sample_files):
        """Test text file extraction."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_files['txt'])
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'sample text file' in content
                assert 'multiple lines' in content
                assert 'testing purposes' in content
            finally:
                os.unlink(f.name)
    
    def test_markdown_file_extraction(self, document_processor, sample_files):
        """Test Markdown file extraction."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(sample_files['md'])
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'Sample Markdown' in content
                assert 'bold' in content
                assert 'Item 1' in content
                assert 'Item 2' in content
                # Code blocks should be preserved
                assert 'print' in content
            finally:
                os.unlink(f.name)
    
    def test_asciidoc_file_extraction(self, document_processor, sample_files):
        """Test AsciiDoc file extraction."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(sample_files['adoc'])
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'Sample AsciiDoc Document' in content
                assert 'paragraph' in content
                assert 'note' in content
                assert 'Section' in content
                assert 'More content' in content
            finally:
                os.unlink(f.name)
    
    def test_dita_file_extraction(self, document_processor, sample_files):
        """Test DITA file extraction."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dita', delete=False) as f:
            f.write(sample_files['dita'])
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'Sample DITA' in content
                assert 'This is content' in content
            finally:
                os.unlink(f.name)
    
    @patch('fitz.open')
    def test_pdf_file_extraction(self, mock_fitz, document_processor, sample_files):
        """Test PDF file extraction."""
        
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_files['pdf_content']
        mock_doc.page_count = 1
        mock_doc.__getitem__.return_value = mock_page
        mock_fitz.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'extracted PDF content' in content
                assert 'Multiple lines' in content
                mock_fitz.assert_called_once()
                mock_doc.close.assert_called_once()
            finally:
                os.unlink(f.name)
    
    @patch('structural_parsing.extractors.document_processor.Document')
    def test_docx_file_extraction(self, mock_docx, document_processor, sample_files):
        """Test DOCX file extraction."""
        
        # Mock python-docx
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = sample_files['docx_content']
        mock_doc.paragraphs = [mock_paragraph]
        mock_doc.tables = []
        mock_docx.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'extracted DOCX content' in content
                assert 'formatting preserved' in content
                mock_docx.assert_called_once()
            finally:
                os.unlink(f.name)
    
    @patch('structural_parsing.extractors.document_processor.Document')
    def test_docx_with_tables_extraction(self, mock_docx, document_processor):
        """Test DOCX file extraction with tables."""
        
        # Mock python-docx with tables
        mock_doc = MagicMock()
        mock_doc.paragraphs = []
        
        # Mock table
        mock_table = MagicMock()
        mock_row = MagicMock()
        mock_cell = MagicMock()
        mock_cell.text = "Table cell content"
        mock_row.cells = [mock_cell]
        mock_table.rows = [mock_row]
        mock_doc.tables = [mock_table]
        
        mock_docx.return_value = mock_doc
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'Table cell content' in content
            finally:
                os.unlink(f.name)
    
    def test_extract_text_file_not_found(self, document_processor):
        """Test extraction with non-existent file."""
        
        content = document_processor.extract_text('nonexistent.txt')
        assert content is None
    
    def test_extract_text_unsupported_format(self, document_processor):
        """Test extraction with unsupported format."""
        
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b'content')
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is None
            finally:
                os.unlink(f.name)
    
    def test_extract_text_with_errors(self, document_processor):
        """Test extraction error handling."""
        
        with patch('builtins.open', side_effect=Exception("Read error")):
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                try:
                    content = document_processor.extract_text(f.name)
                    assert content is None
                finally:
                    os.unlink(f.name)
    
    def test_text_cleaning(self, document_processor):
        """Test text cleaning functionality."""
        
        # Test with text that needs cleaning
        messy_text = "This  has   multiple    spaces\n\n\n\n\nand\n\n\nexcessive\n\nline\nbreaks"
        cleaned = document_processor._clean_text(messy_text)
        
        # Should normalize spaces
        assert '  ' not in cleaned
        assert '   ' not in cleaned
        
        # Should reduce excessive line breaks
        assert '\n\n\n' not in cleaned
        
        # Should preserve content
        assert 'multiple' in cleaned
        assert 'excessive' in cleaned
        assert 'line' in cleaned
        assert 'breaks' in cleaned
    
    def test_get_document_info(self, document_processor, sample_files):
        """Test getting document information."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sample_files['txt'])
            f.flush()
            
            try:
                info = document_processor.get_document_info(f.name)
                assert isinstance(info, dict)
                assert 'filepath' in info
                assert 'filename' in info
                assert 'file_size' in info
                assert 'format' in info
                assert 'extractable' in info
                
                assert info['filepath'] == f.name
                assert info['filename'] == os.path.basename(f.name)
                assert info['file_size'] > 0
                assert info['format'] == 'txt'
                assert info['extractable'] is True
            finally:
                os.unlink(f.name)
    
    def test_get_document_info_nonexistent(self, document_processor):
        """Test getting document info for non-existent file."""
        
        info = document_processor.get_document_info('nonexistent.txt')
        assert isinstance(info, dict)
        assert info['file_size'] == 0
        assert info['format'] == 'txt'
        assert info['extractable'] is True  # txt is supported format
    
    def test_format_detector_initialization(self, format_detector):
        """Test format detector initialization."""
        
        assert isinstance(format_detector, FormatDetector)
        assert hasattr(format_detector, 'asciidoc_patterns')
        assert hasattr(format_detector, 'markdown_patterns')
        assert len(format_detector.asciidoc_patterns) > 0
        assert len(format_detector.markdown_patterns) > 0
    
    def test_format_detection_asciidoc(self, format_detector):
        """Test AsciiDoc format detection."""
        
        # Test various AsciiDoc patterns
        asciidoc_samples = [
            "= Main Title\n\nContent here",
            "[NOTE]\n====\nThis is a note\n====",
            ":author: John Doe\n:version: 1.0\n\nContent",
            "== Section Title\n\nContent",
            "****\nSidebar content\n****",
            "====\nExample content\n====",
            "----\nCode listing\n----",
            "++++\nPassthrough content\n++++",
            ".Prerequisites\nBefore you begin...",
            "** Second level list\n*** Third level list",
            ". Ordered list item",
            "[[anchor]]\nContent with anchor",
            "include::other.adoc[]",
            "image::diagram.png[]",
            "link:http://example.com[Link text]"
        ]
        
        for sample in asciidoc_samples:
            format_result = format_detector.detect_format(sample)
            assert format_result == 'asciidoc', f"Failed to detect AsciiDoc in: {sample[:50]}..."
    
    def test_format_detection_markdown(self, format_detector):
        """Test Markdown format detection."""
        
        # Test various Markdown patterns
        markdown_samples = [
            "# Main Title\n\nContent here",
            "## Section Title\n\nContent",
            "### Subsection\n\nContent",
            "```python\nprint('hello')\n```",
            "* Unordered list\n* Another item",
            "1. Ordered list\n2. Second item",
            "> This is a blockquote\n> Second line",
            "| Header 1 | Header 2 |\n|----------|----------|",
            "This is **bold** and *italic*",
            "[Link text](http://example.com)",
            "![Alt text](image.png)"
        ]
        
        for sample in markdown_samples:
            format_result = format_detector.detect_format(sample)
            assert format_result == 'markdown', f"Failed to detect Markdown in: {sample[:50]}..."
    
    def test_format_detection_mixed_content(self, format_detector):
        """Test format detection with mixed content."""
        
        # Content with both AsciiDoc and Markdown patterns
        mixed_content = """
        = AsciiDoc Title
        
        This has **markdown bold** and = asciidoc title
        
        - markdown list
        ** asciidoc list
        
        ```code
        print('hello')
        ```
        
        [NOTE]
        ====
        This is clearly AsciiDoc
        ====
        """
        
        # Should detect as AsciiDoc due to stronger indicators
        format_result = format_detector.detect_format(mixed_content)
        assert format_result == 'asciidoc'
    
    def test_format_detection_empty_content(self, format_detector):
        """Test format detection with empty content."""
        
        format_result = format_detector.detect_format("")
        assert format_result == 'markdown'  # Default for empty content
        
        format_result = format_detector.detect_format("   \n\t  ")
        assert format_result == 'markdown'  # Default for whitespace-only
    
    def test_parser_factory_initialization(self, parser_factory):
        """Test parser factory initialization."""
        
        assert isinstance(parser_factory, StructuralParserFactory)
        assert hasattr(parser_factory, 'format_detector')
        assert hasattr(parser_factory, 'asciidoc_parser')
        assert hasattr(parser_factory, 'markdown_parser')
        
        assert isinstance(parser_factory.format_detector, FormatDetector)
        assert isinstance(parser_factory.asciidoc_parser, AsciiDocParser)
        assert isinstance(parser_factory.markdown_parser, MarkdownParser)
    
    def test_parser_factory_auto_detection(self, parser_factory):
        """Test parser factory with auto format detection."""
        
        # Test with clear AsciiDoc content
        asciidoc_content = "= Title\n\nContent\n\n[NOTE]\nThis is a note."
        result = parser_factory.parse(asciidoc_content, "test.adoc", 'auto')
        assert result is not None
        assert hasattr(result, 'success')
        
        # Test with clear Markdown content
        markdown_content = "# Title\n\nContent\n\n```python\nprint('hello')\n```"
        result = parser_factory.parse(markdown_content, "test.md", 'auto')
        assert result is not None
        assert hasattr(result, 'success')
        assert result.success is True
    
    def test_parser_factory_explicit_format(self, parser_factory):
        """Test parser factory with explicit format hints."""
        
        content = "# Title\n\nContent here"
        
        # Test explicit AsciiDoc parsing
        result = parser_factory.parse(content, "test.txt", 'asciidoc')
        assert result is not None
        assert hasattr(result, 'success')
        
        # Test explicit Markdown parsing
        result = parser_factory.parse(content, "test.txt", 'markdown')
        assert result is not None
        assert hasattr(result, 'success')
        assert result.success is True
    
    def test_parser_factory_available_parsers(self, parser_factory):
        """Test getting available parsers information."""
        
        parsers = parser_factory.get_available_parsers()
        assert isinstance(parsers, dict)
        assert 'asciidoc' in parsers
        assert 'markdown' in parsers
        
        # Check structure
        for parser_name, parser_info in parsers.items():
            assert 'available' in parser_info
            assert 'parser' in parser_info
            assert 'description' in parser_info
    
    def test_markdown_parser_initialization(self):
        """Test Markdown parser initialization."""
        
        parser = MarkdownParser()
        assert isinstance(parser, MarkdownParser)
        assert hasattr(parser, 'md')
        assert parser.md is not None
    
    def test_markdown_parser_basic_parsing(self):
        """Test basic Markdown parsing."""
        
        parser = MarkdownParser()
        content = "# Title\n\nThis is a paragraph.\n\n- Item 1\n- Item 2"
        
        result = parser.parse(content, "test.md")
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'document')
        assert result.success is True
        assert isinstance(result.document, MarkdownDocument)
    
    def test_markdown_parser_complex_content(self):
        """Test Markdown parser with complex content."""
        
        parser = MarkdownParser()
        content = """# Main Title

This is a paragraph with **bold** and *italic* text.

## Section 2

Here's a list:
- Item 1
- Item 2
  - Nested item
  - Another nested item

### Code Example

```python
def hello():
    print("Hello, world!")
```

> This is a blockquote
> with multiple lines

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
        
        result = parser.parse(content, "complex.md")
        assert result.success is True
        assert isinstance(result.document, MarkdownDocument)
        assert len(result.document.blocks) > 0
    
    def test_markdown_parser_error_handling(self):
        """Test Markdown parser error handling."""
        
        parser = MarkdownParser()
        
        # Test with invalid content (should still parse)
        content = "Invalid markdown content with weird formatting"
        result = parser.parse(content, "test.md")
        assert result is not None
        assert hasattr(result, 'success')
        
        # Test with empty content
        result = parser.parse("", "empty.md")
        assert result is not None
        assert result.success is True
    
    def test_asciidoc_parser_initialization(self):
        """Test AsciiDoc parser initialization."""
        
        parser = AsciiDocParser()
        assert isinstance(parser, AsciiDocParser)
        assert hasattr(parser, 'asciidoctor_available')
    
    def test_asciidoc_parser_availability_check(self):
        """Test AsciiDoc parser availability check."""
        
        parser = AsciiDocParser()
        # Should not crash regardless of availability
        assert isinstance(parser.asciidoctor_available, bool)
    
    def test_asciidoc_parser_basic_parsing(self):
        """Test basic AsciiDoc parsing."""
        
        parser = AsciiDocParser()
        content = "= Title\n\nThis is a paragraph."
        
        result = parser.parse(content, "test.adoc")
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'document')
        
        if parser.asciidoctor_available:
            assert result.success is True
            assert isinstance(result.document, AsciiDocDocument)
        else:
            # Should handle unavailability gracefully
            assert result.success is False
            assert 'Asciidoctor is not available' in str(result.errors)
    
    def test_asciidoc_parser_complex_content(self):
        """Test AsciiDoc parser with complex content."""
        
        parser = AsciiDocParser()
        content = """= Document Title
:author: John Doe
:version: 1.0

This is the preamble.

== Section 1

This is a paragraph.

[NOTE]
====
This is a note admonition.
====

=== Subsection

- List item 1
- List item 2

. Ordered item 1
. Ordered item 2

----
Code block content
----

[source,python]
----
def hello():
    print("Hello!")
----

****
This is a sidebar.
****
"""
        
        result = parser.parse(content, "complex.adoc")
        assert result is not None
        
        if parser.asciidoctor_available:
            assert result.success is True
            assert isinstance(result.document, AsciiDocDocument)
            assert len(result.document.blocks) > 0
        else:
            assert result.success is False
    
    def test_asciidoc_parser_error_handling(self):
        """Test AsciiDoc parser error handling."""
        
        parser = AsciiDocParser()
        
        # Test with malformed content
        content = "= Title\n\n[INVALID_ADMONITION\nMalformed content"
        result = parser.parse(content, "test.adoc")
        assert result is not None
        
        # Should handle errors gracefully
        if not parser.asciidoctor_available:
            assert result.success is False
    
    def test_convenience_parse_function(self):
        """Test the convenience parse_document function."""
        
        # Test with Markdown content
        markdown_content = "# Title\n\nContent here"
        result = parse_document(markdown_content, "test.md", 'markdown')
        assert result is not None
        assert hasattr(result, 'success')
        assert result.success is True
        
        # Test with auto detection
        result = parse_document(markdown_content, "test.md", 'auto')
        assert result is not None
        assert hasattr(result, 'success')
        assert result.success is True
    
    def test_markdown_document_structure(self):
        """Test Markdown document structure."""
        
        parser = MarkdownParser()
        content = "# Title\n\nParagraph\n\n- Item 1\n- Item 2"
        
        result = parser.parse(content, "test.md")
        if result.success:
            doc = result.document
            assert isinstance(doc, MarkdownDocument)
            assert hasattr(doc, 'blocks')
            assert hasattr(doc, 'metadata')
            assert hasattr(doc, 'source_file')
            
            # Test document methods
            content_blocks = doc.get_content_blocks()
            assert isinstance(content_blocks, list)
            
            # Test getting blocks by type
            headings = doc.get_blocks_by_type(MarkdownBlockType.HEADING)
            assert isinstance(headings, list)
    
    def test_asciidoc_document_structure(self):
        """Test AsciiDoc document structure."""
        
        parser = AsciiDocParser()
        content = "= Title\n\nParagraph content"
        
        result = parser.parse(content, "test.adoc")
        if result.success:
            doc = result.document
            assert isinstance(doc, AsciiDocDocument)
            assert hasattr(doc, 'blocks')
            assert hasattr(doc, 'attributes')
            assert hasattr(doc, 'source_file')
            
            # Test document methods
            content_blocks = doc.get_content_blocks()
            assert isinstance(content_blocks, list)
            
            # Test getting blocks by type
            headings = doc.get_blocks_by_type(AsciiDocBlockType.HEADING)
            assert isinstance(headings, list)
    
    def test_block_types_and_enums(self):
        """Test block type enums."""
        
        # Test Markdown block types
        assert hasattr(MarkdownBlockType, 'HEADING')
        assert hasattr(MarkdownBlockType, 'PARAGRAPH')
        assert hasattr(MarkdownBlockType, 'CODE_BLOCK')
        assert hasattr(MarkdownBlockType, 'ORDERED_LIST')
        assert hasattr(MarkdownBlockType, 'UNORDERED_LIST')
        
        # Test AsciiDoc block types
        assert hasattr(AsciiDocBlockType, 'HEADING')
        assert hasattr(AsciiDocBlockType, 'PARAGRAPH')
        assert hasattr(AsciiDocBlockType, 'ADMONITION')
        assert hasattr(AsciiDocBlockType, 'LISTING')
        assert hasattr(AsciiDocBlockType, 'SIDEBAR')
    
    def test_large_document_processing(self, document_processor):
        """Test processing of large documents."""
        
        # Create a large text document
        large_content = "This is a test sentence. " * 10000
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_content)
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert len(content) > 0
                # Should not crash or take excessive time
            finally:
                os.unlink(f.name)
    
    def test_special_characters_in_documents(self, document_processor):
        """Test documents with special characters."""
        
        special_content = """
        Special characters: áéíóú, çñ, ßü, 中文, العربية, русский
        Emojis: 🚀 🎉 💡 ⭐ 🔥
        Symbols: ©®™ ±×÷ ∞∑∏ αβγ
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(special_content)
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert '中文' in content
                assert '🚀' in content
                assert '©' in content
            finally:
                os.unlink(f.name)
    
    def test_binary_file_handling(self, document_processor):
        """Test handling of binary files."""
        
        # Create a binary file
        binary_content = b'\x00\x01\x02\x03\x04\x05'
        
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as f:
            f.write(binary_content)
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is None  # Should not extract binary files
            finally:
                os.unlink(f.name)
    
    def test_concurrent_document_processing(self, document_processor):
        """Test concurrent document processing."""
        
        import threading
        import time
        
        results = []
        
        def process_document(content, index):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Document {index}: {content}")
                f.flush()
                
                try:
                    extracted = document_processor.extract_text(f.name)
                    results.append((index, extracted is not None))
                finally:
                    os.unlink(f.name)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_document, args=(f"Content for document {i}", i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(results) == 5
        for index, success in results:
            assert success is True, f"Document {index} processing failed"
    
    def test_parser_factory_error_handling(self, parser_factory):
        """Test parser factory error handling."""
        
        # Test with invalid content
        result = parser_factory.parse("", "test.txt", 'invalid_format')
        assert result is not None
        # Should fall back to auto detection
        
        # Test with None content
        result = parser_factory.parse(None, "test.txt", 'auto')
        assert result is not None
    
    def test_document_metadata_extraction(self, document_processor):
        """Test extraction of document metadata."""
        
        # Test with AsciiDoc that has metadata
        asciidoc_with_metadata = """= Document Title
:author: John Doe
:version: 1.0
:description: A test document

This is the content.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(asciidoc_with_metadata)
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content is not None
                assert 'Document Title' in content
                # Attributes are removed during extraction, which is correct
                assert 'This is the content' in content
            finally:
                os.unlink(f.name)
    
    def test_empty_document_handling(self, document_processor):
        """Test handling of empty documents."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")  # Empty file
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content == ""  # Should return empty string, not None
            finally:
                os.unlink(f.name)
    
    def test_whitespace_only_document(self, document_processor):
        """Test handling of whitespace-only documents."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("   \n\t\n   ")  # Only whitespace
            f.flush()
            
            try:
                content = document_processor.extract_text(f.name)
                assert content == ""  # Should be cleaned to empty string
            finally:
                os.unlink(f.name) 