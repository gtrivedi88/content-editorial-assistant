"""
AsciiDoc List Parser

Handles parsing of AsciiDoc list structures:
- Unordered lists (bulleted)
- Ordered lists (numbered, non-procedure)
- Description lists (term/definition pairs)
- Nested list structures
- List items and formatting
"""

from typing import Dict, Any, List
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class ListParser(ElementParser):
    """Parser for AsciiDoc list structures (excluding procedures)."""
    
    # List type configurations
    LIST_TYPES = {
        'ulist': {
            'name': 'Unordered List',
            'icon': 'fas fa-list-ul',
            'marker_style': 'bullet'
        },
        'olist': {
            'name': 'Ordered List',
            'icon': 'fas fa-list-ol',
            'marker_style': 'number'
        },
        'dlist': {
            'name': 'Description List',
            'icon': 'fas fa-list',
            'marker_style': 'definition'
        }
    }
    
    # Procedure keywords to avoid (let ProcedureParser handle these)
    PROCEDURE_KEYWORDS = {
        'step', 'procedure', 'process', 'install', 'configure', 'setup',
        'create', 'build', 'deploy', 'run', 'execute', 'perform'
    }
    
    @property
    def element_type(self) -> str:
        return "list"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["ulist", "olist", "dlist", "list_item"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a general list (not a procedure)."""
        context = block_data.get('context', '')
        
        if context not in ['ulist', 'olist', 'dlist', 'list_item']:
            return False
        
        # For ordered lists, make sure it's NOT a procedure
        if context == 'olist':
            return not self._looks_like_procedure(block_data)
        
        # Unordered lists and description lists are always handled here
        return True
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse list element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with list-specific data
        """
        try:
            context = block_data.get('context', '')
            
            if context in ['ulist', 'olist', 'dlist']:
                return self._parse_list_container(block_data)
            elif context == 'list_item':
                return self._parse_list_item(block_data)
            else:
                return ElementParseResult(
                    success=False,
                    errors=[f"Unknown list context: {context}"]
                )
                
        except Exception as e:
            logger.error(f"Error parsing list element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"List parsing failed: {str(e)}"]
            )
    
    def _parse_list_container(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse main list container."""
        context = block_data.get('context', '')
        children = block_data.get('children', [])
        title = block_data.get('title', '')
        attributes = block_data.get('attributes', {})
        
        # Analyze list structure
        list_analysis = self._analyze_list_structure(children, context)
        
        # Get list type configuration
        list_config = self.LIST_TYPES.get(context, self.LIST_TYPES['ulist'])
        
        element_data = {
            'context': context,
            'list_type': context,
            'title': title,
            'item_count': len(children),
            'analysis': list_analysis,
            'config': list_config,
            'attributes': attributes,
            'has_title': bool(title),
            'raw_markup': self._reconstruct_list_markup(context, children, title)
        }
        
        validation_errors = self.validate_element(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def _parse_list_item(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse individual list item."""
        content = block_data.get('content', '').strip()
        text = block_data.get('text', '').strip()
        marker = block_data.get('marker', '')
        
        # Use text if content is empty (common in list items)
        item_content = content or text
        
        # Analyze item content
        item_analysis = self._analyze_item_content(item_content)
        
        element_data = {
            'context': 'list_item',
            'content': item_content,
            'marker': marker,
            'analysis': item_analysis,
            'word_count': len(item_content.split()) if item_content else 0,
            'length': len(item_content)
        }
        
        validation_errors = self._validate_list_item(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        context = element_data.get('context', 'list')
        
        if context in ['ulist', 'olist', 'dlist']:
            return self._get_list_display_info(element_data)
        elif context == 'list_item':
            return self._get_item_display_info(element_data)
        else:
            return {'icon': 'fas fa-list', 'title': 'List'}
    
    def _get_list_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for list container."""
        list_type = element_data.get('list_type', 'ulist')
        config = element_data.get('config', self.LIST_TYPES['ulist'])
        item_count = element_data.get('item_count', 0)
        title = element_data.get('title', '')
        analysis = element_data.get('analysis', {})
        
        display_title = f"{config['name']} ({item_count} items)"
        if title:
            display_title = f"{config['name']}: {title}"
        
        nested_levels = analysis.get('max_nesting_level', 0)
        complexity = analysis.get('complexity', 'simple')
        
        preview_text = f"{item_count} items"
        if nested_levels > 1:
            preview_text += f", {nested_levels} levels deep"
        if complexity != 'simple':
            preview_text += f", {complexity} structure"
        
        return {
            'icon': config['icon'],
            'title': display_title,
            'content_preview': preview_text,
            'skip_analysis': False,  # Lists should be analyzed
            'list_type': list_type,
            'item_count': item_count,
            'complexity': complexity,
            'has_nesting': nested_levels > 1,
            'has_custom_title': bool(title)
        }
    
    def _get_item_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for list item."""
        content = element_data.get('content', '')
        analysis = element_data.get('analysis', {})
        
        return {
            'icon': 'fas fa-circle',
            'title': 'List Item',
            'content_preview': content[:50] + '...' if len(content) > 50 else content,
            'skip_analysis': True,  # Individual items analyzed as part of list
            'item_type': analysis.get('type', 'text'),
            'has_content': bool(content.strip())
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate list element data."""
        context = element_data.get('context', '')
        
        if context in ['ulist', 'olist', 'dlist']:
            return self._validate_list_container(element_data)
        elif context == 'list_item':
            return self._validate_list_item(element_data)
        else:
            return []
    
    def _validate_list_container(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate list container."""
        errors = []
        item_count = element_data.get('item_count', 0)
        analysis = element_data.get('analysis', {})
        list_type = element_data.get('list_type', 'ulist')
        
        # Check item count
        if item_count == 0:
            errors.append("List has no items")
        elif item_count == 1:
            errors.append("Single-item list may be better as a paragraph")
        elif item_count > 50:
            errors.append("List has many items (>50) - consider restructuring")
        
        # Check nesting
        max_nesting = analysis.get('max_nesting_level', 0)
        if max_nesting > 4:
            errors.append("List has deep nesting (>4 levels) - consider simplifying")
        
        # Check empty items
        empty_items = analysis.get('empty_items', 0)
        if empty_items > 0:
            errors.append(f"{empty_items} list items are empty")
        
        # Type-specific validation
        if list_type == 'dlist':
            incomplete_definitions = analysis.get('incomplete_definitions', 0)
            if incomplete_definitions > 0:
                errors.append(f"{incomplete_definitions} terms lack definitions")
        
        return errors
    
    def _validate_list_item(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate list item."""
        errors = []
        content = element_data.get('content', '')
        word_count = element_data.get('word_count', 0)
        
        # Check item content
        if not content.strip():
            errors.append("List item is empty")
        elif word_count > 100:
            errors.append("List item is very long - consider breaking into paragraphs")
        
        # Check for sentence fragments
        if word_count > 5 and not content.rstrip().endswith(('.', '!', '?', ':')):
            errors.append("Long list item should end with punctuation")
        
        return errors
    
    def _looks_like_procedure(self, block_data: Dict[str, Any]) -> bool:
        """Check if an ordered list looks like a procedure."""
        title = block_data.get('title', '').lower()
        children = block_data.get('children', [])
        
        # Check title for procedure keywords
        if any(keyword in title for keyword in self.PROCEDURE_KEYWORDS):
            return True
        
        # Check if items start with action verbs
        action_verbs = {
            'open', 'click', 'select', 'choose', 'enter', 'type', 'press',
            'navigate', 'go', 'visit', 'access', 'run', 'execute'
        }
        
        action_item_count = 0
        for child in children[:3]:  # Check first 3 items
            content = child.get('content', '') or child.get('text', '')
            if content:
                first_word = content.split()[0].lower().rstrip('.,!?:;')
                if first_word in action_verbs:
                    action_item_count += 1
        
        # If most items start with action verbs, likely a procedure
        return action_item_count >= len(children[:3]) * 0.7
    
    def _analyze_list_structure(self, children: List[Dict[str, Any]], list_type: str) -> Dict[str, Any]:
        """Analyze list structure and content."""
        if not children:
            return {
                'total_items': 0,
                'empty_items': 0,
                'max_nesting_level': 0,
                'complexity': 'empty',
                'average_item_length': 0
            }
        
        empty_items = 0
        total_length = 0
        max_nesting = 0
        
        for child in children:
            content = child.get('content', '') or child.get('text', '')
            
            if not content.strip():
                empty_items += 1
            else:
                total_length += len(content)
            
            # Check for nested children (sub-lists)
            if child.get('children'):
                max_nesting = max(max_nesting, 1)
                # Could recursively check deeper nesting
        
        avg_length = total_length / max(1, len(children) - empty_items)
        
        # Determine complexity
        complexity = 'simple'
        if len(children) > 10 or max_nesting > 0:
            complexity = 'moderate'
        if len(children) > 25 or max_nesting > 2 or avg_length > 200:
            complexity = 'complex'
        
        analysis = {
            'total_items': len(children),
            'empty_items': empty_items,
            'max_nesting_level': max_nesting,
            'complexity': complexity,
            'average_item_length': int(avg_length)
        }
        
        # List type specific analysis
        if list_type == 'dlist':
            analysis['incomplete_definitions'] = self._count_incomplete_definitions(children)
        
        return analysis
    
    def _analyze_item_content(self, content: str) -> Dict[str, Any]:
        """Analyze individual list item content."""
        if not content:
            return {
                'type': 'empty',
                'word_count': 0,
                'has_punctuation': False
            }
        
        word_count = len(content.split())
        
        # Determine item type
        item_type = 'text'
        if any(marker in content for marker in ['http://', 'https://', 'ftp://']):
            item_type = 'link'
        elif content.strip().startswith('image:'):
            item_type = 'image'
        elif word_count <= 3:
            item_type = 'short'
        elif word_count > 20:
            item_type = 'long'
        
        return {
            'type': item_type,
            'word_count': word_count,
            'has_punctuation': content.rstrip().endswith(('.', '!', '?', ':'))
        }
    
    def _count_incomplete_definitions(self, children: List[Dict[str, Any]]) -> int:
        """Count definition list items that lack proper definitions."""
        # This is a simplified check - actual implementation would need
        # to understand the structure of definition lists better
        incomplete = 0
        for child in children:
            content = child.get('content', '') or child.get('text', '')
            # Simple heuristic: very short items might lack definitions
            if content and len(content.split()) < 3:
                incomplete += 1
        return incomplete
    
    def _reconstruct_list_markup(self, list_type: str, children: List[Dict[str, Any]], title: str = '') -> str:
        """Reconstruct AsciiDoc list markup."""
        markup_lines = []
        
        if title:
            markup_lines.append(f".{title}")
        
        for i, child in enumerate(children):
            content = child.get('content', '') or child.get('text', '')
            
            if list_type == 'ulist':
                markup_lines.append(f"* {content}")
            elif list_type == 'olist':
                markup_lines.append(f"{i + 1}. {content}")
            elif list_type == 'dlist':
                # Simplified - actual dlist structure is more complex
                markup_lines.append(f"Term:: {content}")
        
        return '\n'.join(markup_lines) 