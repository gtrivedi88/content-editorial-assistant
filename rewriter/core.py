"""
Core AI Rewriter Module
Main orchestration class that coordinates all rewriter components.
"""

import logging
from typing import List, Dict, Any, Optional

from .models import ModelManager
from .prompts import PromptGenerator
from .generators import TextGenerator
from .processors import TextProcessor
from .evaluators import RewriteEvaluator

logger = logging.getLogger(__name__)


class AIRewriter:
    """Main AI Rewriter class that orchestrates the rewriting process."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", 
                 use_ollama: bool = False, ollama_model: str = "llama3:8b", 
                 progress_callback=None):
        """Initialize the AI rewriter with all components."""
        self.progress_callback = progress_callback
        
        # Initialize all components
        self.model_manager = ModelManager(model_name, use_ollama, ollama_model)
        self.prompt_generator = PromptGenerator(style_guide='ibm_style', use_ollama=use_ollama)
        self.text_generator = TextGenerator(self.model_manager)
        self.text_processor = TextProcessor()
        self.evaluator = RewriteEvaluator()
        
        logger.info(f"✅ AIRewriter initialized with {len(self._get_available_components())} components")
    
    def rewrite(self, content: str, errors: List[Dict[str, Any]], 
                context: str = "sentence", pass_number: int = 1) -> Dict[str, Any]:
        """
        Generate AI-powered rewrite suggestions.
        
        Args:
            content: Original text content
            errors: List of detected errors
            context: Context level ('sentence' or 'paragraph')
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
            
            if not errors and pass_number == 1:
                return {
                    'rewritten_text': content,
                    'improvements': ['No errors detected'],
                    'confidence': 1.0
                }
            
            # Check if AI models are available
            if not self.text_generator.is_available():
                return {
                    'rewritten_text': content,
                    'improvements': [],
                    'confidence': 0.0,
                    'error': 'AI models are not available. Please check your model configuration.'
                }
            
            if pass_number == 1:
                return self._perform_first_pass(content, errors, context)
            else:
                return self._perform_second_pass(content, errors, context)
            
        except Exception as e:
            logger.error(f"Error in rewrite: {str(e)}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'AI rewrite failed: {str(e)}'
            }
    
    def _perform_first_pass(self, content: str, errors: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Perform the first pass of AI rewriting."""
        logger.info("🔄 Starting AI Pass 1: Initial rewrite based on detected errors")
        logger.info(f"📊 Processing {len(errors)} detected errors: {[e.get('type', 'unknown') for e in errors]}")
        
        if self.progress_callback:
            self.progress_callback('pass1_start', 'Pass 1: Generating initial improvements...', 
                                 'AI addressing specific style issues', 20)
        
        # Generate context-aware prompt for first pass
        initial_prompt = self.prompt_generator.generate_prompt(content, errors, context)
        logger.info(f"🎯 Pass 1 prompt length: {len(initial_prompt)} characters")
        
        if self.progress_callback:
            self.progress_callback('pass1_processing', 'Pass 1: AI processing detected issues...', 
                                 'Converting passive voice, shortening sentences', 60)
        
        # Generate first rewrite
        raw_rewrite = self.text_generator.generate_text(initial_prompt, content)
        
        # Clean and process the generated text
        first_rewrite = self.text_processor.clean_generated_text(raw_rewrite, content)
        logger.info(f"✅ Pass 1 complete. Length: {len(first_rewrite)} chars (original: {len(content)} chars)")
        
        # Check if first pass made changes
        if first_rewrite == content:
            logger.warning("❌ Pass 1 failed to make changes")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': 'AI model failed to make meaningful improvements to the text'
            }
        
        if self.progress_callback:
            self.progress_callback('pass1_complete', 'Pass 1: Initial rewrite completed', 
                                 'First pass improvements applied', 100)
        
        # Evaluate the rewrite
        evaluation = self.evaluator.evaluate_rewrite_quality(
            content, first_rewrite, errors, 
            self.model_manager.use_ollama, pass_number=1
        )
        
        logger.info(f"✅ Pass 1 complete. Confidence: {evaluation['confidence']:.2f}")
        logger.info(f"📊 Pass 1 stats - Original: {len(content.split())} words, Rewritten: {len(first_rewrite.split())} words")
        
        return {
            'rewritten_text': first_rewrite,
            'improvements': evaluation['improvements'],
            'confidence': evaluation['confidence'],
            'original_errors': len(errors),
            'model_used': evaluation['model_used'] + '_pass1',
            'pass_number': 1,
            'can_refine': True,  # Indicate that Pass 2 is available
            'evaluation': evaluation
        }
    
    def _perform_second_pass(self, first_pass_result: str, original_errors: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Perform the second pass of AI rewriting (refinement)."""
        logger.info("🔍 Starting AI Pass 2: Self-review and refinement")
        logger.info(f"🔄 Reviewing first pass output for further improvements...")
        
        if self.progress_callback:
            self.progress_callback('pass2_start', 'Pass 2: AI self-review and refinement...', 
                                 'AI critically reviewing its own work', 20)
        
        # Generate self-review prompt
        review_prompt = self.prompt_generator.generate_self_review_prompt(first_pass_result, original_errors)
        logger.info(f"🎯 Pass 2 prompt length: {len(review_prompt)} characters")
        
        if self.progress_callback:
            self.progress_callback('pass2_processing', 'Pass 2: Applying final polish...', 
                                 'Enhancing clarity and flow', 60)
        
        # Get AI's self-assessment and refinement
        raw_final_rewrite = self.text_generator.generate_text(review_prompt, first_pass_result)
        final_rewrite = self.text_processor.clean_generated_text(raw_final_rewrite, first_pass_result)
        logger.info(f"✅ Pass 2 complete. Length: {len(final_rewrite)} chars")
        
        # If second pass didn't improve, use first pass
        if not final_rewrite or final_rewrite == first_pass_result or len(final_rewrite.strip()) < 10:
            logger.info("🔄 Second pass: No further improvements made, using first pass result")
            final_rewrite = first_pass_result
            second_pass_improvements = ['Second pass: No further refinements needed']
        else:
            second_pass_improvements = self.evaluator.extract_second_pass_improvements(first_pass_result, final_rewrite)
            logger.info(f"🎯 Second pass improvements: {second_pass_improvements}")
        
        if self.progress_callback:
            self.progress_callback('pass2_complete', 'Pass 2: Refinement completed successfully!', 
                                 'Your polished text is ready', 100)
        
        # Calculate enhanced confidence for second pass
        final_confidence = self.evaluator.calculate_second_pass_confidence(first_pass_result, final_rewrite, original_errors)
        
        logger.info(f"✅ Pass 2 complete. Final confidence: {final_confidence:.2f}")
        logger.info(f"📊 Final stats - Pass 1: {len(first_pass_result.split())} words, Final: {len(final_rewrite.split())} words")
        
        return {
            'rewritten_text': final_rewrite,
            'improvements': second_pass_improvements,
            'confidence': final_confidence,
            'original_errors': len(original_errors),
            'model_used': ('ollama' if self.model_manager.use_ollama else 'huggingface') + '_pass2',
            'pass_number': 2,
            'can_refine': False  # No further refinement available
        }
    
    def refine_text(self, first_pass_result: str, original_errors: List[Dict[str, Any]], 
                    context: str = "sentence") -> Dict[str, Any]:
        """
        Refine the first pass result with AI Pass 2.
        
        Args:
            first_pass_result: The result from the first AI pass
            original_errors: Original errors detected by style analyzer
            context: Context level
            
        Returns:
            Dictionary with refined rewrite results
        """
        return self._perform_second_pass(first_pass_result, original_errors, context)
    
    def batch_rewrite(self, content_list: List[str], errors_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Rewrite multiple pieces of content in batch."""
        results = []
        
        for content, errors in zip(content_list, errors_list):
            result = self.rewrite(content, errors)
            results.append(result)
        
        return results
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the rewriter system."""
        return {
            'model_info': self.model_manager.get_model_info(),
            'generation_info': self.text_generator.get_model_info(),
            'available_components': self._get_available_components(),
            'is_ready': self.is_ready()
        }
    
    def is_ready(self) -> bool:
        """Check if the rewriter system is ready for use."""
        return self.text_generator.is_available()
    
    def _get_available_components(self) -> List[str]:
        """Get list of available components."""
        components = ['model_manager', 'prompt_generator', 'text_processor', 'evaluator']
        
        if self.text_generator.is_available():
            components.append('text_generator')
        
        return components 