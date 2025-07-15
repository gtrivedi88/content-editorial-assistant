"""
AsciiDoc Title Parser

Handles parsing of AsciiDoc titles and headings:
- Document titles (= Title)
- Section headings (== Section, === Subsection, etc.)
- Title hierarchy and levels
"""

from typing import Dict, Any, List
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class TitleParser(ElementParser):
    """Parser for AsciiDoc titles and headings."""
    
    @property
    def element_type(self) -> str:
        return "title"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["heading"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a title/heading."""
        context = block_data.get('context', '')
        return context == 'heading'
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse title/heading element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with title-specific data
        """
        try:
            content = block_data.get('content', '').strip()
            level = block_data.get('level', 0)
            
            if not content:
                return ElementParseResult(
                    success=False,
                    errors=["Title content is empty"]
                )
            
            # Determine title type based on level
            title_type = self._determine_title_type(level)
            
            # Extract title hierarchy information
            hierarchy_info = self._extract_hierarchy_info(block_data)
            
            # Create element data
            element_data = {
                'content': content,
                'level': level,
                'title_type': title_type,
                'hierarchy': hierarchy_info,
                'raw_markup': self._reconstruct_markup(content, level),
                'length': len(content),
                'word_count': len(content.split()) if content else 0
            }
            
            # Validate title
            validation_errors = self.validate_element(element_data)
            
            return ElementParseResult(
                success=True,
                element_data=element_data,
                errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error parsing title element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Title parsing failed: {str(e)}"]
            )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        level = element_data.get('level', 0)
        title_type = element_data.get('title_type', 'heading')
        content = element_data.get('content', '')
        
        # Choose appropriate icon based on level
        icon = self._get_title_icon(level)
        
        # Create display title
        display_title = f"{title_type.title()} (Level {level})"
        if level == 0:
            display_title = "Document Title"
        
        return {
            'icon': icon,
            'title': display_title,
            'content_preview': content[:50] + '...' if len(content) > 50 else content,
            'skip_analysis': False,  # Titles should be analyzed for style
            'level_class': f'title-level-{level}',
            'is_document_title': level == 0,
            'estimated_importance': self._calculate_importance(level)
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate title element data."""
        errors = []
        
        content = element_data.get('content', '')
        level = element_data.get('level', 0)
        word_count = element_data.get('word_count', 0)
        
        # Check for empty titles
        if not content.strip():
            errors.append("Title content is empty")
        
        # Check title length
        if len(content) > 200:
            errors.append("Title is too long (>200 characters)")
        elif len(content) < 3:
            errors.append("Title is too short (<3 characters)")
        
        # Check word count
        if word_count > 15:
            errors.append("Title has too many words (>15)")
        elif word_count == 0:
            errors.append("Title has no words")
        
        # Check level validity
        if level < 0 or level > 6:
            errors.append(f"Invalid title level: {level} (should be 0-6)")
        
        # Check for common title issues
        if content.endswith('.'):
            errors.append("Title should not end with a period")
        
        if content.isupper() and len(content) > 10:
            errors.append("Title should not be in all caps")
        
        if content.islower() and word_count > 1:
            errors.append("Title should be properly capitalized")
        
        return errors
    
    def _determine_title_type(self, level: int) -> str:
        """Determine the type of title based on level."""
        if level == 0:
            return "document_title"
        elif level == 1:
            return "section"
        elif level == 2:
            return "subsection"
        elif level == 3:
            return "subsubsection"
        else:
            return "heading"
    
    def _extract_hierarchy_info(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract hierarchy information."""
        level = block_data.get('level', 0)
        
        return {
            'level': level,
            'is_root': level == 0,
            'is_section': level == 1,
            'is_subsection': level >= 2,
            'depth': level,
            'max_expected_level': 6
        }
    
    def _reconstruct_markup(self, content: str, level: int) -> str:
        """Reconstruct the AsciiDoc markup for this title."""
        if level == 0:
            return f"= {content}"
        else:
            equals = "=" * (level + 1)
            return f"{equals} {content}"
    
    def _get_title_icon(self, level: int) -> str:
        """Get appropriate icon for title level."""
        icon_map = {
            0: "fas fa-crown",      # Document title
            1: "fas fa-heading",    # Section
            2: "fas fa-h1",         # Subsection  
            3: "fas fa-h2",         # Subsubsection
            4: "fas fa-h3",         # Lower levels
            5: "fas fa-h3",
            6: "fas fa-h3"
        }
        return icon_map.get(level, "fas fa-heading")
    
    def _calculate_importance(self, level: int) -> float:
        """Calculate importance score based on level (0.0-1.0)."""
        if level == 0:
            return 1.0  # Document title is most important
        elif level == 1:
            return 0.8  # Section titles
        elif level == 2:
            return 0.6  # Subsections
        elif level == 3:
            return 0.4  # Subsubsections
        else:
            return 0.2  # Lower level headings 