"""
AsciiDoc structural parser using asciidoctor library with DocBook XML output.
This parser leverages asciidoctor's robust parsing via DocBook XML for structural analysis.
"""

import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

from .types import (
    AsciiDocDocument, 
    AsciiDocBlock, 
    AsciiDocBlockType,
    AdmonitionType,
    AsciiDocAttributes,
    ParseResult
)


@dataclass
class AsciiDocParseError(Exception):
    """Exception raised when AsciiDoc parsing fails."""
    message: str
    original_error: Optional[Exception] = None


class AsciiDocParser:
    """
    AsciiDoc parser using asciidoctor with DocBook XML output.
    
    This parser uses asciidoctor to convert AsciiDoc to DocBook XML,
    then parses the structured XML to extract document structure.
    This approach ensures maximum compatibility and accuracy.
    """
    
    def __init__(self):
        self.asciidoctor_available = self._check_asciidoctor_availability()
        
        # DocBook namespace
        self.ns = {'db': 'http://docbook.org/ns/docbook'}
        
    def _check_asciidoctor_availability(self) -> bool:
        """Check if asciidoctor is available on the system."""
        try:
            result = subprocess.run(
                ['asciidoctor', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def parse(self, content: str, filename: str = "") -> ParseResult:
        """
        Parse AsciiDoc content into structural blocks using asciidoctor.
        
        Args:
            content: Raw AsciiDoc content
            filename: Optional filename for error reporting
            
        Returns:
            ParseResult with properly structured document
        """
        if not self.asciidoctor_available:
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=["Asciidoctor is not available. Please install with: gem install asciidoctor"]
            )
        
        try:
            # First, extract document attributes from source before conversion
            # This preserves the original attribute syntax for context-aware analysis
            source_attributes = self._extract_source_attributes(content)
            
            # Convert to DocBook XML using asciidoctor
            docbook_xml = self._convert_to_docbook(content)
            
            # Parse the DocBook XML structure
            document = self._parse_docbook_structure(docbook_xml, filename, source_attributes)
            
            return ParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse AsciiDoc: {str(e)}"]
            )
    
    def _convert_to_docbook(self, content: str) -> str:
        """
        Convert AsciiDoc content to DocBook XML using asciidoctor.
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            DocBook XML as string
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            # Use asciidoctor to convert to DocBook XML
            result = subprocess.run([
                'asciidoctor',
                '-b', 'docbook5',  # DocBook 5 backend
                '-o', '-',         # Output to stdout
                temp_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise AsciiDocParseError(
                    f"Asciidoctor failed: {result.stderr}",
                    original_error=None
                )
            
            return result.stdout
            
        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)
    
    def _extract_source_attributes(self, content: str) -> List[Dict[str, Union[str, int]]]:
        """
        Extract document attributes from AsciiDoc source before conversion.
        This preserves the original attribute syntax for context-aware analysis.
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            List of attribute dictionaries with line info
        """
        import re
        
        attributes = []
        lines = content.split('\n')
        
        # Pattern for AsciiDoc document attributes: :name: value
        attr_pattern = re.compile(r'^:([^:]+):\s*(.*)$')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            match = attr_pattern.match(line)
            if match:
                attr_name = match.group(1)
                attr_value = match.group(2)
                attributes.append({
                    'name': attr_name,
                    'value': attr_value,
                    'line_number': line_num,
                    'raw_content': line
                })
        
        return attributes
    
    def _parse_docbook_structure(self, docbook_xml: str, filename: str, source_attributes: Optional[List[Dict[str, Union[str, int]]]] = None) -> AsciiDocDocument:
        """
        Parse DocBook XML to extract AsciiDoc document structure.
        
        Args:
            docbook_xml: DocBook XML string from asciidoctor
            filename: Source filename for reference
            
        Returns:
            AsciiDocDocument with proper structure
        """
        try:
            # Parse XML
            root = ET.fromstring(docbook_xml)
            
            # Extract document metadata
            document_attrs = self._extract_document_attributes(root)
            document_title = self._extract_document_title(root)
            
            # Parse all blocks
            blocks = []
            
            # First, add document attribute blocks if we have source attributes
            if source_attributes:
                for attr in source_attributes:
                    raw_content = str(attr['raw_content'])
                    line_number = int(attr['line_number'])
                    
                    attr_block = AsciiDocBlock(
                        block_type=AsciiDocBlockType.ATTRIBUTE_ENTRY,
                        content=raw_content,
                        raw_content=raw_content,
                        start_line=line_number,
                        end_line=line_number,
                        start_pos=0,
                        end_pos=len(raw_content),
                        level=0,
                        parent=None,
                        children=[],
                        attributes=AsciiDocAttributes(),
                        title=None,
                        style=None,
                        admonition_type=None,
                        list_marker=None,
                        source_location=filename
                    )
                    blocks.append(attr_block)
            
            # Then parse the DocBook structure
            self._parse_blocks_recursive(root, blocks, level=0)
            
            return AsciiDocDocument(
                blocks=blocks,
                attributes=document_attrs,
                title=document_title,
                source_file=filename
            )
            
        except ET.ParseError as e:
            raise AsciiDocParseError(f"Failed to parse DocBook XML: {e}")
    
    def _extract_document_attributes(self, root: ET.Element) -> Dict[str, str]:
        """Extract document-level attributes from DocBook XML."""
        attrs = {}
        
        # Find info section
        info = root.find('.//db:info', self.ns)
        if info is not None:
            # Extract date
            date_elem = info.find('db:date', self.ns)
            if date_elem is not None:
                attrs['revdate'] = date_elem.text
            
            # Extract author
            author = info.find('db:author', self.ns)
            if author is not None:
                name_elem = author.find('db:personname', self.ns)
                if name_elem is not None:
                    first = name_elem.find('db:firstname', self.ns)
                    last = name_elem.find('db:surname', self.ns)
                    if first is not None and last is not None:
                        attrs['author'] = f"{first.text} {last.text}"
            
            # Extract other metadata
            authorinitials = info.find('db:authorinitials', self.ns)
            if authorinitials is not None:
                attrs['authorinitials'] = authorinitials.text
        
        return attrs
    
    def _extract_document_title(self, root: ET.Element) -> Optional[str]:
        """Extract document title from DocBook XML."""
        # Look for title in info section first
        info_title = root.find('.//db:info/db:title', self.ns)
        if info_title is not None:
            return info_title.text
        
        # Fall back to first title element
        title = root.find('.//db:title', self.ns)
        if title is not None:
            return title.text
        
        return None
    
    def _parse_blocks_recursive(self, element: ET.Element, blocks: List[AsciiDocBlock], level: int, parent: Optional[AsciiDocBlock] = None):
        """
        Recursively parse DocBook elements into AsciiDoc blocks.
        
        Args:
            element: Current XML element
            blocks: List to append blocks to
            level: Current nesting level
            parent: Parent block if any
        """
        for child in element:
            block = self._convert_element_to_block(child, level, parent)
            if block:
                blocks.append(block)
                
                # Recursively parse children for complex blocks
                if child.tag.endswith('section'):
                    # Parse section content and add to main blocks list
                    self._parse_blocks_recursive(child, blocks, level + 1, block)
                else:
                    # Parse nested content for non-section blocks
                    self._parse_blocks_recursive(child, blocks, level, block)
    
    def _convert_element_to_block(self, element: ET.Element, level: int, parent: Optional[AsciiDocBlock]) -> Optional[AsciiDocBlock]:
        """
        Convert a DocBook XML element to an AsciiDocBlock.
        
        Args:
            element: XML element to convert
            level: Current nesting level
            parent: Parent block if any
            
        Returns:
            AsciiDocBlock or None if element should be skipped
        """
        tag = element.tag.split('}')[-1]  # Remove namespace prefix
        
        # Map DocBook elements to AsciiDoc block types
        # Enhanced mapping to leverage asciidoctor's comprehensive DocBook output
        block_type_map = {
            # Headings and sections
            'title': AsciiDocBlockType.HEADING,
            'section': AsciiDocBlockType.SECTION,
            
            # Paragraphs and text blocks
            'simpara': AsciiDocBlockType.PARAGRAPH,
            'para': AsciiDocBlockType.PARAGRAPH,
            'formalpara': AsciiDocBlockType.PARAGRAPH,
            
            # Admonitions (all types)
            'note': AsciiDocBlockType.ADMONITION,
            'tip': AsciiDocBlockType.ADMONITION,
            'important': AsciiDocBlockType.ADMONITION,
            'warning': AsciiDocBlockType.ADMONITION,
            'caution': AsciiDocBlockType.ADMONITION,
            
            # Lists
            'orderedlist': AsciiDocBlockType.ORDERED_LIST,
            'itemizedlist': AsciiDocBlockType.UNORDERED_LIST,
            'variablelist': AsciiDocBlockType.UNORDERED_LIST,
            'listitem': AsciiDocBlockType.LIST_ITEM,
            'varlistentry': AsciiDocBlockType.LIST_ITEM,
            'term': AsciiDocBlockType.LIST_ITEM,
            
            # Code and literal blocks
            'programlisting': AsciiDocBlockType.LISTING,
            'literallayout': AsciiDocBlockType.LITERAL,
            'screen': AsciiDocBlockType.LITERAL,
            'synopsis': AsciiDocBlockType.LITERAL,
            
            # Examples and quotes
            'example': AsciiDocBlockType.EXAMPLE,
            'blockquote': AsciiDocBlockType.QUOTE,
            'epigraph': AsciiDocBlockType.QUOTE,
            
            # Specialized blocks
            'sidebar': AsciiDocBlockType.SIDEBAR,
            'abstract': AsciiDocBlockType.SIDEBAR,
            'partintro': AsciiDocBlockType.SIDEBAR,
            
            # Tables
            'table': AsciiDocBlockType.TABLE,
            'informaltable': AsciiDocBlockType.TABLE,
            'tgroup': AsciiDocBlockType.TABLE,
            'thead': AsciiDocBlockType.TABLE,
            'tbody': AsciiDocBlockType.TABLE,
            'tfoot': AsciiDocBlockType.TABLE,
            'row': AsciiDocBlockType.TABLE,
            'entry': AsciiDocBlockType.TABLE,
            
            # Media blocks
            'figure': AsciiDocBlockType.IMAGE,
            'informalfigure': AsciiDocBlockType.IMAGE,
            'mediaobject': AsciiDocBlockType.IMAGE,
            'imageobject': AsciiDocBlockType.IMAGE,
            'imagedata': AsciiDocBlockType.IMAGE,
            
            # Structural elements
            'preface': AsciiDocBlockType.SECTION,
            'chapter': AsciiDocBlockType.SECTION,
            'appendix': AsciiDocBlockType.SECTION,
            'part': AsciiDocBlockType.SECTION,
            'article': AsciiDocBlockType.SECTION,
            'book': AsciiDocBlockType.SECTION,
            
            # Inline elements that might appear as blocks
            'phrase': AsciiDocBlockType.PARAGRAPH,
            'emphasis': AsciiDocBlockType.PARAGRAPH,
            'strong': AsciiDocBlockType.PARAGRAPH,
            'literal': AsciiDocBlockType.LITERAL,
            'code': AsciiDocBlockType.LITERAL,
            'command': AsciiDocBlockType.LITERAL,
            'option': AsciiDocBlockType.LITERAL,
            'filename': AsciiDocBlockType.LITERAL,
            'computeroutput': AsciiDocBlockType.LITERAL,
            'userinput': AsciiDocBlockType.LITERAL,
            
            # Special blocks
            'bridgehead': AsciiDocBlockType.HEADING,
            'callout': AsciiDocBlockType.PARAGRAPH,
            'calloutlist': AsciiDocBlockType.UNORDERED_LIST,
            'co': AsciiDocBlockType.PARAGRAPH,
            'footnote': AsciiDocBlockType.PARAGRAPH,
            'annotation': AsciiDocBlockType.PARAGRAPH,
            'remark': AsciiDocBlockType.PARAGRAPH,
            'comment': AsciiDocBlockType.PARAGRAPH,
        }
        
        block_type = block_type_map.get(tag)
        if not block_type:
            return None
        
        # Extract text content (excluding child elements for now)
        content = self._extract_text_content(element)
        
        # Create attributes
        attributes = AsciiDocAttributes()
        if 'xml:id' in element.attrib:
            attributes.id = element.attrib['xml:id']
        
        # Handle special cases
        admonition_type = None
        if tag in ['note', 'tip', 'important', 'warning', 'caution']:
            admonition_type = AdmonitionType[tag.upper()]
        
        # Adjust level for sections
        block_level = level
        if tag == 'section':
            # Extract title from first child title element
            title_elem = element.find('db:title', self.ns)
            if title_elem is not None:
                content = title_elem.text or ""
                block_type = AsciiDocBlockType.HEADING
                block_level = level
        
        return AsciiDocBlock(
            block_type=block_type,
            content=content,
            raw_content=content,
            start_line=0,  # DocBook doesn't preserve line numbers
            end_line=0,
            start_pos=0,
            end_pos=len(content),
            level=block_level,
            parent=parent,
            children=[],
            attributes=attributes,
            title=None,
            style=None,
            admonition_type=admonition_type,
            list_marker=None,
            source_location=None
        )
    
    def _extract_text_content(self, element: ET.Element) -> str:
        """
        Extract clean text content from XML element.
        
        Args:
            element: XML element
            
        Returns:
            Clean text content
        """
        # For simple elements, get direct text
        if element.text and not list(element):
            return element.text.strip()
        
        # For complex elements, get all text content
        text_parts = []
        
        # Get direct text
        if element.text:
            text_parts.append(element.text.strip())
        
        # Get text from child elements recursively
        for child in element:
            child_text = self._extract_text_content(child)
            if child_text:
                text_parts.append(child_text)
            
            # Get tail text after child element
            if child.tail:
                text_parts.append(child.tail.strip())
        
        return ' '.join(part for part in text_parts if part).strip() 