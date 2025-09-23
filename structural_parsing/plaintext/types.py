"""
Plain Text Structural Parsing Types
Core data structures for plain text document parsing and analysis.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class PlainTextBlockType(Enum):
    DOCUMENT = "document"
    PARAGRAPH = "paragraph"
    EMPTY_LINE = "empty_line"


@dataclass
class PlainTextBlock:
    """Represents a structural block in a plain text document."""
    block_type: PlainTextBlockType
    content: str
    raw_content: str
    start_line: int
    level: int = 0
    children: List['PlainTextBlock'] = field(default_factory=list)
    _analysis_errors: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def should_skip_analysis(self) -> bool:
        """Determines if a block should be skipped during style analysis."""
        return self.block_type == PlainTextBlockType.EMPTY_LINE

    def get_context_info(self) -> Dict[str, Any]:
        """Get contextual information for rule processing."""
        return {
            'block_type': self.block_type.value, 
            'level': self.level,
            'contains_inline_formatting': False  # Plain text has no formatting
        }

    def get_text_content(self) -> str:
        """
        Get clean text content for rule analysis.
        For plain text, this is just the content as-is.
        """
        return self.content.strip()
    
    def has_inline_formatting(self) -> bool:
        """
        Check if this block contains inline formatting.
        Plain text has no inline formatting.
        """
        return False

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
class PlainTextDocument(PlainTextBlock):
    """Represents the entire plain text document as the root block."""
    source_file: Optional[str] = None
    blocks: List[PlainTextBlock] = field(default_factory=list)

    def __init__(self, source_file: Optional[str] = None, blocks: Optional[List[PlainTextBlock]] = None):
        # Initialize parent PlainTextBlock with appropriate values for a document
        super().__init__(
            block_type=PlainTextBlockType.DOCUMENT,
            content="",  # Document content is in its blocks
            raw_content="",  # Will be set by parser if needed
            start_line=1,
            level=0
        )
        self.source_file = source_file
        self.blocks = blocks or []
        self.children = self.blocks


@dataclass
class PlainTextParseResult:
    """Result of a plain text parsing operation."""
    success: bool
    document: Optional[PlainTextDocument] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)
