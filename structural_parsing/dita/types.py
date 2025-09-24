"""
DITA Structural Parsing Types
Core data structures for DITA document parsing and analysis.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional


class DITATopicType(Enum):
    """DITA topic types."""
    CONCEPT = "concept"
    TASK = "task"
    REFERENCE = "reference"
    TROUBLESHOOTING = "troubleshooting"
    TOPIC = "topic"  # Generic topic
    MAP = "map"  # DITA map


class DITABlockType(Enum):
    """DITA block types for structural parsing."""
    DOCUMENT = "document"
    TITLE = "title"
    SHORTDESC = "shortdesc"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    EXAMPLE = "example"
    
    # Task-specific blocks
    PREREQ = "prereq"
    CONTEXT = "context"
    STEPS = "steps"
    STEP = "step"
    CMD = "cmd"
    INFO = "info"
    STEPRESULT = "stepresult"
    RESULT = "result"
    
    # Reference-specific blocks
    REFBODY = "refbody"
    PROPERTIES = "properties"
    PROPERTY = "property"
    
    # Lists
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"
    LIST_ITEM = "list_item"
    
    # Code and technical content
    CODEBLOCK = "codeblock"
    CODEPH = "codeph"  # Inline code
    
    # Notes and admonitions
    NOTE = "note"
    
    # Tables
    TABLE = "table"
    SIMPLETABLE = "simpletable"
    
    # Specialized lists
    SIMPLE_LIST = "simple_list"
    DEFINITION_LIST = "definition_list"
    PARAMETER_LIST = "parameter_list"
    
    # Technical elements
    FILEPATH = "filepath"
    CMDNAME = "cmdname"
    VARNAME = "varname"
    APINAME = "apiname"
    UICONTROL = "uicontrol"
    WINTITLE = "wintitle"
    MENUCASCADE = "menucascade"
    
    # Programming elements
    SYNTAXDIAGRAM = "syntaxdiagram"
    CODEREF = "coderef"
    
    # Task-specific additions
    POSTREQ = "postreq"
    SUBSTEPS = "substeps"
    SUBSTEP = "substep"
    CHOICES = "choices"
    CHOICE = "choice"
    TROUBLESHOOTING = "troubleshooting"
    
    # Generic containers
    BODY = "body"  # For conbody, taskbody, refbody, etc.
    UNKNOWN = "unknown"  # For unrecognized elements


@dataclass
class DITABlock:
    """Represents a structural block in a DITA document."""
    block_type: DITABlockType
    content: str
    raw_content: str
    start_line: int
    level: int = 0
    topic_type: Optional[DITATopicType] = None
    element_name: Optional[str] = None  # Original XML element name
    attributes: Dict[str, str] = field(default_factory=dict)
    children: List['DITABlock'] = field(default_factory=list)
    _analysis_errors: List[Dict[str, Any]] = field(default_factory=list, repr=False)

    def should_skip_analysis(self) -> bool:
        """Determines if a block should be skipped during style analysis."""
        return self.block_type in [
            DITABlockType.CODEBLOCK,
            DITABlockType.CODEPH
        ]

    def get_context_info(self) -> Dict[str, Any]:
        """Get contextual information for rule processing."""
        return {
            'block_type': self.block_type.value,
            'level': self.level,
            'topic_type': self.topic_type.value if self.topic_type else None,
            'element_name': self.element_name,
            'contains_inline_formatting': self.has_inline_formatting(),
            'attributes': self.attributes
        }

    def get_text_content(self) -> str:
        """
        Get clean text content for rule analysis.
        Strips XML tags and normalizes whitespace.
        """
        content = self.content
        if not content:
            return ""
        
        # Remove any remaining XML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def has_inline_formatting(self) -> bool:
        """
        Check if this block contains inline formatting.
        DITA has various inline elements.
        """
        if not self.content:
            return False
            
        # Check for DITA inline elements
        inline_patterns = [
            r'<b>.*?</b>',
            r'<i>.*?</i>',
            r'<u>.*?</u>',
            r'<codeph>.*?</codeph>',
            r'<term>.*?</term>',
            r'<keyword>.*?</keyword>',
            r'<xref.*?>.*?</xref>',
            r'<link.*?>.*?</link>'
        ]
        
        return any(re.search(pattern, self.content) for pattern in inline_patterns)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the block to a dictionary for JSON serialization."""
        return {
            "block_type": self.block_type.value,
            "content": self.content,
            "level": self.level,
            "topic_type": self.topic_type.value if self.topic_type else None,
            "element_name": self.element_name,
            "attributes": self.attributes,
            "should_skip_analysis": self.should_skip_analysis(),
            "errors": self._analysis_errors,
            "children": [child.to_dict() for child in self.children]
        }


@dataclass
class DITADocument(DITABlock):
    """Represents the entire DITA document as the root block."""
    source_file: Optional[str] = None
    topic_type: Optional[DITATopicType] = None
    topic_id: Optional[str] = None
    blocks: List[DITABlock] = field(default_factory=list)

    def __init__(self, source_file: Optional[str] = None, 
                 topic_type: Optional[DITATopicType] = None,
                 topic_id: Optional[str] = None,
                 blocks: Optional[List[DITABlock]] = None):
        # Initialize parent DITABlock with appropriate values for a document
        super().__init__(
            block_type=DITABlockType.DOCUMENT,
            content="",  # Document content is in its blocks
            raw_content="",  # Will be set by parser if needed
            start_line=1,
            level=0,
            topic_type=topic_type
        )
        self.source_file = source_file
        self.topic_type = topic_type
        self.topic_id = topic_id
        self.blocks = blocks or []
        self.children = self.blocks
    
    def get_all_blocks_flat(self) -> List[DITABlock]:
        """Get all blocks in document as a flattened list."""
        all_blocks = []
        
        def collect_blocks(block):
            all_blocks.append(block)
            for child in block.children:
                collect_blocks(child)
        
        for block in self.blocks:
            collect_blocks(block)
        
        return all_blocks


@dataclass
class DITAParseResult:
    """Result of a DITA parsing operation."""
    success: bool
    document: Optional[DITADocument] = None
    topic_type: Optional[DITATopicType] = None
    error: Optional[str] = None
    errors: List[str] = field(default_factory=list)
