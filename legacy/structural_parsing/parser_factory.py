"""
Parser factory for structural parsing.
Uses format detection and dispatches to appropriate parsers.
"""

import logging
from typing import Union, Literal
from .format_detector import FormatDetector
from .asciidoc.parser import AsciiDocParser
from .asciidoc.types import ParseResult as AsciiDocParseResult
from .markdown.parser import MarkdownParser
from .markdown.types import MarkdownParseResult
from .plaintext.parser import PlainTextParser
from .plaintext.types import PlainTextParseResult
from .dita.parser import DITAParser
from .dita.types import DITAParseResult

logger = logging.getLogger(__name__)


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
        self.plaintext_parser = PlainTextParser()
        self.dita_parser = DITAParser()
    
    def parse(self, content: str, filename: str = "", 
              format_hint: Literal['asciidoc', 'markdown', 'plaintext', 'dita', 'auto'] = 'auto') -> Union[AsciiDocParseResult, MarkdownParseResult, PlainTextParseResult, DITAParseResult]:
        """
        Parse content using the appropriate parser.
        
        Args:
            content: Raw document content
            filename: Optional filename for error reporting
            format_hint: Format hint ('asciidoc', 'markdown', or 'auto')
            
        Returns:
            ParseResult from the appropriate parser
        """
        logger.info(f"🔍 [PARSER-DEBUG] parse() called with format_hint='{format_hint}', filename='{filename}'")
        logger.info(f"🔍 [PARSER-DEBUG] Content length: {len(content) if content else 0} chars")
        
        # Handle None content
        if content is None:
            logger.warning(f"⚠️ [PARSER-DEBUG] Content is None, using empty string")
            content = ""
        
        if content:
            logger.info(f"🔍 [PARSER-DEBUG] Content preview (first 200 chars): {content[:200]}")
        
        # Handle explicit format hints
        if format_hint == 'asciidoc':
            logger.info(f"✅ [PARSER-DEBUG] Using explicit AsciiDoc parser (format_hint='asciidoc')")
            result = self.asciidoc_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] AsciiDoc parser result: success={result.success}, blocks={len(result.blocks) if hasattr(result, 'blocks') else 'N/A'}")
            return result
        elif format_hint == 'markdown':
            logger.info(f"✅ [PARSER-DEBUG] Using explicit Markdown parser (format_hint='markdown')")
            result = self.markdown_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] Markdown parser result: success={result.success}, blocks={len(result.blocks) if hasattr(result, 'blocks') else 'N/A'}")
            return result
        elif format_hint == 'plaintext':
            logger.info(f"✅ [PARSER-DEBUG] Using explicit PlainText parser (format_hint='plaintext')")
            result = self.plaintext_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] PlainText parser result: success={result.success}, blocks={len(result.blocks) if hasattr(result, 'blocks') else 'N/A'}")
            return result
        elif format_hint == 'dita':
            logger.info(f"✅ [PARSER-DEBUG] Using explicit DITA parser (format_hint='dita')")
            result = self.dita_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] DITA parser result: success={result.success}, blocks={len(result.blocks) if hasattr(result, 'blocks') else 'N/A'}")
            return result
        
        # For 'auto' detection, use improved format detection first
        logger.info(f"🔍 [PARSER-DEBUG] format_hint='auto', detecting format from content...")
        detected_format = self.format_detector.detect_format(content)
        logger.info(f"✅ [PARSER-DEBUG] Auto-detected format: {detected_format}")
        
        if detected_format == 'plaintext':
            logger.info(f"🔍 [PARSER-DEBUG] Using PlainText parser (auto-detected)")
            result = self.plaintext_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] PlainText parser result: success={result.success}")
            return result
        elif detected_format == 'dita':
            logger.info(f"🔍 [PARSER-DEBUG] Using DITA parser (auto-detected)")
            result = self.dita_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] DITA parser result: success={result.success}")
            return result
        elif detected_format == 'asciidoc':
            logger.info(f"🔍 [PARSER-DEBUG] Detected as AsciiDoc, checking parser availability...")
            logger.info(f"🔍 [PARSER-DEBUG] Asciidoctor available: {self.asciidoc_parser.asciidoctor_available}")
            
            if self.asciidoc_parser.asciidoctor_available:
                logger.info(f"🔍 [PARSER-DEBUG] Attempting AsciiDoc parsing...")
                asciidoc_result = self.asciidoc_parser.parse(content, filename)
                logger.info(f"🔍 [PARSER-DEBUG] AsciiDoc result: success={asciidoc_result.success}, blocks={len(asciidoc_result.blocks) if hasattr(asciidoc_result, 'blocks') else 'N/A'}")
                
                if asciidoc_result.success:
                    logger.info(f"✅ [PARSER-DEBUG] AsciiDoc parsing successful!")
                    return asciidoc_result
                else:
                    logger.warning(f"⚠️ [PARSER-DEBUG] AsciiDoc parsing failed, falling back to Markdown")
                    result = self.markdown_parser.parse(content, filename)
                    logger.info(f"🔍 [PARSER-DEBUG] Markdown fallback result: success={result.success}")
                    return result
            else:
                logger.warning(f"⚠️ [PARSER-DEBUG] Asciidoctor not available, falling back to Markdown")
                result = self.markdown_parser.parse(content, filename)
                logger.info(f"🔍 [PARSER-DEBUG] Markdown fallback result: success={result.success}")
                return result
        else:
            logger.info(f"🔍 [PARSER-DEBUG] Detected as Markdown, attempting parsing...")
            markdown_result = self.markdown_parser.parse(content, filename)
            logger.info(f"🔍 [PARSER-DEBUG] Markdown result: success={markdown_result.success}, blocks={len(markdown_result.blocks) if hasattr(markdown_result, 'blocks') else 'N/A'}")
            
            # If Markdown parsing fails and Asciidoctor is available,
            # try AsciiDoc as fallback (in case format detection was wrong)
            if not markdown_result.success and self.asciidoc_parser.asciidoctor_available:
                logger.warning(f"⚠️ [PARSER-DEBUG] Markdown failed, trying AsciiDoc as fallback...")
                asciidoc_result = self.asciidoc_parser.parse(content, filename)
                logger.info(f"🔍 [PARSER-DEBUG] AsciiDoc fallback result: success={asciidoc_result.success}")
                
                if asciidoc_result.success:
                    logger.info(f"✅ [PARSER-DEBUG] AsciiDoc fallback successful!")
                    return asciidoc_result
            
            logger.info(f"🔍 [PARSER-DEBUG] Returning Markdown result")
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
            },
            'plaintext': {
                'available': True,  # plain text parser is always available
                'parser': 'dedicated plain text parser',
                'description': 'Dedicated plain text parser with paragraph detection'
            },
            'dita': {
                'available': True,  # DITA parser is always available
                'parser': 'dedicated DITA XML parser',
                'description': 'DITA XML parser for Adobe Experience Manager workflows'
            }
        }
    
    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown', 'plaintext', 'dita']:
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
                  format_hint: Literal['asciidoc', 'markdown', 'plaintext', 'dita', 'auto'] = 'auto') -> Union[AsciiDocParseResult, MarkdownParseResult, PlainTextParseResult, DITAParseResult]:
    """
    Parse a document using the structural parser factory.
    
    Args:
        content: Raw document content
        filename: Optional filename for error reporting
        format_hint: Format hint ('asciidoc', 'markdown', 'plaintext', 'dita', or 'auto')
        
    Returns:
        ParseResult from the appropriate parser
    """
    factory = StructuralParserFactory()
    return factory.parse(content, filename, format_hint) 