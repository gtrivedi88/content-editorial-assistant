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
        # Handle None content
        if content is None:
            content = ""
        
        # Handle explicit format hints
        if format_hint == 'asciidoc':
            return self.asciidoc_parser.parse(content, filename)
        elif format_hint == 'markdown':
            return self.markdown_parser.parse(content, filename)
        
        # For 'auto' detection, use improved format detection first
        # This ensures we don't incorrectly parse Markdown as AsciiDoc
        detected_format = self.format_detector.detect_format(content)
        
        if detected_format == 'asciidoc':
            # Format detector thinks it's AsciiDoc, try AsciiDoc parser
            if self.asciidoc_parser.asciidoctor_available:
                asciidoc_result = self.asciidoc_parser.parse(content, filename)
                if asciidoc_result.success:
                    return asciidoc_result
                else:
                    # AsciiDoc parsing failed, but detector thought it was AsciiDoc
                    # Fall back to Markdown parser as last resort
                    return self.markdown_parser.parse(content, filename)
            else:
                # Asciidoctor not available, fall back to Markdown
                return self.markdown_parser.parse(content, filename)
        else:
            # Format detector thinks it's Markdown
            markdown_result = self.markdown_parser.parse(content, filename)
            
            # If Markdown parsing fails and Asciidoctor is available,
            # try AsciiDoc as fallback (in case format detection was wrong)
            if not markdown_result.success and self.asciidoc_parser.asciidoctor_available:
                asciidoc_result = self.asciidoc_parser.parse(content, filename)
                if asciidoc_result.success:
                    return asciidoc_result
            
            return markdown_result
    
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