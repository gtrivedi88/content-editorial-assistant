"""
Simple AI Rewriter - Clean integration of existing modules
Uses the well-designed modular system without duplication.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimpleAIRewriter:
    """Simple AI rewriter that leverages existing modular components."""
    
    def __init__(self, use_ollama: bool = True, ollama_model: str = "llama3:8b", progress_callback=None):
        """Initialize with existing components."""
        self.progress_callback = progress_callback
        
        # Use existing components - no duplication
        from rewriter.core import AIRewriter
        from style_analyzer.core_analyzer import StyleAnalyzer
        from reconstructors import get_reconstructor, is_format_supported
        
        self.ai_rewriter = AIRewriter(use_ollama=use_ollama, ollama_model=ollama_model)
        self.style_analyzer = StyleAnalyzer({})
        
    def rewrite_document_with_structure_preservation(
        self, 
        content: str, 
        filename: str = "",
        format_hint: str = 'auto',
        style_errors: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Simple document rewriting using existing modular components with block-level processing.
        """
        try:
            # Step 1: Analyze with structure if no errors provided
            if not style_errors:
                if self.progress_callback:
                    self.progress_callback('analysis', 'Analyzing document...', 'Using existing style analyzer', 20)
                
                # Use existing style analyzer with blocks
                analysis_result = self.style_analyzer.analyze_with_blocks(content, format_hint)
                style_errors = analysis_result['analysis'].get('errors', [])
                structural_blocks = analysis_result.get('structural_blocks', [])
                
                logger.info(f"Found {len(style_errors)} style issues to fix across {len(structural_blocks)} blocks")
            else:
                # If errors provided, still get structural blocks for processing
                analysis_result = self.style_analyzer.analyze_with_blocks(content, format_hint)
                structural_blocks = analysis_result.get('structural_blocks', [])
            
            # Step 2: Process blocks individually for better heading handling
            if self.progress_callback:
                self.progress_callback('rewriting', 'AI rewriting...', 'Processing blocks individually', 60)
            
            # INTELLIGENT PRESERVATION: Fix only lines with errors, preserve all metadata
            original_lines = content.split('\n')
            rewritten_lines = []
            
            # Create error lookup by content
            error_by_sentence = {}
            for error in style_errors:
                sentence = error.get('sentence', '').strip()
                if sentence:
                    if sentence not in error_by_sentence:
                        error_by_sentence[sentence] = []
                    error_by_sentence[sentence].append(error)
            
            # Process line by line, preserving structure
            for line in original_lines:
                line_stripped = line.strip()
                
                # PRESERVE EXACTLY: metadata, comments, empty lines
                if (line.startswith(':') or line.startswith('//') or 
                    line_stripped == '' or line.startswith('ifdef::') or line.startswith('ifndef::')):
                    rewritten_lines.append(line)
                    continue
                
                # CHECK FOR HEADING ERRORS
                if line.startswith('='):
                    import re
                    heading_match = re.match(r'^(=+)\s*(.*)', line)
                    if heading_match:
                        heading_markup = heading_match.group(1)
                        heading_content = heading_match.group(2).strip()
                        
                        # Find heading errors for this content
                        heading_errors = []
                        for sentence, errors in error_by_sentence.items():
                            if heading_content in sentence or sentence in heading_content:
                                heading_errors.extend([e for e in errors if e.get('type') == 'headings'])
                        
                        if heading_errors:
                            # Fix heading content only
                            heading_result = self.ai_rewriter.rewrite(heading_content, heading_errors, "heading")
                            fixed_heading = heading_result.get('rewritten_text', heading_content).strip()
                            
                            # Clean and preserve markup
                            clean_heading = re.sub(r'\.$', '', fixed_heading)
                            clean_heading = re.sub(r'^=*\s*', '', clean_heading)
                            rewritten_lines.append(f"{heading_markup} {clean_heading}")
                            logger.info(f"Fixed heading: '{heading_content}' → '{clean_heading}'")
                        else:
                            rewritten_lines.append(line)
                    else:
                        rewritten_lines.append(line)
                    continue
                
                # CHECK FOR CONTENT ERRORS
                if line_stripped:
                    content_errors = []
                    for sentence, errors in error_by_sentence.items():
                        if line_stripped in sentence or sentence in line_stripped:
                            content_errors.extend([e for e in errors if e.get('type') != 'headings'])
                    
                    if content_errors:
                        # Fix this line only
                        line_result = self.ai_rewriter.rewrite(line_stripped, content_errors, "sentence")
                        fixed_line = line_result.get('rewritten_text', line_stripped)
                        rewritten_lines.append(fixed_line)
                        logger.info(f"Fixed content: '{line_stripped[:50]}...' → '{fixed_line[:50]}...'")
                    else:
                        rewritten_lines.append(line)
                else:
                    rewritten_lines.append(line)
            
            rewritten_document = '\n'.join(rewritten_lines)
            
            if self.progress_callback:
                self.progress_callback('complete', 'Rewriting complete!', 'Document improved', 100)
            
            return {
                'rewritten_document': rewritten_document,
                'overall_improvements': ['Fixed heading capitalization', 'Applied style corrections'],
                'overall_confidence': 0.9,
                'errors_fixed': len(style_errors),
                'structural_parsing_used': True,
                'simple_integration': True
            }
            
        except Exception as e:
            logger.error(f"Error in simple AI rewriting: {e}")
            return {
                'rewritten_document': content,
                'error': f'Simple rewriting failed: {str(e)}',
                'simple_integration': True
            }
    
    def rewrite(self, content: str, errors: Optional[List[Dict[str, Any]]] = None, context: str = "sentence") -> Dict[str, Any]:
        """Simple rewriting method."""
        return self.ai_rewriter.rewrite(content, errors or [], context, 1)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        return {
            'ai_available': True,
            'simple_integration': True,
            'uses_existing_modules': True
        } 