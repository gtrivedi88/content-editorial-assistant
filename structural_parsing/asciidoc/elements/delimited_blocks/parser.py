"""
AsciiDoc Delimited Blocks Parser

Handles parsing of AsciiDoc delimited blocks:
- Sidebar blocks (****)
- Example blocks (====)
- Quote blocks (____)
- Verse blocks ([verse])
- Pass blocks (++++))
- Open blocks (--)
"""

from typing import Dict, Any, List, Optional
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class DelimitedBlockParser(ElementParser):
    """Parser for AsciiDoc delimited block structures."""
    
    # Delimited block type configurations
    BLOCK_TYPES = {
        'sidebar': {
            'name': 'Sidebar',
            'icon': 'fas fa-columns',
            'delimiter': '****',
            'purpose': 'Supplementary content',
            'skip_analysis': False
        },
        'example': {
            'name': 'Example',
            'icon': 'fas fa-lightbulb',
            'delimiter': '====',
            'purpose': 'Illustrative content',
            'skip_analysis': False
        },
        'quote': {
            'name': 'Quote',
            'icon': 'fas fa-quote-left',
            'delimiter': '____',
            'purpose': 'Quoted content',
            'skip_analysis': False
        },
        'verse': {
            'name': 'Verse',
            'icon': 'fas fa-feather',
            'delimiter': '____',
            'purpose': 'Poetry or verse',
            'skip_analysis': False
        },
        'pass': {
            'name': 'Passthrough',
            'icon': 'fas fa-arrow-right',
            'delimiter': '++++',
            'purpose': 'Raw content passthrough',
            'skip_analysis': True  # Skip analysis for passthrough content
        },
        'open': {
            'name': 'Open Block',
            'icon': 'fas fa-square',
            'delimiter': '--',
            'purpose': 'Generic container',
            'skip_analysis': False
        }
    }
    
    @property
    def element_type(self) -> str:
        return "delimited_block"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["sidebar", "example", "quote", "verse", "pass", "open"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a delimited block."""
        context = block_data.get('context', '')
        return context in self.supported_contexts
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse delimited block element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with delimited block-specific data
        """
        try:
            context = block_data.get('context', '')
            content = block_data.get('content', '').strip()
            title = block_data.get('title', '')
            attributes = block_data.get('attributes', {})
            
            # Get block type configuration
            block_config = self.BLOCK_TYPES.get(context, self.BLOCK_TYPES['open'])
            
            # Analyze block content
            content_analysis = self._analyze_block_content(content, context)
            
            # Extract block-specific attributes
            block_attributes = self._extract_block_attributes(attributes, context)
            
            element_data = {
                'context': context,
                'block_type': context,
                'content': content,
                'title': title,
                'config': block_config,
                'analysis': content_analysis,
                'attributes': block_attributes,
                'has_title': bool(title),
                'raw_markup': self._reconstruct_block_markup(context, content, title, attributes or {})
            }
            
            validation_errors = self.validate_element(element_data)
            
            return ElementParseResult(
                success=True,
                element_data=element_data,
                errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error parsing delimited block element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Delimited block parsing failed: {str(e)}"]
            )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        block_type = element_data.get('block_type', 'open')
        config = element_data.get('config', self.BLOCK_TYPES['open'])
        content = element_data.get('content', '')
        title = element_data.get('title', '')
        analysis = element_data.get('analysis', {})
        
        # Create display title
        display_title = config['name']
        if title:
            display_title = f"{config['name']}: {title}"
        
        # Create content preview
        content_preview = self._create_content_preview(content, block_type, analysis)
        
        return {
            'icon': config['icon'],
            'title': display_title,
            'content_preview': content_preview,
            'skip_analysis': config['skip_analysis'],
            'block_type': block_type,
            'purpose': config['purpose'],
            'has_custom_title': bool(title),
            'estimated_reading_time': analysis.get('reading_time', 0)
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate delimited block element data."""
        errors = []
        
        content = element_data.get('content', '')
        block_type = element_data.get('block_type', '')
        analysis = element_data.get('analysis', {})
        
        # General content validation
        if not content.strip():
            errors.append(f"{block_type.title()} block is empty")
        
        # Type-specific validation
        if block_type == 'quote':
            errors.extend(self._validate_quote_block(element_data))
        elif block_type == 'verse':
            errors.extend(self._validate_verse_block(element_data))
        elif block_type == 'sidebar':
            errors.extend(self._validate_sidebar_block(element_data))
        elif block_type == 'example':
            errors.extend(self._validate_example_block(element_data))
        
        # Check content length
        word_count = analysis.get('word_count', 0)
        if word_count > 500:
            errors.append(f"{block_type.title()} block is very long (>{word_count} words) - consider splitting")
        
        return errors
    
    def _analyze_block_content(self, content: str, block_type: str) -> Dict[str, Any]:
        """Analyze delimited block content."""
        if not content:
            return {
                'word_count': 0,
                'line_count': 0,
                'paragraph_count': 0,
                'reading_time': 0,
                'has_formatting': False
            }
        
        lines = content.split('\n')
        words = content.split()
        
        # Count paragraphs (separated by blank lines)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # Check for formatting markers
        has_formatting = any(marker in content for marker in ['*', '_', '`', '+', '^', '~'])
        
        # Estimate reading time (average 200 words per minute)
        reading_time = max(1, len(words) // 200)
        
        analysis = {
            'word_count': len(words),
            'line_count': len(lines),
            'paragraph_count': len(paragraphs),
            'reading_time': reading_time,
            'has_formatting': has_formatting
        }
        
        # Block type specific analysis
        if block_type == 'quote':
            analysis.update(self._analyze_quote_content(content))
        elif block_type == 'verse':
            analysis.update(self._analyze_verse_content(content))
        
        return analysis
    
    def _analyze_quote_content(self, content: str) -> Dict[str, Any]:
        """Analyze quote-specific content."""
        # Check for attribution patterns
        has_attribution = any(pattern in content for pattern in [' -- ', ' - ', '\n--', '\n-'])
        
        # Check for citation patterns
        has_citation = any(pattern in content for pattern in ['(', '[', 'Source:', 'From:'])
        
        return {
            'has_attribution': has_attribution,
            'has_citation': has_citation,
            'is_complete_quote': has_attribution or has_citation
        }
    
    def _analyze_verse_content(self, content: str) -> Dict[str, Any]:
        """Analyze verse-specific content."""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Check line length consistency (poems often have similar line lengths)
        if lines:
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            line_length_variance = sum((len(line) - avg_line_length) ** 2 for line in lines) / len(lines)
            is_structured = line_length_variance < 100  # Low variance suggests structure
        else:
            is_structured = False
        
        # Check for rhyme patterns (very basic)
        has_potential_rhyme = any(line.endswith(('ing', 'ed', 'tion', 'ly')) for line in lines)
        
        return {
            'verse_lines': len(lines),
            'average_line_length': int(avg_line_length) if lines else 0,
            'is_structured': is_structured,
            'has_potential_rhyme': has_potential_rhyme
        }
    
    def _extract_block_attributes(self, attributes: Dict[str, Any], block_type: str) -> Dict[str, Any]:
        """Extract block-specific attributes."""
        block_attrs = {
            'style': attributes.get('style'),
            'role': attributes.get('role'),
            'id': attributes.get('id')
        }
        
        # Block type specific attributes
        if block_type == 'quote':
            block_attrs.update({
                'attribution': attributes.get('attribution'),
                'citetitle': attributes.get('citetitle'),
                'citework': attributes.get('citework')
            })
        elif block_type == 'verse':
            block_attrs.update({
                'attribution': attributes.get('attribution'),
                'citetitle': attributes.get('citetitle')
            })
        
        return block_attrs
    
    def _validate_quote_block(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate quote block specific requirements."""
        errors = []
        analysis = element_data.get('analysis', {})
        attributes = element_data.get('attributes', {})
        
        # Check for attribution
        if not analysis.get('is_complete_quote', False) and not attributes.get('attribution'):
            errors.append("Quote block should include attribution or source")
        
        # Check quote formatting
        content = element_data.get('content', '')
        if content.startswith('"') and not content.endswith('"'):
            errors.append("Quote appears to have unmatched quotation marks")
        
        return errors
    
    def _validate_verse_block(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate verse block specific requirements."""
        errors = []
        analysis = element_data.get('analysis', {})
        
        # Check for reasonable verse structure
        verse_lines = analysis.get('verse_lines', 0)
        if verse_lines == 1:
            errors.append("Single-line verse may be better as a quote")
        elif verse_lines > 50:
            errors.append("Very long verse - consider breaking into stanzas")
        
        return errors
    
    def _validate_sidebar_block(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate sidebar block specific requirements."""
        errors = []
        title = element_data.get('title', '')
        
        # Sidebars should generally have titles
        if not title:
            errors.append("Sidebar block should have a title for better context")
        
        return errors
    
    def _validate_example_block(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate example block specific requirements."""
        errors = []
        content = element_data.get('content', '')
        analysis = element_data.get('analysis', {})
        
        # Examples should be substantial enough to be useful
        word_count = analysis.get('word_count', 0)
        if word_count < 10:
            errors.append("Example block should contain substantial illustrative content")
        
        return errors
    
    def _create_content_preview(self, content: str, block_type: str, analysis: Dict[str, Any]) -> str:
        """Create appropriate content preview for block type."""
        if not content:
            return "Empty block"
        
        word_count = analysis.get('word_count', 0)
        
        if block_type == 'quote':
            preview = f"Quote ({word_count} words)"
            if analysis.get('has_attribution', False):
                preview += " with attribution"
        elif block_type == 'verse':
            line_count = analysis.get('verse_lines', 0)
            preview = f"Verse ({line_count} lines, {word_count} words)"
        elif block_type == 'sidebar':
            preview = f"Sidebar content ({word_count} words)"
        elif block_type == 'example':
            preview = f"Example ({word_count} words)"
        elif block_type == 'pass':
            preview = f"Passthrough content ({len(content)} chars)"
        else:
            preview = f"{word_count} words"
        
        # Add reading time for longer content
        reading_time = analysis.get('reading_time', 0)
        if reading_time > 0:
            preview += f", ~{reading_time} min read"
        
        return preview
    
    def _reconstruct_block_markup(self, block_type: str, content: str, title: str = '', attributes: Optional[Dict[str, Any]] = None) -> str:
        """Reconstruct AsciiDoc delimited block markup."""
        if attributes is None:
            attributes = {}
        
        markup_lines = []
        
        # Add title if present
        if title:
            markup_lines.append(f".{title}")
        
        # Add style/role attributes if present
        attrs = []
        if attributes.get('style'):
            attrs.append(attributes['style'])
        if attributes.get('role'):
            attrs.append(f"role={attributes['role']}")
        
        if attrs:
            markup_lines.append(f"[{', '.join(attrs)}]")
        elif block_type == 'verse':
            markup_lines.append("[verse]")
        
        # Add delimiter
        config = self.BLOCK_TYPES.get(block_type, self.BLOCK_TYPES['open'])
        delimiter = config['delimiter']
        markup_lines.append(delimiter)
        
        # Add content
        if content:
            markup_lines.append(content)
        
        # Close delimiter
        markup_lines.append(delimiter)
        
        return '\n'.join(markup_lines) 