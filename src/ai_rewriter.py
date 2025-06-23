"""
AI Rewriter Module
Generates AI-powered rewriting suggestions based on detected style errors.
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

import requests

logger = logging.getLogger(__name__)

class AIRewriter:
    """Handles AI-powered text rewriting based on style analysis errors."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", use_ollama: bool = False, ollama_model: str = "llama3:8b", progress_callback=None):
        """Initialize the AI rewriter with a language model."""
        self.model_name = model_name
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"
        self.progress_callback = progress_callback
        
        self.model = None
        self.tokenizer = None
        self.generator = None
        
        # Initialize the appropriate model
        if use_ollama:
            self._test_ollama_connection()
        else:
            self._initialize_hf_model()
        
    
    def _test_ollama_connection(self):
        """Test if Ollama is running and the model is available."""
        try:
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.ollama_model in available_models:
                    logger.info(f"✅ Ollama connected successfully. Using model: {self.ollama_model}")
                    self.use_ollama = True
                else:
                    logger.warning(f"⚠️ Model {self.ollama_model} not found in Ollama. Available models: {available_models}")
                    logger.info("You can pull it with: ollama pull llama3:8b")
                    self.use_ollama = False
            else:
                logger.warning("⚠️ Ollama is not responding properly")
                self.use_ollama = False
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            self.use_ollama = False
    
    def _initialize_hf_model(self):
        """Initialize the Hugging Face model for text generation."""
        if not HF_AVAILABLE:
            logger.warning("Transformers not available. Install with: pip install transformers torch")
            return
            
        try:
            logger.info(f"Initializing Hugging Face model: {self.model_name}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.tokenizer,
                max_length=512,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            logger.info("✅ Hugging Face model initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Hugging Face model: {e}")
            self.generator = None
    
    def rewrite(self, content: str, errors: List[Dict[str, Any]], context: str = "sentence", pass_number: int = 1) -> Dict[str, Any]:
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
            
            # Only use Ollama - no fallbacks
            if not self.use_ollama:
                return {
                    'rewritten_text': content,
                    'improvements': [],
                    'confidence': 0.0,
                    'error': 'Ollama is not available. AI rewriting requires a working Ollama connection.'
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
        initial_prompt = self._generate_prompt(content, errors, context)
        logger.info(f"🎯 Pass 1 prompt length: {len(initial_prompt)} characters")
        
        if self.progress_callback:
            self.progress_callback('pass1_processing', 'Pass 1: AI processing detected issues...', 
                                 'Converting passive voice, shortening sentences', 60)
        
        # Generate first rewrite using Ollama
        first_rewrite = self._generate_with_ollama(initial_prompt, content)
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
        
        # Extract improvements from first pass
        first_pass_improvements = self._extract_improvements(content, first_rewrite, errors)
        
        # Calculate confidence for first pass
        first_pass_confidence = self._calculate_confidence(content, first_rewrite, errors)
        
        logger.info(f"✅ Pass 1 complete. Confidence: {first_pass_confidence:.2f}")
        logger.info(f"📊 Pass 1 stats - Original: {len(content.split())} words, Rewritten: {len(first_rewrite.split())} words")
        
        return {
            'rewritten_text': first_rewrite,
            'improvements': first_pass_improvements,
            'confidence': first_pass_confidence,
            'original_errors': len(errors),
            'model_used': 'ollama_pass1',
            'pass_number': 1,
            'can_refine': True  # Indicate that Pass 2 is available
        }
    
    def _perform_second_pass(self, first_pass_result: str, original_errors: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """Perform the second pass of AI rewriting (refinement)."""
        logger.info("🔍 Starting AI Pass 2: Self-review and refinement")
        logger.info(f"🔄 Reviewing first pass output for further improvements...")
        
        if self.progress_callback:
            self.progress_callback('pass2_start', 'Pass 2: AI self-review and refinement...', 
                                 'AI critically reviewing its own work', 20)
        
        # Generate self-review prompt
        review_prompt = self._generate_self_review_prompt_v2(first_pass_result, original_errors)
        logger.info(f"🎯 Pass 2 prompt length: {len(review_prompt)} characters")
        
        if self.progress_callback:
            self.progress_callback('pass2_processing', 'Pass 2: Applying final polish...', 
                                 'Enhancing clarity and flow', 60)
        
        # Get AI's self-assessment and refinement
        final_rewrite = self._generate_with_ollama(review_prompt, first_pass_result)
        logger.info(f"✅ Pass 2 complete. Length: {len(final_rewrite)} chars")
        
        # If second pass didn't improve, use first pass
        if not final_rewrite or final_rewrite == first_pass_result or len(final_rewrite.strip()) < 10:
            logger.info("🔄 Second pass: No further improvements made, using first pass result")
            final_rewrite = first_pass_result
            second_pass_improvements = ['Second pass: No further refinements needed']
        else:
            second_pass_improvements = self._extract_second_pass_improvements(first_pass_result, final_rewrite)
            logger.info(f"🎯 Second pass improvements: {second_pass_improvements}")
        
        if self.progress_callback:
            self.progress_callback('pass2_complete', 'Pass 2: Refinement completed successfully!', 
                                 'Your polished text is ready', 100)
        
        # Calculate enhanced confidence for second pass
        final_confidence = self._calculate_second_pass_confidence(first_pass_result, final_rewrite, original_errors)
        
        logger.info(f"✅ Pass 2 complete. Final confidence: {final_confidence:.2f}")
        logger.info(f"📊 Final stats - Pass 1: {len(first_pass_result.split())} words, Final: {len(final_rewrite.split())} words")
        
        return {
            'rewritten_text': final_rewrite,
            'improvements': second_pass_improvements,
            'confidence': final_confidence,
            'original_errors': len(original_errors),
            'model_used': 'ollama_pass2',
            'pass_number': 2,
            'can_refine': False  # No further refinement available
        }
    
    def refine_text(self, first_pass_result: str, original_errors: List[Dict[str, Any]], context: str = "sentence") -> Dict[str, Any]:
        """
        Refine the first pass result with AI Pass 2.
        
        Args:
            first_pass_result: The result from the first AI pass
            original_errors: Original errors detected by SpaCy
            context: Context level
            
        Returns:
            Dictionary with refined rewrite results
        """
        return self._perform_second_pass(first_pass_result, original_errors, context)
    
    def _generate_self_review_prompt_v2(self, first_rewrite: str, original_errors: List[Dict[str, Any]]) -> str:
        """Generate prompt for AI self-review and refinement (Pass 2)."""
        
        error_types = [error.get('type', '') for error in original_errors]
        error_summary = ', '.join(set(error_types))
        
        prompt = f"""You are a professional editor reviewing your own work for final polish.

YOUR FIRST REWRITE:
{first_rewrite}

ORIGINAL ISSUES ADDRESSED: {error_summary}

Please create a FINAL POLISHED VERSION that:
1. Maintains all improvements from your first rewrite
2. Enhances clarity and flow even further
3. Ensures perfect readability and professionalism
4. Keeps the original meaning intact

Be critical and look for any remaining opportunities to improve clarity, conciseness, or flow.

FINAL POLISHED VERSION:"""
        
        return prompt
    
    def _calculate_second_pass_confidence(self, first_pass: str, final_rewrite: str, errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for second pass refinement."""
        try:
            base_confidence = 0.7  # Start with higher confidence for second pass
            
            # Bonus for completing second pass
            base_confidence += 0.2
            
            # Check if second pass made meaningful changes
            if final_rewrite != first_pass:
                base_confidence += 0.1
            
            # Adjust based on number of original errors addressed
            if errors:
                base_confidence += min(0.1, len(errors) * 0.02)
            
            return max(0.0, min(1.0, base_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating second pass confidence: {e}")
            return 0.8  # Default high confidence for second pass
    
    def _extract_second_pass_improvements(self, first_rewrite: str, final_rewrite: str) -> List[str]:
        """Extract improvements made in the second pass."""
        improvements = []
        
        # Compare lengths
        first_words = len(first_rewrite.split())
        final_words = len(final_rewrite.split())
        
        if final_words < first_words:
            improvements.append(f"Second pass: Further reduced word count by {first_words - final_words} words")
        elif final_words > first_words:
            improvements.append(f"Second pass: Enhanced clarity with {final_words - first_words} additional words")
        
        # Check for structural improvements
        first_sentences = len([s for s in first_rewrite.split('.') if s.strip()])
        final_sentences = len([s for s in final_rewrite.split('.') if s.strip()])
        
        if final_sentences > first_sentences:
            improvements.append("Second pass: Improved sentence structure and flow")
        
        # Check for word choice improvements
        if first_rewrite.lower() != final_rewrite.lower():
            improvements.append("Second pass: Refined word choice and phrasing")
        
        # Default improvement if text changed
        if not improvements and first_rewrite != final_rewrite:
            improvements.append("Second pass: Applied additional polish and refinements")
        
        return improvements if improvements else ["Second pass: Minor refinements applied"]
    
    def _calculate_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for the rewrite."""
        try:
            confidence = 0.7
            
            # Higher confidence for Ollama (local model)
            if self.use_ollama and rewritten != original:
                confidence += 0.3
            elif self.generator and rewritten != original:
                confidence += 0.2
            
            # Adjust based on number of errors addressed
            if errors:
                confidence += min(0.1, len(errors) * 0.02)
            
            # Penalize if no changes were made
            if rewritten == original:
                confidence -= 0.3
            
            # Check length ratio
            original_length = len(original.split())
            rewritten_length = len(rewritten.split())
            
            if original_length > 0:
                length_ratio = rewritten_length / original_length
                if length_ratio > 1.5 or length_ratio < 0.5:
                    confidence -= 0.2
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _generate_prompt(self, content: str, errors: List[Dict[str, Any]], context: str) -> str:
        """Generate a context-aware prompt based on detected errors."""
        
        # Build prompt using actual suggestions from StyleAnalyzer per sentence
        sentence_suggestions = []
        
        for error in errors:
            error_type = error.get('type', '')
            sentence = error.get('sentence', '')
            suggestions = error.get('suggestions', [])
            
            if sentence and suggestions:
                # Keep sentence-specific suggestions together
                for suggestion in suggestions:
                    sentence_suggestions.append(f"For '{sentence[:60]}...': {suggestion}")
        
        # Build enhanced prompt using actual detected suggestions
        if self.use_ollama:
            prompt = self._build_ollama_prompt(content, sentence_suggestions)
        else:
            prompt = self._build_hf_prompt(content, sentence_suggestions)
        
        return prompt
    
    def _build_ollama_prompt(self, content: str, sentence_suggestions: List[str]) -> str:
        """Build optimized prompt for Ollama/Llama models."""
        
        if sentence_suggestions:
            suggestions_text = "\n".join(f"- {suggestion}" for suggestion in sentence_suggestions)
            prompt = f"""You are a professional technical writing editor. Rewrite the following text to address these specific issues:

{suggestions_text}

REWRITING GUIDELINES:
- Convert all passive voice to active voice
- Use simple, direct language instead of corporate jargon
- Break long sentences into shorter, clearer ones (15-20 words each)
- Remove unnecessary words and phrases
- Maintain the original meaning and all key information
- Write for a 9th-11th grade reading level

Original text:
{content}

Improved text:"""
        else:
            prompt = f"""You are a professional technical writing editor. Improve this text for clarity and conciseness:

REWRITING GUIDELINES:
- Use active voice throughout
- Choose simple, direct words over complex ones
- Keep sentences short and clear (15-20 words each)
- Remove unnecessary words and corporate jargon
- Maintain all original meaning and information
- Write for a 9th-11th grade reading level

Original text:
{content}

Improved text:"""
        
        return prompt
    
    def _build_hf_prompt(self, content: str, sentence_suggestions: List[str]) -> str:
        """Build prompt for Hugging Face models."""
        prompt_parts = [
            "Task: Improve the following text based on these specific issues:",
            "\n".join(f"- {ctx}" for ctx in sentence_suggestions),
            f"\nOriginal text: {content}",
            "\nImproved text:"
        ]
        return "\n".join(prompt_parts)
    
    def _generate_with_ollama(self, prompt: str, original_text: str) -> str:
        """Generate rewritten text using Ollama."""
        try:
            # Conservative parameters but with sufficient length for full rewrites
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.4,  # Increased from 0.1 for more creative rewrites
                    "top_p": 0.7,        # Increased from 0.5 for more variety
                    "top_k": 20,         # Increased from 10 for more vocabulary options
                    "num_predict": 512,  # Increased from 100 to allow full text completion
                    "stop": ["\n\nOriginal:", "\n\nRewrite:", "###", "---"]  # Clear stop tokens
                }
            }
            
            logger.info(f"Sending prompt to Ollama: {prompt[:100]}...")
            
            response = requests.post(
                self.ollama_url,
                json=payload
                # No timeout - let the model take the time it needs
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                logger.info(f"Raw Ollama response: '{generated_text}'")
                
                # Clean and validate the output
                rewritten = self._clean_generated_text(generated_text, original_text)
                
                logger.info(f"Cleaned response: '{rewritten}'")
                
                return rewritten if rewritten else original_text
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return original_text
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return original_text
    
    def _generate_with_hf_model(self, prompt: str, original_text: str) -> str:
        """Generate rewritten text using Hugging Face model."""
        try:
            response = self.generator(
                prompt,
                max_length=len(prompt.split()) + 100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            generated_text = response[0]['generated_text']
            
            if "Improved text:" in generated_text:
                rewritten = generated_text.split("Improved text:")[-1].strip()
            else:
                rewritten = generated_text.replace(prompt, "").strip()
            
            rewritten = self._clean_generated_text(rewritten, original_text)
            return rewritten if rewritten else original_text
            
        except Exception as e:
            logger.error(f"Hugging Face model generation failed: {e}")
            return original_text
    
    def _rule_based_rewrite(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Fallback rule-based rewriting when AI models are not available."""
        rewritten = content
        
        try:
            for error in errors:
                error_type = error.get('type', '')
                
                if error_type == 'conciseness':
                    wordy_replacements = {
                        'in order to': 'to',
                        'due to the fact that': 'because',
                        'at this point in time': 'now',
                        'a large number of': 'many',
                        'make a decision': 'decide',
                        'for the purpose of': 'to',
                        'in spite of the fact that': 'although'
                    }
                    
                    for wordy, concise in wordy_replacements.items():
                        rewritten = re.sub(r'\b' + re.escape(wordy) + r'\b', concise, rewritten, flags=re.IGNORECASE)
                
                elif error_type == 'clarity':
                    complex_replacements = {
                        'utilize': 'use',
                        'facilitate': 'help',
                        'demonstrate': 'show',
                        'implement': 'do',
                        'commence': 'start',
                        'terminate': 'end'
                    }
                    
                    for complex_word, simple_word in complex_replacements.items():
                        rewritten = re.sub(r'\b' + complex_word + r'\b', simple_word, rewritten, flags=re.IGNORECASE)
                
                elif error_type == 'sentence_length':
                    sentence = error.get('sentence', '')
                    if sentence and sentence in rewritten:
                        if ' and ' in sentence and len(sentence.split()) > 20:
                            parts = sentence.split(' and ', 1)
                            if len(parts) == 2:
                                new_sentence = f"{parts[0].strip()}. {parts[1].strip()}"
                                rewritten = rewritten.replace(sentence, new_sentence)
            
            return rewritten
            
        except Exception as e:
            logger.error(f"Rule-based rewrite failed: {e}")
            return content
    
    def _clean_generated_text(self, generated_text: str, original_text: str) -> str:
        """Clean and validate generated text, extracting only the rewritten content."""
        if not generated_text:
            logger.warning("Empty generated text")
            return original_text
        
        cleaned = generated_text.strip()
        logger.info(f"Raw AI response: '{cleaned[:200]}...'")
        
        # Remove meta-commentary and explanations more aggressively
        
        # Split into paragraphs and find the actual content
        paragraphs = cleaned.split('\n\n')
        content_paragraphs = []
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Skip paragraphs that are clearly meta-commentary
            meta_indicators = [
                'note:', 'i\'ve rewritten', 'i have rewritten', 'i applied', 'i made',
                'the following changes', 'here are the improvements', 'improvements made:',
                'changes made:', 'key improvements:', 'i converted', 'i removed',
                'i shortened', 'i replaced', 'the rewrite', 'this rewrite',
                'to address the issues', 'as requested', 'per your instructions'
            ]
            
            # Check if paragraph starts with meta-commentary
            para_lower = para.lower()
            is_meta = any(para_lower.startswith(indicator) for indicator in meta_indicators)
            
            # Also check if paragraph contains explanation patterns
            explanation_patterns = [
                'i\'ve', 'i have', 'i applied', 'i made', 'i converted', 'i removed',
                'to address', 'as you specified', 'per the guidelines', 'following the instructions'
            ]
            
            has_explanation = any(pattern in para_lower for pattern in explanation_patterns)
            
            # Skip if it's clearly meta-commentary
            if is_meta or (has_explanation and len(para.split()) < 50):
                logger.info(f"Skipping meta-commentary paragraph: '{para[:100]}...'")
                continue
            
            content_paragraphs.append(para)
        
        # Rejoin content paragraphs
        if content_paragraphs:
            cleaned = '\n\n'.join(content_paragraphs)
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "here is the improved text:",
            "here's the improved text:",
            "improved text:",
            "rewritten text:",
            "revised text:",
            "the improved version:",
            "here is the rewrite:",
            "here's the rewrite:",
            "sure, here's",
            "certainly, here's",
            "here's a rewritten version:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove sentences that are clearly explanatory
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        content_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_lower = sentence.lower()
            
            # Skip explanatory sentences
            explanatory_starts = [
                'note:', 'i\'ve', 'i have', 'i applied', 'i made', 'i converted',
                'i removed', 'i shortened', 'i replaced', 'this addresses',
                'these changes', 'the rewrite', 'as requested', 'per your'
            ]
            
            is_explanatory = any(sentence_lower.startswith(start) for start in explanatory_starts)
            
            if not is_explanatory:
                content_sentences.append(sentence)
        
        if content_sentences:
            cleaned = ' '.join(content_sentences)
        
        # Remove any remaining artifacts
        cleaned = re.sub(r'\[insert[^\]]*\]', '', cleaned)  # Remove placeholder text like [insert specific examples]
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        logger.info(f"Cleaned AI response: '{cleaned[:200]}...'")
        
        # Validation
        if len(cleaned) < 10:
            logger.warning("Generated text too short after cleaning")
            return original_text
        
        # Check if it's meaningfully different from original
        if cleaned.lower().strip() == original_text.lower().strip():
            logger.warning("Generated text identical to original after cleaning")
            return original_text
        
        # Ensure proper sentence endings
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            # Find the last complete sentence
            sentences = re.split(r'[.!?]+', cleaned)
            if len(sentences) > 1:
                # Take all complete sentences except the last incomplete one
                complete_sentences = sentences[:-1]
                if complete_sentences:
                    cleaned = '. '.join(complete_sentences) + '.'
        
        logger.info(f"Final cleaned text: '{cleaned}'")
        return cleaned
    
    def _extract_improvements(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> List[str]:
        """Extract and describe the improvements made."""
        improvements = []
        
        original_words = len(original.split())
        rewritten_words = len(rewritten.split())
        
        if rewritten_words < original_words:
            improvements.append(f"Reduced word count from {original_words} to {rewritten_words}")
        
        error_types = set(error.get('type', '') for error in errors)
        
        if 'passive_voice' in error_types:
            improvements.append("Converted passive voice to active voice")
        
        if 'sentence_length' in error_types:
            improvements.append("Shortened overly long sentences")
        
        if 'conciseness' in error_types:
            improvements.append("Removed wordy phrases")
        
        if 'clarity' in error_types:
            improvements.append("Replaced complex words with simpler alternatives")
        
        if not improvements:
            improvements.append("Applied general style improvements")
        
        return improvements
    
    def batch_rewrite(self, content_list: List[str], errors_list: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Rewrite multiple pieces of content in batch."""
        results = []
        
        for content, errors in zip(content_list, errors_list):
            result = self.rewrite(content, errors)
            results.append(result)
        
        return results 