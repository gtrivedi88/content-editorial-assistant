"""
DITA structural parser using XML processing.
This parser handles DITA topic types and provides structural analysis.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import re

from .types import (
    DITADocument,
    DITABlock,
    DITABlockType,
    DITATopicType,
    DITAParseResult
)


class DITAParser:
    """
    DITA parser for Adobe Experience Manager workflows.
    
    This parser handles DITA XML documents and provides structural
    parsing for concept, task, and reference topic types.
    """
    
    def __init__(self):
        """Initialize DITA parser."""
        # Comprehensive DITA element mapping
        self.element_mapping = {
            # Basic elements
            'title': DITABlockType.TITLE,
            'shortdesc': DITABlockType.SHORTDESC,
            'p': DITABlockType.PARAGRAPH,
            'section': DITABlockType.SECTION,
            'example': DITABlockType.EXAMPLE,
            
            # Task-specific elements
            'prereq': DITABlockType.PREREQ,
            'context': DITABlockType.CONTEXT,
            'steps': DITABlockType.STEPS,
            'step': DITABlockType.STEP,
            'cmd': DITABlockType.CMD,
            'info': DITABlockType.INFO,
            'stepresult': DITABlockType.STEPRESULT,
            'result': DITABlockType.RESULT,
            'postreq': DITABlockType.POSTREQ,
            'substeps': DITABlockType.SUBSTEPS,
            'substep': DITABlockType.SUBSTEP,
            'choices': DITABlockType.CHOICES,
            'choice': DITABlockType.CHOICE,
            'troubleshooting': DITABlockType.TROUBLESHOOTING,
            
            # Reference-specific elements
            'refbody': DITABlockType.REFBODY,
            'properties': DITABlockType.PROPERTIES,
            'property': DITABlockType.PROPERTY,
            
            # Lists
            'ul': DITABlockType.UNORDERED_LIST,
            'ol': DITABlockType.ORDERED_LIST,
            'li': DITABlockType.LIST_ITEM,
            'sl': DITABlockType.SIMPLE_LIST,
            'sli': DITABlockType.LIST_ITEM,
            'dl': DITABlockType.DEFINITION_LIST,
            'dlentry': DITABlockType.LIST_ITEM,
            'parml': DITABlockType.PARAMETER_LIST,
            'plentry': DITABlockType.LIST_ITEM,
            
            # Code and technical
            'codeblock': DITABlockType.CODEBLOCK,
            'codeph': DITABlockType.CODEPH,
            'coderef': DITABlockType.CODEREF,
            'filepath': DITABlockType.FILEPATH,
            'cmdname': DITABlockType.CMDNAME,
            'varname': DITABlockType.VARNAME,
            'apiname': DITABlockType.APINAME,
            'syntaxdiagram': DITABlockType.SYNTAXDIAGRAM,
            
            # UI elements
            'uicontrol': DITABlockType.UICONTROL,
            'wintitle': DITABlockType.WINTITLE,
            'menucascade': DITABlockType.MENUCASCADE,
            
            # Tables
            'table': DITABlockType.TABLE,
            'simpletable': DITABlockType.SIMPLETABLE,
            
            # Notes
            'note': DITABlockType.NOTE,
            
            # Body containers
            'conbody': DITABlockType.BODY,
            'taskbody': DITABlockType.BODY,
            'refbody': DITABlockType.BODY,
            'troublebody': DITABlockType.BODY,
            'body': DITABlockType.BODY,  # Generic topic body
            
            # Additional DITA elements that exist in the wild
            'abstract': DITABlockType.PARAGRAPH,
            'sectiondiv': DITABlockType.SECTION,
            'bodydiv': DITABlockType.SECTION,
            'div': DITABlockType.SECTION,
            'fig': DITABlockType.EXAMPLE,
            'image': DITABlockType.PARAGRAPH,
            'object': DITABlockType.PARAGRAPH,
            'desc': DITABlockType.PARAGRAPH,
            'longdesc': DITABlockType.PARAGRAPH,
            
            # Table elements
            'table': DITABlockType.TABLE,
            'simpletable': DITABlockType.SIMPLETABLE,
            'sthead': DITABlockType.PARAGRAPH,
            'strow': DITABlockType.PARAGRAPH,
            'stentry': DITABlockType.PARAGRAPH,
            'thead': DITABlockType.PARAGRAPH,
            'tbody': DITABlockType.PARAGRAPH,
            'row': DITABlockType.PARAGRAPH,
            'entry': DITABlockType.PARAGRAPH,
            
            # Definition list elements
            'dt': DITABlockType.PARAGRAPH,
            'dd': DITABlockType.PARAGRAPH,
            'dlentry': DITABlockType.LIST_ITEM,
            'dlhead': DITABlockType.PARAGRAPH,
            'dthd': DITABlockType.PARAGRAPH,
            'ddhd': DITABlockType.PARAGRAPH,
            
            # Parameter list elements
            'pt': DITABlockType.PARAGRAPH,
            'pd': DITABlockType.PARAGRAPH,
            'plentry': DITABlockType.LIST_ITEM,
            
            # Choice elements
            'choicetable': DITABlockType.TABLE,
            'chhead': DITABlockType.PARAGRAPH,
            'chrow': DITABlockType.PARAGRAPH,
            'choption': DITABlockType.PARAGRAPH,
            'chdesc': DITABlockType.PARAGRAPH,
            'choptionhd': DITABlockType.PARAGRAPH,
            'chdeschd': DITABlockType.PARAGRAPH,
            
            # Task-specific detailed elements
            'tutorialinfo': DITABlockType.INFO,
            'responsestmt': DITABlockType.PARAGRAPH,
            'stepsection': DITABlockType.PARAGRAPH,
            
            # Troubleshooting elements
            'condition': DITABlockType.PARAGRAPH,
            'troublesolution': DITABlockType.SECTION,
            'cause': DITABlockType.PARAGRAPH,
            'remedy': DITABlockType.PARAGRAPH,
            
            # Inline elements that might appear as blocks
            'term': DITABlockType.PARAGRAPH,
            'keyword': DITABlockType.PARAGRAPH,
            'ph': DITABlockType.PARAGRAPH,
            'text': DITABlockType.PARAGRAPH,
            
            # Navigation and metadata (usually skipped but handle gracefully)
            'prolog': None,  # Skip metadata
            'metadata': None,  # Skip metadata
            'critdates': None,  # Skip dates
            'author': None,  # Skip author
            'source': None,  # Skip source
            'publisher': None,  # Skip publisher
            'permissions': None,  # Skip permissions
            'audience': None,  # Skip audience metadata
            'category': None,  # Skip category
            'keywords': None,  # Skip keywords metadata
            'prodinfo': None,  # Skip product info
            'related-links': None,  # Skip related links
            'linkpool': None,  # Skip link pools
            'link': None,  # Skip individual links
        }
        
        # Map root elements to topic types
        self.topic_type_mapping = {
            'concept': DITATopicType.CONCEPT,
            'task': DITATopicType.TASK,
            'reference': DITATopicType.REFERENCE,
            'troubleshooting': DITATopicType.TROUBLESHOOTING,
            'topic': DITATopicType.TOPIC,
            'map': DITATopicType.MAP,
        }
    
    def parse(self, content: str, filename: str = "") -> DITAParseResult:
        """
        Parse DITA content into structural blocks.
        
        Args:
            content: Raw DITA XML content
            filename: Optional filename for error reporting
            
        Returns:
            DITAParseResult with document structure
        """
        try:
            # Parse XML content
            root = ET.fromstring(content)
            
            # Determine topic type
            topic_type = self.topic_type_mapping.get(root.tag, DITATopicType.TOPIC)
            
            # Extract topic ID
            topic_id = root.get('id', '')
            
            # Convert XML to our internal structure
            document = self._convert_xml_to_blocks(root, content, filename, topic_type, topic_id)
            
            return DITAParseResult(
                document=document,
                topic_type=topic_type,
                success=True
            )
            
        except ET.ParseError as e:
            # XML parsing error
            empty_document = DITADocument()
            empty_document.source_file = filename
            return DITAParseResult(
                document=empty_document,
                success=False,
                errors=[f"XML parse error: {str(e)}"]
            )
        except Exception as e:
            # Other parsing errors
            empty_document = DITADocument()
            empty_document.source_file = filename
            return DITAParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse DITA: {str(e)}"]
            )
    
    def _convert_xml_to_blocks(self, root: ET.Element, content: str, 
                              filename: str, topic_type: DITATopicType, 
                              topic_id: str) -> DITADocument:
        """
        Convert XML structure to DITA blocks.
        
        Args:
            root: XML root element
            content: Original content for line calculation
            filename: Source filename
            topic_type: Detected topic type
            topic_id: Topic ID from root element
            
        Returns:
            DITADocument with structured blocks
        """
        blocks = []
        content_lines = content.split('\n')
        
        # Process child elements of the root
        for child in root:
            block = self._create_block_from_element(child, content_lines, topic_type)
            if block:
                blocks.append(block)
        
        document = DITADocument(
            source_file=filename,
            topic_type=topic_type,
            topic_id=topic_id,
            blocks=blocks
        )
        
        return document
    
    def _create_block_from_element(self, element: ET.Element, 
                                  content_lines: List[str],
                                  topic_type: DITATopicType,
                                  level: int = 0) -> Optional[DITABlock]:
        """
        Create a DITABlock from an XML element.
        
        Args:
            element: XML element
            content_lines: Original content split by lines
            topic_type: Document topic type
            level: Nesting level
            
        Returns:
            DITABlock or None if element should be skipped
        """
        # Skip elements we don't want to process (metadata, navigation, etc.)
        skip_elements = ['prolog', 'metadata', 'critdates', 'permissions', 'author', 
                        'source', 'publisher', 'audience', 'category', 'keywords',
                        'prodinfo', 'related-links', 'linkpool', 'link', 'copyright',
                        'copyryear', 'copyrholder', 'titlealts', 'navtitle', 'searchtitle']
        if element.tag in skip_elements:
            return None
        
        # Also check if element mapping explicitly says to skip (None value)
        if element.tag in self.element_mapping and self.element_mapping[element.tag] is None:
            return None
        
        # Map element to block type
        block_type = self.element_mapping.get(element.tag, DITABlockType.UNKNOWN)
        
        # For unknown elements, try to infer a reasonable type
        if block_type == DITABlockType.UNKNOWN:
            # If it contains mostly text, treat as paragraph
            text_content = self._extract_element_content(element)
            if text_content and len(text_content.strip()) > 0:
                block_type = DITABlockType.PARAGRAPH
            else:
                # If no text content, might be a container
                if len(list(element)) > 0:
                    block_type = DITABlockType.SECTION
                else:
                    # Empty unknown element, skip it
                    return None
        
        # Extract text content
        content = self._extract_element_content(element)
        raw_content = ET.tostring(element, encoding='unicode', method='xml')
        
        # Calculate line position (simplified - would need more sophisticated logic for exact lines)
        start_line = 1  # Simplified for now
        
        # Extract attributes
        attributes = dict(element.attrib)
        
        # Create the block
        block = DITABlock(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            start_line=start_line,
            level=level,
            topic_type=topic_type,
            element_name=element.tag,
            attributes=attributes
        )
        
        # Process child elements
        children = []
        for child in element:
            child_block = self._create_block_from_element(child, content_lines, topic_type, level + 1)
            if child_block:
                children.append(child_block)
        
        block.children = children
        
        return block
    
    def _extract_element_content(self, element: ET.Element) -> str:
        """Extract clean text content from XML element."""
        # Get direct text content
        text_parts = []
        
        if element.text:
            text_parts.append(element.text.strip())
        
        # Get text from child elements (recursive)
        for child in element:
            child_text = self._extract_element_content(child)
            if child_text:
                text_parts.append(child_text)
            
            if child.tail:
                text_parts.append(child.tail.strip())
        
        # Join and clean
        content = ' '.join(text_parts)
        content = re.sub(r'\s+', ' ', content)
        
        return content.strip()
    
    def get_parser_info(self) -> dict:
        """Get information about the DITA parser."""
        return {
            'parser_type': 'dita',
            'supported_topic_types': [t.value for t in DITATopicType],
            'supported_elements': list(self.element_mapping.keys()),
            'description': 'DITA XML parser for Adobe Experience Manager workflows'
        }
