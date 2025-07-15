"""
AsciiDoc Content Formatter

Handles formatting of individual AsciiDoc content blocks including:
- Headings and section titles
- Paragraphs and text content
- Admonitions (NOTE, TIP, WARNING, etc.)
- Lists (ordered, unordered, description)
- Code blocks and literal content
- Tables and other special blocks
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ContentFormatter:
    """
    Formats individual AsciiDoc content blocks.
    
    Converts parsed block structures and rewritten content back into
    proper AsciiDoc markup while preserving formatting and structure.
    """
    
    def __init__(self, preserve_original_formatting: bool = True):
        """
        Initialize the content formatter.
        
        Args:
            preserve_original_formatting: Whether to preserve original formatting hints
        """
        self.preserve_original_formatting = preserve_original_formatting
        self.logger = logging.getLogger(__name__)
    
    def format_block(self, block: Any, rewritten_content: Optional[str] = None) -> str:
        """
        Format a single block into AsciiDoc markup.
        
        Args:
            block: Original parsed block
            rewritten_content: Rewritten content (if available)
            
        Returns:
            Formatted AsciiDoc content
        """
        if not block:
            return ""
        
        # Use rewritten content if available, otherwise use original
        content = rewritten_content if rewritten_content is not None else self._extract_block_content(block)
        
        # Get block type and format accordingly
        block_type = self._get_block_type(block)
        
        # Route to appropriate formatter
        formatter_map = {
            'heading': self._format_heading,
            'paragraph': self._format_paragraph,
            'admonition': self._format_admonition,
            'section': self._format_section,
            'preamble': self._format_preamble,
            'list_item': self._format_list_item,
            'ordered_list': self._format_ordered_list,
            'unordered_list': self._format_unordered_list,
            'description_list': self._format_description_list,
            'listing': self._format_code_block,
            'literal': self._format_literal_block,
            'quote': self._format_quote,
            'verse': self._format_verse,
            'sidebar': self._format_sidebar,
            'example': self._format_example,
            'table': self._format_table,
        }
        
        formatter = formatter_map.get(block_type, self._format_generic)
        return formatter(block, content)
    
    def _get_block_type(self, block: Any) -> str:
        """Get the block type string."""
        if hasattr(block, 'block_type'):
            if hasattr(block.block_type, 'value'):
                return block.block_type.value
            else:
                return str(block.block_type)
        
        # Fallback: try to infer from other attributes
        if hasattr(block, 'context'):
            return block.context
        
        return 'paragraph'  # Default fallback
    
    def _extract_block_content(self, block: Any) -> str:
        """Extract content from a block."""
        if hasattr(block, 'get_text_content'):
            return block.get_text_content()
        elif hasattr(block, 'content'):
            return block.content or ""
        else:
            return ""
    
    def _format_heading(self, block: Any, content: str) -> str:
        """Format a heading block."""
        level = getattr(block, 'level', 0)
        
        # AsciiDoc uses = for document title (level 0) and multiple = for sections
        if level == 0:
            return f"= {content}"
        else:
            equals = "=" * (level + 1)
            return f"{equals} {content}"
    
    def _format_paragraph(self, block: Any, content: str) -> str:
        """Format a paragraph block."""
        # Check if this paragraph has any special attributes
        title = getattr(block, 'title', None)
        
        if title:
            return f".{title}\n{content}"
        else:
            return content
    
    def _format_admonition(self, block: Any, content: str) -> str:
        """Format an admonition block."""
        # Get admonition type
        admonition_type = self._get_admonition_type(block)
        title = getattr(block, 'title', None)
        
        if title:
            return f"[{admonition_type}]\n.{title}\n====\n{content}\n===="
        else:
            return f"[{admonition_type}]\n====\n{content}\n===="
    
    def _format_section(self, block: Any, content: str) -> str:
        """Format a section block."""
        # Sections are containers - format title and children separately
        title = getattr(block, 'title', '')
        level = getattr(block, 'level', 1)
        
        if title:
            equals = "=" * (level + 1)
            section_header = f"{equals} {title}"
            
            # If there's content, add it after the header
            if content and content.strip():
                return f"{section_header}\n\n{content}"
            else:
                return section_header
        else:
            # No title, just return content
            return content
    
    def _format_preamble(self, block: Any, content: str) -> str:
        """Format a preamble block."""
        # Preambles are just content before the first section
        return content
    
    def _format_list_item(self, block: Any, content: str) -> str:
        """Format a list item."""
        # Get the list marker from the parent or infer
        marker = self._get_list_marker(block)
        return f"{marker} {content}"
    
    def _format_ordered_list(self, block: Any, content: str) -> str:
        """Format an ordered list."""
        # Ordered lists are containers - content should be formatted items
        return content
    
    def _format_unordered_list(self, block: Any, content: str) -> str:
        """Format an unordered list."""
        # Unordered lists are containers - content should be formatted items
        return content
    
    def _format_description_list(self, block: Any, content: str) -> str:
        """Format a description list."""
        # Description lists have term::definition format
        return content
    
    def _format_code_block(self, block: Any, content: str) -> str:
        """Format a code/listing block."""
        title = getattr(block, 'title', None)
        language = self._get_code_language(block)
        
        # Build source block
        parts = []
        
        if title:
            parts.append(f".{title}")
        
        if language:
            parts.append(f"[source,{language}]")
        else:
            parts.append("[source]")
        
        parts.append("----")
        parts.append(content)
        parts.append("----")
        
        return "\n".join(parts)
    
    def _format_literal_block(self, block: Any, content: str) -> str:
        """Format a literal block."""
        title = getattr(block, 'title', None)
        
        parts = []
        if title:
            parts.append(f".{title}")
        
        parts.append("....")
        parts.append(content)
        parts.append("....")
        
        return "\n".join(parts)
    
    def _format_quote(self, block: Any, content: str) -> str:
        """Format a quote block."""
        title = getattr(block, 'title', None)
        attribution = self._get_quote_attribution(block)
        
        parts = []
        
        if title:
            parts.append(f".{title}")
        
        if attribution:
            parts.append(f"[quote, {attribution}]")
        else:
            parts.append("[quote]")
        
        parts.append("____")
        parts.append(content)
        parts.append("____")
        
        return "\n".join(parts)
    
    def _format_verse(self, block: Any, content: str) -> str:
        """Format a verse block."""
        title = getattr(block, 'title', None)
        attribution = self._get_quote_attribution(block)
        
        parts = []
        
        if title:
            parts.append(f".{title}")
        
        if attribution:
            parts.append(f"[verse, {attribution}]")
        else:
            parts.append("[verse]")
        
        parts.append("____")
        parts.append(content)
        parts.append("____")
        
        return "\n".join(parts)
    
    def _format_sidebar(self, block: Any, content: str) -> str:
        """Format a sidebar block."""
        title = getattr(block, 'title', None)
        
        parts = []
        if title:
            parts.append(f".{title}")
        
        parts.append("****")
        parts.append(content)
        parts.append("****")
        
        return "\n".join(parts)
    
    def _format_example(self, block: Any, content: str) -> str:
        """Format an example block."""
        title = getattr(block, 'title', None)
        
        parts = []
        if title:
            parts.append(f".{title}")
        
        parts.append("====")
        parts.append(content)
        parts.append("====")
        
        return "\n".join(parts)
    
    def _format_table(self, block: Any, content: str) -> str:
        """Format a table block."""
        title = getattr(block, 'title', None)
        
        parts = []
        if title:
            parts.append(f".{title}")
        
        # Add table delimiter and content
        parts.append("|===")
        parts.append(content)
        parts.append("|===")
        
        return "\n".join(parts)
    
    def _format_generic(self, block: Any, content: str) -> str:
        """Generic formatter for unknown block types."""
        self.logger.warning(f"Unknown block type, using generic formatting: {self._get_block_type(block)}")
        return content
    
    def _get_admonition_type(self, block: Any) -> str:
        """Get the admonition type from a block."""
        # Try different ways to get admonition type
        if hasattr(block, 'admonition_type') and block.admonition_type:
            if hasattr(block.admonition_type, 'value'):
                return block.admonition_type.value.upper()
            else:
                return str(block.admonition_type).upper()
        
        # Check attributes
        if hasattr(block, 'attributes') and 'admonition-name' in block.attributes:
            return block.attributes['admonition-name'].upper()
        
        # Default fallback
        return "NOTE"
    
    def _get_list_marker(self, block: Any) -> str:
        """Get the list marker for a list item."""
        # Try to get from parent or block attributes
        if hasattr(block, 'marker'):
            return block.marker
        
        # Try to infer from parent block type
        parent = getattr(block, 'parent', None)
        if parent:
            parent_type = self._get_block_type(parent)
            if parent_type == 'ordered_list':
                return "."
            elif parent_type == 'unordered_list':
                return "*"
        
        # Default to unordered
        return "*"
    
    def _get_code_language(self, block: Any) -> Optional[str]:
        """Get the programming language for a code block."""
        if hasattr(block, 'attributes'):
            # Check for language attribute
            if 'language' in block.attributes:
                return block.attributes['language']
            elif 'source-language' in block.attributes:
                return block.attributes['source-language']
        
        return None
    
    def _get_quote_attribution(self, block: Any) -> Optional[str]:
        """Get attribution for quote/verse blocks."""
        if hasattr(block, 'attributes'):
            if 'attribution' in block.attributes:
                return block.attributes['attribution']
            elif 'citetitle' in block.attributes:
                attr = block.attributes['attribution']
                cite = block.attributes['citetitle']
                return f"{attr}, {cite}"
        
        return None 