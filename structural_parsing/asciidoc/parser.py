"""
Simplified AsciiDoc structural parser using native Asciidoctor AST.
This version is a drop-in replacement, ensuring full compatibility with the existing system.
"""
import logging
import re
from typing import Dict, Any, Optional, List
from .ruby_client import get_client
from .types import (
    AsciiDocBlock, AsciiDocDocument, ParseResult, AsciiDocBlockType,
    AdmonitionType, AsciiDocAttributes
)

logger = logging.getLogger(__name__)

class AsciiDocParser:
    def __init__(self):
        self.ruby_client = get_client()
        self.asciidoctor_available = self.ruby_client.ping()
        # Enable intelligent block splitting for better user experience
        self.enable_smart_block_splitting = True

    def parse(self, content: str, filename: str = "") -> ParseResult:
        if not self.asciidoctor_available:
            return ParseResult(success=False, errors=["Asciidoctor Ruby gem is not available."])

        # Correctly calls the 'run' method in the updated client
        result = self.ruby_client.run(content, filename)

        if not result.get('success'):
            return ParseResult(success=False, errors=[result.get('error', 'Unknown Ruby error')])

        json_ast = result.get('data', {})
        if not json_ast:
            return ParseResult(success=False, errors=["Parser returned empty document."])

        try:
            document_node = self._build_block_from_ast(json_ast, filename=filename)
            if isinstance(document_node, AsciiDocDocument):
                # Apply smart block splitting for better user experience
                if self.enable_smart_block_splitting:
                    self._apply_smart_block_splitting(document_node)
                # Fix misidentified admonition blocks that were parsed as definition lists
                self._fix_misidentified_admonitions(document_node)
                return ParseResult(document=document_node, success=True)
            return ParseResult(success=False, errors=["AST root was not a document."])
        except Exception as e:
            logger.exception("Failed to build block structure from AsciiDoc AST.")
            return ParseResult(success=False, errors=[f"Failed to process AST: {e}"])

    def _build_block_from_ast(self, node: Dict[str, Any], parent: Optional[AsciiDocBlock] = None, filename: str = "") -> AsciiDocBlock:
        context = node.get('context', 'unknown')
        block_type = self._map_context_to_block_type(context)
        raw_content = node.get('source', '') or ''
        start_line = node.get('lineno', 0)
        content = self._get_content_from_node(node)

        block = AsciiDocBlock(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            title=node.get('title'),
            level=node.get('level', 0),
            start_line=start_line,
            end_line=start_line + raw_content.count('\n'),
            start_pos=0,
            end_pos=len(raw_content),
            style=node.get('style'),
            list_marker=node.get('marker'),
            source_location=filename,
            attributes=self._create_attributes(node.get('attributes', {})),
            parent=parent
        )

        # **NEW**: Handle the new description_list_item context
        if block_type == AsciiDocBlockType.DESCRIPTION_LIST_ITEM:
            block.term = node.get('term')
            block.description = node.get('description')
            # The 'content' of the item block itself is the combination for context,
            # but analysis will happen on term/description separately.
            block.content = f"{block.term}:: {block.description}"


        if block_type == AsciiDocBlockType.ADMONITION:
            style = node.get('style', 'NOTE').upper()
            block.admonition_type = AdmonitionType[style] if style in AdmonitionType.__members__ else AdmonitionType.NOTE

        block.children = [self._build_block_from_ast(child, parent=block, filename=filename) for child in node.get('children', [])]

        if context == 'document':
            return AsciiDocDocument(
                blocks=block.children,
                source_file=filename,
                block_type=AsciiDocBlockType.DOCUMENT,
                content=node.get('title', ''),
                raw_content=node.get('source', ''),
                start_line=0,
                title=node.get('title', ''),
                attributes=self._create_attributes(node.get('attributes', {}))
            )
        return block

    def _create_attributes(self, attrs: Dict[str, Any]) -> AsciiDocAttributes:
        """Creates the AsciiDocAttributes object for compatibility."""
        attributes = AsciiDocAttributes()
        attributes.id = attrs.get('id')
        for key, value in attrs.items():
            if isinstance(value, (str, int, float, bool)):
                attributes.named_attributes[key] = str(value)
        return attributes

    def _get_content_from_node(self, node: Dict[str, Any]) -> str:
        """Determines the correct content field from the AST node for analysis."""
        context = node.get('context')
        if context == 'list_item': return node.get('text', '')
        if context == 'section': return node.get('title', '')
        if context in ['listing', 'literal']: return node.get('source', '')
        
        if context == 'table_cell': return node.get('text', '') or node.get('source', '')

        # **FIX**: For dlist containers, the content is built from its children by the UI.
        # It has no direct content itself.
        if context == 'dlist': return ''
        
        # **NEW**: For description list items, the primary content is the description.
        # The term is handled separately.
        if context == 'description_list_item':
            return node.get('description', '')

        if context in ['ulist', 'olist'] and node.get('children'):
            list_items = []
            for child in node.get('children', []):
                if child.get('context') == 'list_item':
                    item_text = child.get('text', '') or child.get('content', '')
                    if item_text:
                        list_items.append(item_text.strip())
            return '\n'.join(list_items) if list_items else ''
        
        if node.get('children') and context not in ['table']:
            return "\n".join(child.get('source', '') for child in node.get('children', []))
        return node.get('content', '') or ''


    def _map_context_to_block_type(self, context: str) -> AsciiDocBlockType:
        """Maps the Asciidoctor context string to our enum."""
        if context == 'section': return AsciiDocBlockType.HEADING
        try:
            # **FIX**: Ensure 'dlist' from Ruby maps to the DLIST enum member.
            return AsciiDocBlockType(context)
        except ValueError:
            # Fallback for contexts not explicitly in our enum
            return AsciiDocBlockType.UNKNOWN

    def _apply_smart_block_splitting(self, document: 'AsciiDocDocument') -> None:
        """
        Apply intelligent block splitting to handle cases where lists immediately
        follow paragraphs without blank lines. This makes the parser more versatile
        and user-friendly while maintaining production-grade reliability.
        """
        def process_blocks_recursively(blocks: List['AsciiDocBlock']) -> List['AsciiDocBlock']:
            new_blocks = []
            
            for block in blocks:
                # Process children recursively first
                if block.children:
                    block.children = process_blocks_recursively(block.children)
                
                # Check if this is a paragraph block that needs splitting
                if (block.block_type == AsciiDocBlockType.PARAGRAPH and 
                    block.raw_content and 
                    self._should_split_paragraph_block(block.raw_content)):
                    
                    split_blocks = self._split_paragraph_with_lists(block)
                    new_blocks.extend(split_blocks)
                else:
                    new_blocks.append(block)
            
            return new_blocks
        
        # Apply the splitting to the document blocks
        document.blocks = process_blocks_recursively(document.blocks)
    
    def _should_split_paragraph_block(self, raw_content: str) -> bool:
        """
        Determine if a paragraph block should be split because it contains
        list-like content that should be separate blocks.
        """
        lines = raw_content.split('\n')
        
        # Look for lines that start with list markers
        list_markers = [
            r'^\s*\*\s+',        # Unordered list (* item)
            r'^\s*-\s+',         # Unordered list (- item)  
            r'^\s*\+\s+',        # Unordered list (+ item)
            r'^\s*\d+\.\s+',     # Ordered list (1. item)
            r'^\s*[a-zA-Z]\.\s+', # Ordered list (a. item)
        ]
        
        list_pattern = '|'.join(list_markers)
        
        # Check if we have both non-list content and list content
        has_non_list_content = False
        has_list_content = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if re.match(list_pattern, line):
                has_list_content = True
            else:
                has_non_list_content = True
        
        # Split only if we have BOTH non-list and list content
        return has_non_list_content and has_list_content
    
    def _split_paragraph_with_lists(self, block: 'AsciiDocBlock') -> List['AsciiDocBlock']:
        """
        Split a paragraph block that contains list items into separate blocks.
        Returns a list of new blocks (paragraph + list blocks).
        """
        lines = block.raw_content.split('\n')
        result_blocks = []
        
        current_paragraph_lines = []
        current_list_lines = []
        current_list_type = None
        
        list_markers = {
            r'^\s*\*\s+': 'ulist',       # Unordered list (* item)
            r'^\s*-\s+': 'ulist',        # Unordered list (- item)  
            r'^\s*\+\s+': 'ulist',       # Unordered list (+ item)
            r'^\s*\d+\.\s+': 'olist',    # Ordered list (1. item)
            r'^\s*[a-zA-Z]\.\s+': 'olist', # Ordered list (a. item)
        }
        
        def create_block_from_lines(lines: List[str], block_type: AsciiDocBlockType, list_type: str = None) -> 'AsciiDocBlock':
            """Helper to create a block from lines."""
            raw_content = '\n'.join(lines)
            content = raw_content.strip()
            
            # For list blocks, clean up the content
            if block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
                # Remove list markers and create clean content
                clean_lines = []
                for line in lines:
                    # Remove the list marker but keep the content
                    for pattern in list_markers.keys():
                        line = re.sub(pattern, '', line)
                    clean_lines.append(line.strip())
                content = '\n'.join(clean_lines)
            
            new_block = AsciiDocBlock(
                block_type=block_type,
                content=content,
                raw_content=raw_content,
                start_line=block.start_line,
                end_line=block.start_line + len(lines),
                start_pos=0,
                end_pos=len(raw_content),
                source_location=block.source_location,
                attributes=block.attributes,
                parent=block.parent
            )
            
            # For list blocks, create list item children
            if block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
                children = []
                for line in lines:
                    if line.strip():
                        # Remove list marker and create list item
                        item_content = line
                        for pattern in list_markers.keys():
                            item_content = re.sub(pattern, '', item_content)
                        
                        list_item = AsciiDocBlock(
                            block_type=AsciiDocBlockType.LIST_ITEM,
                            content=item_content.strip(),
                            raw_content=line,
                            start_line=block.start_line,
                            end_line=block.start_line + 1,
                            start_pos=0,
                            end_pos=len(line),
                            source_location=block.source_location,
                            parent=new_block
                        )
                        children.append(list_item)
                new_block.children = children
            
            return new_block
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if this line is a list item
            detected_list_type = None
            for pattern, list_type in list_markers.items():
                if re.match(pattern, line):
                    detected_list_type = list_type
                    break
            
            if detected_list_type:
                # This is a list item
                if current_paragraph_lines:
                    # Finish the current paragraph block
                    paragraph_block = create_block_from_lines(current_paragraph_lines, AsciiDocBlockType.PARAGRAPH)
                    result_blocks.append(paragraph_block)
                    current_paragraph_lines = []
                
                # Add to current list or start a new one
                if current_list_type != detected_list_type and current_list_lines:
                    # Different list type, finish current list
                    list_block_type = AsciiDocBlockType.UNORDERED_LIST if current_list_type == 'ulist' else AsciiDocBlockType.ORDERED_LIST
                    list_block = create_block_from_lines(current_list_lines, list_block_type, current_list_type)
                    result_blocks.append(list_block)
                    current_list_lines = []
                
                current_list_lines.append(line)
                current_list_type = detected_list_type
                
            else:
                # This is regular paragraph content
                if current_list_lines:
                    # Finish the current list block
                    list_block_type = AsciiDocBlockType.UNORDERED_LIST if current_list_type == 'ulist' else AsciiDocBlockType.ORDERED_LIST
                    list_block = create_block_from_lines(current_list_lines, list_block_type, current_list_type)
                    result_blocks.append(list_block)
                    current_list_lines = []
                    current_list_type = None
                
                current_paragraph_lines.append(line)
        
        # Handle remaining content
        if current_paragraph_lines:
            paragraph_block = create_block_from_lines(current_paragraph_lines, AsciiDocBlockType.PARAGRAPH)
            result_blocks.append(paragraph_block)
        
        if current_list_lines:
            list_block_type = AsciiDocBlockType.UNORDERED_LIST if current_list_type == 'ulist' else AsciiDocBlockType.ORDERED_LIST
            list_block = create_block_from_lines(current_list_lines, list_block_type, current_list_type)
            result_blocks.append(list_block)
        
        return result_blocks

    def _fix_misidentified_admonitions(self, document: 'AsciiDocDocument') -> None:
        """
        Fix admonition blocks that were incorrectly parsed as definition list items.
        This handles cases where CAUTION::, NOTE::, etc. are interpreted as definition
        lists instead of proper admonition blocks due to spacing issues.
        
        This is a production-grade fix that:
        - Detects all admonition types (NOTE, TIP, IMPORTANT, WARNING, CAUTION)
        - Extracts them from incorrect nesting within other blocks
        - Promotes them to the appropriate section level
        - Works recursively through all block hierarchies
        """
        admonition_types = {member.value for member in AdmonitionType}
        
        # Process each section (heading) in the document
        for section in document.blocks:
            if section.block_type == AsciiDocBlockType.HEADING and section.children:
                extracted_admonitions = []
                
                # Look for nested admonitions in this section's children
                for child in section.children:
                    if (child.block_type in [AsciiDocBlockType.ORDERED_LIST, AsciiDocBlockType.UNORDERED_LIST] and 
                        self._list_contains_nested_admonitions(child.children, admonition_types)):
                        
                        # Extract admonitions from list items and clean up the list
                        section_admonitions = self._extract_and_clean_list_admonitions(child, admonition_types, section)
                        extracted_admonitions.extend(section_admonitions)
                
                # Add extracted admonitions as new children of the section
                section.children.extend(extracted_admonitions)
    
    def _contains_misidentified_admonitions(self, children: List['AsciiDocBlock'], admonition_types: set) -> bool:
        """Check if definition list children contain misidentified admonitions."""
        return any(
            child.block_type == AsciiDocBlockType.DESCRIPTION_LIST_ITEM and
            child.term and child.term.upper() in admonition_types
            for child in children
        )
    
    def _list_contains_nested_admonitions(self, list_items: List['AsciiDocBlock'], admonition_types: set) -> bool:
        """Check if any list items contain nested admonitions."""
        for item in list_items:
            if item.block_type == AsciiDocBlockType.LIST_ITEM and item.children:
                for child in item.children:
                    if child.block_type == AsciiDocBlockType.DLIST and child.children:
                        if self._contains_misidentified_admonitions(child.children, admonition_types):
                            return True
        return False
    
    def _extract_admonitions_from_dlist(self, dlist_block: 'AsciiDocBlock', admonition_types: set) -> List['AsciiDocBlock']:
        """Extract admonitions from a definition list and return separate blocks."""
        result_blocks = []
        remaining_items = []
        
        for item in dlist_block.children:
            if (item.block_type == AsciiDocBlockType.DESCRIPTION_LIST_ITEM and
                item.term and item.term.upper() in admonition_types):
                
                # Create a proper admonition block
                admonition_block = AsciiDocBlock(
                    block_type=AsciiDocBlockType.ADMONITION,
                    content=item.description or '',
                    raw_content=f"{item.term}:: {item.description or ''}",
                    start_line=item.start_line,
                    end_line=item.end_line,
                    start_pos=item.start_pos,
                    end_pos=item.end_pos,
                    source_location=item.source_location,
                    attributes=item.attributes,
                    parent=dlist_block.parent,
                    admonition_type=AdmonitionType[item.term.upper()]
                )
                result_blocks.append(admonition_block)
            else:
                remaining_items.append(item)
        
        # If there are remaining definition list items, keep the dlist
        if remaining_items:
            dlist_block.children = remaining_items
            result_blocks.insert(0, dlist_block)  # Keep original dlist with remaining items
        # If no remaining items, the dlist should be completely removed (not returned)
        
        return result_blocks
    
    def _extract_and_clean_list_admonitions(self, list_block: 'AsciiDocBlock', admonition_types: set, section: 'AsciiDocBlock') -> List['AsciiDocBlock']:
        """Extract admonitions from nested list items and clean up the list structure."""
        extracted_admonitions = []
        
        # Process each list item  
        for item in list_block.children:
            if item.block_type == AsciiDocBlockType.LIST_ITEM and item.children:
                # Filter out dlist children that contain admonitions, extract the admonitions
                cleaned_children = []
                
                for child in item.children:
                    if (child.block_type == AsciiDocBlockType.DLIST and 
                        self._contains_misidentified_admonitions(child.children, admonition_types)):
                        
                        # Extract admonitions from this dlist
                        for dlist_item in child.children:
                            if (dlist_item.block_type == AsciiDocBlockType.DESCRIPTION_LIST_ITEM and 
                                dlist_item.term and dlist_item.term.upper() in admonition_types):
                                
                                # Create proper admonition block
                                admonition_block = AsciiDocBlock(
                                    block_type=AsciiDocBlockType.ADMONITION,
                                    content=dlist_item.description or '',
                                    raw_content=f"{dlist_item.term}:: {dlist_item.description or ''}",
                                    start_line=dlist_item.start_line,
                                    end_line=dlist_item.end_line,
                                    start_pos=dlist_item.start_pos,
                                    end_pos=dlist_item.end_pos,
                                    source_location=dlist_item.source_location,
                                    attributes=dlist_item.attributes,
                                    parent=section,  # Set parent to the section
                                    admonition_type=AdmonitionType[dlist_item.term.upper()]
                                )
                                extracted_admonitions.append(admonition_block)
                            else:
                                # Keep non-admonition dlist items (if any)
                                # This preserves legitimate definition lists mixed with admonitions
                                pass
                        
                        # Don't add the dlist back as child - it's been processed
                    else:
                        # Keep other children that aren't problematic dlists
                        cleaned_children.append(child)
                
                # Update the list item with cleaned children (removes empty dlists)
                item.children = cleaned_children
        
        return extracted_admonitions
