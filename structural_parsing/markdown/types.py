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
        """
        Get clean text content for rule analysis by stripping inline HTML formatting.
        This prevents false positives in rules when analyzing formatted text.
        """
        content = self.content
        if not content:
            return ""
        
        # Strip HTML inline formatting that comes from Markdown conversion
        # Remove <code>...</code> tags
        content = re.sub(r'<code>(.*?)</code>', r'\1', content)
        
        # Remove <em>...</em> tags (italic)
        content = re.sub(r'<em>(.*?)</em>', r'\1', content)
        
        # Remove <strong>...</strong> tags (bold)
        content = re.sub(r'<strong>(.*?)</strong>', r'\1', content)
        
        # Remove other inline formatting tags
        content = re.sub(r'<mark>(.*?)</mark>', r'\1', content)
        content = re.sub(r'<kbd>(.*?)</kbd>', r'\1', content)
        content = re.sub(r'<var>(.*?)</var>', r'\1', content)
        content = re.sub(r'<samp>(.*?)</samp>', r'\1', content)
        
        return content.strip()
    
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