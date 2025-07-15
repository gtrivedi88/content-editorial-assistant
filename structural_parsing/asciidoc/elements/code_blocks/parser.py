"""
AsciiDoc Code Block Parser

Handles parsing of AsciiDoc code blocks:
- Listing blocks (----)
- Literal blocks (....)
- Source code with syntax highlighting
- Code attributes and metadata
"""

from typing import Dict, Any, List
import logging
import re

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class CodeBlockParser(ElementParser):
    """Parser for AsciiDoc code blocks."""
    
    # Define code block types and their properties
    CODE_BLOCK_TYPES = {
        'listing': {
            'icon': 'fas fa-code',
            'purpose': 'Source code listing',
            'delimiter': '----',
            'skip_analysis': True
        },
        'literal': {
            'icon': 'fas fa-terminal',
            'purpose': 'Literal text block',
            'delimiter': '....',
            'skip_analysis': True
        }
    }
    
    # Common programming languages for syntax highlighting
    KNOWN_LANGUAGES = {
        'python', 'java', 'javascript', 'typescript', 'c', 'cpp', 'csharp',
        'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala',
        'html', 'css', 'xml', 'json', 'yaml', 'sql', 'bash', 'shell',
        'dockerfile', 'markdown', 'asciidoc', 'properties', 'ini'
    }
    
    @property
    def element_type(self) -> str:
        return "code_block"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["listing", "literal"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is a code block."""
        context = block_data.get('context', '')
        return context in ['listing', 'literal']
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse code block element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with code block-specific data
        """
        try:
            content = block_data.get('content', '')
            context = block_data.get('context', 'listing')
            attributes = block_data.get('attributes', {})
            
            # Extract language and other code attributes
            language = self._extract_language(attributes)
            line_numbers = self._extract_line_numbers(attributes)
            
            # Analyze code content
            code_stats = self._analyze_code_content(content)
            
            # Get block type properties
            block_props = self.CODE_BLOCK_TYPES.get(context, self.CODE_BLOCK_TYPES['listing'])
            
            # Create element data
            element_data = {
                'content': content,
                'context': context,
                'language': language,
                'line_numbers': line_numbers,
                'properties': block_props,
                'stats': code_stats,
                'has_title': bool(block_data.get('title')),
                'title': block_data.get('title', ''),
                'raw_markup': self._reconstruct_markup(context, content, language, block_data.get('title', ''))
            }
            
            # Validate code block (minimal validation since we skip analysis)
            validation_errors = self.validate_element(element_data)
            
            return ElementParseResult(
                success=True,
                element_data=element_data,
                errors=validation_errors
            )
            
        except Exception as e:
            logger.error(f"Error parsing code block element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Code block parsing failed: {str(e)}"]
            )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        context = element_data.get('context', 'listing')
        language = element_data.get('language', '')
        properties = element_data.get('properties', self.CODE_BLOCK_TYPES['listing'])
        stats = element_data.get('stats', {})
        title = element_data.get('title', '')
        
        # Create display title
        display_title = f"Code Block ({context.title()})"
        if language:
            display_title = f"Code Block ({language.title()})"
        if title:
            display_title = f"{display_title}: {title}"
        
        return {
            'icon': properties['icon'],
            'title': display_title,
            'content_preview': f"{stats.get('line_count', 0)} lines of {language or 'text'}",
            'skip_analysis': properties['skip_analysis'],  # Code blocks skip style analysis
            'code_type': context,
            'language': language,
            'line_count': stats.get('line_count', 0),
            'estimated_complexity': self._estimate_complexity(stats),
            'has_custom_title': bool(title)
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate code block element data (minimal validation)."""
        errors = []
        
        content = element_data.get('content', '')
        language = element_data.get('language', '')
        stats = element_data.get('stats', {})
        
        # Basic content checks
        if not content.strip():
            errors.append("Code block is empty")
        
        # Line count checks
        line_count = stats.get('line_count', 0)
        if line_count > 200:
            errors.append("Code block is very long (>200 lines) - consider splitting")
        
        # Language validation
        if language and language.lower() not in self.KNOWN_LANGUAGES:
            errors.append(f"Unknown or unsupported language: {language}")
        
        # Check for potential security issues in code content
        if 'password' in content.lower() or 'secret' in content.lower():
            errors.append("Code block may contain sensitive information")
        
        return errors
    
    def _extract_language(self, attributes: Dict[str, Any]) -> str:
        """Extract programming language from attributes."""
        # Check common language attribute names
        language_keys = ['language', 'lang', 'source-language', 'source']
        
        for key in language_keys:
            if key in attributes:
                return str(attributes[key]).strip().lower()
        
        return ''
    
    def _extract_line_numbers(self, attributes: Dict[str, Any]) -> bool:
        """Check if line numbers are enabled."""
        linenums_keys = ['linenums', 'line-numbers', 'numbered']
        
        for key in linenums_keys:
            if key in attributes:
                value = str(attributes[key]).lower()
                return value in ['true', '1', 'yes', 'on']
        
        return False
    
    def _analyze_code_content(self, content: str) -> Dict[str, Any]:
        """Analyze code content and extract statistics."""
        if not content:
            return {'line_count': 0, 'char_count': 0, 'has_comments': False}
        
        lines = content.split('\n')
        
        # Count different types of lines
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif self._is_comment_line(stripped):
                comment_lines += 1
            else:
                code_lines += 1
        
        return {
            'line_count': len(lines),
            'code_lines': code_lines,
            'comment_lines': comment_lines,
            'blank_lines': blank_lines,
            'char_count': len(content),
            'has_comments': comment_lines > 0,
            'comment_ratio': comment_lines / max(1, code_lines + comment_lines)
        }
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is primarily a comment."""
        # Common comment patterns
        comment_patterns = [
            r'^\s*#',      # Python, shell, etc.
            r'^\s*//',     # Java, C++, JavaScript, etc.
            r'^\s*/\*',    # C-style block comments
            r'^\s*\*',     # Continuation of block comments
            r'^\s*--',     # SQL, Lua, etc.
            r'^\s*%',      # LaTeX, MATLAB
            r'^\s*"',      # Some languages use quotes for comments
        ]
        
        return any(re.match(pattern, line) for pattern in comment_patterns)
    
    def _estimate_complexity(self, stats: Dict[str, Any]) -> str:
        """Estimate code complexity based on statistics."""
        line_count = stats.get('line_count', 0)
        
        if line_count <= 10:
            return 'simple'
        elif line_count <= 50:
            return 'moderate'
        elif line_count <= 100:
            return 'complex'
        else:
            return 'very_complex'
    
    def _reconstruct_markup(self, context: str, content: str, language: str = '', title: str = '') -> str:
        """Reconstruct the AsciiDoc markup for this code block."""
        markup_lines = []
        
        # Add title if present
        if title:
            markup_lines.append(f".{title}")
        
        # Add source language attribute if present
        if language:
            markup_lines.append(f"[source,{language}]")
        
        # Add delimiter based on context
        delimiter = self.CODE_BLOCK_TYPES.get(context, {}).get('delimiter', '----')
        markup_lines.append(delimiter)
        
        # Add content
        markup_lines.append(content)
        markup_lines.append(delimiter)
        
        return '\n'.join(markup_lines) 