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
                    # For tables, skip child token processing since we handle structure manually
                    if block.block_type == MarkdownBlockType.TABLE:
                        # Skip to closing token
                        j = i + 1
                        nesting_level = 1
                        
                        while j < len(tokens) and nesting_level > 0:
                            if tokens[j].nesting == 1:
                                nesting_level += 1
                            elif tokens[j].nesting == -1:
                                nesting_level -= 1
                            j += 1
                        
                        i = j
                    else:
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
        document.children = blocks  # Ensure children is kept in sync with blocks
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
        
        # Extract content from source lines
        content = ""
        raw_content = ""
        
        if token.map and start_line < len(content_lines):
            if end_line <= len(content_lines):
                raw_content = '\n'.join(content_lines[start_line:end_line])
            else:
                raw_content = '\n'.join(content_lines[start_line:])
            
            # For most block types, extract clean content without markup
            if block_type == MarkdownBlockType.HEADING:
                # Remove heading markers (# ## ###) and trailing hashes
                lines = raw_content.split('\n')
                for line in lines:
                    clean_line = line.strip()
                    if clean_line.startswith('#'):
                        # Remove leading hashes
                        content = clean_line.lstrip('#').strip()
                        # Remove trailing hashes if present
                        content = content.rstrip('#').strip()
                        break
            elif block_type == MarkdownBlockType.PARAGRAPH:
                # For paragraphs, use the raw content as-is
                content = raw_content.strip()
            elif block_type == MarkdownBlockType.BLOCKQUOTE:
                # Remove blockquote markers (>)
                lines = raw_content.split('\n')
                clean_lines = []
                for line in lines:
                    clean_line = line.strip()
                    if clean_line.startswith('>'):
                        clean_lines.append(clean_line.lstrip('>').strip())
                    elif clean_line:
                        clean_lines.append(clean_line)
                content = '\n'.join(clean_lines)
            elif block_type in [MarkdownBlockType.CODE_BLOCK]:
                # For code blocks, preserve content but clean fences
                lines = raw_content.split('\n')
                if len(lines) >= 2:
                    # Remove opening and closing fences
                    if lines[0].strip().startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                content = '\n'.join(lines)
            elif block_type == MarkdownBlockType.TABLE:
                # For tables, keep raw content for parsing rows/cells later
                content = raw_content.strip()
            else:
                # For other types, use raw content
                content = raw_content.strip()
        else:
            # Fallback to token content if available
            content = token.content or ''
            raw_content = content
        
        # Create the block
        block = MarkdownBlock(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            start_line=start_line + 1,  # Convert to 1-based indexing
            level=self._get_heading_level(token)
        )
        
        # For tables, parse content and create structured children
        if block_type == MarkdownBlockType.TABLE and content:
            self._parse_table_children(block)
        
        # Set token-specific attributes
        if token.type.startswith('heading_'):
            block.heading_level = self._get_heading_level(token)
        
        if token.type == 'fence':
            block.language = token.info.strip() if token.info else None
        
        return block
    
    def _convert_child_tokens(self, tokens: List[Token], content_lines: List[str]) -> List[MarkdownBlock]:
        """Convert child tokens to blocks, avoiding duplicates for list items."""
        blocks = []
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Skip closing tokens
            if token.nesting == -1:
                i += 1
                continue
            
            # For list items, we want to extract the actual content instead of creating nested paragraphs
            if token.type == 'list_item_open':
                # Find the content within this list item
                j = i + 1
                nesting_level = 1
                item_content = ""
                
                while j < len(tokens) and nesting_level > 0:
                    if tokens[j].nesting == 1:
                        nesting_level += 1
                    elif tokens[j].nesting == -1:
                        nesting_level -= 1
                    
                    # Extract content from inline tokens
                    if tokens[j].type == 'inline':
                        item_content = tokens[j].content
                    
                    j += 1
                
                # Create list item block with extracted content
                start_line = token.map[0] if token.map else 0
                list_item_block = MarkdownBlock(
                    block_type=MarkdownBlockType.LIST_ITEM,
                    content=item_content,
                    raw_content=item_content,
                    start_line=start_line + 1,
                    level=0
                )
                blocks.append(list_item_block)
                i = j
            else:
                # For non-list items, use regular processing
                block = self._create_block_from_token(token, content_lines)
                if block:
                    blocks.append(block)
                i += 1
        
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
            # Removed thead_open and tbody_open to keep tables as single blocks
            # 'thead_open': MarkdownBlockType.TABLE_HEADER,
            # 'tbody_open': MarkdownBlockType.TABLE_BODY,
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
    
    def _parse_table_children(self, table_block: MarkdownBlock) -> None:
        """Parse markdown table content and create structured table_row and table_cell children."""
        lines = table_block.content.split('\n')
        table_lines = []
        
        # Filter out separator lines (like |----------|----------|)
        for line in lines:
            line = line.strip()
            if line and not self._is_table_separator_line(line):
                table_lines.append(line)
        
        # Clear existing children to avoid duplicates
        table_block.children = []
        
        # Parse each table row
        current_line = table_block.start_line
        for line in table_lines:
            if line.startswith('|') and line.endswith('|'):
                # Split by | and clean up cells
                cells = [cell.strip() for cell in line[1:-1].split('|')]
                
                # Create table_row block
                row_block = MarkdownBlock(
                    block_type=MarkdownBlockType.TABLE_ROW,
                    content='',  # Row content is in its children
                    raw_content=line,
                    start_line=current_line,
                    level=0
                )
                
                # Create table_cell blocks for each cell
                for cell_content in cells:
                    cell_block = MarkdownBlock(
                        block_type=MarkdownBlockType.TABLE_CELL,
                        content=cell_content,
                        raw_content=cell_content,
                        start_line=current_line,
                        level=0
                    )
                    row_block.children.append(cell_block)
                
                table_block.children.append(row_block)
            
            current_line += 1
    
    def _is_table_separator_line(self, line: str) -> bool:
        """Check if a line is a table separator (like |----------|----------|)."""
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            return False
        
        # Remove outer pipes and check if it's mostly dashes, colons, and spaces
        content = line[1:-1]
        cells = content.split('|')
        
        for cell in cells:
            cell = cell.strip()
            # A separator cell should only contain -, :, and spaces
            if not all(c in '-: ' for c in cell) or not cell:
                return False
            # Should have at least some dashes
            if '-' not in cell:
                return False
        
        return True 