"""
Block Processing Utilities
Handles document structure parsing and block-level processing for style analysis.
"""

import logging
from typing import List, Dict, Any, Optional

try:
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlockType, AsciiDocBlock, AsciiDocAttributes
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlockType
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

logger = logging.getLogger(__name__)


class BlockProcessor:
    """Utility class for processing document blocks and extracting content."""
    
    @staticmethod
    def get_analyzable_blocks(parsed_document):
        """Get blocks that should be analyzed for style issues."""
        analyzable_blocks = []
        
        try:
            if hasattr(parsed_document, 'get_content_blocks'):
                # Use document's built-in method to get content blocks
                content_blocks = parsed_document.get_content_blocks()
                for block in content_blocks:
                    if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                        analyzable_blocks.append(block)
                    elif not hasattr(block, 'should_skip_analysis'):
                        # If should_skip_analysis doesn't exist, include the block
                        analyzable_blocks.append(block)
            else:
                # Fall back to manual filtering
                all_blocks = getattr(parsed_document, 'blocks', [])
                for block in all_blocks:
                    if hasattr(block, 'is_content_block') and block.is_content_block():
                        if hasattr(block, 'should_skip_analysis') and not block.should_skip_analysis():
                            analyzable_blocks.append(block)
                        elif not hasattr(block, 'should_skip_analysis'):
                            analyzable_blocks.append(block)
                        
        except Exception as e:
            logger.error(f"Error getting analyzable blocks: {e}")
            
        return analyzable_blocks
    
    @staticmethod
    def extract_content_sentences(parsed_document, sentence_splitter) -> List[str]:
        """Extract sentences from content blocks only."""
        sentences = []
        try:
            content_blocks = BlockProcessor.get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    block_sentences = sentence_splitter(block_content)
                    sentences.extend(block_sentences)
        except Exception as e:
            logger.error(f"Error extracting content sentences: {e}")
            # Fall back to full text
            full_text = BlockProcessor.extract_all_text(parsed_document)
            sentences = sentence_splitter(full_text)
        return sentences
    
    @staticmethod
    def extract_content_paragraphs(parsed_document, paragraph_splitter) -> List[str]:
        """Extract paragraphs from content blocks only."""
        paragraphs = []
        try:
            content_blocks = BlockProcessor.get_analyzable_blocks(parsed_document)
            for block in content_blocks:
                block_content = block.get_text_content()
                if block_content.strip():
                    paragraphs.append(block_content)
        except Exception as e:
            logger.error(f"Error extracting content paragraphs: {e}")
            # Fall back to full text
            full_text = BlockProcessor.extract_all_text(parsed_document)
            paragraphs = paragraph_splitter(full_text)
        return paragraphs
    
    @staticmethod
    def extract_all_text(parsed_document) -> str:
        """Extract all text from the parsed document."""
        try:
            all_text = []
            blocks = getattr(parsed_document, 'blocks', [])
            for block in blocks:
                if hasattr(block, 'get_all_text'):
                    # Use the block's get_all_text method which includes children
                    text = block.get_all_text()
                    if text.strip():
                        all_text.append(text)
                elif hasattr(block, 'get_text_content'):
                    # Fallback to get_text_content
                    text = block.get_text_content()
                    if text.strip():
                        all_text.append(text)
            return '\n\n'.join(all_text)
        except Exception as e:
            logger.error(f"Error extracting all text: {e}")
            return ""
    
    @staticmethod
    def get_block_display_content(block):
        """Get appropriate display content for different block types."""
        if not block:
            return ""
            
        block_type_str = getattr(block.block_type, 'value', str(block.block_type))
        
        # For attribute entries, show the raw content (e.g., ":author: Jane Doe")
        if block_type_str == 'attribute_entry':
            return getattr(block, 'raw_content', '') or getattr(block, 'content', '')
            
        # For other blocks, use the standard text content
        if hasattr(block, 'get_text_content'):
            return block.get_text_content().strip()
        elif hasattr(block, 'content'):
            return block.content.strip()
        else:
            return getattr(block, 'raw_content', '').strip()
    
    @staticmethod
    def flatten_document_blocks(blocks, parent_section_level=0):
        """Recursively flatten document blocks to individual analyzable elements with intelligent grouping."""
        flattened = []
        
        for block in blocks:
            block_type = getattr(block, 'block_type', None)
            
            if not block_type:
                continue
                
            block_type_str = getattr(block_type, 'value', str(block_type))
            
            # Determine how to handle this block based on its characteristics
            if BlockProcessor._should_extract_children(block_type_str):
                # Extract and process children instead of the container
                if block_type_str == 'section':
                    # Create a heading block for the section title
                    if hasattr(block, 'title') and block.title:
                        heading_block = BlockProcessor._create_synthetic_heading_block(block)
                        if heading_block:
                            flattened.append(heading_block)
                    
                    # Recursively process children of the section
                    if hasattr(block, 'children') and block.children:
                        child_blocks = BlockProcessor.flatten_document_blocks(block.children, getattr(block, 'level', 0))
                        flattened.extend(child_blocks)
                        
                elif block_type_str == 'preamble':
                    # Process children but don't include preamble itself
                    if hasattr(block, 'children') and block.children:
                        child_blocks = BlockProcessor.flatten_document_blocks(block.children, parent_section_level)
                        flattened.extend(child_blocks)
                        
                elif block_type_str == 'document':
                    # Process document children
                    if hasattr(block, 'children') and block.children:
                        child_blocks = BlockProcessor.flatten_document_blocks(block.children, parent_section_level)
                        flattened.extend(child_blocks)
                        
            elif BlockProcessor._should_group_children(block_type_str):
                # Handle blocks that should group their children intelligently
                if block_type_str in ['ordered_list', 'unordered_list', 'dlist']:
                    # Use intelligent list processing for title detection
                    processed_list_blocks = BlockProcessor._process_list_block(block)
                    flattened.extend(processed_list_blocks)
                elif block_type_str in ['admonition', 'sidebar', 'quote', 'example']:
                    # For compound blocks, consolidate their content from children
                    consolidated_block = BlockProcessor._consolidate_compound_block(block)
                    flattened.append(consolidated_block)
                else:
                    # For other groupable blocks, add them as single units
                    flattened.append(block)
                    
            else:
                # For all other blocks, add them directly as individual elements
                flattened.append(block)
                
        return flattened
    
    @staticmethod
    def _should_extract_children(block_type_str: str) -> bool:
        """Determine if a block's children should be extracted rather than keeping the container."""
        # These are structural containers that should be broken down
        container_types = {'document', 'section', 'preamble'}
        return block_type_str in container_types
    
    @staticmethod
    def _should_group_children(block_type_str: str) -> bool:
        """Determine if a block should intelligently group its children."""
        # These are blocks that have children but should be treated as cohesive units
        # with intelligent grouping logic
        groupable_types = {'ordered_list', 'unordered_list', 'dlist', 'admonition', 'sidebar', 'quote', 'example'}
        return block_type_str in groupable_types
    
    @staticmethod
    def _consolidate_compound_block(block):
        """Consolidate compound block content from its children."""
        try:
            if not hasattr(block, 'children') or not block.children:
                return block
            
            # Extract content from all child blocks
            combined_content = []
            for child in block.children:
                if hasattr(child, 'content') and child.content:
                    child_content = child.content.strip()
                    child_type = getattr(child.block_type, 'value', str(child.block_type))
                    
                    # Skip unordered lists with Ruby AST content (> 1000 characters)
                    if child_type == 'unordered_list' and len(child_content) > 1000:
                        # Extract clean list items dynamically
                        list_items = BlockProcessor._extract_clean_list_items_from_block(child)
                        if list_items:
                            combined_content.extend(list_items)
                        else:
                            # Fallback - indicate list is present but content unavailable
                            combined_content.append("* [List content not available]")
                    else:
                        combined_content.append(child_content)
            
            # Update the block's content with consolidated content
            if combined_content:
                block.content = '\n\n'.join(combined_content)
                # Also update raw_content if it exists
                if hasattr(block, 'raw_content'):
                    block.raw_content = block.content
            
            return block
            
        except Exception as e:
            logger.error(f"Error consolidating compound block: {e}")
            return block
    
    @staticmethod
    def _extract_clean_list_items_from_block(list_block):
        """Extract clean text from list items, handling Ruby AST objects."""
        list_items = []
        
        try:
            # Try to extract from children first
            children = getattr(list_block, 'children', [])
            if children:
                for child in children:
                    # Try multiple methods to get clean text
                    item_text = None
                    
                    # Method 1: Check for 'text' attribute (often clean)
                    if hasattr(child, 'text') and child.text:
                        item_text = str(child.text).strip()
                    
                    # Method 2: Check for clean content
                    elif hasattr(child, 'content') and isinstance(child.content, str):
                        content = child.content.strip()
                        if len(content) < 500 and not content.startswith('[#'):  # Not Ruby AST
                            item_text = content
                    
                    # Method 3: Try get_text_content if available
                    elif hasattr(child, 'get_text_content'):
                        try:
                            text_content = child.get_text_content().strip()
                            if text_content and len(text_content) < 500:
                                item_text = text_content
                        except:
                            pass
                    
                    if item_text:
                        list_items.append(f"* {item_text}")
            
            # If no clean items found, try to parse the raw content
            if not list_items:
                list_items = BlockProcessor._parse_list_from_ruby_ast(list_block)
                
        except Exception as e:
            logger.error(f"Error extracting list items: {e}")
            
        return list_items
    
    @staticmethod
    def _parse_list_from_ruby_ast(list_block):
        """Parse list items from Ruby AST object as last resort."""
        list_items = []
        
        try:
            # Look for common patterns in the Ruby AST string
            content = getattr(list_block, 'content', '')
            if isinstance(content, str) and len(content) > 1000:
                # Try to find text patterns that look like list items
                import re
                
                # Look for quoted strings that might be list items
                quoted_patterns = re.findall(r'"([^"]{10,100})"', content)
                for pattern in quoted_patterns:
                    # Filter out Ruby code patterns
                    if not any(ruby_keyword in pattern.lower() for ruby_keyword in 
                              ['context', 'document', 'attributes', 'node_name', 'blocks']):
                        # Clean up the text
                        clean_text = pattern.strip()
                        if clean_text and len(clean_text.split()) >= 2:  # At least 2 words
                            list_items.append(f"* {clean_text}")
                
                # If still no items, try a different approach
                if not list_items:
                    # Look for lines that might be list content
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if (line and 
                            len(line.split()) >= 2 and 
                            not line.startswith('[') and 
                            not line.startswith('"@') and
                            not any(ruby_keyword in line.lower() for ruby_keyword in 
                                   ['context', 'document', 'attributes', 'node_name', 'blocks'])):
                            # This might be list content
                            list_items.append(f"* {line}")
                            if len(list_items) >= 5:  # Don't extract too many
                                break
                                
        except Exception as e:
            logger.error(f"Error parsing Ruby AST: {e}")
            
        return list_items
    
    @staticmethod
    def _process_list_block(list_block):
        """Process a list block with intelligent grouping based on content."""
        processed_blocks = []
        
        if not hasattr(list_block, 'children') or not list_block.children:
            return [list_block]
            
        list_items = list_block.children
        block_type_str = getattr(list_block.block_type, 'value', str(list_block.block_type))
        
        # Only check for list titles in ordered lists (procedures)
        # Unordered lists should not have title detection
        if (block_type_str == 'ordered_list' and 
            list_items and 
            BlockProcessor._is_list_title(list_items[0])):
            
            # First item becomes a "list title"
            title_item = list_items[0]
            
            # Mark the title item as a list title for proper display
            if hasattr(title_item, 'block_type'):
                # Create a synthetic block type for list title
                title_item._synthetic_block_type = 'list_title'
            
            processed_blocks.append(title_item)
            
            # If there are remaining items, group them into a single list block
            if len(list_items) > 1:
                remaining_items = list_items[1:]
                grouped_list = BlockProcessor._create_grouped_list_block(list_block, remaining_items)
                if grouped_list:
                    processed_blocks.append(grouped_list)
        else:
            # No title detection needed - treat as a regular list with all items grouped
            processed_blocks.append(list_block)
            
        return processed_blocks
    
    @staticmethod
    def _is_list_title(list_item):
        """Check if a list item looks like a title rather than content."""
        if not hasattr(list_item, 'content'):
            return False
            
        content = list_item.content.strip()
        
        if not content:
            return False
        
        # Check for title-like characteristics
        words = content.split()
        
        # Short descriptive phrases (1-6 words) that look like titles
        if len(words) <= 6:
            # Check if it doesn't start with typical action verbs (common in procedure steps)
            action_verbs = {
                'download', 'install', 'run', 'execute', 'click', 'select', 
                'choose', 'enter', 'type', 'navigate', 'open', 'close',
                'save', 'delete', 'create', 'modify', 'edit', 'update',
                'configure', 'set', 'enable', 'disable', 'start', 'stop',
                'follow', 'complete', 'finish', 'verify', 'check', 'test',
                'copy', 'paste', 'move', 'remove', 'add', 'insert', 'press'
            }
            
            first_word = words[0].lower()
            if first_word not in action_verbs:
                # Check for title-like patterns
                title_patterns = [
                    'procedure', 'installation', 'setup', 'configuration', 
                    'overview', 'summary', 'introduction', 'conclusion',
                    'requirements', 'prerequisites', 'steps', 'process',
                    'method', 'approach', 'guide', 'tutorial', 'manual',
                    'checklist', 'instructions', 'guidelines', 'preparation'
                ]
                
                content_lower = content.lower()
                for pattern in title_patterns:
                    if pattern in content_lower:
                        return True
                        
                # Also check if it looks like a title format (Title Case, etc.)
                if content.istitle() or (len(words) <= 3 and not content.endswith(('.', '!', '?'))):
                    return True
                    
        return False
    
    @staticmethod
    def _create_grouped_list_block(original_list, items):
        """Create a new list block that groups multiple list items."""
        try:
            if not STRUCTURAL_PARSING_AVAILABLE:
                return None
                
            # Combine content from all items
            combined_content = []
            for item in items:
                if hasattr(item, 'content') and item.content:
                    combined_content.append(item.content.strip())
            
            # Create a new block that represents the grouped list
            grouped_block = AsciiDocBlock(
                block_type=original_list.block_type,
                content='\n\n'.join(combined_content),
                raw_content=original_list.raw_content,
                start_line=original_list.start_line,
                end_line=original_list.end_line,
                start_pos=original_list.start_pos,
                end_pos=original_list.end_pos,
                level=original_list.level,
                attributes=original_list.attributes,
                parent=original_list.parent,
                children=items,  # Keep the original items as children
                title=original_list.title,
                style=original_list.style,
                admonition_type=original_list.admonition_type,
                list_marker=original_list.list_marker,
                source_location=original_list.source_location
            )
            
            return grouped_block
            
        except Exception as e:
            logger.error(f"Error creating grouped list block: {e}")
            return original_list
    
    @staticmethod
    def _create_synthetic_heading_block(section_block):
        """Create a synthetic heading block from a section block."""
        try:
            if not STRUCTURAL_PARSING_AVAILABLE:
                return None
                
            section_level = getattr(section_block, 'level', 1)
            section_title = getattr(section_block, 'title', '')
            
            if not section_title:
                return None
            
            # Create heading block with appropriate markup
            heading_markup = '=' * (section_level + 1) + ' ' + section_title
            
            heading_block = AsciiDocBlock(
                block_type=AsciiDocBlockType.HEADING,
                content=section_title,
                raw_content=heading_markup,
                start_line=getattr(section_block, 'start_line', 0),
                end_line=getattr(section_block, 'start_line', 0),
                start_pos=0,
                end_pos=len(heading_markup),
                level=section_level,
                attributes=AsciiDocAttributes(),
                parent=None,
                children=[],
                title=None,
                style=None,
                admonition_type=None,
                list_marker=None,
                source_location=getattr(section_block, 'source_location', '')
            )
            
            return heading_block
            
        except Exception as e:
            logger.error(f"Error creating synthetic heading block: {e}")
            return None
    
    @staticmethod
    def convert_children_to_dict(children) -> List[Dict[str, Any]]:
        """Convert child blocks to dictionary format for serialization."""
        children_list = []
        
        try:
            for child in children:
                # Check for synthetic block type first
                child_block_type = getattr(child, '_synthetic_block_type', getattr(child.block_type, 'value', str(child.block_type)))
                
                # Get errors from child if they were stored there during analysis
                child_errors = getattr(child, '_analysis_errors', [])
                
                child_dict = {
                    'block_type': child_block_type,
                    'content': BlockProcessor.get_block_display_content(child),
                    'raw_content': getattr(child, 'raw_content', ''),
                    'level': getattr(child, 'level', 0),
                    'children': BlockProcessor.convert_children_to_dict(getattr(child, 'children', [])),
                    'errors': child_errors  # Include errors that were stored on the child
                }
                children_list.append(child_dict)
        except Exception as e:
            logger.error(f"Error converting children to dict: {e}")
            
        return children_list
    
    @staticmethod
    def get_block_type_display_name(block_type_value: str, context: Dict[str, Any]) -> str:
        """Get a human-readable display name for a block type."""
        # Check both level keys since different parsers use different keys
        level = context.get('level', 0) or context.get('heading_level', 0)
        admonition_type = context.get('admonition_type')
        
        display_names = {
            'heading': f'HEADING (Level {level})',
            'paragraph': 'PARAGRAPH',
            'ordered_list': 'ORDERED LIST',
            'unordered_list': 'UNORDERED LIST',
            'list_item': 'LIST ITEM',
            'list_title': 'LIST TITLE',
            'admonition': f'ADMONITION ({admonition_type.upper()})' if admonition_type else 'ADMONITION',
            'sidebar': 'SIDEBAR',
            'example': 'EXAMPLE',
            'quote': 'QUOTE',
            'verse': 'VERSE',
            'listing': 'CODE BLOCK',
            'literal': 'LITERAL BLOCK',
            'attribute_entry': 'ATTRIBUTE',
            'comment': 'COMMENT',
            'table': 'TABLE',
            'image': 'IMAGE',
            'audio': 'AUDIO',
            'video': 'VIDEO'
        }
        
        return display_names.get(block_type_value, block_type_value.upper().replace('_', ' '))