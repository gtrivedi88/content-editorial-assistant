"""
AsciiDoc Structural Parsing Types
Core data structures for AsciiDoc document parsing and analysis.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union
import json


class AsciiDocBlockType(Enum):
    """Types of structural blocks in AsciiDoc documents."""
    
    # Document structure
    DOCUMENT = "document"
    PREAMBLE = "preamble"
    SECTION = "section"
    
    # Content blocks
    PARAGRAPH = "paragraph"
    
    # Headings
    HEADING = "heading"
    
    # Lists
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    DESCRIPTION_LIST = "description_list"
    LIST_ITEM = "list_item"
    
    # Delimited blocks
    SIDEBAR = "sidebar"          # ****
    EXAMPLE = "example"          # ====
    LISTING = "listing"          # ----
    LITERAL = "literal"          # ....
    QUOTE = "quote"              # ____
    VERSE = "verse"              # [verse]
    PASS = "pass"                # ++++
    OPEN = "open"                # --
    
    # Admonitions
    ADMONITION = "admonition"    # [NOTE], [TIP], [IMPORTANT], [WARNING], [CAUTION]
    
    # Tables
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    
    # Media and references
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    
    # Inline elements
    INLINE_QUOTED = "inline_quoted"
    INLINE_ANCHOR = "inline_anchor"
    INLINE_IMAGE = "inline_image"
    
    # Document attributes and metadata
    ATTRIBUTE_ENTRY = "attribute_entry"
    COMMENT = "comment"
    
    # Special blocks
    TOC = "toc"
    PAGE_BREAK = "page_break"
    THEMATIC_BREAK = "thematic_break"


class AdmonitionType(Enum):
    """Types of AsciiDoc admonitions."""
    NOTE = "NOTE"
    TIP = "TIP"
    IMPORTANT = "IMPORTANT"
    WARNING = "WARNING"
    CAUTION = "CAUTION"


@dataclass
class AsciiDocAttributes:
    """Represents AsciiDoc block attributes."""
    id: Optional[str] = None
    role: Optional[str] = None
    options: List[str] = field(default_factory=list)
    named_attributes: Dict[str, str] = field(default_factory=dict)
    positional_attributes: List[str] = field(default_factory=list)
    
    def has_option(self, option: str) -> bool:
        """Check if a specific option is set."""
        return option in self.options
    
    def get_attribute(self, name: str, default: Any = None) -> Any:
        """Get a named attribute value."""
        return self.named_attributes.get(name, default)


@dataclass
class AsciiDocBlock:
    """Represents a structural block in an AsciiDoc document."""
    
    # Core identification
    block_type: AsciiDocBlockType
    content: str
    raw_content: str
    
    # Document position
    start_line: int
    end_line: int
    start_pos: int
    end_pos: int
    
    # Structure and hierarchy
    level: int = 0
    parent: Optional['AsciiDocBlock'] = None
    children: List['AsciiDocBlock'] = field(default_factory=list)
    
    # AsciiDoc-specific metadata
    attributes: AsciiDocAttributes = field(default_factory=AsciiDocAttributes)
    title: Optional[str] = None
    style: Optional[str] = None
    
    # Content-specific data
    admonition_type: Optional[AdmonitionType] = None
    list_marker: Optional[str] = None
    
    # Document metadata
    source_location: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.children is None:
            self.children = []
    
    def add_child(self, child: 'AsciiDocBlock'):
        """Add a child block."""
        child.parent = self
        self.children.append(child)
    
    def remove_child(self, child: 'AsciiDocBlock'):
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
        # Determine specific block type based on context
        block_type = self.block_type.value
        
        # For list items, provide more specific context based on parent
        if self.block_type == AsciiDocBlockType.LIST_ITEM and self.parent:
            if self.parent.block_type == AsciiDocBlockType.ORDERED_LIST:
                block_type = 'list_item_ordered'
            elif self.parent.block_type == AsciiDocBlockType.UNORDERED_LIST:
                block_type = 'list_item_unordered'
        
        return {
            'block_type': block_type,
            'level': self.level,
            'title': self.title,
            'style': self.style,
            'attributes': {
                'id': self.attributes.id,
                'role': self.attributes.role,
                'options': self.attributes.options,
                'named': self.attributes.named_attributes,
                'positional': self.attributes.positional_attributes
            },
            'admonition_type': self.admonition_type.value if self.admonition_type else None,
            'list_marker': self.list_marker,
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
            AsciiDocBlockType.PARAGRAPH,
            AsciiDocBlockType.HEADING,
            AsciiDocBlockType.ADMONITION,
            AsciiDocBlockType.QUOTE,
            AsciiDocBlockType.VERSE,
            AsciiDocBlockType.SIDEBAR,
            AsciiDocBlockType.EXAMPLE,
            AsciiDocBlockType.LIST_ITEM
        }
        return self.block_type in content_blocks
    
    def should_skip_analysis(self) -> bool:
        """Check if this block should be skipped during style analysis."""
        skip_blocks = {
            AsciiDocBlockType.LISTING,
            AsciiDocBlockType.LITERAL,
            AsciiDocBlockType.PASS,
            AsciiDocBlockType.COMMENT,
            AsciiDocBlockType.ATTRIBUTE_ENTRY,
            AsciiDocBlockType.TOC,
            AsciiDocBlockType.PAGE_BREAK,
            AsciiDocBlockType.THEMATIC_BREAK
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
            'title': self.title,
            'style': self.style,
            'admonition_type': self.admonition_type.value if self.admonition_type else None,
            'attributes': {
                'id': self.attributes.id,
                'role': self.attributes.role,
                'options': self.attributes.options,
                'named': self.attributes.named_attributes
            },
            'children_count': len(self.children)
        }


@dataclass
class AsciiDocDocument:
    """Represents a complete AsciiDoc document structure."""
    
    blocks: List[AsciiDocBlock] = field(default_factory=list)
    attributes: Dict[str, str] = field(default_factory=dict)
    title: Optional[str] = None
    source_file: Optional[str] = None
    
    def get_blocks_by_type(self, block_type: AsciiDocBlockType) -> List[AsciiDocBlock]:
        """Get all blocks of a specific type."""
        result = []
        for block in self.blocks:
            if block.block_type == block_type:
                result.append(block)
            # Recursively search children
            result.extend(self._get_blocks_by_type_recursive(block.children, block_type))
        return result
    
    def _get_blocks_by_type_recursive(self, blocks: List[AsciiDocBlock], 
                                    block_type: AsciiDocBlockType) -> List[AsciiDocBlock]:
        """Recursively search for blocks of a specific type."""
        result = []
        for block in blocks:
            if block.block_type == block_type:
                result.append(block)
            result.extend(self._get_blocks_by_type_recursive(block.children, block_type))
        return result
    
    def get_content_blocks(self) -> List[AsciiDocBlock]:
        """Get all blocks that contain analyzable content."""
        result = []
        for block in self.blocks:
            if block.is_content_block():
                result.append(block)
            result.extend(self._get_content_blocks_recursive(block.children))
        return result
    
    def _get_content_blocks_recursive(self, blocks: List[AsciiDocBlock]) -> List[AsciiDocBlock]:
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
            'attributes_count': len(self.attributes),
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
    
    def _get_all_blocks_flat(self) -> List[AsciiDocBlock]:
        """Get all blocks in a flat list."""
        result = []
        for block in self.blocks:
            result.append(block)
            result.extend(self._get_all_blocks_flat_recursive(block.children))
        return result
    
    def _get_all_blocks_flat_recursive(self, blocks: List[AsciiDocBlock]) -> List[AsciiDocBlock]:
        """Recursively get all blocks."""
        result = []
        for block in blocks:
            result.append(block)
            result.extend(self._get_all_blocks_flat_recursive(block.children))
        return result


class ParseResult:
    """Result of AsciiDoc parsing operation."""
    
    def __init__(self, document: AsciiDocDocument, success: bool = True, 
                 errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.document = document
        self.success = success
        self.errors = errors or []
        self.warnings = warnings or []
        self.parsing_method = "asciidoctor"
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