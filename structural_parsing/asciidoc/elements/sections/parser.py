"""
AsciiDoc Section Parser

Handles parsing of AsciiDoc structural sections:
- Document sections (== Section, === Subsection, etc.)
- Preamble blocks (content before first section)
- Section hierarchy and organization
"""

from typing import Dict, Any, List
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class SectionParser(ElementParser):
    """Parser for AsciiDoc structural sections and preambles."""
    
    @property
    def element_type(self) -> str:
        return "section"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["section", "preamble"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a section or preamble."""
        context = block_data.get('context', '')
        return context in ['section', 'preamble']
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse section/preamble element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with section-specific data
        """
        try:
            context = block_data.get('context', '')
            content = block_data.get('content', '').strip()
            level = block_data.get('level', 0)
            title = block_data.get('title', '')
            children = block_data.get('children', [])
            
            if context == 'section':
                return self._parse_section(block_data)
            elif context == 'preamble':
                return self._parse_preamble(block_data)
            else:
                return ElementParseResult(
                    success=False,
                    errors=[f"Unknown section context: {context}"]
                )
                
        except Exception as e:
            logger.error(f"Error parsing section element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Section parsing failed: {str(e)}"]
            )
    
    def _parse_section(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse a document section."""
        title = block_data.get('title', '')
        level = block_data.get('level', 1)
        content = block_data.get('content', '').strip()
        children = block_data.get('children', [])
        
        # Analyze section structure
        section_analysis = self._analyze_section_structure(children, title, level)
        
        element_data = {
            'context': 'section',
            'title': title,
            'level': level,
            'content': content,
            'section_type': self._determine_section_type(level),
            'child_count': len(children),
            'analysis': section_analysis,
            'has_title': bool(title),
            'is_root_section': level == 1,
            'raw_markup': self._reconstruct_section_markup(title, level)
        }
        
        validation_errors = self.validate_element(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def _parse_preamble(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse document preamble."""
        content = block_data.get('content', '').strip()
        children = block_data.get('children', [])
        
        # Analyze preamble structure
        preamble_analysis = self._analyze_preamble_structure(children)
        
        element_data = {
            'context': 'preamble',
            'content': content,
            'child_count': len(children),
            'analysis': preamble_analysis,
            'has_content': bool(content) or len(children) > 0,
            'purpose': 'Document introduction before first section'
        }
        
        validation_errors = self.validate_element(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        context = element_data.get('context', 'section')
        
        if context == 'section':
            return self._get_section_display_info(element_data)
        elif context == 'preamble':
            return self._get_preamble_display_info(element_data)
        else:
            return {
                'icon': 'fas fa-file-alt',
                'title': 'Unknown Section',
                'skip_analysis': False
            }
    
    def _get_section_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for sections."""
        title = element_data.get('title', 'Untitled Section')
        level = element_data.get('level', 1)
        child_count = element_data.get('child_count', 0)
        section_type = element_data.get('section_type', 'section')
        
        # Choose icon based on level
        icon_map = {
            1: "fas fa-bookmark",     # Section
            2: "fas fa-tag",          # Subsection
            3: "fas fa-tags",         # Subsubsection
            4: "fas fa-arrow-right",  # Lower levels
            5: "fas fa-arrow-right",
            6: "fas fa-arrow-right"
        }
        icon = icon_map.get(level, "fas fa-bookmark")
        
        display_title = f"{section_type.title()}: {title}"
        
        return {
            'icon': icon,
            'title': display_title,
            'content_preview': f"{child_count} child blocks",
            'skip_analysis': False,  # Sections should be analyzed
            'section_level': level,
            'section_type': section_type,
            'estimated_importance': self._calculate_section_importance(level)
        }
    
    def _get_preamble_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for preamble."""
        child_count = element_data.get('child_count', 0)
        has_content = element_data.get('has_content', False)
        
        content_desc = f"{child_count} blocks" if child_count > 0 else "empty"
        
        return {
            'icon': 'fas fa-align-left',
            'title': 'Document Preamble',
            'content_preview': f"Introduction content ({content_desc})",
            'skip_analysis': False,  # Preambles should be analyzed
            'is_introduction': True,
            'has_content': has_content
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate section/preamble element data."""
        errors = []
        context = element_data.get('context', 'section')
        
        if context == 'section':
            title = element_data.get('title', '')
            level = element_data.get('level', 1)
            
            # Validate section title
            if not title or not title.strip():
                errors.append("Section title is missing or empty")
            
            # Validate section level
            if level < 1 or level > 6:
                errors.append(f"Invalid section level: {level} (should be 1-6)")
            
            # Check title length
            if len(title) > 100:
                errors.append("Section title is too long (>100 characters)")
        
        elif context == 'preamble':
            child_count = element_data.get('child_count', 0)
            
            # Warn if preamble is empty (not an error, but worth noting)
            if child_count == 0:
                # This is not an error, just a note
                pass
        
        return errors
    
    def _analyze_section_structure(self, children: List[Dict[str, Any]], title: str, level: int) -> Dict[str, Any]:
        """Analyze section structure and content."""
        child_contexts = [child.get('context', 'unknown') for child in children]
        
        return {
            'child_count': len(children),
            'child_types': list(set(child_contexts)),
            'has_subsections': any(child.get('context') == 'section' for child in children),
            'paragraph_count': child_contexts.count('paragraph'),
            'list_count': sum(1 for ctx in child_contexts if 'list' in ctx),
            'estimated_reading_time': len(children) * 0.5  # rough estimate
        }
    
    def _analyze_preamble_structure(self, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze preamble structure and content."""
        child_contexts = [child.get('context', 'unknown') for child in children]
        
        return {
            'child_count': len(children),
            'child_types': list(set(child_contexts)),
            'paragraph_count': child_contexts.count('paragraph'),
            'serves_as_introduction': len(children) > 0,
            'complexity': 'simple' if len(children) <= 2 else 'complex'
        }
    
    def _determine_section_type(self, level: int) -> str:
        """Determine section type based on level."""
        if level == 1:
            return "section"
        elif level == 2:
            return "subsection"
        elif level == 3:
            return "subsubsection"
        else:
            return "heading"
    
    def _calculate_section_importance(self, level: int) -> float:
        """Calculate section importance based on level (0.0-1.0)."""
        if level == 1:
            return 0.9  # Main sections are very important
        elif level == 2:
            return 0.7  # Subsections
        elif level == 3:
            return 0.5  # Subsubsections
        else:
            return 0.3  # Lower level headings
    
    def _reconstruct_section_markup(self, title: str, level: int) -> str:
        """Reconstruct AsciiDoc section markup."""
        equals = "=" * (level + 1)
        return f"{equals} {title}" 