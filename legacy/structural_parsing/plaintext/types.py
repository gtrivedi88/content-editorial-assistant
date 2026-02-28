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
    start_pos: int = 0
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
        """Get clean text content for rule analysis.

        Delegates to get_text_content_with_source_map() and discards the map.
        """
        text, _ = self.get_text_content_with_source_map()
        return text

    def get_text_content_with_source_map(self):
        """Get clean text content + source map from plain text content.

        Returns (cleaned_text, source_map) where source_map[i] = position in
        content that produced character i in cleaned_text.
        For plain text, this is nearly an identity map (only strip applied).
        """
        from structural_parsing.source_map import SourceMap

        raw = self.content or ""
        if not raw:
            return "", []

        sm = SourceMap(raw)
        sm.strip()
        return sm.result
    
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
            "raw_content": self.raw_content,
            "start_pos": self.start_pos,
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
