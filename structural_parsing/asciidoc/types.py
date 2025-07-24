"""
AsciiDoc Structural Parsing Types
Core data structures for AsciiDoc document parsing and analysis.
This version is fully compatible with the existing application structure.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional

# Re-introducing AsciiDocAttributes to maintain compatibility
@dataclass
class AsciiDocAttributes:
    id: Optional[str] = None
    named_attributes: Dict[str, str] = field(default_factory=dict)

class AsciiDocBlockType(Enum):
    DOCUMENT = "document"
    PREAMBLE = "preamble"
    SECTION = "section"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    ORDERED_LIST = "olist"
    UNORDERED_LIST = "ulist"
    DESCRIPTION_LIST = "dlist"
    LIST_ITEM = "list_item"
    SIDEBAR = "sidebar"
    EXAMPLE = "example"
    LISTING = "listing"
    LITERAL = "literal"
    QUOTE = "quote"
    VERSE = "verse"
    PASS = "pass"
    OPEN = "open"
    ADMONITION = "admonition"
    TABLE = "table"
    TABLE_ROW = "table_row"
    TABLE_CELL = "table_cell"
    ATTRIBUTE_ENTRY = "attribute_entry"
    COMMENT = "comment"
    IMAGE = "image"
    UNKNOWN = "unknown"

class AdmonitionType(Enum):
    NOTE = "NOTE"
    TIP = "TIP"
    IMPORTANT = "IMPORTANT"
    WARNING = "WARNING"
    CAUTION = "CAUTION"

@dataclass
class AsciiDocBlock:
    """Represents a single, structured block in an AsciiDoc document (Compatibility Version)."""
    block_type: AsciiDocBlockType
    content: str
    raw_content: str
    start_line: int
    end_line: int = 0
    start_pos: int = 0
    end_pos: int = 0
    level: int = 0
    title: Optional[str] = None
    style: Optional[str] = None
    list_marker: Optional[str] = None
    source_location: str = ""
    parent: Optional['AsciiDocBlock'] = None
    children: List['AsciiDocBlock'] = field(default_factory=list)
    admonition_type: Optional[AdmonitionType] = None
    attributes: AsciiDocAttributes = field(default_factory=AsciiDocAttributes)
    _analysis_errors: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def get_text_content(self) -> str:
        return self.content

    def should_skip_analysis(self) -> bool:
        return self.block_type in [
            AsciiDocBlockType.LISTING, AsciiDocBlockType.LITERAL,
            AsciiDocBlockType.COMMENT, AsciiDocBlockType.PASS,
            AsciiDocBlockType.ATTRIBUTE_ENTRY,
        ]

    def get_context_info(self) -> Dict[str, Any]:
        return {
            'block_type': self.block_type.value, 'level': self.level,
            'admonition_type': self.admonition_type.value if self.admonition_type else None,
            'style': self.style, 'title': self.title, 'list_marker': self.list_marker,
            'source_location': self.source_location
        }

    # CRITICAL FIX: Added the missing to_dict() method
    def to_dict(self) -> Dict[str, Any]:
        """Converts the block to a dictionary for JSON serialization to the UI."""
        return {
            "block_type": self.block_type.value,
            "content": self.content,
            "raw_content": self.raw_content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "level": self.level,
            "title": self.title,
            "style": self.style,
            "admonition_type": self.admonition_type.value if self.admonition_type else None,
            "list_marker": self.list_marker,
            "errors": self._analysis_errors,
            "children": [child.to_dict() for child in self.children]
        }

@dataclass
class AsciiDocDocument(AsciiDocBlock):
    source_file: Optional[str] = None
    blocks: List[AsciiDocBlock] = field(default_factory=list)
    def __post_init__(self):
        self.children = self.blocks

@dataclass
class ParseResult:
    success: bool
    document: Optional[AsciiDocDocument] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)