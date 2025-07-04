"""
Markdown structural parser using markdown-it-py library.
This parser uses markdown-it-py for robust CommonMark-compliant parsing.
"""

from markdown_it import MarkdownIt
from markdown_it.token import Token
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .types import (
    MarkdownDocument,
    MarkdownBlock,
    MarkdownBlockType,
    MarkdownParseResult
)


class MarkdownParser:
    """
    Markdown parser using markdown-it-py library.
    
    This parser delegates all parsing to markdown-it-py for maximum
    CommonMark compliance and robustness.
    """
    
    def __init__(self):
        # Initialize markdown-it with CommonMark preset
        self.md = MarkdownIt('commonmark', {
            'html': True,
            'xhtmlOut': True,
            'breaks': False,
            'langPrefix': 'language-',
            'linkify': True,
            'typographer': True
        })
        
        # Enable useful plugins
        self.md.enable(['table', 'strikethrough'])
    
    def parse(self, content: str, filename: str = "") -> MarkdownParseResult:
        """
        Parse Markdown content into structural blocks.
        
        Args:
            content: Raw Markdown content
            filename: Optional filename for error reporting
            
        Returns:
            MarkdownParseResult with document structure
        """
        try:
            # Parse using markdown-it-py
            tokens = self.md.parse(content)
            
            # Convert tokens to our internal structure
            document = self._convert_tokens_to_blocks(tokens, content, filename)
            
            return MarkdownParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            # Create empty document for error case
            empty_document = MarkdownDocument()
            empty_document.source_file = filename
            return MarkdownParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse Markdown: {str(e)}"]
            )
    
    def _convert_tokens_to_blocks(self, tokens: List[Token], content: str, filename: str) -> MarkdownDocument:
        """
        Convert markdown-it tokens to internal block structure.
        
        Args:
            tokens: List of markdown-it tokens
            content: Original content for position calculation
            filename: Source filename
            
        Returns:
            MarkdownDocument with structured blocks
        """
        blocks = []
        content_lines = content.split('\n')
        
        # Process tokens into blocks
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Skip closing tokens - we handle them with their opening tokens
            if token.nesting == -1:
                i += 1
                continue
            
            block = self._create_block_from_token(token, content_lines)
            
            if block:
                # Handle nested tokens for container blocks
                if token.nesting == 1:
                    # Find matching closing token
                    j = i + 1
                    nesting_level = 1
                    child_tokens = []
                    
                    while j < len(tokens) and nesting_level > 0:
                        if tokens[j].nesting == 1:
                            nesting_level += 1
                        elif tokens[j].nesting == -1:
                            nesting_level -= 1
                        
                        if nesting_level > 0:
                            child_tokens.append(tokens[j])
                        j += 1
                    
                    # Convert child tokens to child blocks
                    if child_tokens:
                        child_blocks = self._convert_child_tokens(child_tokens, content_lines)
                        block.children.extend(child_blocks)
                    
                    i = j
                else:
                    i += 1
                
                blocks.append(block)
            else:
                i += 1
        
        document = MarkdownDocument()
        document.source_file = filename
        document.blocks = blocks
        return document
    
    def _create_block_from_token(self, token: Token, content_lines: List[str]) -> Optional[MarkdownBlock]:
        """
        Create a MarkdownBlock from a markdown-it token.
        
        Args:
            token: markdown-it token
            content_lines: Original content split by lines
            
        Returns:
            MarkdownBlock or None if token should be skipped
        """
        # Map token types to our block types
        block_type = self._map_token_type(token.type)
        
        if not block_type:
            return None
        
        # Calculate positions
        start_line = token.map[0] if token.map else 0
        end_line = token.map[1] if token.map else start_line + 1
        
        # Extract content
        if token.map and start_line < len(content_lines):
            if end_line <= len(content_lines):
                raw_content = '\n'.join(content_lines[start_line:end_line])
            else:
                raw_content = '\n'.join(content_lines[start_line:])
        else:
            raw_content = token.content or ''
        
        # Create the block
        block = MarkdownBlock(
            block_type=block_type,
            content=token.content or '',
            raw_content=raw_content,
            start_line=start_line + 1,  # Convert to 1-based indexing
            end_line=end_line,
            start_pos=0,  # Would need more complex calculation
            end_pos=len(raw_content),
            level=self._get_heading_level(token),
            children=[]
        )
        
        # Set token-specific attributes
        if token.type.startswith('heading_'):
            block.heading_level = self._get_heading_level(token)
        
        if token.type == 'fence':
            block.language = token.info.strip() if token.info else None
        
        return block
    
    def _convert_child_tokens(self, tokens: List[Token], content_lines: List[str]) -> List[MarkdownBlock]:
        """Convert child tokens to blocks."""
        blocks = []
        
        for token in tokens:
            if token.nesting != -1:  # Skip closing tokens
                block = self._create_block_from_token(token, content_lines)
                if block:
                    blocks.append(block)
        
        return blocks
    
    def _map_token_type(self, token_type: str) -> Optional[MarkdownBlockType]:
        """Map markdown-it token type to our block type."""
        type_mapping = {
            'heading_open': MarkdownBlockType.HEADING,
            'paragraph_open': MarkdownBlockType.PARAGRAPH,
            'blockquote_open': MarkdownBlockType.BLOCKQUOTE,
            'bullet_list_open': MarkdownBlockType.UNORDERED_LIST,
            'ordered_list_open': MarkdownBlockType.ORDERED_LIST,
            'list_item_open': MarkdownBlockType.LIST_ITEM,
            'table_open': MarkdownBlockType.TABLE,
            'thead_open': MarkdownBlockType.TABLE_HEADER,
            'tbody_open': MarkdownBlockType.TABLE_BODY,
            'tr_open': MarkdownBlockType.TABLE_ROW,
            'td_open': MarkdownBlockType.TABLE_CELL,
            'th_open': MarkdownBlockType.TABLE_CELL,
            'code_block': MarkdownBlockType.CODE_BLOCK,
            'fence': MarkdownBlockType.CODE_BLOCK,
            'hr': MarkdownBlockType.HORIZONTAL_RULE,
            'html_block': MarkdownBlockType.HTML_BLOCK,
        }
        
        return type_mapping.get(token_type)
    
    def _get_heading_level(self, token: Token) -> int:
        """Extract heading level from token."""
        if token.type == 'heading_open':
            return int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
        return 0 