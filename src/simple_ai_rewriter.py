"""
Simple AI Rewriter - Assembly Line Precision Only
Uses the well-designed modular system with assembly line error fixing exclusively.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleAIRewriter:
    """Simple AI rewriter that uses assembly line precision exclusively."""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = "llama3:8b", progress_callback=None):
        """Initialize with assembly line capability only."""
        self.progress_callback = progress_callback
        
        # Use existing components - no duplication
        from rewriter.core import AIRewriter
        from style_analyzer.core_analyzer import StyleAnalyzer
        from reconstructors import get_reconstructor
        
        self.ai_rewriter = AIRewriter(
            use_ollama=use_ollama, 
            ollama_model=ollama_model,
            progress_callback=progress_callback
        )
        self.style_analyzer = StyleAnalyzer()
        self.get_reconstructor = get_reconstructor
        
        logger.info("SimpleAIRewriter initialized - Assembly Line ONLY")
    
    def rewrite_document_with_structure_preservation(self, content: str, format_hint: str = None, 
                                                   session_id: str = None, pass_number: int = 1) -> Dict[str, Any]:
        """
        Rewrite document preserving structure using assembly line approach.
        
        Args:
            content: Document content to rewrite
            format_hint: Document format ('markdown', 'asciidoc', etc.)
            session_id: Session identifier for progress tracking
            pass_number: 1 for initial rewrite, 2 for refinement
            
        Returns:
            Dictionary with rewrite results
        """
        try:
            if not content or not content.strip():
                return {
                    'rewritten_text': '',
                    'improvements': [],
                    'confidence': 0.0,
                    'error': 'No content provided'
                }
            
            logger.info(f"🔄 Starting document rewrite (Pass {pass_number}) - Assembly Line approach")
            logger.info(f"📄 Content length: {len(content)} characters")
            
            if self.progress_callback:
                self.progress_callback(session_id, 'structure_analysis', 
                                     'Analyzing document structure...', 
                                     'Parsing blocks and detecting format', 10)
            
            # Analyze document structure and errors
            analysis_result = self.style_analyzer.analyze_with_blocks(content, format_hint=format_hint)
            
            # Extract analysis and structural blocks from the result
            analysis = analysis_result.get('analysis', {})
            structural_blocks = analysis_result.get('structural_blocks', [])
            has_structure = analysis_result.get('has_structure', False)
            
            # Check if analysis succeeded (look at the nested analysis object)
            if not analysis.get('success', False):
                # Try to extract errors from structural blocks as fallback
                errors_from_blocks = []
                for block in structural_blocks:
                    errors_from_blocks.extend(block.get('errors', []))
                
                if not errors_from_blocks:
                    return {
                        'rewritten_text': content,
                        'improvements': [],
                        'confidence': 0.0,
                        'error': analysis.get('error', 'Analysis failed')
                    }
                else:
                    # Use errors from structural blocks if analysis failed but errors exist
                    errors = errors_from_blocks
                    logger.info(f"📊 Using {len(errors)} errors from structural blocks (analysis failed but errors detected)")
            else:
                # Extract errors from the nested analysis result
                errors = analysis.get('errors', [])
                
                # Also collect any additional errors from structural blocks
                for block in structural_blocks:
                    errors.extend(block.get('errors', []))
            
            logger.info(f"📊 Found {len(errors)} errors across {len(structural_blocks)} blocks")
            
            if self.progress_callback:
                self.progress_callback(session_id, 'assembly_line_start', 
                                     f'Assembly Line: Processing {len(errors)} errors...', 
                                     'Organizing errors by priority for surgical fixes', 30)
            
            # Use assembly line for ALL rewriting (no legacy mode)
            rewrite_result = self.ai_rewriter.rewrite(content, errors, context="document", pass_number=pass_number)
            
            if not rewrite_result.get('rewritten_text'):
                return {
                    'rewritten_text': content,
                    'improvements': [],
                    'confidence': 0.0,
                    'error': rewrite_result.get('error', 'Assembly line rewriting failed')
                }
            
            # Preserve document structure during reconstruction
            if self.progress_callback:
                self.progress_callback(session_id, 'structure_preservation', 
                                     'Preserving document structure...', 
                                     'Maintaining headings, lists, and formatting', 80)
            
            reconstructed_result = self._preserve_document_structure(
                original_content=content,
                rewritten_content=rewrite_result['rewritten_text'],
                structural_blocks=structural_blocks,
                format_hint=format_hint
            )
            
            # Combine results
            final_result = {
                'rewritten_text': reconstructed_result['content'],
                'improvements': rewrite_result.get('improvements', []),
                'confidence': rewrite_result.get('confidence', 0.0),
                'errors_fixed': rewrite_result.get('errors_fixed', 0),
                'original_errors': rewrite_result.get('original_errors', len(errors)),
                'passes_completed': rewrite_result.get('passes_completed', 1),
                'pass_number': pass_number,
                'can_refine': rewrite_result.get('can_refine', pass_number == 1),
                'assembly_line_used': True,
                'structure_preserved': reconstructed_result.get('structure_preserved', True),
                'model_used': rewrite_result.get('model_used', 'assembly_line')
            }
            
            if self.progress_callback:
                self.progress_callback(session_id, 'rewrite_complete', 
                                     f'Assembly Line Pass {pass_number}: Complete!', 
                                     f"Fixed {final_result['errors_fixed']} errors with surgical precision", 100)
            
            logger.info(f"✅ Document rewrite Pass {pass_number} complete: {final_result['errors_fixed']}/{final_result['original_errors']} errors fixed")
            
            return final_result
            
        except Exception as e:
            logger.error(f"Document rewriting failed: {e}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'Document rewriting failed: {str(e)}',
                'structure_preserved': False
            }
    
    def _preserve_document_structure(self, original_content: str, rewritten_content: str, 
                                   structural_blocks: List[Dict], format_hint: str = None) -> Dict[str, Any]:
        """
        Preserve document structure using appropriate reconstructor.
        
        Args:
            original_content: Original document content
            rewritten_content: AI-rewritten content
            structural_blocks: Parsed structural blocks
            format_hint: Document format hint
            
        Returns:
            Dictionary with reconstructed content and metadata
        """
        try:
            # Get appropriate reconstructor
            reconstructor = self.get_reconstructor(format_hint or 'markdown')
            
            if not reconstructor:
                logger.warning(f"No reconstructor found for format: {format_hint}, using original structure")
                return {
                    'content': rewritten_content,
                    'structure_preserved': False,
                    'method': 'no_reconstruction'
                }
            
            # Reconstruct with preserved structure
            reconstruction_result = reconstructor.reconstruct_with_preserved_structure(
                original_content=original_content,
                rewritten_content=rewritten_content,
                structural_blocks=structural_blocks
            )
            
            return {
                'content': reconstruction_result.get('content', rewritten_content),
                'structure_preserved': reconstruction_result.get('success', False),
                'method': reconstruction_result.get('method', 'unknown'),
                'metadata': reconstruction_result.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Structure preservation failed: {e}")
            return {
                'content': rewritten_content,
                'structure_preserved': False,
                'method': 'fallback',
                'error': str(e)
            }
    
    def refine_document(self, content: str, format_hint: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Refine document using assembly line approach (Pass 2).
        
        Args:
            content: Document content to refine
            format_hint: Document format hint
            session_id: Session identifier for progress tracking
            
        Returns:
            Dictionary with refinement results
        """
        return self.rewrite_document_with_structure_preservation(
            content=content, 
            format_hint=format_hint, 
            session_id=session_id, 
            pass_number=2
        )
    
    def is_available(self) -> bool:
        """Check if the AI rewriter is available."""
        return self.ai_rewriter.text_generator.is_available()
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about the rewriter."""
        return {
            'ai_available': self.is_available(),
            'assembly_line_enabled': True,  # Always true
            'model_info': self.ai_rewriter.model_manager.get_model_info() if hasattr(self.ai_rewriter, 'model_manager') else {},
            'capabilities': {
                'document_structure_preservation': True,
                'assembly_line_rewriting': True,
                'legacy_rewriting': False,  # No longer supported
                'pass_refinement': True,
                'format_detection': True
            }
        } 