"""
AsciiDoc Admonition Parser

Handles parsing of AsciiDoc admonition blocks:
- NOTE: General information
- TIP: Helpful hints
- IMPORTANT: Critical information
- WARNING: Potential problems
- CAUTION: Danger warnings
"""

from typing import Dict, Any, List
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class AdmonitionParser(ElementParser):
    """Parser for AsciiDoc admonition blocks."""
    
    # Define admonition types and their properties
    ADMONITION_TYPES = {
        'NOTE': {
            'icon': 'fas fa-info-circle',
            'color': 'blue',
            'severity': 'info',
            'purpose': 'General information'
        },
        'TIP': {
            'icon': 'fas fa-lightbulb',
            'color': 'green', 
            'severity': 'info',
            'purpose': 'Helpful hint'
        },
        'IMPORTANT': {
            'icon': 'fas fa-exclamation-circle',
            'color': 'orange',
            'severity': 'warning',
            'purpose': 'Critical information'
        },
        'WARNING': {
            'icon': 'fas fa-exclamation-triangle',
            'color': 'red',
            'severity': 'warning',
            'purpose': 'Potential problem'
        },
        'CAUTION': {
            'icon': 'fas fa-ban',
            'color': 'red',
            'severity': 'danger',
            'purpose': 'Danger warning'
        }
    }
    
    @property
    def element_type(self) -> str:
        return "admonition"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["admonition"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is an admonition."""
        context = block_data.get('context', '')
        return context == 'admonition'
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse admonition element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with admonition-specific data
        """
        try:
            content = block_data.get('content', '').strip()
            admonition_name = block_data.get('admonition_name', 'NOTE').upper()
            
            if not content:
                return ElementParseResult(
                    success=False,
                    errors=["Admonition content is empty"]
                )
            
            # Validate admonition type
            if admonition_name not in self.ADMONITION_TYPES:
                logger.warning(f"Unknown admonition type: {admonition_name}, defaulting to NOTE")
                admonition_name = 'NOTE'
            
            # Get admonition properties
            admonition_props = self.ADMONITION_TYPES[admonition_name]
            
            # Create element data
            element_data = {
                'content': content,
                'type': admonition_name,
                'properties': admonition_props,
                'length': len(content),
                'word_count': len(content.split()) if content else 0,
                'line_count': len(content.split('\n')) if content else 0,
                'has_title': bool(block_data.get('title')),
                'title': block_data.get('title', ''),
                'raw_markup': self._reconstruct_markup(admonition_name, content, block_data.get('title', ''))
            }
            
            # Validate admonition
            validation_errors = self.validate_element(element_data)
            
            return ElementParseResult(
                success=True,
                element_data=element_data,
                errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error parsing admonition element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Admonition parsing failed: {str(e)}"]
            )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        admonition_type = element_data.get('type', 'NOTE')
        properties = element_data.get('properties', self.ADMONITION_TYPES['NOTE'])
        content = element_data.get('content', '')
        title = element_data.get('title', '')
        
        # Create display title
        display_title = f"Admonition ({admonition_type})"
        if title:
            display_title = f"{admonition_type}: {title}"
        
        return {
            'icon': properties['icon'],
            'title': display_title,
            'content_preview': content[:100] + '...' if len(content) > 100 else content,
            'skip_analysis': False,  # Admonitions should be analyzed
            'admonition_type': admonition_type.lower(),
            'severity': properties['severity'],
            'color': properties['color'],
            'purpose': properties['purpose'],
            'has_custom_title': bool(title),
            'estimated_importance': self._calculate_importance(admonition_type)
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate admonition element data."""
        errors = []
        
        content = element_data.get('content', '')
        admonition_type = element_data.get('type', '')
        word_count = element_data.get('word_count', 0)
        line_count = element_data.get('line_count', 0)
        
        # Check for empty content
        if not content.strip():
            errors.append("Admonition content is empty")
        
        # Check content length
        if len(content) > 1000:
            errors.append("Admonition content is too long (>1000 characters)")
        elif len(content) < 5:
            errors.append("Admonition content is too short (<5 characters)")
        
        # Check word count
        if word_count > 150:
            errors.append("Admonition has too many words (>150) - consider breaking into paragraphs")
        elif word_count == 0:
            errors.append("Admonition has no words")
        
        # Check line count
        if line_count > 10:
            errors.append("Admonition spans too many lines (>10) - consider restructuring")
        
        # Type-specific validation
        if admonition_type == 'TIP':
            if 'must' in content.lower() or 'required' in content.lower():
                errors.append("TIP admonitions should provide helpful suggestions, not requirements")
        
        if admonition_type == 'WARNING' or admonition_type == 'CAUTION':
            if 'nice' in content.lower() or 'good' in content.lower():
                errors.append(f"{admonition_type} admonitions should focus on potential problems")
        
        if admonition_type == 'IMPORTANT':
            if len(content) < 20:
                errors.append("IMPORTANT admonitions should provide substantial information")
        
        # Check for unclear language
        unclear_phrases = ['might', 'maybe', 'possibly', 'could be']
        if any(phrase in content.lower() for phrase in unclear_phrases):
            errors.append("Admonition content should be clear and definitive")
        
        return errors
    
    def _reconstruct_markup(self, admonition_type: str, content: str, title: str = '') -> str:
        """Reconstruct the AsciiDoc markup for this admonition."""
        markup_lines = []
        
        # Add title if present
        if title:
            markup_lines.append(f".{title}")
        
        # Add admonition marker
        markup_lines.append(f"[{admonition_type}]")
        markup_lines.append("====")
        
        # Add content
        markup_lines.append(content)
        markup_lines.append("====")
        
        return '\n'.join(markup_lines)
    
    def _calculate_importance(self, admonition_type: str) -> float:
        """Calculate importance score based on admonition type (0.0-1.0)."""
        importance_map = {
            'CAUTION': 1.0,     # Highest - safety critical
            'WARNING': 0.9,     # Very high - problems
            'IMPORTANT': 0.8,   # High - critical info
            'TIP': 0.4,         # Medium - helpful
            'NOTE': 0.3         # Lower - general info
        }
        return importance_map.get(admonition_type, 0.5) 