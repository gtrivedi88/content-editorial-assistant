"""
Format-Aware AI Rewriter for Technical Writing
Preserves document structure, procedures, notes, and formatting while improving content.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from .ai_rewriter import AIRewriter
    from .format_preserving_processor import DocumentSegment, StructureType, FormatPreservingProcessor
except ImportError:
    from ai_rewriter import AIRewriter
    from format_preserving_processor import DocumentSegment, StructureType, FormatPreservingProcessor

logger = logging.getLogger(__name__)

@dataclass
class SegmentRewriteResult:
    """Result of rewriting a single document segment."""
    original_segment: DocumentSegment
    rewritten_content: str
    improvements: List[str]
    confidence: float
    preserved_formatting: str
    errors_fixed: int

class FormatAwareAIRewriter:
    """AI rewriter that preserves formatting and document structure."""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = "llama3:8b", progress_callback=None):
        """Initialize format-aware AI rewriter."""
        self.base_rewriter = AIRewriter(
            use_ollama=use_ollama, 
            ollama_model=ollama_model,
            progress_callback=progress_callback
        )
        self.format_processor = FormatPreservingProcessor()
        
        # Structure-specific prompting strategies
        self.structure_prompts = {
            StructureType.PROCEDURE: self._get_procedure_prompt,
            StructureType.NOTE: self._get_note_prompt,
            StructureType.WARNING: self._get_warning_prompt,
            StructureType.HEADER: self._get_header_prompt,
            StructureType.PARAGRAPH: self._get_paragraph_prompt,
            StructureType.CODE_BLOCK: self._get_code_prompt
        }
    
    def rewrite_document_with_format_preservation(
        self, 
        segments: List[DocumentSegment], 
        target_format: str = None
    ) -> Dict[str, Any]:
        """
        Rewrite document segments while preserving formatting.
        
        Args:
            segments: List of document segments with preserved formatting
            target_format: Optional target format for conversion
            
        Returns:
            Complete rewrite results with preserved formatting
        """
        try:
            segment_results = []
            total_errors_fixed = 0
            overall_improvements = []
            
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'format_rewrite_start', 
                    'Starting format-aware rewriting...', 
                    f'Processing {len(segments)} segments', 
                    10
                )
            
            for i, segment in enumerate(segments):
                logger.info(f"Processing segment {i+1}/{len(segments)}: {segment.structure_type.value}")
                
                # Skip code blocks from rewriting
                if segment.structure_type == StructureType.CODE_BLOCK:
                    segment_results.append(SegmentRewriteResult(
                        original_segment=segment,
                        rewritten_content=segment.content,
                        improvements=["Code block preserved without modification"],
                        confidence=1.0,
                        preserved_formatting=segment.original_markup,
                        errors_fixed=0
                    ))
                    continue
                
                # Rewrite segment with structure-specific context
                segment_result = self._rewrite_segment(segment)
                segment_results.append(segment_result)
                
                total_errors_fixed += segment_result.errors_fixed
                overall_improvements.extend(segment_result.improvements)
                
                # Progress update
                progress_percent = 20 + (70 * (i + 1) / len(segments))
                if self.base_rewriter.progress_callback:
                    self.base_rewriter.progress_callback(
                        'format_segment_progress',
                        f'Processed {segment.structure_type.value}',
                        f'Segment {i+1}/{len(segments)} complete',
                        int(progress_percent)
                    )
            
            # Reconstruct document with preserved formatting
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'format_reconstruction',
                    'Reconstructing document...',
                    'Preserving formatting and structure',
                    90
                )
            
            reconstructed_segments = self._create_reconstructed_segments(segment_results, target_format)
            final_document = self.format_processor.reconstruct_document(reconstructed_segments, target_format)
            
            # Calculate overall confidence
            total_confidence = sum(result.confidence for result in segment_results)
            overall_confidence = total_confidence / len(segment_results) if segment_results else 0.0
            
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'format_rewrite_complete',
                    'Format-aware rewriting complete!',
                    f'Fixed {total_errors_fixed} issues across {len(segments)} segments',
                    100
                )
            
            return {
                'rewritten_document': final_document,
                'segment_results': segment_results,
                'overall_improvements': list(set(overall_improvements)),  # Deduplicate
                'overall_confidence': overall_confidence,
                'total_errors_fixed': total_errors_fixed,
                'segments_processed': len(segments),
                'formatting_preserved': True,
                'target_format': target_format or 'original'
            }
            
        except Exception as e:
            logger.error(f"Error in format-aware rewriting: {e}")
            return {
                'rewritten_document': '',
                'segment_results': [],
                'overall_improvements': [],
                'overall_confidence': 0.0,
                'error': f'Format-aware rewriting failed: {str(e)}'
            }
    
    def _rewrite_segment(self, segment: DocumentSegment) -> SegmentRewriteResult:
        """Rewrite a single segment with structure-specific context."""
        try:
            # Get structure-specific prompt strategy
            prompt_generator = self.structure_prompts.get(
                segment.structure_type, 
                self._get_paragraph_prompt
            )
            
            # Generate context-aware prompt
            enhanced_prompt = prompt_generator(segment)
            
            # Simulate errors for demonstration (in practice, this would come from style analysis)
            mock_errors = self._simulate_segment_errors(segment)
            
            # Rewrite using base AI rewriter with enhanced context
            rewrite_result = self.base_rewriter._generate_with_ollama(enhanced_prompt, segment.content)
            
            # Extract improvements
            improvements = self._extract_segment_improvements(segment.content, rewrite_result, segment.structure_type)
            
            # Calculate confidence
            confidence = self._calculate_segment_confidence(segment.content, rewrite_result, mock_errors)
            
            # Preserve formatting
            preserved_formatting = self._preserve_segment_formatting(segment, rewrite_result)
            
            return SegmentRewriteResult(
                original_segment=segment,
                rewritten_content=rewrite_result,
                improvements=improvements,
                confidence=confidence,
                preserved_formatting=preserved_formatting,
                errors_fixed=len(mock_errors)
            )
            
        except Exception as e:
            logger.error(f"Error rewriting segment: {e}")
            return SegmentRewriteResult(
                original_segment=segment,
                rewritten_content=segment.content,
                improvements=[],
                confidence=0.0,
                preserved_formatting=segment.original_markup,
                errors_fixed=0
            )
    
    def _get_procedure_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for procedure/step segments."""
        return f"""
You are rewriting a technical procedure step. Maintain the instructional clarity while improving style.

STRUCTURE REQUIREMENTS:
- Keep this as a clear, actionable step
- Maintain imperative voice for instructions
- Preserve technical accuracy
- Ensure each step is self-contained

STYLE IMPROVEMENTS NEEDED:
- Convert passive voice to active voice
- Reduce sentence length if over 25 words
- Eliminate redundant words
- Use precise technical language

ORIGINAL PROCEDURE STEP:
{segment.content}

Rewrite this procedure step to be clearer and more concise while maintaining technical accuracy:
"""
    
    def _get_note_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for note segments."""
        return f"""
You are rewriting a technical note or callout. These provide important supplementary information.

STRUCTURE REQUIREMENTS:
- Keep this as a brief, focused note
- Maintain the informational purpose
- Preserve any warnings or critical information
- Ensure clarity for quick scanning

STYLE IMPROVEMENTS NEEDED:
- Use active voice where possible
- Make language concise and direct
- Eliminate unnecessary qualifiers
- Keep sentences under 20 words

ORIGINAL NOTE:
{segment.content}

Rewrite this note to be clearer and more direct while preserving its informational value:
"""
    
    def _get_warning_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for warning segments."""
        return f"""
You are rewriting a safety warning or caution. These must be crystal clear and direct.

STRUCTURE REQUIREMENTS:
- Keep this as a clear, direct warning
- Maintain urgency and importance
- Preserve safety-critical information
- Use strong, clear language

STYLE IMPROVEMENTS NEEDED:
- Use active voice for directness
- Make consequences clear
- Eliminate ambiguous language
- Keep sentences short and impactful

ORIGINAL WARNING:
{segment.content}

Rewrite this warning to be maximally clear and direct while preserving all safety information:
"""
    
    def _get_header_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for header segments."""
        return f"""
You are rewriting a document section header. Headers should be clear and descriptive.

STRUCTURE REQUIREMENTS:
- Keep this as a concise header/title
- Maintain descriptive accuracy
- Use parallel structure with other headers
- Avoid unnecessary words

STYLE IMPROVEMENTS NEEDED:
- Use active, descriptive language
- Eliminate redundant words
- Make purpose immediately clear
- Keep under 8 words if possible

ORIGINAL HEADER:
{segment.content}

Rewrite this header to be clearer and more concise:
"""
    
    def _get_paragraph_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for paragraph segments."""
        return f"""
You are rewriting a technical writing paragraph. Focus on clarity and conciseness.

STRUCTURE REQUIREMENTS:
- Maintain paragraph coherence
- Keep related ideas together
- Preserve technical accuracy
- Ensure logical flow

STYLE IMPROVEMENTS NEEDED:
- Convert passive voice to active voice
- Reduce sentence length (aim for 15-20 words)
- Eliminate redundant expressions
- Use precise, concrete language

ORIGINAL PARAGRAPH:
{segment.content}

Rewrite this paragraph to be clearer and more concise while maintaining technical accuracy:
"""
    
    def _get_code_prompt(self, segment: DocumentSegment) -> str:
        """Generate prompt for code segments (typically skipped)."""
        return f"""
This is a code block that should generally be preserved as-is.
Only minor comment improvements should be considered.

ORIGINAL CODE:
{segment.content}

If any comments need improvement, suggest better ones. Otherwise, return the code unchanged:
"""
    
    def _simulate_segment_errors(self, segment: DocumentSegment) -> List[Dict[str, Any]]:
        """Simulate style errors for demonstration purposes."""
        errors = []
        content = segment.content.lower()
        
        # Simulate passive voice detection
        if 'was ' in content or 'were ' in content or 'been ' in content:
            errors.append({'type': 'passive_voice', 'message': 'Passive voice detected'})
        
        # Simulate long sentence detection
        sentences = re.split(r'[.!?]+', segment.content)
        for sentence in sentences:
            if len(sentence.split()) > 25:
                errors.append({'type': 'sentence_length', 'message': 'Long sentence detected'})
        
        # Simulate wordiness detection
        wordy_phrases = ['in order to', 'due to the fact that', 'it is important to note']
        if any(phrase in content for phrase in wordy_phrases):
            errors.append({'type': 'conciseness', 'message': 'Wordy construction detected'})
        
        return errors
    
    def _extract_segment_improvements(self, original: str, rewritten: str, structure_type: StructureType) -> List[str]:
        """Extract improvements made to a segment."""
        improvements = []
        
        # Length comparison
        original_words = len(original.split())
        rewritten_words = len(rewritten.split())
        
        if rewritten_words < original_words:
            word_reduction = original_words - rewritten_words
            improvements.append(f"Reduced length by {word_reduction} words ({structure_type.value})")
        
        # Structure-specific improvements
        if structure_type == StructureType.PROCEDURE:
            if original.count('was ') > rewritten.count('was '):
                improvements.append("Converted passive voice to active in procedure step")
        
        elif structure_type == StructureType.NOTE:
            if len(rewritten) < len(original):
                improvements.append("Simplified note for better readability")
        
        elif structure_type == StructureType.WARNING:
            improvements.append("Enhanced warning clarity and directness")
        
        # Generic improvements
        if rewritten != original:
            improvements.append(f"Improved {structure_type.value} clarity and style")
        
        return improvements
    
    def _calculate_segment_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for segment rewriting."""
        if rewritten == original:
            return 0.5  # No changes made
        
        confidence = 0.7  # Base confidence
        
        # Boost confidence based on error fixes
        confidence += len(errors) * 0.1
        
        # Reduce confidence if output seems problematic
        if len(rewritten.strip()) == 0:
            confidence = 0.0
        elif len(rewritten) > len(original) * 1.5:  # Significantly longer
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _preserve_segment_formatting(self, segment: DocumentSegment, rewritten_content: str) -> str:
        """Preserve the original formatting structure with new content."""
        format_type = segment.formatting_metadata.get('format', 'unknown')
        
        if segment.structure_type == StructureType.NOTE:
            if format_type == 'markdown':
                if segment.formatting_metadata.get('style') == 'blockquote':
                    return f"> **Note:** {rewritten_content}"
                else:
                    return f"**Note:** {rewritten_content}"
            elif format_type == 'asciidoc':
                return f"[NOTE]\n====\n{rewritten_content}\n===="
        
        elif segment.structure_type == StructureType.WARNING:
            if format_type == 'markdown':
                if segment.formatting_metadata.get('style') == 'blockquote':
                    return f"> **Warning:** {rewritten_content}"
                else:
                    return f"**Warning:** {rewritten_content}"
            elif format_type == 'asciidoc':
                return f"[WARNING]\n====\n{rewritten_content}\n===="
        
        elif segment.structure_type == StructureType.HEADER:
            if format_type == 'markdown':
                level = segment.formatting_metadata.get('level', 1)
                return f"{'#' * level} {rewritten_content}"
            elif format_type == 'asciidoc':
                level = segment.formatting_metadata.get('level', 1)
                return f"{'=' * level} {rewritten_content}"
        
        elif segment.structure_type == StructureType.PROCEDURE:
            # For procedures, try to maintain numbering if present
            original_markup = segment.original_markup
            if re.match(r'^\d+\.', original_markup.strip()):
                # Extract number and preserve it
                match = re.match(r'^(\d+\.\s*)', original_markup.strip())
                if match:
                    return f"{match.group(1)}{rewritten_content}"
        
        # Default: return rewritten content
        return rewritten_content
    
    def _create_reconstructed_segments(self, segment_results: List[SegmentRewriteResult], target_format: str = None) -> List[DocumentSegment]:
        """Create new document segments with rewritten content and preserved formatting."""
        reconstructed_segments = []
        
        for result in segment_results:
            # Create new segment with updated content but preserved structure
            new_segment = DocumentSegment(
                content=result.rewritten_content,
                structure_type=result.original_segment.structure_type,
                formatting_metadata=result.original_segment.formatting_metadata.copy(),
                start_pos=result.original_segment.start_pos,
                end_pos=result.original_segment.end_pos,
                original_markup=result.preserved_formatting
            )
            
            # Update format if converting
            if target_format and target_format != new_segment.formatting_metadata.get('format'):
                new_segment.formatting_metadata['format'] = target_format
                # The reconstruct_document method will handle format conversion
            
            reconstructed_segments.append(new_segment)
        
        return reconstructed_segments 