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
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] parse() called")
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] content length: {len(content)}")
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] content preview: {content[:200]}")
        
        if not self.asciidoctor_available:
            logger.error(f"❌ [ASCIIDOC-PARSER-DEBUG] Asciidoctor not available")
            return ParseResult(success=False, errors=["Asciidoctor Ruby gem is not available."])

        # Correctly calls the 'run' method in the updated client
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] Calling ruby_client.run()...")
        result = self.ruby_client.run(content, filename)
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] ruby_client.run() returned: success={result.get('success')}")

        if not result.get('success'):
            logger.error(f"❌ [ASCIIDOC-PARSER-DEBUG] Ruby client failed: {result.get('error')}")
            return ParseResult(success=False, errors=[result.get('error', 'Unknown Ruby error')])

        json_ast = result.get('data', {})
        if not json_ast:
            logger.error(f"❌ [ASCIIDOC-PARSER-DEBUG] Parser returned empty document")
            return ParseResult(success=False, errors=["Parser returned empty document."])
        
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] json_ast keys: {list(json_ast.keys())}")
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] json_ast context: {json_ast.get('context')}")
        logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] json_ast children count: {len(json_ast.get('children', []))}")

        try:
            logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] Building block structure from AST...")
            document_node = self._build_block_from_ast(json_ast, filename=filename)
            logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] document_node type: {type(document_node)}")
            
            if isinstance(document_node, AsciiDocDocument):
                logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] Document blocks count: {len(document_node.blocks)}")
                if document_node.blocks:
                    logger.info(f"🔍 [ASCIIDOC-PARSER-DEBUG] First 3 block types: {[b.block_type for b in document_node.blocks[:3]]}")
                else:
                    logger.warning(f"⚠️ [ASCIIDOC-PARSER-DEBUG] Document has 0 blocks!")
                
                # Apply smart block splitting for better user experience
                if self.enable_smart_block_splitting:
                    self._apply_smart_block_splitting(document_node)
                # Fix misidentified admonition blocks that were parsed as definition lists
                self._fix_misidentified_admonitions(document_node)
                # Fix block titles that were merged into lists due to missing blank lines
                self._fix_merged_block_titles(document_node)
                # Promote list titles to proper sections for better structural clarity
                self._promote_list_titles_to_sections(document_node)
                
                logger.info(f"✅ [ASCIIDOC-PARSER-DEBUG] After splitting/fixing: {len(document_node.blocks)} blocks")
                
                return ParseResult(document=document_node, success=True)
            
            logger.error(f"❌ [ASCIIDOC-PARSER-DEBUG] AST root was not a document, got: {type(document_node)}")
            return ParseResult(success=False, errors=["AST root was not a document."])
        except Exception as e:
            logger.exception("❌ [ASCIIDOC-PARSER-DEBUG] Failed to build block structure from AsciiDoc AST.")
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
        
        # **FIX**: For table cells, if they have nested blocks (children), let those be analyzed.
        # The cell itself should have empty content so we don't double-analyze.
        # Only use text content if there are no nested blocks.
        if context == 'table_cell':
            if node.get('children') and len(node.get('children', [])) > 0:
                return ''  # Content will be in children (lists, notes, paragraphs)
            return node.get('text', '') or node.get('source', '')

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
    
    def _fix_merged_block_titles(self, document: 'AsciiDocDocument') -> None:
        """
        Fix cases where block titles (lines starting with .) are merged into list items
        due to missing blank lines. This is a common issue when users don't leave blank
        lines between list items and subsequent block titles like .Procedure, .Additional resources, etc.
        
        For example:
        * List item text
        .Procedure
        
        1. Step one
        
        Without a blank line, Asciidoctor may nest the .Procedure and subsequent content
        as children of the list item. This method detects and fixes such cases.
        """
        def process_blocks_recursively(blocks: List['AsciiDocBlock']) -> List['AsciiDocBlock']:
            new_blocks = []
            
            for block in blocks:
                # Process children recursively first
                if block.children:
                    block.children = process_blocks_recursively(block.children)
                
                # Check if this is a list block with items that need splitting
                if block.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
                    # Check each list item for embedded block titles
                    fixed_items = []
                    extracted_blocks = []
                    
                    for item in block.children:
                        if item.block_type == AsciiDocBlockType.LIST_ITEM:
                            # Check if this item has child lists that might be misplaced
                            if self._item_has_misplaced_content(item):
                                # Split the item and extract the misplaced content
                                split_result = self._split_list_item_with_block_title(item, block)
                                fixed_items.extend(split_result['items'])
                                extracted_blocks.extend(split_result['extracted'])
                            else:
                                fixed_items.append(item)
                        else:
                            fixed_items.append(item)
                    
                    # Update the list with fixed items
                    block.children = fixed_items
                    
                    # Add the fixed list block
                    new_blocks.append(block)
                    
                    # Add any extracted blocks after the list
                    new_blocks.extend(extracted_blocks)
                else:
                    new_blocks.append(block)
            
            return new_blocks
        
        # Apply the fixing to the document blocks
        document.blocks = process_blocks_recursively(document.blocks)
    
    def _item_has_misplaced_content(self, item: 'AsciiDocBlock') -> bool:
        """
        Check if a list item has content that suggests a block title was merged into it.
        This typically happens when:
        1. The item has child lists (which should probably be siblings)
        2. The raw content contains lines starting with '.' (block titles)
        """
        # Check if item has child lists - this is suspicious for a simple list item
        if item.children:
            for child in item.children:
                if child.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
                    # This item has a nested list, which might be from a merged block title
                    return True
        
        return False
    
    def _split_list_item_with_block_title(self, item: 'AsciiDocBlock', parent_list: 'AsciiDocBlock') -> dict:
        """
        Split a list item that has misplaced content (likely due to a merged block title).
        
        Returns:
            dict with 'items' (list items to keep) and 'extracted' (new blocks to add after the list)
        """
        result = {
            'items': [],  # List items that belong in the original list
            'extracted': []  # Blocks that should come after the list
        }
        
        # Check if this item has child lists
        has_child_lists = any(
            child.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]
            for child in item.children
        )
        
        if not has_child_lists:
            # No issue detected, keep the item as-is
            result['items'].append(item)
            return result
        
        # Extract block title from the list item's content
        extracted_title = None
        cleaned_content = item.content
        cleaned_raw_content = item.raw_content
        
        # Check both content and raw_content for block titles
        for content_field in [item.content, item.raw_content]:
            if not content_field:
                continue
                
            lines = content_field.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                # Check if this line is a block title (starts with . but not .. or .<digit>)
                if (line_stripped.startswith('.') and 
                    not line_stripped.startswith('..') and 
                    len(line_stripped) > 1):
                    
                    # Check if the character after . is not a digit (to avoid list markers like ". item")
                    char_after_dot = line_stripped[1]
                    if not char_after_dot.isdigit() and char_after_dot != ' ':
                        # This is a block title
                        potential_title = line_stripped[1:].strip()  # Remove leading .
                        if potential_title:
                            extracted_title = potential_title
                            # Don't add this line to cleaned content
                            continue
                
                cleaned_lines.append(line)
            
            # Update cleaned content only if we found a title
            if extracted_title:
                if content_field == item.content:
                    cleaned_content = '\n'.join(cleaned_lines).strip()
                else:
                    cleaned_raw_content = '\n'.join(cleaned_lines).strip()
        
        # Create a cleaned list item without the block title line
        cleaned_item = AsciiDocBlock(
            block_type=item.block_type,
            content=cleaned_content,
            raw_content=cleaned_raw_content,
            start_line=item.start_line,
            end_line=item.end_line,
            start_pos=item.start_pos,
            end_pos=item.end_pos,
            level=item.level,
            title=item.title,
            style=item.style,
            list_marker=item.list_marker,
            source_location=item.source_location,
            parent=item.parent,
            attributes=item.attributes
        )
        
        # Keep only non-list children (like paragraphs)
        cleaned_item.children = [
            child for child in item.children
            if child.block_type not in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]
        ]
        
        result['items'].append(cleaned_item)
        
        # Extract child lists as separate blocks after the parent list
        for child in item.children:
            if child.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
                # Update parent reference
                child.parent = parent_list.parent
                
                # Apply the extracted title if we found one
                if extracted_title:
                    child.title = extracted_title
                
                result['extracted'].append(child)
        
        return result
    
    def _promote_list_titles_to_sections(self, document: 'AsciiDocDocument') -> None:
        """
        Promote lists with common section-like titles (Prerequisites, Procedure, etc.) 
        to proper heading + list structure. This handles cases where block titles 
        immediately follow list items without blank lines.
        
        For example, when the source has:
            * Last item in Prerequisites
            .Procedure
            . First procedure step
        
        Asciidoctor treats .Procedure as a title for the ordered list, which is valid
        but creates structural ambiguity. This method converts such patterns into:
            HEADING: Prerequisites
                LIST: (items)
            HEADING: Procedure  
                LIST: (items)
        
        This makes the structure clearer and works with or without blank lines.
        """
        # Common section-like titles that should be promoted to headings
        SECTION_LIKE_TITLES = {
            'prerequisites', 'procedure', 'verification', 'next steps',
            'additional resources', 'related information', 'examples',
            'troubleshooting', 'known issues', 'limitations', 'notes',
            'important', 'before you begin', 'requirements', 'steps'
        }
        
        new_blocks = []
        i = 0
        
        while i < len(document.blocks):
            block = document.blocks[i]
            
            # Check if this is a list with a section-like title
            if (block.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST] and
                block.title and
                block.title.lower() in SECTION_LIKE_TITLES):
                
                # Check if previous block is also a titled list (no blank line scenario)
                # Use new_blocks (already processed) instead of document.blocks
                is_consecutive_titled_list = (
                    len(new_blocks) > 0 and
                    new_blocks[-1].block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST] and
                    new_blocks[-1].title and
                    new_blocks[-1].title.lower() in SECTION_LIKE_TITLES
                )
                
                # Check if we should promote based on already-processed blocks
                should_promote = (
                    i == 0 or 
                    is_consecutive_titled_list or 
                    self._should_promote_to_section_based_on_processed(block, new_blocks)
                )
                
                # If this is the first titled list OR follows another titled list,
                # promote it to a heading + list structure
                if should_promote:
                    # Create a heading block for the title
                    heading_block = AsciiDocBlock(
                        block_type=AsciiDocBlockType.HEADING,
                        content=block.title,
                        raw_content=f".{block.title}",
                        start_line=block.start_line - 1,  # Title is on the line before the list
                        end_line=block.start_line - 1,
                        start_pos=0,
                        end_pos=len(block.title) + 1,
                        level=2,  # Level 2 heading (== or .Title)
                        title=block.title,
                        source_location=block.source_location,
                        attributes=block.attributes,
                        parent=document
                    )
                    
                    # Remove the title from the list block
                    list_block = block
                    list_block.title = None
                    
                    # Add both blocks
                    new_blocks.append(heading_block)
                    new_blocks.append(list_block)
                else:
                    # Keep the block as-is (with title)
                    new_blocks.append(block)
            else:
                # Regular block, keep as-is
                new_blocks.append(block)
            
            i += 1
        
        # Replace document blocks with the promoted structure
        document.blocks = new_blocks
        # Update children reference for compatibility
        document.children = new_blocks
    
    def _should_promote_to_section_based_on_processed(self, block: 'AsciiDocBlock', processed_blocks: List['AsciiDocBlock']) -> bool:
        """
        Determine if a titled list should be promoted to a section heading based on
        already-processed blocks.
        
        Heuristics:
        1. If there's no previous block (first block)
        2. If previous block is a paragraph (intro text before a section)
        3. If previous block is a list (either titled or not - indicates section sequence)
        4. If previous is a heading (section after section)
        """
        # If no previous blocks, promote
        if not processed_blocks:
            return True
        
        prev_block = processed_blocks[-1]
        
        # If previous is a paragraph, this starts a new section
        if prev_block.block_type == AsciiDocBlockType.PARAGRAPH:
            return True
        
        # If previous is ANY list (titled or not), promote for consistency
        # This handles the case where the previous list was already promoted
        if prev_block.block_type in [AsciiDocBlockType.UNORDERED_LIST, AsciiDocBlockType.ORDERED_LIST]:
            return True
        
        # If previous is a heading, this is another section
        if prev_block.block_type == AsciiDocBlockType.HEADING:
            return True
        
        # Default: don't promote
        return False
