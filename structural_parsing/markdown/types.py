"""
Markdown Structural Parsing Types
Core data structures for Markdown document parsing and analysis.
This version includes compatibility methods to align with the AsciiDoc parser.
"""
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
        return {'block_type': self.block_type.value, 'level': self.level}

    def get_text_content(self) -> str:
        """Returns the primary text content of the block for analysis."""
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        """Converts the block to a dictionary for JSON serialization."""
        return {
            "block_type": self.block_type.value,
            "content": self.content,
            "level": self.level,
            "errors": self._analysis_errors,
            "children": [child.to_dict() for child in self.children]
        }

@dataclass
class MarkdownDocument(MarkdownBlock):
    """Represents the entire Markdown document as the root block."""
    source_file: Optional[str] = None
    blocks: List[MarkdownBlock] = field(default_factory=list)

    def __post_init__(self):
        self.children = self.blocks

@dataclass
class MarkdownParseResult:
    """Result of a Markdown parsing operation."""
    success: bool
    document: Optional[MarkdownDocument] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)