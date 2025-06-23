"""
Format-Preserving Document Processor for Technical Writing
Retains formatting, procedures, notes, and structured elements while applying style analysis.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class StructureType(Enum):
    """Types of document structures in technical writing."""
    PROCEDURE = "procedure"
    NOTE = "note"
    WARNING = "warning"
    CAUTION = "caution"
    TIP = "tip"
    CODE_BLOCK = "code_block"
    NUMBERED_LIST = "numbered_list"
    BULLET_LIST = "bullet_list"
    TABLE = "table"
    HEADER = "header"
    PARAGRAPH = "paragraph"
    CROSS_REFERENCE = "cross_reference"

@dataclass
class DocumentSegment:
    """Represents a segment of document with preserved formatting."""
    content: str
    structure_type: StructureType
    formatting_metadata: Dict[str, Any]
    start_pos: int
    end_pos: int
    original_markup: str
    
class FormatPreservingProcessor:
    """Processes technical documents while preserving formatting and structure."""
    
    def __init__(self):
        """Initialize the format-preserving processor."""
        self.patterns = {
            # Markdown patterns
            'md_procedure': re.compile(r'^(\d+\.\s+.+?)(?=^\d+\.\s|\n\n|$)', re.MULTILINE | re.DOTALL),
            'md_note': re.compile(r'(?:^\s*>\s*\*\*Note:\*\*|^\s*Note:)(.+?)(?=\n\n|$)', re.MULTILINE | re.DOTALL),
            'md_warning': re.compile(r'(?:^\s*>\s*\*\*Warning:\*\*|^\s*Warning:)(.+?)(?=\n\n|$)', re.MULTILINE | re.DOTALL),
            'md_code_block': re.compile(r'```[\w]*\n(.*?)\n```', re.DOTALL),
            'md_header': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
            'md_bullet': re.compile(r'^(\s*[-*+]\s+.+?)(?=^\s*[-*+]|\n\n|$)', re.MULTILINE | re.DOTALL),
            
            # AsciiDoc patterns
            'adoc_procedure': re.compile(r'^(\d+\.\s+.+?)(?=^\d+\.\s|\n\n|$)', re.MULTILINE | re.DOTALL),
            'adoc_note': re.compile(r'^\[NOTE\]\n====\n(.*?)\n====', re.MULTILINE | re.DOTALL),
            'adoc_warning': re.compile(r'^\[WARNING\]\n====\n(.*?)\n====', re.MULTILINE | re.DOTALL),
            'adoc_code': re.compile(r'^\[source.*?\]\n----\n(.*?)\n----', re.MULTILINE | re.DOTALL),
            'adoc_header': re.compile(r'^(=+)\s+(.+)$', re.MULTILINE),
            
            # DITA patterns
            'dita_step': re.compile(r'<step[^>]*>(.*?)</step>', re.DOTALL),
            'dita_note': re.compile(r'<note[^>]*>(.*?)</note>', re.DOTALL),
            'dita_codeblock': re.compile(r'<codeblock[^>]*>(.*?)</codeblock>', re.DOTALL),
            'dita_section': re.compile(r'<section[^>]*>\s*<title[^>]*>(.*?)</title>(.*?)</section>', re.DOTALL),
        }
    
    def process_document(self, content: str, file_format: str) -> List[DocumentSegment]:
        """
        Process document while preserving formatting and structure.
        
        Args:
            content: Original document content
            file_format: File format (md, adoc, dita, etc.)
            
        Returns:
            List of document segments with preserved formatting
        """
        segments = []
        
        if file_format == 'md':
            segments = self._process_markdown(content)
        elif file_format == 'adoc':
            segments = self._process_asciidoc(content)
        elif file_format == 'dita':
            segments = self._process_dita(content)
        else:
            # Fallback to paragraph-based processing
            segments = self._process_plain_text(content)
        
        return segments
    
    def _process_markdown(self, content: str) -> List[DocumentSegment]:
        """Process Markdown content while preserving structure."""
        segments = []
        processed_ranges = set()
        
        # Process procedures (numbered lists)
        for match in self.patterns['md_procedure'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.PROCEDURE,
                    formatting_metadata={
                        'format': 'markdown',
                        'list_type': 'numbered',
                        'indentation': len(match.group(0)) - len(match.group(0).lstrip())
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process notes
        for match in self.patterns['md_note'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.NOTE,
                    formatting_metadata={
                        'format': 'markdown',
                        'style': 'blockquote' if match.group(0).strip().startswith('>') else 'inline'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process warnings
        for match in self.patterns['md_warning'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.WARNING,
                    formatting_metadata={
                        'format': 'markdown',
                        'style': 'blockquote' if match.group(0).strip().startswith('>') else 'inline'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process code blocks
        for match in self.patterns['md_code_block'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.CODE_BLOCK,
                    formatting_metadata={
                        'format': 'markdown',
                        'language': self._extract_code_language(match.group(0))
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process headers
        for match in self.patterns['md_header'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(2).strip(),
                    structure_type=StructureType.HEADER,
                    formatting_metadata={
                        'format': 'markdown',
                        'level': len(match.group(1))
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process remaining content as paragraphs
        segments.extend(self._process_remaining_paragraphs(content, processed_ranges))
        
        # Sort segments by position
        segments.sort(key=lambda s: s.start_pos)
        
        return segments
    
    def _process_asciidoc(self, content: str) -> List[DocumentSegment]:
        """Process AsciiDoc content while preserving structure."""
        segments = []
        processed_ranges = set()
        
        # Process AsciiDoc notes
        for match in self.patterns['adoc_note'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.NOTE,
                    formatting_metadata={
                        'format': 'asciidoc',
                        'block_type': 'admonition'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process AsciiDoc warnings
        for match in self.patterns['adoc_warning'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=match.group(1).strip(),
                    structure_type=StructureType.WARNING,
                    formatting_metadata={
                        'format': 'asciidoc',
                        'block_type': 'admonition'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process remaining content as paragraphs
        segments.extend(self._process_remaining_paragraphs(content, processed_ranges))
        segments.sort(key=lambda s: s.start_pos)
        
        return segments
    
    def _process_dita(self, content: str) -> List[DocumentSegment]:
        """Process DITA content while preserving structure."""
        segments = []
        processed_ranges = set()
        
        # Process DITA steps (procedures)
        for match in self.patterns['dita_step'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=self._clean_xml_content(match.group(1)),
                    structure_type=StructureType.PROCEDURE,
                    formatting_metadata={
                        'format': 'dita',
                        'element': 'step'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        # Process DITA notes
        for match in self.patterns['dita_note'].finditer(content):
            if not self._overlaps_processed(match.span(), processed_ranges):
                segments.append(DocumentSegment(
                    content=self._clean_xml_content(match.group(1)),
                    structure_type=StructureType.NOTE,
                    formatting_metadata={
                        'format': 'dita',
                        'element': 'note'
                    },
                    start_pos=match.start(),
                    end_pos=match.end(),
                    original_markup=match.group(0)
                ))
                processed_ranges.add(match.span())
        
        segments.extend(self._process_remaining_paragraphs(content, processed_ranges))
        segments.sort(key=lambda s: s.start_pos)
        
        return segments
    
    def _process_plain_text(self, content: str) -> List[DocumentSegment]:
        """Process plain text as paragraphs."""
        segments = []
        paragraphs = re.split(r'\n\s*\n', content)
        current_pos = 0
        
        for para in paragraphs:
            if para.strip():
                start_pos = content.find(para.strip(), current_pos)
                end_pos = start_pos + len(para.strip())
                
                segments.append(DocumentSegment(
                    content=para.strip(),
                    structure_type=StructureType.PARAGRAPH,
                    formatting_metadata={'format': 'plain_text'},
                    start_pos=start_pos,
                    end_pos=end_pos,
                    original_markup=para
                ))
                current_pos = end_pos
        
        return segments
    
    def _process_remaining_paragraphs(self, content: str, processed_ranges: set) -> List[DocumentSegment]:
        """Process content not captured by specific patterns as paragraphs."""
        segments = []
        lines = content.split('\n')
        current_paragraph = []
        start_pos = 0
        
        for line in lines:
            line_start = content.find(line, start_pos)
            line_end = line_start + len(line)
            
            # Check if this line is already processed
            if not any(start <= line_start < end or start < line_end <= end 
                      for start, end in processed_ranges):
                
                if line.strip():
                    current_paragraph.append(line.strip())
                else:
                    if current_paragraph:
                        para_content = ' '.join(current_paragraph)
                        para_start = content.find(current_paragraph[0])
                        para_end = content.find(current_paragraph[-1]) + len(current_paragraph[-1])
                        
                        segments.append(DocumentSegment(
                            content=para_content,
                            structure_type=StructureType.PARAGRAPH,
                            formatting_metadata={'format': 'inferred'},
                            start_pos=para_start,
                            end_pos=para_end,
                            original_markup='\n'.join(current_paragraph)
                        ))
                        current_paragraph = []
            
            start_pos = line_end + 1
        
        # Handle final paragraph
        if current_paragraph:
            para_content = ' '.join(current_paragraph)
            para_start = content.find(current_paragraph[0])
            para_end = content.find(current_paragraph[-1]) + len(current_paragraph[-1])
            
            segments.append(DocumentSegment(
                content=para_content,
                structure_type=StructureType.PARAGRAPH,
                formatting_metadata={'format': 'inferred'},
                start_pos=para_start,
                end_pos=para_end,
                original_markup='\n'.join(current_paragraph)
            ))
        
        return segments
    
    def reconstruct_document(self, segments: List[DocumentSegment], target_format: str = None) -> str:
        """
        Reconstruct document from processed segments, preserving formatting.
        
        Args:
            segments: List of processed document segments
            target_format: Target format for output (defaults to original format)
            
        Returns:
            Reconstructed document with preserved formatting
        """
        if not segments:
            return ""
        
        # Sort segments by position
        segments.sort(key=lambda s: s.start_pos)
        
        reconstructed_parts = []
        
        for segment in segments:
            if target_format and target_format != segment.formatting_metadata.get('format'):
                # Convert to target format
                converted_markup = self._convert_segment_format(segment, target_format)
                reconstructed_parts.append(converted_markup)
            else:
                # Use original markup structure with updated content
                updated_markup = self._update_segment_content(segment)
                reconstructed_parts.append(updated_markup)
        
        return '\n\n'.join(reconstructed_parts)
    
    def _convert_segment_format(self, segment: DocumentSegment, target_format: str) -> str:
        """Convert segment to target format."""
        content = segment.content
        
        if target_format == 'markdown':
            if segment.structure_type == StructureType.NOTE:
                return f"> **Note:** {content}"
            elif segment.structure_type == StructureType.WARNING:
                return f"> **Warning:** {content}"
            elif segment.structure_type == StructureType.HEADER:
                level = segment.formatting_metadata.get('level', 1)
                return f"{'#' * level} {content}"
            elif segment.structure_type == StructureType.CODE_BLOCK:
                lang = segment.formatting_metadata.get('language', '')
                return f"```{lang}\n{content}\n```"
        
        elif target_format == 'asciidoc':
            if segment.structure_type == StructureType.NOTE:
                return f"[NOTE]\n====\n{content}\n===="
            elif segment.structure_type == StructureType.WARNING:
                return f"[WARNING]\n====\n{content}\n===="
            elif segment.structure_type == StructureType.HEADER:
                level = segment.formatting_metadata.get('level', 1)
                return f"{'=' * level} {content}"
        
        # Default: return content as-is
        return content
    
    def _update_segment_content(self, segment: DocumentSegment) -> str:
        """Update segment with potentially modified content while preserving structure."""
        # For now, return the original markup with the content
        # In practice, this would intelligently update the markup
        return segment.original_markup
    
    def _overlaps_processed(self, span: Tuple[int, int], processed_ranges: set) -> bool:
        """Check if span overlaps with already processed ranges."""
        start, end = span
        return any(
            not (end <= p_start or start >= p_end) 
            for p_start, p_end in processed_ranges
        )
    
    def _extract_code_language(self, code_block: str) -> str:
        """Extract programming language from code block."""
        match = re.match(r'```(\w+)', code_block)
        return match.group(1) if match else ''
    
    def _clean_xml_content(self, xml_content: str) -> str:
        """Clean XML content to extract plain text."""
        # Remove XML tags but preserve content
        clean_content = re.sub(r'<[^>]+>', '', xml_content)
        return clean_content.strip()

class FormatAwareStyleAnalyzer:
    """Style analyzer that works with format-preserving segments."""
    
    def __init__(self, base_analyzer):
        """Initialize with base style analyzer."""
        self.base_analyzer = base_analyzer
    
    def analyze_segments(self, segments: List[DocumentSegment]) -> Dict[str, Any]:
        """
        Analyze segments while preserving structure context.
        
        Args:
            segments: List of document segments
            
        Returns:
            Analysis results with format preservation metadata
        """
        results = {
            'segments': [],
            'overall_errors': [],
            'structure_stats': {}
        }
        
        structure_counts = {}
        
        for segment in segments:
            # Skip code blocks from style analysis
            if segment.structure_type == StructureType.CODE_BLOCK:
                results['segments'].append({
                    'segment': segment,
                    'errors': [],
                    'skip_reason': 'code_block'
                })
                continue
            
            # Analyze segment content using the correct method name
            analysis_result = self.base_analyzer.analyze(segment.content)
            segment_errors = analysis_result.get('errors', [])
            
            # Add structure context to errors
            for error in segment_errors:
                error['structure_context'] = {
                    'type': segment.structure_type.value,
                    'format': segment.formatting_metadata.get('format'),
                    'metadata': segment.formatting_metadata
                }
            
            results['segments'].append({
                'segment': segment,
                'errors': segment_errors,
                'analysis_result': analysis_result  # Include full analysis results
            })
            
            results['overall_errors'].extend(segment_errors)
            
            # Count structure types
            struct_type = segment.structure_type.value
            structure_counts[struct_type] = structure_counts.get(struct_type, 0) + 1
        
        results['structure_stats'] = structure_counts
        
        return results 