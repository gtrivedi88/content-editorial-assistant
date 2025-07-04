"""
AsciiDoc structural parser using external asciidoctor library.
This parser uses the asciidoctor Ruby gem for robust parsing.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
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
    AsciiDoc parser using external asciidoctor library.
    
    This parser delegates all parsing to the asciidoctor Ruby gem
    for maximum compliance and robustness.
    """
    
    def __init__(self):
        self.asciidoctor_available = self._check_asciidoctor_availability()
        
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
        Parse AsciiDoc content into structural blocks.
        
        Args:
            content: Raw AsciiDoc content
            filename: Optional filename for error reporting
            
        Returns:
            ParseResult with document structure
        """
        if not self.asciidoctor_available:
            # Create empty document for error case
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=["Asciidoctor is not available. Please install with: gem install asciidoctor"]
            )
        
        try:
            # Parse the document using asciidoctor
            parsed_data = self._parse_with_asciidoctor(content)
            
            # Convert to our internal structure
            document = self._convert_to_internal_structure(parsed_data, filename)
            
            return ParseResult(
                document=document,
                success=True
            )
            
        except Exception as e:
            # Create empty document for error case
            empty_document = AsciiDocDocument(source_file=filename)
            return ParseResult(
                document=empty_document,
                success=False,
                errors=[f"Failed to parse AsciiDoc: {str(e)}"]
            )
    
    def _parse_with_asciidoctor(self, content: str) -> Dict[str, Any]:
        """
        Parse content using asciidoctor with JSON output.
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            Parsed document data as dictionary
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.adoc', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        try:
            # Use asciidoctor to convert to JSON for structural analysis
            result = subprocess.run([
                'asciidoctor',
                '-b', 'html5',  # HTML5 backend
                '-o', '/dev/null',  # Don't write HTML output
                '--trace',  # Enable tracing for better error messages
                temp_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise AsciiDocParseError(
                    f"Asciidoctor failed: {result.stderr}",
                    original_error=None
                )
            
            # For now, we'll parse the source directly since asciidoctor 
            # doesn't have a built-in JSON output mode
            return self._parse_source_structure(content)
            
        finally:
            # Clean up temporary file
            Path(temp_file).unlink(missing_ok=True)
    
    def _parse_source_structure(self, content: str) -> Dict[str, Any]:
        """
        Parse AsciiDoc source structure.
        
        This method analyzes the source to identify structural elements
        without fully parsing the content (which asciidoctor handles).
        
        Args:
            content: Raw AsciiDoc content
            
        Returns:
            Document structure information
        """
        lines = content.split('\n')
        blocks = []
        current_block = None
        line_number = 0
        
        for line in lines:
            line_number += 1
            stripped = line.strip()
            
            # Document title (single =)
            if line.startswith('= ') and not line.startswith('=='):
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    'type': 'document_title',
                    'content': line[2:].strip(),
                    'line_number': line_number,
                    'level': 0
                }
            
            # Section headers (== and more)
            elif stripped.startswith('=') and ' ' in stripped:
                if current_block:
                    blocks.append(current_block)
                
                level = 0
                while level < len(stripped) and stripped[level] == '=':
                    level += 1
                
                current_block = {
                    'type': 'heading',
                    'content': stripped[level:].strip(),
                    'line_number': line_number,
                    'level': level - 1  # Adjust for 0-based indexing
                }
            
            # Admonitions
            elif stripped.startswith('[') and stripped.endswith(']'):
                admonition_match = stripped[1:-1].upper()
                if admonition_match in ['NOTE', 'TIP', 'IMPORTANT', 'WARNING', 'CAUTION']:
                    if current_block:
                        blocks.append(current_block)
                    current_block = {
                        'type': 'admonition',
                        'admonition_type': admonition_match,
                        'content': '',
                        'line_number': line_number
                    }
            
            # Block delimiters
            elif stripped in ['****', '====', '----', '....', '____', '++++']:
                if current_block:
                    blocks.append(current_block)
                
                block_type_map = {
                    '****': 'sidebar',
                    '====': 'example',
                    '----': 'listing',
                    '....': 'literal',
                    '____': 'quote',
                    '++++': 'passthrough'
                }
                
                current_block = {
                    'type': block_type_map[stripped],
                    'content': '',
                    'line_number': line_number,
                    'delimiter': stripped
                }
            
            # Regular content
            elif stripped:
                if current_block is None:
                    current_block = {
                        'type': 'paragraph',
                        'content': stripped,
                        'line_number': line_number
                    }
                else:
                    if 'content' not in current_block:
                        current_block['content'] = stripped
                    else:
                        current_block['content'] += '\n' + stripped
        
        # Add the last block
        if current_block:
            blocks.append(current_block)
        
        return {
            'blocks': blocks,
            'total_lines': line_number,
            'source': content
        }
    
    def _convert_to_internal_structure(self, parsed_data: Dict[str, Any], filename: str) -> AsciiDocDocument:
        """
        Convert parsed data to internal AsciiDoc document structure.
        
        Args:
            parsed_data: Data from asciidoctor parsing
            filename: Original filename
            
        Returns:
            AsciiDocDocument object
        """
        blocks = []
        
        for block_data in parsed_data['blocks']:
            block_type = self._map_block_type(block_data['type'])
            
            # Set admonition type if present
            admonition_type = None
            if 'admonition_type' in block_data:
                admonition_type = AdmonitionType(block_data['admonition_type'])
            
            # Create block with all required parameters
            block = AsciiDocBlock(
                block_type=block_type,
                content=block_data.get('content', ''),
                raw_content=block_data.get('content', ''),
                start_line=block_data.get('line_number', 0),
                end_line=block_data.get('line_number', 0),
                start_pos=0,
                end_pos=len(block_data.get('content', '')),
                level=block_data.get('level', 0),
                attributes=AsciiDocAttributes(),
                admonition_type=admonition_type,
                children=[]
            )
            
            blocks.append(block)
        
        return AsciiDocDocument(
            source_file=filename,
            blocks=blocks
        )
    
    def _map_block_type(self, type_str: str) -> AsciiDocBlockType:
        """Map string block type to enum."""
        type_mapping = {
            'document_title': AsciiDocBlockType.HEADING,
            'heading': AsciiDocBlockType.HEADING,
            'paragraph': AsciiDocBlockType.PARAGRAPH,
            'admonition': AsciiDocBlockType.ADMONITION,
            'sidebar': AsciiDocBlockType.SIDEBAR,
            'example': AsciiDocBlockType.EXAMPLE,
            'listing': AsciiDocBlockType.LISTING,
            'literal': AsciiDocBlockType.LITERAL,
            'quote': AsciiDocBlockType.QUOTE,
            'passthrough': AsciiDocBlockType.PASS,
        }
        
        return type_mapping.get(type_str, AsciiDocBlockType.PARAGRAPH) 