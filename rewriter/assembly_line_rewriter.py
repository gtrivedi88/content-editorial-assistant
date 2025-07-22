"""
Assembly Line AI Rewriter
Applies fixes sequentially in priority order for surgical precision.
Uses config-driven approach to automatically handle all error types.
"""

import logging
import time
import yaml
import os
from typing import List, Dict, Any, Optional, Callable
from collections import defaultdict
import fnmatch
import re

logger = logging.getLogger(__name__)


class AssemblyLineRewriter:
    """
    Assembly line approach: Each error type gets processed by a specialist.
    This prevents AI from being overwhelmed and ensures surgical fixes.
    Config-driven to automatically handle all error types.
    """
    
    def __init__(self, text_generator, text_processor, progress_callback: Optional[Callable] = None):
        """Initialize with existing components and load config."""
        self.text_generator = text_generator
        self.text_processor = text_processor
        self.progress_callback = progress_callback
        
        # Load configuration from YAML file
        self.config = self._load_config()
        
        # Extract configuration components
        self.processing_passes = self.config.get('processing_passes', {})
        self.instruction_templates = self.config.get('instruction_templates', {})
        self.fallback_instruction = self.config.get('fallback_instruction', 
            "Fix {error_type} issues according to the style guide. Make minimal changes to preserve meaning.")
        self.severity_mapping = self.config.get('severity_mapping', {})
    
    def _load_config(self) -> Dict[str, Any]:
        """Load assembly line configuration from YAML file."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'assembly_line_config.yaml')
            
            if not os.path.exists(config_path):
                logger.warning(f"Config file not found at {config_path}, using fallback")
                return self._get_fallback_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"✅ Loaded assembly line config from {config_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}, using fallback")
            return self._get_fallback_config()
    
    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if YAML file is not available."""
        return {
            'processing_passes': {
                'urgent': {'name': 'Critical Pass'},
                'high': {'name': 'Structural Pass'},
                'medium': {'name': 'Grammar Pass'},
                'low': {'name': 'Style Pass'}
            },
            'instruction_templates': {},
            'fallback_instruction': "Fix {error_type} issues according to the style guide. Make minimal changes to preserve meaning.",
            'severity_mapping': {'high': 'urgent', 'medium': 'high', 'low': 'medium'}
        }
    
    def _get_instruction_for_error_type(self, error_type: str) -> str:
        """Get specialized instruction for error type using pattern matching."""
        
        # Try exact match first
        if error_type in self.instruction_templates:
            return self.instruction_templates[error_type]
        
        # Try pattern matching (e.g., word_usage_* matches word_usage_e)
        for pattern, instruction in self.instruction_templates.items():
            if '*' in pattern:
                # Convert pattern to fnmatch pattern
                if fnmatch.fnmatch(error_type, pattern):
                    return instruction
        
        # Use fallback with error type substitution
        return self.fallback_instruction.format(error_type=error_type.replace('_', ' '))
    
    def apply_assembly_line_fixes(self, content: str, errors: List[Dict[str, Any]], 
                                context: str = "sentence") -> Dict[str, Any]:
        """
        Apply fixes using assembly line approach.
        Each error type is handled by a specialist in priority order.
        """
        try:
            if not errors:
                return {
                    'rewritten_text': content,
                    'improvements': ['No errors detected'],
                    'confidence': 1.0,
                    'passes_completed': 0,
                    'errors_fixed': 0
                }
            
            # Group errors by priority using config-driven system
            priority_groups = self._group_errors_by_priority(errors)
            
            current_text = content
            total_fixes_applied = 0
            improvements = []
            passes_completed = 0
            
            # Process in priority order defined by config
            for priority in ['urgent', 'high', 'medium', 'low']:
                if priority not in priority_groups:
                    continue
                    
                priority_errors = priority_groups[priority]
                if not priority_errors:
                    continue
                
                pass_info = self.processing_passes.get(priority, {'name': f'{priority.title()} Pass'})
                pass_name = pass_info['name']
                
                logger.info(f"🏭 Starting {pass_name}: {len(priority_errors)} errors")
                
                if self.progress_callback:
                    self.progress_callback(
                        f'pass_{priority}', 
                        f'{pass_name} in progress...', 
                        f'Fixing {len(priority_errors)} {priority} priority issues',
                        20 + (passes_completed * 20)
                    )
                
                # Apply fixes for this priority level
                pass_result = self._apply_priority_pass(current_text, priority_errors, pass_name)
                
                if pass_result['success']:
                    current_text = pass_result['text']
                    total_fixes_applied += pass_result['fixes_applied']
                    improvements.extend(pass_result['improvements'])
                    passes_completed += 1
                    
                    logger.info(f"✅ {pass_name} complete: {pass_result['fixes_applied']} fixes applied")
                else:
                    logger.warning(f"⚠️ {pass_name} had issues: {pass_result.get('error', 'Unknown error')}")
            
            # Calculate confidence based on success rate
            confidence = min(0.95, 0.7 + (total_fixes_applied / len(errors)) * 0.25)
            
            return {
                'rewritten_text': current_text,
                'improvements': improvements if improvements else ['Text processed through assembly line'],
                'confidence': confidence,
                'passes_completed': passes_completed,
                'errors_fixed': total_fixes_applied,
                'original_errors': len(errors),
                'assembly_line_used': True
            }
            
        except Exception as e:
            logger.error(f"Assembly line rewriting failed: {e}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'Assembly line rewriting failed: {str(e)}',
                'assembly_line_used': False
            }
    
    def apply_sentence_level_assembly_line_fixes(self, content: str, errors: List[Dict[str, Any]], 
                                               context: str = "sentence") -> Dict[str, Any]:
        """
        Apply assembly line fixes at sentence level - each sentence goes through sequential passes.
        
        Args:
            content: Original text content
            errors: List of detected errors
            context: Context level ('sentence' or 'paragraph')
            
        Returns:
            Dictionary with rewrite results
        """
        try:
            if not errors:
                return {
                    'rewritten_text': content,
                    'improvements': ['No errors detected'],
                    'confidence': 1.0,
                    'passes_completed': 0,
                    'errors_fixed': 0,
                    'assembly_line_used': True
                }
            
            logger.info("🏭 Starting Sentence-Level Assembly Line Processing")
            logger.info(f"📊 Processing {len(errors)} errors with sentence-level precision")
            
            # Segment content into sentences
            sentences = self._segment_sentences(content)
            logger.info(f"📝 Segmented into {len(sentences)} sentences")
            
            # Group errors by sentence
            errors_by_sentence = self._group_errors_by_sentence(errors, sentences)
            
            # Process each sentence through assembly line
            rewritten_sentences = []
            total_fixes_applied = 0
            all_improvements = []
            total_passes_completed = 0
            
            for i, sentence in enumerate(sentences):
                sentence_errors = errors_by_sentence.get(i, [])
                
                if not sentence_errors:
                    # No errors for this sentence, keep as-is
                    rewritten_sentences.append(sentence)
                    continue
                
                logger.info(f"🔧 Processing sentence {i+1}: {len(sentence_errors)} errors")
                
                # Apply assembly line to this sentence
                sentence_result = self._process_sentence_assembly_line(sentence, sentence_errors, i+1)
                
                rewritten_sentences.append(sentence_result['rewritten_text'])
                total_fixes_applied += sentence_result['fixes_applied']
                all_improvements.extend(sentence_result['improvements'])
                total_passes_completed += sentence_result['passes_completed']
            
            # Reconstruct full content
            rewritten_content = self._reconstruct_content(rewritten_sentences, content)
            
            # Calculate confidence
            confidence = min(0.95, 0.7 + (total_fixes_applied / len(errors)) * 0.25)
            
            logger.info(f"✅ Sentence-Level Assembly Line complete: {total_fixes_applied}/{len(errors)} errors fixed")
            
            return {
                'rewritten_text': rewritten_content,
                'improvements': all_improvements if all_improvements else ['Text processed through sentence-level assembly line'],
                'confidence': confidence,
                'passes_completed': total_passes_completed,
                'errors_fixed': total_fixes_applied,
                'original_errors': len(errors),
                'sentences_processed': len([s for s in sentences if s.strip()]),
                'assembly_line_used': True
            }
            
        except Exception as e:
            logger.error(f"Sentence-level assembly line rewriting failed: {e}")
            return {
                'rewritten_text': content,
                'improvements': [],
                'confidence': 0.0,
                'error': f'Sentence-level assembly line rewriting failed: {str(e)}',
                'assembly_line_used': False
            }
    
    def _group_errors_by_priority(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group errors by priority using config-driven severity mapping."""
        priority_groups = defaultdict(list)
        
        for error in errors:
            severity = error.get('severity', 'medium')
            priority = self.severity_mapping.get(severity, 'medium')
            priority_groups[priority].append(error)
        
        return dict(priority_groups)
    
    def _apply_priority_pass(self, text: str, errors: List[Dict[str, Any]], 
                           pass_name: str) -> Dict[str, Any]:
        """Apply all fixes for a specific priority level."""
        current_text = text
        fixes_applied = 0
        improvements = []
        
        try:
            # Group by error type to process similar errors together
            error_groups = defaultdict(list)
            for error in errors:
                error_type = error.get('type', 'unknown')
                error_groups[error_type].append(error)
            
            # Apply fixes for each error type in this priority
            for error_type, error_list in error_groups.items():
                fix_result = self._apply_error_type_fix(current_text, error_type, error_list)
                
                if fix_result['success']:
                    current_text = fix_result['text']
                    fixes_applied += len(error_list)
                    improvements.append(f"{pass_name}: Fixed {error_type} ({len(error_list)} instances)")
                    
                    # Small delay for streaming effect
                    if self.progress_callback:
                        time.sleep(0.2)
                else:
                    logger.warning(f"Failed to fix {error_type}: {fix_result.get('error', 'Unknown')}")
            
            return {
                'success': True,
                'text': current_text,
                'fixes_applied': fixes_applied,
                'improvements': improvements
            }
            
        except Exception as e:
            return {
                'success': False,
                'text': text,
                'fixes_applied': 0,
                'improvements': [],
                'error': str(e)
            }
    
    def _apply_error_type_fix(self, text: str, error_type: str, 
                            error_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply fix for a specific error type using config-driven prompt."""
        try:
            # Get specialized instruction for this error type
            instruction = self._get_instruction_for_error_type(error_type)
            
            # Create focused prompt
            prompt = f"""Fix ONLY {error_type.replace('_', ' ')} in the following text.

INSTRUCTION: {instruction}

TEXT TO FIX:
{text}

CORRECTED TEXT:"""
            
            # Apply fix
            raw_result = self.text_generator.generate_text(prompt, text)
            cleaned_result = self.text_processor.clean_generated_text(raw_result, text)
            
            # Validate that a reasonable change was made
            if self._validate_fix(text, cleaned_result, error_type):
                return {
                    'success': True,
                    'text': cleaned_result
                }
            else:
                logger.warning(f"Fix validation failed for {error_type}")
                return {
                    'success': False,
                    'text': text,
                    'error': 'Fix validation failed'
                }
                
        except Exception as e:
            logger.error(f"Error applying {error_type} fix: {e}")
            return {
                'success': False,
                'text': text,
                'error': str(e)
            }
    
    def _validate_fix(self, original: str, fixed: str, error_type: str) -> bool:
        """Basic validation that fix was reasonable - now more lenient for surgical changes."""
        try:
            # Must not be empty
            if not fixed.strip():
                return False
            
            # Check for surgical changes (small word differences)
            original_words = original.split()
            fixed_words = fixed.split()
            word_diff = abs(len(fixed_words) - len(original_words))
            
            # For surgical changes, be more accepting
            if word_diff <= 3:  # Very small change
                logger.info(f"🔧 Surgical change detected for {error_type}: '{original}' → '{fixed}'")
                
                # Accept if ANY words changed (even if just spacing/hyphenation)
                if original.strip() != fixed.strip():
                    return True
                    
                # Check for subtle changes like "setup" → "set up"
                original_normalized = re.sub(r'\s+', ' ', original.strip().lower())
                fixed_normalized = re.sub(r'\s+', ' ', fixed.strip().lower())
                
                if original_normalized != fixed_normalized:
                    logger.info(f"✅ Surgical word change accepted: '{original.strip()}' → '{fixed.strip()}'")
                    return True
            
            # Original validation for larger changes
            if original == fixed:
                logger.info(f"❌ No change detected for {error_type}")
                return False  # No change made
            
            # RELAXED: More permissive length validation for meaningful changes
            length_ratio = len(fixed) / len(original) if len(original) > 0 else 1
            
            # Special cases for specific error types that may need longer/shorter fixes
            if error_type in ['references_citations', 'ambiguity', 'verbs']:
                # More permissive for these types that often need substantial changes
                if length_ratio > 10.0:  # Only reject extreme cases
                    logger.warning(f"❌ Change extremely long for {error_type}: {length_ratio:.1f}x longer")
                    return False
                if length_ratio < 0.1:  # Only reject extreme truncation
                    logger.warning(f"❌ Change extremely short for {error_type}: {length_ratio:.1f}x shorter")
                    return False
            else:
                # Standard validation for other types
                if length_ratio > 3.0:  # More permissive than 1.5x
                    logger.warning(f"❌ Change too long for {error_type}: {length_ratio:.1f}x longer")
                    return False
                if length_ratio < 0.3:  # More permissive than 0.5x
                    logger.warning(f"❌ Change too short for {error_type}: {length_ratio:.1f}x shorter")
                    return False
            
            logger.info(f"✅ Standard change accepted for {error_type} (ratio: {length_ratio:.1f}x)")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False 
    
    def _segment_sentences(self, content: str) -> List[str]:
        """Segment content into sentences."""
        # Simple sentence segmentation - can be enhanced later
        sentences = re.split(r'(?<=[.!?])\s+', content)
        return [s.strip() for s in sentences if s.strip()]
    
    def _group_errors_by_sentence(self, errors: List[Dict[str, Any]], sentences: List[str]) -> Dict[int, List[Dict[str, Any]]]:
        """Group errors by sentence index."""
        errors_by_sentence = defaultdict(list)
        
        for error in errors:
            sentence_index = error.get('sentence_index', 0)
            # Ensure sentence index is valid
            if 0 <= sentence_index < len(sentences):
                errors_by_sentence[sentence_index].append(error)
            else:
                # Default to first sentence if index is invalid
                errors_by_sentence[0].append(error)
        
        return dict(errors_by_sentence)
    
    def _process_sentence_assembly_line(self, sentence: str, sentence_errors: List[Dict[str, Any]], 
                                      sentence_num: int) -> Dict[str, Any]:
        """
        Process a single sentence through assembly line passes.
        
        Args:
            sentence: The sentence to process
            sentence_errors: Errors detected in this sentence
            sentence_num: Sentence number for logging
            
        Returns:
            Dictionary with sentence processing results
        """
        current_sentence = sentence
        fixes_applied = 0
        improvements = []
        passes_completed = 0
        
        # Group errors by priority for this sentence
        priority_groups = self._group_errors_by_priority(sentence_errors)
        
        # Process in priority order: urgent -> high -> medium -> low
        for priority in ['urgent', 'high', 'medium', 'low']:
            priority_errors = priority_groups.get(priority, [])
            
            if not priority_errors:
                # Skip empty passes entirely
                continue
            
            pass_info = self.processing_passes.get(priority, {'name': f'{priority.title()} Pass'})
            pass_name = pass_info['name']
            
            logger.info(f"    🔄 Sentence {sentence_num} - {pass_name}: {len(priority_errors)} errors")
            
            # Apply this priority pass to the sentence
            pass_result = self._apply_priority_pass_to_sentence(current_sentence, priority_errors, pass_name, sentence_num)
            
            if pass_result['success']:
                current_sentence = pass_result['text']
                fixes_applied += pass_result['fixes_applied']
                improvements.extend(pass_result['improvements'])
                passes_completed += 1
                
                logger.info(f"    ✅ Sentence {sentence_num} - {pass_name}: {pass_result['fixes_applied']} fixes applied")
            else:
                logger.warning(f"    ⚠️ Sentence {sentence_num} - {pass_name}: {pass_result.get('error', 'Unknown error')}")
        
        return {
            'rewritten_text': current_sentence,
            'fixes_applied': fixes_applied,
            'improvements': improvements,
            'passes_completed': passes_completed
        }
    
    def _apply_priority_pass_to_sentence(self, sentence: str, errors: List[Dict[str, Any]], 
                                       pass_name: str, sentence_num: int) -> Dict[str, Any]:
        """Apply a priority pass to a single sentence."""
        try:
            # Group by error type to process similar errors together
            error_groups = defaultdict(list)
            for error in errors:
                error_type = error.get('type', 'unknown')
                error_groups[error_type].append(error)
            
            current_text = sentence
            fixes_applied = 0
            improvements = []
            
            # Apply fixes for each error type in this priority
            for error_type, error_list in error_groups.items():
                fix_result = self._apply_error_type_fix(current_text, error_type, error_list)
                
                if fix_result['success']:
                    current_text = fix_result['text']
                    fixes_applied += len(error_list)
                    improvements.append(f"S{sentence_num} {pass_name}: Fixed {error_type} ({len(error_list)} instances)")
                else:
                    logger.warning(f"Failed to fix {error_type} in sentence {sentence_num}: {fix_result.get('error', 'Unknown')}")
            
            return {
                'success': True,
                'text': current_text,
                'fixes_applied': fixes_applied,
                'improvements': improvements
            }
            
        except Exception as e:
            return {
                'success': False,
                'text': sentence,
                'fixes_applied': 0,
                'improvements': [],
                'error': str(e)
            }
    
    def _reconstruct_content(self, sentences: List[str], original_content: str) -> str:
        """Reconstruct content from processed sentences, preserving original structure."""
        # Simple reconstruction - join sentences with appropriate spacing
        # This can be enhanced to preserve original formatting better
        return ' '.join(sentences) 