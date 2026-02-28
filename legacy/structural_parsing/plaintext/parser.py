"""
Plain text structural parser.
This parser handles plain text documents by detecting paragraphs separated by blank lines.
"""

import re
from typing import List, Optional
from .types import (
    PlainTextDocument,
    PlainTextBlock,
    PlainTextBlockType,
    PlainTextParseResult
)


class PlainTextParser:
    """
    Plain text parser for structural analysis.
    
    This parser treats plain text documents as collections of paragraphs
    separated by blank lines, providing optimal structure for style analysis.
    """
    
    def __init__(self):
        """Initialize the plain text parser."""
        pass
    
    def parse(self, content: str, filename: str = "") -> PlainTextParseResult:
        """
        Parse plain text content into structural blocks.
        
        Args:
            content: Raw plain text content
            filename: Optional filename for error reporting
            
        Returns:
            PlainTextParseResult with document structure
        """
        try:
            # Handle None or empty content
            if content is None:
                content = ""
            
            # Split into paragraphs and process
            document = self._parse_paragraphs(content, filename)
            
            return PlainTextParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            # Create empty document for error case
            empty_document = PlainTextDocument()
            empty_document.source_file = filename
            return PlainTextParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse plain text: {str(e)}"]
            )
    
    def _parse_paragraphs(self, content: str, filename: str) -> PlainTextDocument:
        """
        Parse plain text into paragraph blocks.
        
        Args:
            content: Raw content
            filename: Source filename
            
        Returns:
            PlainTextDocument with structured paragraphs
        """
        blocks = []
        
        if not content.strip():
            # Empty document
            document = PlainTextDocument()
            document.source_file = filename
            return document
        
        # Split content by double newlines to detect paragraphs
        # But first, normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Split into potential paragraphs
        chunks = content.split('\n\n')
        
        current_line = 1
        
        for chunk in chunks:
            chunk = chunk.strip()
            
            if not chunk:
                # Skip empty chunks
                continue
            
            # Count lines in this chunk for line numbering
            lines_in_chunk = chunk.count('\n') + 1
            
            # Create paragraph block
            paragraph_block = PlainTextBlock(
                block_type=PlainTextBlockType.PARAGRAPH,
                content=chunk,
                raw_content=chunk,
                start_line=current_line,
                level=0
            )
            
            blocks.append(paragraph_block)
            
            # Update line counter
            current_line += lines_in_chunk + 1  # +1 for the blank line separator
        
        # If no paragraph blocks were created, treat entire content as one paragraph
        if not blocks and content.strip():
            blocks.append(PlainTextBlock(
                block_type=PlainTextBlockType.PARAGRAPH,
                content=content.strip(),
                raw_content=content,
                start_line=1,
                level=0
            ))
        
        document = PlainTextDocument()
        document.source_file = filename
        document.blocks = blocks
        document.children = blocks  # Keep in sync
        
        return document
    
    def _split_into_lines(self, content: str, filename: str) -> PlainTextDocument:
        """
        Alternative parsing: split text into line-based blocks.
        This method treats each line as a separate paragraph.
        
        Args:
            content: Raw content
            filename: Source filename
            
        Returns:
            PlainTextDocument with line-based structure
        """
        blocks = []
        
        if not content.strip():
            document = PlainTextDocument()
            document.source_file = filename
            return document
        
        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line_content = line.strip()
            
            if line_content:
                # Non-empty line becomes a paragraph
                block = PlainTextBlock(
                    block_type=PlainTextBlockType.PARAGRAPH,
                    content=line_content,
                    raw_content=line,
                    start_line=line_num,
                    level=0
                )
                blocks.append(block)
            else:
                # Empty line - could be kept as structure marker
                # For now, skip empty lines in line-based mode
                pass
        
        document = PlainTextDocument()
        document.source_file = filename
        document.blocks = blocks
        document.children = blocks
        
        return document
    
    def parse_as_lines(self, content: str, filename: str = "") -> PlainTextParseResult:
        """
        Parse plain text treating each line as a separate paragraph.
        
        Args:
            content: Raw plain text content
            filename: Optional filename for error reporting
            
        Returns:
            PlainTextParseResult with line-based structure
        """
        try:
            if content is None:
                content = ""
            
            document = self._split_into_lines(content, filename)
            
            return PlainTextParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            empty_document = PlainTextDocument()
            empty_document.source_file = filename
            return PlainTextParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse plain text as lines: {str(e)}"]
            )
    
    def get_parsing_info(self) -> dict:
        """Get information about the plain text parser."""
        return {
            'parser_type': 'plain_text',
            'default_mode': 'paragraph_based',
            'available_modes': ['paragraph_based', 'line_based'],
            'description': 'Dedicated plain text parser with paragraph detection'
        }
