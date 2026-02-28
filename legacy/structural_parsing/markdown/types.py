"""
Markdown Structural Parsing Types
Core data structures for Markdown document parsing and analysis.
This version includes compatibility methods to align with the AsciiDoc parser.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

class MarkdownBlockType(Enum):
    DOCUMENT = "document"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BLOCKQUOTE = "blockquote"
    ORDERED_LIST = "ordered_list"
    UNORDERED_LIST = "unordered_list"
    LIST_ITEM = "list_item"
    CODE_BLOCK = "code_block"
    INLINE_CODE = "inline_code"
    TABLE = "table"
    TABLE_HEADER = "table_header"
    TABLE_BODY = "table_body"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    HORIZONTAL_RULE = "horizontal_rule"
    HTML_BLOCK = "html_block"

@dataclass
class MarkdownBlock:
    """Represents a structural block in a Markdown document."""
    block_type: MarkdownBlockType
    content: str
    raw_content: str
    start_line: int
    level: int = 0
    start_pos: int = 0
    children: List['MarkdownBlock'] = field(default_factory=list)
    _analysis_errors: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    # COMPATIBILITY FIX: Added method to match the AsciiDocBlock interface.
    def should_skip_analysis(self) -> bool:
        """Determines if a block should be skipped during style analysis."""
        return self.block_type in [MarkdownBlockType.CODE_BLOCK, MarkdownBlockType.INLINE_CODE, MarkdownBlockType.HTML_BLOCK]

    # COMPATIBILITY FIX: Added method to match the AsciiDocBlock interface.
    def get_context_info(self) -> Dict[str, Any]:
        """Get contextual information for rule processing."""
        return {
            'block_type': self.block_type.value, 
            'level': self.level,
            'contains_inline_formatting': self.has_inline_formatting()
        }

    def get_text_content(self) -> str:
        """Get clean text content for rule analysis.

        Delegates to get_text_content_with_source_map() and discards the map.
        """
        text, _ = self.get_text_content_with_source_map()
        return text

    def get_text_content_with_source_map(self):
        """Get clean text content + source map from raw Markdown content.

        Returns (cleaned_text, source_map) where source_map[i] = position in
        raw_content that produced character i in cleaned_text.
        """
        from structural_parsing.source_map import SourceMap

        raw = self.raw_content or self.content or ""
        if not raw:
            return "", []

        sm = SourceMap(raw)

        # Strip bold: **text** → text
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        # Strip bold: __text__ → text
        sm.apply_sub(r'__(.+?)__', r'\1')
        # Strip italic: *text* → text (not preceded/followed by *)
        sm.apply_sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'\1')
        # Strip italic: _text_ → text (not preceded/followed by _)
        sm.apply_sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'\1')
        # Strip inline code: `text` → text
        sm.apply_sub(r'`([^`]+)`', r'\1')
        # Strip links: [text](url) → text
        sm.apply_sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1')
        # Strip images: ![alt](url) → alt
        sm.apply_sub(r'!\[([^\]]*)\]\([^\)]*\)', r'\1')
        # Remove email addresses
        sm.apply_delete(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # Remove standalone URLs
        sm.apply_delete(r'https?://[^\s\[\]]+')
        # Clean up whitespace
        sm.collapse_spaces()
        sm.strip()

        return sm.result
    
    def has_inline_formatting(self) -> bool:
        """
        Check if this block contains inline formatting that was stripped.
        This helps rules understand the original formatting context.
        """
        if not self.content:
            return False
            
        # Check for common inline formatting patterns
        formatting_patterns = [
            r'<code>.*?</code>',
            r'<em>.*?</em>', 
            r'<strong>.*?</strong>',
            r'<mark>.*?</mark>',
            r'<kbd>.*?</kbd>',
            r'<var>.*?</var>',
            r'<samp>.*?</samp>'
        ]
        
        return any(re.search(pattern, self.content) for pattern in formatting_patterns)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the block to a dictionary for JSON serialization."""
        return {
            "block_type": self.block_type.value,
            "content": self.content,
            "raw_content": self.raw_content,
            "start_pos": self.start_pos,
            "level": self.level,
            "should_skip_analysis": self.should_skip_analysis(),
            "errors": self._analysis_errors,
            "children": [child.to_dict() for child in self.children]
        }

@dataclass
class MarkdownDocument(MarkdownBlock):
    """Represents the entire Markdown document as the root block."""
    source_file: Optional[str] = None
    blocks: List[MarkdownBlock] = field(default_factory=list)

    def __init__(self, source_file: Optional[str] = None, blocks: Optional[List[MarkdownBlock]] = None):
        # Initialize parent MarkdownBlock with appropriate values for a document
        super().__init__(
            block_type=MarkdownBlockType.DOCUMENT,
            content="",  # Document content is in its blocks
            raw_content="",  # Will be set by parser if needed
            start_line=1,
            level=0
        )
        self.source_file = source_file
        self.blocks = blocks or []
        self.children = self.blocks

@dataclass
class MarkdownParseResult:
    """Result of a Markdown parsing operation."""
    success: bool
    document: Optional[MarkdownDocument] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)