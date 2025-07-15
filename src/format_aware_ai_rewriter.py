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
        
        # Initialize style analyzer for SpaCy error detection
        try:
            from style_analyzer.core_analyzer import StyleAnalyzer
            self.style_analyzer = StyleAnalyzer({})  # Pass empty rules dict as required
            logger.info("✅ StyleAnalyzer loaded for SpaCy error detection")
        except ImportError as e:
            logger.warning(f"⚠️ StyleAnalyzer not available: {e}")
            self.style_analyzer = None
        except Exception as e:
            logger.warning(f"⚠️ Error initializing StyleAnalyzer: {e}")
            self.style_analyzer = None
    
    def rewrite_document_with_structure_preservation(
        self, 
        content: str, 
        filename: str = "",
        format_hint: Literal['asciidoc', 'markdown', 'auto'] = 'auto',
        style_errors: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Rewrite document using structural parsing for context-aware improvements.
        
        Args:
            content: Raw document content
            filename: Optional filename for parsing context
            format_hint: Format hint ('asciidoc', 'markdown', or 'auto')
            style_errors: Real style analysis errors to fix (instead of mock errors)
            
        Returns:
            Complete rewrite results with preserved structure
        """
        try:
            # Perform SpaCy analysis if no errors provided
            if not style_errors and self.style_analyzer:
                logger.info("No style errors provided, performing SpaCy analysis...")
                try:
                    analysis_result = self.style_analyzer.analyze(content, format_hint)
                    
                    if analysis_result:
                        # The StyleAnalyzer returns errors directly in the top-level result, not nested under 'analysis'
                        style_errors = analysis_result.get('errors', [])
                        if style_errors:
                            logger.info(f"SpaCy analysis found {len(style_errors)} errors")
                        else:
                            logger.info("SpaCy analysis found no errors")
                    else:
                        logger.warning("SpaCy analysis returned no result")
                        style_errors = []
                except Exception as e:
                    logger.error(f"Error during SpaCy analysis: {e}")
                    style_errors = []
            elif style_errors:
                logger.info(f"Using provided style errors: {len(style_errors)} errors")
            else:
                logger.info("No style analyzer available and no errors provided")
                style_errors = []
            
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
                
                # Rewrite block with context-aware prompting and real errors
                block_result = self._rewrite_content_block(block, style_errors or [])
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
    
    def _rewrite_content_block(self, block, style_errors: List[Dict[str, Any]]) -> BlockRewriteResult:
        """Rewrite a single content block using SpaCy errors to generate dynamic prompts."""
        try:
            # Determine content type from block type
            content_type = self._map_block_to_content_type(block)
            
            # Filter errors relevant to this specific block's content
            block_content = block.get_text_content()
            relevant_errors = []
            
            for error in style_errors:
                # Check if this error is relevant to this block
                error_sentence = error.get('sentence', '')
                if error_sentence and error_sentence.strip() in block_content:
                    relevant_errors.append(error)
                elif content_type == ContentType.HEADING and error.get('type') in ['headings', 'capitalization']:
                    # For headings, include heading-specific errors even if sentence doesn't match exactly
                    relevant_errors.append(error)
            
            # If no specific errors for this block, skip rewriting
            if not relevant_errors:
                logger.info(f"No relevant errors for {content_type.value} block, skipping rewrite")
                return BlockRewriteResult(
                    original_block=block,
                    rewritten_content=block.get_text_content(),
                    improvements=[],
                    confidence=1.0,  # No changes needed
                    content_type=content_type,
                    errors_fixed=0
                )
            
            logger.info(f"Processing {content_type.value} block with {len(relevant_errors)} SpaCy errors")
            
            # Use base rewriter with SpaCy errors to generate dynamic prompts
            # This will use the prompt configs in /rewriter/prompt_configs/ to convert errors to prompts
            # Map content type to appropriate context for prompt generation
            context = self._map_content_type_to_context(content_type)
            
            rewrite_result = self.base_rewriter.rewrite(
                block.get_text_content(), 
                relevant_errors, 
                context,  # Use appropriate context for prompt generation
                1  # Pass 1
            )
            rewritten_content = rewrite_result.get('rewritten_text', block.get_text_content())
            
            # Extract improvements from rewrite result
            improvements = rewrite_result.get('improvements', [])
            if not improvements:
                improvements = self._extract_block_improvements(
                    block.get_text_content(), 
                    rewritten_content, 
                    content_type
                )
            
            # Get confidence from rewrite result
            confidence = rewrite_result.get('confidence', 0.8)
            
            return BlockRewriteResult(
                original_block=block,
                rewritten_content=rewritten_content,
                improvements=improvements,
                confidence=confidence,
                content_type=content_type,
                errors_fixed=len(relevant_errors)
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
    
    def _map_content_type_to_context(self, content_type: ContentType) -> str:
        """Map content type to context string for prompt generation."""
        mapping = {
            ContentType.HEADING: "heading",
            ContentType.PARAGRAPH: "paragraph", 
            ContentType.LIST_ITEM: "list",
            ContentType.CODE_BLOCK: "code",
            ContentType.QUOTE: "quote",
            ContentType.TABLE_CELL: "table",
            ContentType.ADMONITION: "admonition"
        }
        return mapping.get(content_type, "paragraph")
    

    

    
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
        try:
            # Try to use the new reconstructor system
            from reconstructors import get_reconstructor, is_format_supported
            
            # Determine document format
            format_name = 'asciidoc'
            if hasattr(document, '__class__'):
                class_name = document.__class__.__name__.lower()
                if 'markdown' in class_name:
                    format_name = 'markdown'
                elif 'asciidoc' in class_name:
                    format_name = 'asciidoc'
            
            # Use appropriate reconstructor if available
            if is_format_supported(format_name):
                reconstructor = get_reconstructor(format_name)
                result = reconstructor.reconstruct(document, block_results)
                
                if result.success:
                    return result.reconstructed_content
                else:
                    # Fall back to legacy method if reconstruction fails
                    logger.warning(f"Reconstructor failed: {result.errors}")
            
        except ImportError:
            # Reconstructor system not available, use legacy method
            logger.info("Using legacy reconstruction method")
        except Exception as e:
            # Reconstructor failed, use legacy method
            logger.warning(f"Reconstructor error: {e}, falling back to legacy method")
        
        # Legacy reconstruction method (fallback)
        return self._legacy_reconstruct_document(document, block_results)
    
    def _legacy_reconstruct_document(self, document, block_results: List[BlockRewriteResult]) -> str:
        """Legacy document reconstruction method (fallback)."""
        reconstructed_blocks = []
        
        for result in block_results:
            block = result.original_block
            rewritten_content = result.rewritten_content
            
            # Try to get context info
            try:
                context_info = block.get_context_info() if hasattr(block, 'get_context_info') else {}
            except:
                context_info = {}
            
            block_type = context_info.get('block_type', 'paragraph')
            
            if block_type == 'heading':
                level = context_info.get('level', 1)
                if hasattr(document, 'blocks') and hasattr(document.blocks[0], 'block_type'):
                    # AsciiDoc format
                    reconstructed_blocks.append(f"{'=' * level} {rewritten_content}")
                else:
                    # Markdown format
                    reconstructed_blocks.append(f"{'#' * level} {rewritten_content}")
            
            elif block_type == 'admonition':
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


    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for AI rewriting (compatibility method)."""
        try:
            base_info = self.base_rewriter.get_system_info() if hasattr(self.base_rewriter, 'get_system_info') else {}
            
            return {
                'ai_available': True,
                'model_info': base_info.get('model_info', {}),
                'structural_parsing_available': True,
                'reconstructor_available': True,
                'fallback_available': True
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'ai_available': False,
                'structural_parsing_available': True,
                'reconstructor_available': True,
                'fallback_available': True
            }
    
    def rewrite(self, content: str, errors: Optional[List[Dict[str, Any]]] = None, context: str = "sentence") -> Dict[str, Any]:
        """Compatibility method for simple rewriting (fallback to base rewriter)."""
        try:
            if errors is None:
                errors = []
            
            # Use base rewriter for simple rewriting
            return self.base_rewriter.rewrite(content, errors, context, 1)
        except Exception as e:
            logger.error(f"Error in compatibility rewrite: {e}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'Rewrite failed: {str(e)}'
            }
    
    def refine_text(self, content: str, errors: Optional[List[Dict[str, Any]]] = None, context: str = "sentence") -> Dict[str, Any]:
        """Compatibility method for text refinement (Pass 2)."""
        try:
            if errors is None:
                errors = []
            
            # Use base rewriter for refinement
            return self.base_rewriter.rewrite(content, errors, context, 2)
        except Exception as e:
            logger.error(f"Error in text refinement: {e}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'Refinement failed: {str(e)}'
            }


# Backward compatibility alias
FormatAwareAIRewriter = StructuralAIRewriter 