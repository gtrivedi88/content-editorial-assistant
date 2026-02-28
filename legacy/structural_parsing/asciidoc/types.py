"""
AsciiDoc Structural Parsing Types
Core data structures for AsciiDoc document parsing and analysis.
This version is fully compatible with the existing application structure.
"""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union

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
    # **FIX**: Changed from DESCRIPTION_LIST to DLIST to match Asciidoctor context
    DLIST = "dlist"
    # **NEW**: Added to represent a term/description pair in a dlist.
    DESCRIPTION_LIST_ITEM = "description_list_item"
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
    MACRO = "macro"
    INCLUDE = "include"
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

    # **NEW**: Fields to hold definition list term and description
    term: Optional[str] = None
    description: Optional[str] = None

    def get_text_content(self) -> str:
        """Get clean text content for rule analysis.

        Delegates to get_text_content_with_source_map() and discards the map.
        """
        text, _ = self.get_text_content_with_source_map()
        return text

    def get_text_content_with_source_map(self):
        """Get clean text content + source map from raw AsciiDoc content.

        Returns (cleaned_text, source_map) where source_map[i] = position in
        raw_content that produced character i in cleaned_text.

        Operates on raw_content (raw AsciiDoc markup) so the source map
        directly targets what the editor displays.
        """
        from structural_parsing.source_map import SourceMap

        if self.block_type == AsciiDocBlockType.DESCRIPTION_LIST_ITEM:
            raw = self.description or ""
        else:
            # Use raw_content only — never fall back to self.content (rendered HTML).
            # Container blocks (admonition, example, etc.) have empty raw_content;
            # their children hold the actual content and are analyzed separately.
            raw = self.raw_content or ""

        if not raw:
            return "", []

        sm = SourceMap(raw)

        # Strip AsciiDoc heading marker: = Title → Title, == Subtitle → Subtitle
        sm.apply_sub(r'^(={1,6})\s+', '')
        # Strip AsciiDoc block title marker: .Title → Title
        sm.apply_sub(r'^\.(?=\S)', '')

        # Strip AsciiDoc bold: **text** → text
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        # Strip AsciiDoc italic (unconstrained): __text__ → text
        sm.apply_sub(r'__(.+?)__', r'\1')
        # Strip backtick monospace: `text` → text
        sm.apply_sub(r'`([^`]+)`', r'\1')
        # Strip plus monospace (word-boundary aware): +text+ → text
        sm.apply_sub(r'(?<!\w)\+([^+]+)\+(?!\w)', r'\1')
        # Strip xref macro: xref:target[text] → text
        sm.apply_sub(r'xref:[^\[]+\[([^\]]*)\]', r'\1')
        # Strip link macro: link:URL[text] → text
        sm.apply_sub(r'link:https?://[^\s\[\]]+\[([^\]]*)\]', r'\1')
        # Strip mailto macro: mailto:email[text] → text
        sm.apply_sub(r'mailto:[^\[]+\[([^\]]*)\]', r'\1')
        # Replace AsciiDoc attributes {like-this} with placeholder
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        # Remove email addresses
        sm.apply_delete(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # Remove standalone URLs
        sm.apply_delete(r'https?://[^\s\[\]]+')
        # Clean up whitespace artifacts
        sm.clean_space_before_punct()
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

    def has_link_macros(self) -> bool:
        """
        Check if this block contains link macros (link:URL[text], xref:target[text], etc).
        This helps rules understand when text originates from link titles/labels.
        """
        if not self.content:
            return False
            
        # Check for AsciiDoc link macro patterns
        link_patterns = [
            r'link:https?://[^\s\[\]]+\[[^\]]*\]',
            r'xref:[^\[]+\[[^\]]*\]',
            r'mailto:[^\[]+\[[^\]]*\]',
            r'<a\s+href=["\'][^"\']*["\'][^>]*>.*?</a>' 
        ]
        
        return any(re.search(pattern, self.content) for pattern in link_patterns)

    def should_skip_analysis(self) -> bool:
        """Determines if a block should be skipped during style analysis."""
        return self.block_type in [
            AsciiDocBlockType.LISTING, AsciiDocBlockType.LITERAL,
            AsciiDocBlockType.COMMENT, AsciiDocBlockType.PASS,
            AsciiDocBlockType.ATTRIBUTE_ENTRY,
            AsciiDocBlockType.MACRO,
            AsciiDocBlockType.INCLUDE,
        ]

    def get_context_info(self) -> Dict[str, Any]:
        """
        Get contextual information for rule processing.
        
        CRITICAL FIX: Propagates document-level metadata (like content_type) down to all blocks
        by traversing up the parent chain to find the document root.
        """
        context = {
            'block_type': self.block_type.value,
            'level': self.level,
            'admonition_type': self.admonition_type.value if self.admonition_type else None,
            'style': self.style,
            'title': self.title,
            'list_marker': self.list_marker,
            'source_location': self.source_location,
            'contains_inline_formatting': self.has_inline_formatting(),
            'is_link_text': self.has_link_macros()
        }
        
        # === CRITICAL FIX: Propagate document-level metadata ===
        # Traverse up the parent chain to find the document and extract metadata
        document = self._get_document_root()
        if document and document.attributes and document.attributes.named_attributes:
            # Extract content_type from document attributes
            # AsciiDoc attribute: :_mod-docs-content-type: PROCEDURE
            content_type = document.attributes.named_attributes.get('_mod-docs-content-type')
            if content_type:
                context['content_type'] = content_type.upper()  # Normalize to uppercase
            
            # Also extract other useful document metadata
            doc_type = document.attributes.named_attributes.get('doctype')
            if doc_type:
                context['doctype'] = doc_type
            
            # Extract document title if available
            if document.title and not context.get('document_title'):
                context['document_title'] = document.title
        
        # === NEW: Add parent context for structural inference ===
        # Include parent block info for context-aware analysis
        if self.parent:
            context['parent_block_type'] = self.parent.block_type.value
            if self.parent.title:
                context['parent_title'] = self.parent.title
        
        return context
    
    def _get_document_root(self) -> Optional['AsciiDocBlock']:
        """
        Traverse up the parent chain to find the document root.
        Returns the document block if found, None otherwise.
        """
        current = self
        while current:
            # Check if this is the document root
            if current.block_type == AsciiDocBlockType.DOCUMENT:
                return current
            # Move up to parent
            current = current.parent
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the block to a dictionary for JSON serialization to the UI."""
        
        # Create a UI-friendly version of the content.
        display_content = self.content
        if display_content:
            # Replace AsciiDoc link syntax with readable text for the UI.
            # Handle xref:path#anchor[display text] - extract display text
            display_content = re.sub(r'xref:[^\[]+\[([^\]]*)\]', r'\1', display_content)
            # Handle link:URL[display text] - extract display text (or show [Link] if empty)
            display_content = re.sub(r'link:https?://[^\s\[\]]+\[([^\]]+)\]', r'\1', display_content)
            display_content = re.sub(r'link:https?://[^\s\[\]]+\[\]', '[Link]', display_content)
            # Handle mailto:email[display text] - extract display text
            display_content = re.sub(r'mailto:[^\[]+\[([^\]]*)\]', r'\1', display_content)

        return {
            "block_type": self.block_type.value,
            "content": display_content,
            "raw_content": self.raw_content,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_pos": self.start_pos,
            "level": self.level,
            "title": self.title,
            "style": self.style,
            "admonition_type": self.admonition_type.value if self.admonition_type else None,
            "list_marker": self.list_marker,
            "should_skip_analysis": self.should_skip_analysis(),
            "errors": self._analysis_errors,
            "children": [child.to_dict() for child in self.children],
            "term": self.term,
            "description": self.description,
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
