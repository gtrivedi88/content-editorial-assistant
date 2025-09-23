"""
Structural parsing package for AsciiDoc and Markdown documents.

This package provides robust document parsing using external libraries:
- AsciiDoc: Uses asciidoctor Ruby gem
- Markdown: Uses markdown-it-py library
- Extractors: Plain text extraction from various document formats

The implementation follows clean separation principles:
- Format detection: Simple regex patterns for quick format identification
- Parsing: Delegated to specialized external libraries for accuracy
- Extraction: Plain text extraction for non-structured analysis
"""

from .parser_factory import StructuralParserFactory, parse_document
from .format_detector import FormatDetector
from .extractors import DocumentProcessor
from .plaintext import PlainTextParser, PlainTextDocument, PlainTextParseResult

__version__ = "0.1.0"
__all__ = ['StructuralParserFactory', 'parse_document', 'FormatDetector', 'DocumentProcessor',
           'PlainTextParser', 'PlainTextDocument', 'PlainTextParseResult'] 