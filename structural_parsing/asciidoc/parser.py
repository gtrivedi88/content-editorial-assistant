"""
AsciiDoc structural parser using asciidoctor library via persistent Ruby server.
This parser leverages asciidoctor's Ruby server for high-performance structural analysis.
"""

import json
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

from .types import (
    AsciiDocDocument, 
    AsciiDocBlock, 
    AsciiDocBlockType,
    AdmonitionType,
    AsciiDocAttributes,
    ParseResult
)
from .ruby_server import get_server, RubyAsciidoctorServer


@dataclass
class AsciiDocParseError(Exception):
    """Exception raised when AsciiDoc parsing fails."""
    message: str
    original_error: Optional[Exception] = None


class AsciiDocParser:
    """
    High-performance AsciiDoc parser using persistent Ruby server.
    
    This parser uses a persistent Ruby server to avoid subprocess overhead
    and provides fast, reliable parsing of AsciiDoc documents.
    """
    
    def __init__(self):
        self.asciidoctor_available = self._check_asciidoctor_availability()
        
    def _check_asciidoctor_availability(self) -> bool:
        """Check if asciidoctor is available on the system."""
        try:
            server = get_server()
            return server.ping()
        except:
            return False
    
    def parse(self, content: str, filename: str = "") -> ParseResult:
        """
        Parse AsciiDoc content into structural blocks using persistent Ruby server.
        
        Args:
            content: Raw AsciiDoc content
            filename: Optional filename for error reporting
            
        Returns:
            ParseResult with properly structured document
        """
        if not self.asciidoctor_available:
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=["Asciidoctor is not available. Please install with: gem install asciidoctor"]
            )
        
        try:
            # Use persistent Ruby server for parsing
            server = get_server()
            document_data = server.parse_document(content)
            
            # Convert the server result to our document structure
            document = self._convert_server_result_to_document(document_data, filename)
            
            return ParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse AsciiDoc: {str(e)}"]
            )
    
    def _convert_server_result_to_document(self, data: Dict[str, Any], filename: str) -> AsciiDocDocument:
        """
        Convert Ruby server result to AsciiDocDocument.
        
        Args:
            data: Dictionary from Ruby server
            filename: Source filename
            
        Returns:
            AsciiDocDocument with proper structure
        """
        blocks = []
        
        for block_data in data.get('blocks', []):
            block = self._convert_block_data(block_data, filename)
            if block:
                blocks.append(block)
        
        return AsciiDocDocument(
            blocks=blocks,
            attributes=data.get('attributes', {}),
            title=data.get('title'),
            source_file=filename
        )
    
    def _convert_block_data(self, block_data: Dict[str, Any], filename: str, parent: Optional[AsciiDocBlock] = None) -> Optional[AsciiDocBlock]:
        """
        Convert block data from Ruby server to AsciiDocBlock.
        
        Args:
            block_data: Block data from Ruby server
            filename: Source filename
            parent: Parent block if any
            
        Returns:
            AsciiDocBlock or None if conversion fails
        """
        # Map asciidoctor contexts to our block types
        context_map = {
            'document': AsciiDocBlockType.DOCUMENT,
            'preamble': AsciiDocBlockType.PREAMBLE,
            'section': AsciiDocBlockType.SECTION,
            'paragraph': AsciiDocBlockType.PARAGRAPH,
            'heading': AsciiDocBlockType.HEADING,
            'ulist': AsciiDocBlockType.UNORDERED_LIST,
            'olist': AsciiDocBlockType.ORDERED_LIST,
            'dlist': AsciiDocBlockType.DESCRIPTION_LIST,
            'list_item': AsciiDocBlockType.LIST_ITEM,
            'sidebar': AsciiDocBlockType.SIDEBAR,
            'example': AsciiDocBlockType.EXAMPLE,
            'listing': AsciiDocBlockType.LISTING,
            'literal': AsciiDocBlockType.LITERAL,
            'quote': AsciiDocBlockType.QUOTE,
            'verse': AsciiDocBlockType.VERSE,
            'pass': AsciiDocBlockType.PASS,
            'open': AsciiDocBlockType.OPEN,
            'admonition': AsciiDocBlockType.ADMONITION,
            'table': AsciiDocBlockType.TABLE,
            'image': AsciiDocBlockType.IMAGE,
            'audio': AsciiDocBlockType.AUDIO,
            'video': AsciiDocBlockType.VIDEO,
            'attribute_entry': AsciiDocBlockType.ATTRIBUTE_ENTRY,
            'comment': AsciiDocBlockType.COMMENT,
            'toc': AsciiDocBlockType.TOC,
            'page_break': AsciiDocBlockType.PAGE_BREAK,
            'thematic_break': AsciiDocBlockType.THEMATIC_BREAK,
        }
        
        context = block_data.get('context', '')
        block_type = context_map.get(context)
        if not block_type:
            return None
        
        # Extract source location
        source_loc = block_data.get('source_location', {})
        start_line = source_loc.get('lineno', 0) if source_loc else 0
        
        # Create attributes
        attributes = AsciiDocAttributes()
        if block_data.get('id'):
            attributes.id = block_data['id']
        if block_data.get('style'):
            attributes.named_attributes['style'] = block_data['style']
        
        # Add block-specific attributes
        block_attributes = block_data.get('attributes', {})
        for key, value in block_attributes.items():
            if isinstance(value, str):
                attributes.named_attributes[key] = value
        
        # Handle admonitions
        admonition_type = None
        if block_type == AsciiDocBlockType.ADMONITION:
            admonition_name = block_data.get('admonition_name', '').upper()
            admonition_map = {
                'NOTE': AdmonitionType.NOTE,
                'TIP': AdmonitionType.TIP,
                'IMPORTANT': AdmonitionType.IMPORTANT,
                'WARNING': AdmonitionType.WARNING,
                'CAUTION': AdmonitionType.CAUTION,
            }
            admonition_type = admonition_map.get(admonition_name, AdmonitionType.NOTE)
        
        # Extract content
        content = block_data.get('content', '')
        raw_content = '\n'.join(block_data.get('lines', [content])) if block_data.get('lines') else content
        
        # Create the block
        block = AsciiDocBlock(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            start_line=start_line,
            end_line=start_line + len(block_data.get('lines', [1])) - 1,
            start_pos=0,
            end_pos=len(raw_content),
            level=block_data.get('level', 0),
            attributes=attributes,
            parent=parent,
            children=[],
            title=block_data.get('title'),
            style=block_data.get('style'),
            admonition_type=admonition_type,
            list_marker=None,
            source_location=filename
        )
        
        # Process children
        for child_data in block_data.get('children', []):
            child_block = self._convert_block_data(child_data, filename, block)
            if child_block:
                block.children.append(child_block)
        
        return block 