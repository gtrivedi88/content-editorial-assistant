"""
Parser factory for structural parsing.
Uses format detection and dispatches to appropriate parsers.
"""

from typing import Union, Literal
from .format_detector import FormatDetector
from .asciidoc.parser import AsciiDocParser
from .asciidoc.types import ParseResult as AsciiDocParseResult
from .markdown.parser import MarkdownParser
from .markdown.types import MarkdownParseResult


class StructuralParserFactory:
    """
    Factory for creating and managing structural parsers.
    
    This factory maintains clean separation between format detection
    and actual parsing by delegating to specialized parsers.
    """
    
    def __init__(self):
        self.format_detector = FormatDetector()
        self.asciidoc_parser = AsciiDocParser()
        self.markdown_parser = MarkdownParser()
    
    def parse(self, content: str, filename: str = "", 
              format_hint: Literal['asciidoc', 'markdown', 'auto'] = 'auto') -> Union[AsciiDocParseResult, MarkdownParseResult]:
        """
        Parse content using the appropriate parser.
        
        Args:
            content: Raw document content
            filename: Optional filename for error reporting
            format_hint: Format hint ('asciidoc', 'markdown', or 'auto')
            
        Returns:
            ParseResult from the appropriate parser
        """
        # Determine format
        if format_hint == 'auto':
            detected_format = self.format_detector.detect_format(content)
        else:
            detected_format = format_hint
        
        # Dispatch to appropriate parser
        if detected_format == 'asciidoc':
            return self.asciidoc_parser.parse(content, filename)
        else:
            return self.markdown_parser.parse(content, filename)
    
    def get_available_parsers(self) -> dict:
        """Get information about available parsers."""
        return {
            'asciidoc': {
                'available': self.asciidoc_parser.asciidoctor_available,
                'parser': 'asciidoctor (Ruby gem)',
                'description': 'Full AsciiDoc parser with admonitions support'
            },
            'markdown': {
                'available': True,  # markdown-it-py is always available
                'parser': 'markdown-it-py',
                'description': 'CommonMark-compliant Markdown parser'
            }
        }
    
    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown']:
        """
        Detect document format.
        
        Args:
            content: Raw document content
            
        Returns:
            Detected format
        """
        return self.format_detector.detect_format(content)


# Convenience function for one-off parsing
def parse_document(content: str, filename: str = "", 
                  format_hint: Literal['asciidoc', 'markdown', 'auto'] = 'auto') -> Union[AsciiDocParseResult, MarkdownParseResult]:
    """
    Parse a document using the structural parser factory.
    
    Args:
        content: Raw document content
        filename: Optional filename for error reporting
        format_hint: Format hint ('asciidoc', 'markdown', or 'auto')
        
    Returns:
        ParseResult from the appropriate parser
    """
    factory = StructuralParserFactory()
    return factory.parse(content, filename, format_hint) 