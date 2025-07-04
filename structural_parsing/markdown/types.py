"""
Markdown Structural Parsing Types
Core data structures for Markdown document parsing and analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import json


class MarkdownBlockType(Enum):
    """Types of structural blocks in Markdown documents."""
    
    # Document structure
    DOCUMENT = "document"
    
    # Headings
    HEADING = "heading"
    
    # Content blocks
    PARAGRAPH = "paragraph"
    BLOCKQUOTE = "blockquote"
    
    # Lists
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    LIST_ITEM = "list_item"
    
    # Code blocks
    CODE_BLOCK = "code_block"
    INLINE_CODE = "inline_code"
    
    # Tables
    TABLE = "table"
    TABLE_HEADER = "table_header"
    TABLE_BODY = "table_body"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    
    # Media
    IMAGE = "image"
    LINK = "link"
    
    # Formatting
    EMPHASIS = "emphasis"
    STRONG = "strong"
    STRIKETHROUGH = "strikethrough"
    
    # Other elements
    HORIZONTAL_RULE = "horizontal_rule"
    HTML_BLOCK = "html_block"
    HTML_INLINE = "html_inline"
    
    # Line breaks
    SOFTBREAK = "softbreak"
    HARDBREAK = "hardbreak"


@dataclass
class MarkdownBlock:
    """Represents a structural block in a Markdown document."""
    
    # Core identification
    block_type: MarkdownBlockType
    content: str
    raw_content: str
    
    # Document position
    start_line: int
    end_line: int
    start_pos: int
    end_pos: int
    
    # Structure and hierarchy
    level: int = 0
    parent: Optional['MarkdownBlock'] = None
    children: List['MarkdownBlock'] = field(default_factory=list)
    
    # Markdown-specific metadata
    heading_level: int = 0
    language: Optional[str] = None  # For code blocks
    url: Optional[str] = None  # For links and images
    title: Optional[str] = None  # For links and images
    alt_text: Optional[str] = None  # For images
    
    # List metadata
    list_marker: Optional[str] = None
    list_tight: bool = True
    
    # Table metadata
    table_alignment: Optional[str] = None
    
    # Document metadata
    source_location: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.children is None:
            self.children = []
    
    def add_child(self, child: 'MarkdownBlock'):
        """Add a child block."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'MarkdownBlock'):
        """Remove a child block."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)
    
    def get_text_content(self) -> str:
        """Get clean text content without markup."""
        return self.content.strip()
    
    def get_all_text(self) -> str:
        """Get all text content including children."""
        text_parts = [self.get_text_content()]
        for child in self.children:
            child_text = child.get_all_text()
            if child_text:
                text_parts.append(child_text)
        return '\n'.join(part for part in text_parts if part)
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get contextual information for rule processing."""
        return {
            'block_type': self.block_type.value,
            'level': self.level,
            'heading_level': self.heading_level,
            'language': self.language,
            'url': self.url,
            'title': self.title,
            'alt_text': self.alt_text,
            'list_marker': self.list_marker,
            'list_tight': self.list_tight,
            'table_alignment': self.table_alignment,
            'parent_type': self.parent.block_type.value if self.parent else None,
            'has_children': len(self.children) > 0,
            'children_count': len(self.children),
            'position': {
                'start_line': self.start_line,
                'end_line': self.end_line,
                'start_pos': self.start_pos,
                'end_pos': self.end_pos
            },
            'source_location': self.source_location
        }
    
    def is_content_block(self) -> bool:
        """Check if this block contains analyzable content."""
        content_blocks = {
            MarkdownBlockType.PARAGRAPH,
            MarkdownBlockType.HEADING,
            MarkdownBlockType.BLOCKQUOTE,
            MarkdownBlockType.LIST_ITEM,
            MarkdownBlockType.TABLE_CELL
        }
        return self.block_type in content_blocks
    
    def should_skip_analysis(self) -> bool:
        """Check if this block should be skipped during style analysis."""
        skip_blocks = {
            MarkdownBlockType.CODE_BLOCK,
            MarkdownBlockType.INLINE_CODE,
            MarkdownBlockType.HTML_BLOCK,
            MarkdownBlockType.HTML_INLINE,
            MarkdownBlockType.HORIZONTAL_RULE,
            MarkdownBlockType.SOFTBREAK,
            MarkdownBlockType.HARDBREAK
        }
        return self.block_type in skip_blocks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'block_type': self.block_type.value,
            'content': self.content,
            'start_line': self.start_line,
            'end_line': self.end_line,
            'level': self.level,
            'heading_level': self.heading_level,
            'language': self.language,
            'url': self.url,
            'title': self.title,
            'alt_text': self.alt_text,
            'list_marker': self.list_marker,
            'children_count': len(self.children)
        }


@dataclass
class MarkdownDocument:
    """Represents a complete Markdown document structure."""
    
    blocks: List[MarkdownBlock] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    title: Optional[str] = None
    source_file: Optional[str] = None
    
    def get_blocks_by_type(self, block_type: MarkdownBlockType) -> List[MarkdownBlock]:
        """Get all blocks of a specific type."""
        result = []
        for block in self.blocks:
            if block.block_type == block_type:
                result.append(block)
            # Recursively search children
            result.extend(self._get_blocks_by_type_recursive(block.children, block_type))
        return result
    
    def _get_blocks_by_type_recursive(self, blocks: List[MarkdownBlock], 
                                    block_type: MarkdownBlockType) -> List[MarkdownBlock]:
        """Recursively search for blocks of a specific type."""
        result = []
        for block in blocks:
            if block.block_type == block_type:
                result.append(block)
            result.extend(self._get_blocks_by_type_recursive(block.children, block_type))
        return result
    
    def get_content_blocks(self) -> List[MarkdownBlock]:
        """Get all blocks that contain analyzable content."""
        result = []
        for block in self.blocks:
            if block.is_content_block():
                result.append(block)
            result.extend(self._get_content_blocks_recursive(block.children))
        return result
    
    def _get_content_blocks_recursive(self, blocks: List[MarkdownBlock]) -> List[MarkdownBlock]:
        """Recursively get content blocks."""
        result = []
        for block in blocks:
            if block.is_content_block():
                result.append(block)
            result.extend(self._get_content_blocks_recursive(block.children))
        return result
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics."""
        stats = {
            'total_blocks': len(self.blocks),
            'content_blocks': len(self.get_content_blocks()),
            'metadata_count': len(self.metadata),
            'document_title': self.title,
            'source_file': self.source_file,
            'block_type_counts': {}
        }
        
        # Count blocks by type
        all_blocks = self._get_all_blocks_flat()
        for block in all_blocks:
            block_type = block.block_type.value
            stats['block_type_counts'][block_type] = stats['block_type_counts'].get(block_type, 0) + 1
        
        return stats
    
    def _get_all_blocks_flat(self) -> List[MarkdownBlock]:
        """Get all blocks in a flat list."""
        result = []
        for block in self.blocks:
            result.append(block)
            result.extend(self._get_all_blocks_flat_recursive(block.children))
        return result
    
    def _get_all_blocks_flat_recursive(self, blocks: List[MarkdownBlock]) -> List[MarkdownBlock]:
        """Recursively get all blocks."""
        result = []
        for block in blocks:
            result.append(block)
            result.extend(self._get_all_blocks_flat_recursive(block.children))
        return result


class MarkdownParseResult:
    """Result of Markdown parsing operation."""
    
    def __init__(self, document: MarkdownDocument, success: bool = True, 
                 errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.document = document
        self.success = success
        self.errors = errors or []
        self.warnings = warnings or []
        self.parsing_method = "markdown-it-py"
        self.parsing_time = 0.0
    
    def add_error(self, error: str):
        """Add a parsing error."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Add a parsing warning."""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            'success': self.success,
            'errors': self.errors,
            'warnings': self.warnings,
            'parsing_method': self.parsing_method,
            'parsing_time': self.parsing_time,
            'document_stats': self.document.get_document_statistics(),
            'blocks_count': len(self.document.blocks),
            'content_blocks_count': len(self.document.get_content_blocks())
        } 