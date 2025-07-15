"""
AsciiDoc Structure Builder

Handles construction of AsciiDoc document structure including:
- Document hierarchy (sections, subsections)
- Block ordering and relationships
- Parent-child relationships
- Preamble and section organization
- Proper spacing and structure preservation
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class StructureBuilder:
    """
    Builds the overall structure of AsciiDoc documents.
    
    Handles the hierarchical organization of blocks, proper ordering,
    and structural relationships to maintain document coherence.
    """
    
    def __init__(self, preserve_hierarchy: bool = True, include_empty_sections: bool = False):
        """
        Initialize the structure builder.
        
        Args:
            preserve_hierarchy: Whether to preserve section hierarchy
            include_empty_sections: Whether to include sections with no content
        """
        self.preserve_hierarchy = preserve_hierarchy
        self.include_empty_sections = include_empty_sections
        self.logger = logging.getLogger(__name__)
    
    def build_document_structure(
        self, 
        document: Any, 
        formatted_blocks: List[str],
        block_mapping: Dict[str, str]
    ) -> str:
        """
        Build the complete document structure from formatted blocks.
        
        Args:
            document: Original parsed document
            formatted_blocks: List of formatted block content
            block_mapping: Mapping from original blocks to formatted content
            
        Returns:
            Complete structured document content
        """
        if not document or not hasattr(document, 'blocks'):
            # Fallback: just join formatted blocks
            return self._join_blocks_with_spacing(formatted_blocks)
        
        # Build structured content
        structured_content = self._build_hierarchical_structure(
            document.blocks, 
            block_mapping
        )
        
        return structured_content
    
    def _build_hierarchical_structure(
        self, 
        blocks: List[Any], 
        block_mapping: Dict[str, str]
    ) -> str:
        """
        Build hierarchical structure from document blocks.
        
        Args:
            blocks: List of document blocks
            block_mapping: Mapping from blocks to their formatted content
            
        Returns:
            Hierarchically structured content
        """
        content_parts = []
        
        for block in blocks:
            block_content = self._process_block_with_children(block, block_mapping)
            if block_content:
                content_parts.append(block_content)
        
        return self._join_blocks_with_spacing(content_parts)
    
    def _process_block_with_children(
        self, 
        block: Any, 
        block_mapping: Dict[str, str]
    ) -> Optional[str]:
        """
        Process a block and its children recursively.
        
        Args:
            block: Block to process
            block_mapping: Mapping from blocks to formatted content
            
        Returns:
            Formatted content for block and children
        """
        block_type = self._get_block_type(block)
        
        # Get formatted content for this block
        block_content = block_mapping.get(block, "")
        
        # Handle different block types
        if block_type == 'section':
            return self._process_section_block(block, block_mapping, block_content)
        elif block_type == 'preamble':
            return self._process_preamble_block(block, block_mapping, block_content)
        elif block_type in ['heading', 'paragraph', 'admonition']:
            # These are leaf blocks, return as-is
            return block_content
        else:
            # Generic block processing
            return self._process_generic_block(block, block_mapping, block_content)
    
    def _process_section_block(
        self, 
        section: Any, 
        block_mapping: Dict[str, str],
        section_content: str
    ) -> str:
        """
        Process a section block with its children.
        
        Args:
            section: Section block
            block_mapping: Block to content mapping
            section_content: Formatted section header content
            
        Returns:
            Complete section with children
        """
        parts = []
        
        # Add section header (title)
        title = getattr(section, 'title', '')
        level = getattr(section, 'level', 1)
        
        if title:
            equals = "=" * (level + 1)
            parts.append(f"{equals} {title}")
        
        # Process children
        if hasattr(section, 'children') and section.children:
            child_parts = []
            for child in section.children:
                child_content = self._process_block_with_children(child, block_mapping)
                if child_content:
                    child_parts.append(child_content)
            
            if child_parts:
                # Add spacing between section header and content
                if parts:  # If we have a header
                    parts.append("")  # Empty line for spacing
                parts.extend(child_parts)
        
        return "\n".join(parts) if parts else ""
    
    def _process_preamble_block(
        self, 
        preamble: Any, 
        block_mapping: Dict[str, str],
        preamble_content: str
    ) -> str:
        """
        Process a preamble block with its children.
        
        Args:
            preamble: Preamble block
            block_mapping: Block to content mapping
            preamble_content: Formatted preamble content
            
        Returns:
            Complete preamble content
        """
        # Preambles don't have their own header, just process children
        if hasattr(preamble, 'children') and preamble.children:
            child_parts = []
            for child in preamble.children:
                child_content = self._process_block_with_children(child, block_mapping)
                if child_content:
                    child_parts.append(child_content)
            
            return "\n".join(child_parts) if child_parts else ""
        
        # If no children, return the preamble content itself (unlikely)
        return preamble_content
    
    def _process_generic_block(
        self, 
        block: Any, 
        block_mapping: Dict[str, str],
        block_content: str
    ) -> str:
        """
        Process a generic block with potential children.
        
        Args:
            block: Block to process
            block_mapping: Block to content mapping  
            block_content: Formatted block content
            
        Returns:
            Complete block content with children
        """
        parts = []
        
        # Add block content if available
        if block_content:
            parts.append(block_content)
        
        # Process children if any
        if hasattr(block, 'children') and block.children:
            child_parts = []
            for child in block.children:
                child_content = self._process_block_with_children(child, block_mapping)
                if child_content:
                    child_parts.append(child_content)
            
            if child_parts:
                parts.extend(child_parts)
        
        return "\n".join(parts) if parts else ""
    
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
        
        return 'unknown'
    
    def _join_blocks_with_spacing(self, content_parts: List[str]) -> str:
        """
        Join content parts with appropriate spacing.
        
        Args:
            content_parts: List of content strings
            
        Returns:
            Joined content with proper spacing
        """
        if not content_parts:
            return ""
        
        # Filter out empty parts
        non_empty_parts = [part for part in content_parts if part.strip()]
        
        if not non_empty_parts:
            return ""
        
        # Join with double newlines for proper block separation
        return "\n\n".join(non_empty_parts)
    
    def get_document_outline(self, document: Any) -> List[Dict[str, Any]]:
        """
        Get a structural outline of the document.
        
        Args:
            document: Parsed document
            
        Returns:
            List of outline items with hierarchy info
        """
        outline = []
        
        if not document or not hasattr(document, 'blocks'):
            return outline
        
        for block in document.blocks:
            outline_item = self._create_outline_item(block)
            if outline_item:
                outline.append(outline_item)
        
        return outline
    
    def _create_outline_item(self, block: Any) -> Optional[Dict[str, Any]]:
        """
        Create an outline item for a block.
        
        Args:
            block: Block to create outline for
            
        Returns:
            Outline item dictionary or None
        """
        block_type = self._get_block_type(block)
        
        # Only include structural blocks in outline
        if block_type not in ['heading', 'section', 'preamble']:
            return None
        
        title = getattr(block, 'title', '') or getattr(block, 'content', '')
        level = getattr(block, 'level', 0)
        
        outline_item = {
            'type': block_type,
            'title': title[:50] + '...' if len(title) > 50 else title,
            'level': level,
            'has_children': hasattr(block, 'children') and len(block.children) > 0
        }
        
        # Add children to outline
        if hasattr(block, 'children') and block.children:
            children = []
            for child in block.children:
                child_outline = self._create_outline_item(child)
                if child_outline:
                    children.append(child_outline)
            
            if children:
                outline_item['children'] = children
        
        return outline_item
    
    def validate_structure(self, document: Any) -> List[str]:
        """
        Validate the document structure and return warnings.
        
        Args:
            document: Document to validate
            
        Returns:
            List of structure validation warnings
        """
        warnings = []
        
        if not document:
            warnings.append("Document is empty or None")
            return warnings
        
        if not hasattr(document, 'blocks') or not document.blocks:
            warnings.append("Document has no blocks")
            return warnings
        
        # Check for proper document title
        first_block = document.blocks[0]
        if self._get_block_type(first_block) != 'heading':
            warnings.append("Document does not start with a title (heading)")
        
        # Check section hierarchy
        section_levels = []
        for block in document.blocks:
            if self._get_block_type(block) in ['heading', 'section']:
                level = getattr(block, 'level', 0)
                section_levels.append(level)
        
        # Validate level progression
        for i in range(1, len(section_levels)):
            current_level = section_levels[i]
            prev_level = section_levels[i-1]
            
            if current_level > prev_level + 1:
                warnings.append(f"Section level jumps from {prev_level} to {current_level}")
        
        return warnings 