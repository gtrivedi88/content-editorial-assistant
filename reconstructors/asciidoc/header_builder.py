"""
AsciiDoc Header Builder

Handles construction of AsciiDoc document headers including:
- Document title
- Author information
- Revision information  
- Document attributes
- Table of contents and other settings
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class HeaderBuilder:
    """
    Builds AsciiDoc document headers from document metadata.
    
    Handles the construction of document titles, author information,
    revision data, and document attributes in proper AsciiDoc format.
    """
    
    def __init__(self, include_metadata: bool = True, include_attributes: bool = True):
        """
        Initialize the header builder.
        
        Args:
            include_metadata: Whether to include author/revision metadata
            include_attributes: Whether to include document attributes
        """
        self.include_metadata = include_metadata
        self.include_attributes = include_attributes
        self.logger = logging.getLogger(__name__)
    
    def build_header(self, document: Any, original_content: str = "") -> str:
        """
        Build complete AsciiDoc header from document metadata.
        
        Args:
            document: Parsed AsciiDoc document
            original_content: Original document content for fallback
            
        Returns:
            Formatted AsciiDoc header string
        """
        header_parts = []
        
        # Build document title
        title_part = self._build_document_title(document)
        if title_part:
            header_parts.append(title_part)
        
        # Build author and revision info
        if self.include_metadata:
            metadata_part = self._build_metadata_section(document)
            if metadata_part:
                header_parts.append(metadata_part)
        
        # Build document attributes
        if self.include_attributes:
            attributes_part = self._build_attributes_section(document)
            if attributes_part:
                header_parts.append(attributes_part)
        
        # Join all parts
        if header_parts:
            return '\n'.join(header_parts) + '\n'
        
        # Fallback: extract from original content
        return self._extract_header_from_original(original_content)
    
    def _build_document_title(self, document: Any) -> Optional[str]:
        """
        Build the document title line.
        
        Args:
            document: Parsed document
            
        Returns:
            Formatted document title or None
        """
        # Try to get title from document object
        title = None
        
        if hasattr(document, 'title') and document.title:
            title = document.title
        elif hasattr(document, 'attributes') and 'doctitle' in document.attributes:
            title = document.attributes['doctitle']
        
        if title:
            return f"= {title}"
        
        return None
    
    def _build_metadata_section(self, document: Any) -> Optional[str]:
        """
        Build author and revision metadata section.
        
        Args:
            document: Parsed document
            
        Returns:
            Formatted metadata section or None
        """
        metadata_lines = []
        
        # Extract author information
        author_info = self._extract_author_info(document)
        if author_info:
            metadata_lines.append(author_info)
        
        # Extract revision information
        revision_info = self._extract_revision_info(document)
        if revision_info:
            metadata_lines.append(revision_info)
        
        return '\n'.join(metadata_lines) if metadata_lines else None
    
    def _build_attributes_section(self, document: Any) -> Optional[str]:
        """
        Build document attributes section.
        
        Args:
            document: Parsed document
            
        Returns:
            Formatted attributes section or None
        """
        if not hasattr(document, 'attributes'):
            return None
        
        # Filter out system attributes and get user-defined ones
        user_attributes = self._filter_user_attributes(document.attributes)
        
        if not user_attributes:
            return None
        
        # Format attributes in proper order
        attribute_lines = []
        
        # Common document attributes in preferred order
        ordered_attrs = [
            'toc', 'numbered', 'source-highlighter', 'icons', 'experimental',
            'sectanchors', 'sectlinks', 'sectnums', 'docinfo'
        ]
        
        # Add ordered attributes first
        for attr_name in ordered_attrs:
            if attr_name in user_attributes:
                attr_line = self._format_attribute(attr_name, user_attributes[attr_name])
                if attr_line:
                    attribute_lines.append(attr_line)
                del user_attributes[attr_name]
        
        # Add remaining attributes
        for attr_name, attr_value in user_attributes.items():
            attr_line = self._format_attribute(attr_name, attr_value)
            if attr_line:
                attribute_lines.append(attr_line)
        
        return '\n'.join(attribute_lines) if attribute_lines else None
    
    def _extract_author_info(self, document: Any) -> Optional[str]:
        """Extract and format author information."""
        if not hasattr(document, 'attributes'):
            return None
        
        attrs = document.attributes
        
        # Build author line
        author_parts = []
        
        # Get author name
        if 'author' in attrs:
            author_parts.append(attrs['author'])
        elif 'firstname' in attrs and 'lastname' in attrs:
            author_parts.append(f"{attrs['firstname']} {attrs['lastname']}")
        elif 'firstname' in attrs:
            author_parts.append(attrs['firstname'])
        
        # Add email if available
        if 'email' in attrs and author_parts:
            author_parts.append(f"<{attrs['email']}>")
        
        return ' '.join(author_parts) if author_parts else None
    
    def _extract_revision_info(self, document: Any) -> Optional[str]:
        """Extract and format revision information."""
        if not hasattr(document, 'attributes'):
            return None
        
        attrs = document.attributes
        revision_parts = []
        
        # Build revision line: version, date: remark
        if 'revnumber' in attrs:
            revision_parts.append(f"v{attrs['revnumber']}")
        
        if 'revdate' in attrs:
            if revision_parts:
                revision_parts.append(f", {attrs['revdate']}")
            else:
                revision_parts.append(attrs['revdate'])
        
        if 'revremark' in attrs:
            if revision_parts:
                revision_parts.append(f": {attrs['revremark']}")
            else:
                revision_parts.append(attrs['revremark'])
        
        return ''.join(revision_parts) if revision_parts else None
    
    def _filter_user_attributes(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out system attributes to get user-defined ones.
        
        Args:
            attributes: All document attributes
            
        Returns:
            User-defined attributes only
        """
        # System attributes to exclude (these are set by AsciiDoctor)
        system_attrs = {
            'attribute-undefined', 'attribute-missing', 'appendix-caption',
            'appendix-refsig', 'caution-caption', 'chapter-refsig', 'example-caption',
            'figure-caption', 'important-caption', 'last-update-label', 'note-caption',
            'part-refsig', 'prewrap', 'sectids', 'section-refsig', 'table-caption',
            'tip-caption', 'toc-placement', 'toc-title', 'untitled-label',
            'version-label', 'warning-caption', 'notitle', 'embedded', 'asciidoctor',
            'asciidoctor-version', 'safe-mode-name', 'safe-mode-unsafe', 'safe-mode-level',
            'max-include-depth', 'docdir', 'user-home', 'doctype', 'htmlsyntax',
            'backend-html5-doctype-article', 'doctype-article', 'backend-html5',
            'backend', 'outfilesuffix', 'filetype', 'filetype-html',
            'basebackend-html-doctype-article', 'basebackend-html', 'basebackend',
            'stylesdir', 'iconsdir', 'localdate', 'localyear', 'localtime',
            'localdatetime', 'docdate', 'docyear', 'doctime', 'docdatetime',
            'doctitle', 'authorcount', 'firstname', 'authorinitials', 'lastname',
            'author', 'email', 'authors', 'revnumber', 'revdate', 'revremark'
        }
        
        return {k: v for k, v in attributes.items() if k not in system_attrs}
    
    def _format_attribute(self, name: str, value: Any) -> Optional[str]:
        """
        Format a single attribute in AsciiDoc syntax.
        
        Args:
            name: Attribute name
            value: Attribute value
            
        Returns:
            Formatted attribute line or None
        """
        if value is None:
            return None
        
        # Handle special attributes
        if name.startswith('!'):
            # Unset attribute
            return f":{name}:"
        elif name == 'experimental' and not value:
            # Unset experimental
            return ":!experimental:"
        elif isinstance(value, bool):
            if value:
                return f":{name}:"
            else:
                return f":!{name}:"
        elif str(value).strip() == "":
            # Empty value attribute
            return f":{name}:"
        else:
            # Regular attribute with value
            return f":{name}: {value}"
    
    def _extract_header_from_original(self, original_content: str) -> str:
        """
        Extract header from original content as fallback.
        
        Args:
            original_content: Original document content
            
        Returns:
            Extracted header or empty string
        """
        if not original_content:
            return ""
        
        lines = original_content.split('\n')
        header_lines = []
        in_header = True
        
        for line in lines:
            stripped = line.strip()
            
            if in_header:
                # Check if this is still part of the header
                if (stripped.startswith('=') or  # Title
                    stripped.startswith(':') or  # Attribute
                    stripped == '' or           # Empty line
                    self._looks_like_author_line(stripped) or
                    self._looks_like_revision_line(stripped)):
                    header_lines.append(line)
                else:
                    # End of header
                    in_header = False
                    break
            else:
                break
        
        # Find the last non-empty line to avoid trailing newlines
        while header_lines and header_lines[-1].strip() == '':
            header_lines.pop()
        
        if header_lines:
            return '\n'.join(header_lines) + '\n'
        
        return ""
    
    def _looks_like_author_line(self, line: str) -> bool:
        """Check if line looks like author information."""
        # Simple heuristic: contains name-like patterns and possibly email
        return ('@' in line and '<' in line and '>' in line) or \
               (len(line.split()) >= 2 and not line.startswith(':') and 
                not line.startswith('=') and not line.startswith('v'))
    
    def _looks_like_revision_line(self, line: str) -> bool:
        """Check if line looks like revision information."""
        # Simple heuristic: starts with version pattern or date pattern
        return (line.startswith('v') and ',' in line) or \
               (len(line.split('-')) == 3)  # Date pattern 