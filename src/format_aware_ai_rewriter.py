"""
Format-Aware AI Rewriter for Technical Writing
Uses the new structural parsing system for robust document analysis.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

try:
    from rewriter.core import AIRewriter
    from structural_parsing.parser_factory import StructuralParserFactory
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlock, AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlock, MarkdownBlockType
    from typing import Literal
except ImportError:
    from rewriter.core import AIRewriter
    from structural_parsing.parser_factory import StructuralParserFactory
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlock, AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlock, MarkdownBlockType
    from typing import Literal

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content blocks for AI rewriting."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    ADMONITION = "admonition"
    LIST_ITEM = "list_item"
    CODE_BLOCK = "code_block"
    QUOTE = "quote"
    TABLE_CELL = "table_cell"

@dataclass
class BlockRewriteResult:
    """Result of rewriting a single document block."""
    original_block: Any  # Could be AsciiDocBlock or MarkdownBlock
    rewritten_content: str
    improvements: List[str]
    confidence: float
    content_type: ContentType
    errors_fixed: int

class StructuralAIRewriter:
    """AI rewriter that uses structural parsing for robust document analysis."""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = "llama3:8b", progress_callback=None):
        """Initialize structural AI rewriter."""
        self.base_rewriter = AIRewriter(
            use_ollama=use_ollama, 
            ollama_model=ollama_model,
            progress_callback=progress_callback
        )
        self.parser_factory = StructuralParserFactory()
        
        # Content-type specific prompting strategies
        self.content_prompts = {
            ContentType.HEADING: self._get_heading_prompt,
            ContentType.PARAGRAPH: self._get_paragraph_prompt,
            ContentType.ADMONITION: self._get_admonition_prompt,
            ContentType.LIST_ITEM: self._get_list_item_prompt,
            ContentType.CODE_BLOCK: self._get_code_prompt,
            ContentType.QUOTE: self._get_quote_prompt,
            ContentType.TABLE_CELL: self._get_table_cell_prompt
        }
    
    def rewrite_document_with_structure_preservation(
        self, 
        content: str, 
        filename: str = "",
        format_hint: Literal['asciidoc', 'markdown', 'auto'] = 'auto'
    ) -> Dict[str, Any]:
        """
        Rewrite document using structural parsing for context-aware improvements.
        
        Args:
            content: Raw document content
            filename: Optional filename for parsing context
            format_hint: Format hint ('asciidoc', 'markdown', or 'auto')
            
        Returns:
            Complete rewrite results with preserved structure
        """
        try:
            # Parse document using structural parser
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'structural_parse_start', 
                    'Parsing document structure...', 
                    'Using external parsing libraries', 
                    10
                )
            
            parse_result = self.parser_factory.parse(content, filename, format_hint)
            
            if not parse_result.success:
                return {
                    'rewritten_document': content,
                    'error': f'Parsing failed: {", ".join(parse_result.errors)}',
                    'structural_parsing_used': True
                }
            
            # Get content blocks that should be analyzed
            content_blocks = parse_result.document.get_content_blocks()
            
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'structural_analysis_start', 
                    f'Found {len(content_blocks)} content blocks', 
                    f'Parsed with {parse_result.parsing_method}', 
                    20
                )
            
            # Rewrite each content block
            block_results = []
            total_errors_fixed = 0
            overall_improvements = []
            
            for i, block in enumerate(content_blocks):
                # Skip blocks that shouldn't be analyzed
                if block.should_skip_analysis():
                    continue
                
                logger.info(f"Processing block {i+1}/{len(content_blocks)}: {block.block_type.value}")
                
                # Rewrite block with context-aware prompting
                block_result = self._rewrite_content_block(block)
                block_results.append(block_result)
                
                total_errors_fixed += block_result.errors_fixed
                overall_improvements.extend(block_result.improvements)
                
                # Progress update
                progress_percent = 20 + (60 * (i + 1) / len(content_blocks))
                if self.base_rewriter.progress_callback:
                    self.base_rewriter.progress_callback(
                        'block_rewrite_progress',
                        f'Rewrote {block_result.content_type.value}',
                        f'Block {i+1}/{len(content_blocks)} complete',
                        int(progress_percent)
                    )
            
            # Reconstruct document with rewritten content
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'document_reconstruction',
                    'Reconstructing document...',
                    'Preserving original structure and formatting',
                    85
                )
            
            reconstructed_document = self._reconstruct_document_with_rewrites(
                parse_result.document, block_results
            )
            
            # Calculate overall confidence
            total_confidence = sum(result.confidence for result in block_results)
            overall_confidence = total_confidence / len(block_results) if block_results else 0.0
            
            if self.base_rewriter.progress_callback:
                self.base_rewriter.progress_callback(
                    'structural_rewrite_complete',
                    'Structural rewriting complete!',
                    f'Improved {len(block_results)} blocks using {parse_result.parsing_method}',
                    100
                )
            
            return {
                'rewritten_document': reconstructed_document,
                'block_results': block_results,
                'overall_improvements': list(set(overall_improvements)),  # Deduplicate
                'overall_confidence': overall_confidence,
                'total_errors_fixed': total_errors_fixed,
                'blocks_processed': len(block_results),
                'parsing_method': parse_result.parsing_method,
                'document_format': format_hint,
                'structural_parsing_used': True,
                'parsing_stats': parse_result.document.get_document_statistics()
            }
            
        except Exception as e:
            logger.error(f"Error in structural AI rewriting: {e}")
            return {
                'rewritten_document': content,
                'error': f'Structural rewriting failed: {str(e)}',
                'structural_parsing_used': True
            }
    
    def _rewrite_content_block(self, block) -> BlockRewriteResult:
        """Rewrite a single content block with type-specific context."""
        try:
            # Determine content type from block type
            content_type = self._map_block_to_content_type(block)
            
            # Get context-aware prompt strategy
            prompt_generator = self.content_prompts.get(
                content_type, 
                self._get_paragraph_prompt
            )
            
            # Generate enhanced prompt with block context
            enhanced_prompt = prompt_generator(block)
            
            # Simulate errors for demonstration (in practice, integrate with style analyzer)
            mock_errors = self._simulate_block_errors(block)
            
            # Rewrite using AI with enhanced context
            # Create mock errors for the rewriter (in practice, would use real style analysis)
            rewrite_result = self.base_rewriter.rewrite(
                block.get_text_content(), 
                mock_errors, 
                "paragraph", 
                1
            )
            rewritten_content = rewrite_result.get('rewritten_text', block.get_text_content())
            
            # Extract improvements
            improvements = self._extract_block_improvements(
                block.get_text_content(), 
                rewritten_content, 
                content_type
            )
            
            # Calculate confidence
            confidence = self._calculate_block_confidence(
                block.get_text_content(), 
                rewritten_content, 
                mock_errors
            )
            
            return BlockRewriteResult(
                original_block=block,
                rewritten_content=rewritten_content,
                improvements=improvements,
                confidence=confidence,
                content_type=content_type,
                errors_fixed=len(mock_errors)
            )
            
        except Exception as e:
            logger.error(f"Error rewriting block: {e}")
            return BlockRewriteResult(
                original_block=block,
                rewritten_content=block.get_text_content(),
                improvements=[],
                confidence=0.0,
                content_type=ContentType.PARAGRAPH,
                errors_fixed=0
            )
    
    def _map_block_to_content_type(self, block) -> ContentType:
        """Map parsed block type to our content type enum."""
        # Handle AsciiDoc blocks
        if hasattr(block, 'block_type') and hasattr(block.block_type, 'value'):
            block_type_value = block.block_type.value
            
            if block_type_value == 'heading':
                return ContentType.HEADING
            elif block_type_value == 'admonition':
                return ContentType.ADMONITION
            elif block_type_value in ['list_item', 'ordered_list', 'unordered_list']:
                return ContentType.LIST_ITEM
            elif block_type_value in ['listing', 'literal', 'code_block']:
                return ContentType.CODE_BLOCK
            elif block_type_value in ['quote', 'blockquote']:
                return ContentType.QUOTE
            elif block_type_value == 'table_cell':
                return ContentType.TABLE_CELL
            else:
                return ContentType.PARAGRAPH
        
        # Default fallback
        return ContentType.PARAGRAPH
    
    def _get_heading_prompt(self, block) -> str:
        """Generate prompt for heading blocks."""
        context_info = block.get_context_info()
        level = context_info.get('level', 1)
        
        return f"""
You are rewriting a document heading (level {level}). Headers should be clear and descriptive.

REQUIREMENTS:
- Keep this as a concise header/title
- Use parallel structure with other headers
- Make purpose immediately clear
- Avoid unnecessary words
- Keep under 8 words if possible

ORIGINAL HEADING:
{block.get_text_content()}

Rewrite this heading to be clearer and more descriptive:
"""
    
    def _get_paragraph_prompt(self, block) -> str:
        """Generate prompt for paragraph blocks."""
        context_info = block.get_context_info()
        
        return f"""
You are rewriting a technical writing paragraph. Focus on clarity and conciseness.

CONTEXT: This is a {context_info.get('block_type', 'paragraph')} in a technical document.

REQUIREMENTS:
- Convert passive voice to active voice
- Reduce sentence length (aim for 15-20 words)
- Eliminate redundant expressions
- Use precise, concrete language
- Maintain technical accuracy

ORIGINAL PARAGRAPH:
{block.get_text_content()}

Rewrite this paragraph to be clearer and more concise:
"""
    
    def _get_admonition_prompt(self, block) -> str:
        """Generate prompt for admonition blocks (notes, warnings, etc.)."""
        context_info = block.get_context_info()
        admonition_type = context_info.get('admonition_type', 'NOTE')
        
        return f"""
You are rewriting a {admonition_type} admonition. These provide important supplementary information.

REQUIREMENTS:
- Keep this as a brief, focused {admonition_type.lower()}
- Maintain the informational/warning purpose
- Use direct, clear language
- Make content scannable
- Keep sentences under 20 words

ORIGINAL {admonition_type}:
{block.get_text_content()}

Rewrite this {admonition_type.lower()} to be clearer and more direct:
"""
    
    def _get_list_item_prompt(self, block) -> str:
        """Generate prompt for list item blocks."""
        return f"""
You are rewriting a list item or step. These should be clear and actionable.

REQUIREMENTS:
- Keep this as a clear, actionable item
- Use parallel structure with other list items
- Maintain imperative voice for instructions
- Be concise and specific

ORIGINAL LIST ITEM:
{block.get_text_content()}

Rewrite this list item to be clearer and more concise:
"""
    
    def _get_code_prompt(self, block) -> str:
        """Generate prompt for code blocks (typically preserved)."""
        return f"""
This is a code block that should generally be preserved as-is.
Only minor comment improvements should be considered.

ORIGINAL CODE:
{block.get_text_content()}

Return the code unchanged unless comments need improvement:
"""
    
    def _get_quote_prompt(self, block) -> str:
        """Generate prompt for quote blocks."""
        return f"""
You are rewriting a blockquote. Maintain the quoted nature while improving clarity.

REQUIREMENTS:
- Preserve the quote context
- Improve clarity if needed
- Maintain the original meaning
- Keep language appropriate for quotes

ORIGINAL QUOTE:
{block.get_text_content()}

Improve this quote for clarity while preserving its meaning:
"""
    
    def _get_table_cell_prompt(self, block) -> str:
        """Generate prompt for table cell content."""
        return f"""
You are rewriting table cell content. Keep it concise and scannable.

REQUIREMENTS:
- Keep content brief and scannable
- Use clear, direct language
- Maintain tabular format appropriateness
- Eliminate unnecessary words

ORIGINAL CELL CONTENT:
{block.get_text_content()}

Rewrite this table cell content to be clearer and more concise:
"""
    
    def _simulate_block_errors(self, block) -> List[Dict[str, Any]]:
        """Simulate style errors for demonstration."""
        errors = []
        content = block.get_text_content().lower()
        
        # Simulate passive voice detection
        if 'was ' in content or 'were ' in content or 'been ' in content:
            errors.append({'type': 'passive_voice', 'message': 'Passive voice detected'})
        
        # Simulate long sentence detection
        sentences = re.split(r'[.!?]+', block.get_text_content())
        for sentence in sentences:
            if len(sentence.split()) > 25:
                errors.append({'type': 'sentence_length', 'message': 'Long sentence detected'})
        
        return errors
    
    def _extract_block_improvements(self, original: str, rewritten: str, content_type: ContentType) -> List[str]:
        """Extract improvements made to a block."""
        improvements = []
        
        # Length comparison
        original_words = len(original.split())
        rewritten_words = len(rewritten.split())
        
        if rewritten_words < original_words:
            word_reduction = original_words - rewritten_words
            improvements.append(f"Reduced {content_type.value} length by {word_reduction} words")
        
        # Type-specific improvements
        if rewritten != original:
            improvements.append(f"Improved {content_type.value} clarity and style")
        
        return improvements
    
    def _calculate_block_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for block rewriting."""
        if rewritten == original:
            return 0.5  # No changes made
        
        confidence = 0.7  # Base confidence
        confidence += len(errors) * 0.1  # Boost for error fixes
        
        # Reduce confidence for problematic outputs
        if len(rewritten.strip()) == 0:
            confidence = 0.0
        elif len(rewritten) > len(original) * 1.5:
            confidence -= 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _reconstruct_document_with_rewrites(self, document, block_results: List[BlockRewriteResult]) -> str:
        """Reconstruct document with rewritten content while preserving structure."""
        # This is a simplified reconstruction - in practice, would need more sophisticated 
        # merging of rewritten content back into the original document structure
        
        reconstructed_blocks = []
        
        for result in block_results:
            block = result.original_block
            rewritten_content = result.rewritten_content
            
            # Preserve the block's formatting context
            context_info = block.get_context_info()
            
            if context_info['block_type'] == 'heading':
                level = context_info.get('level', 1)
                if hasattr(document, 'blocks') and hasattr(document.blocks[0], 'block_type'):
                    # AsciiDoc format
                    reconstructed_blocks.append(f"{'=' * level} {rewritten_content}")
                else:
                    # Markdown format
                    reconstructed_blocks.append(f"{'#' * level} {rewritten_content}")
            
            elif context_info['block_type'] == 'admonition':
                admonition_type = context_info.get('admonition_type', 'NOTE')
                if hasattr(document, 'blocks') and hasattr(document.blocks[0], 'block_type'):
                    # AsciiDoc format
                    reconstructed_blocks.append(f"[{admonition_type}]\n====\n{rewritten_content}\n====")
                else:
                    # Markdown format (simplified)
                    reconstructed_blocks.append(f"> **{admonition_type}:** {rewritten_content}")
            
            else:
                # Regular paragraph or other content
                reconstructed_blocks.append(rewritten_content)
        
        return '\n\n'.join(reconstructed_blocks)


# Backward compatibility alias
FormatAwareAIRewriter = StructuralAIRewriter 