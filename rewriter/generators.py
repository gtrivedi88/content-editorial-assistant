"""
Text Generation Module
Handles actual AI text generation using various models.
"""

import logging
import requests
from typing import Optional, Dict, Any
from .models import ModelManager

logger = logging.getLogger(__name__)


class TextGenerator:
    """Handles AI text generation using various models."""
    
    def __init__(self, model_manager: ModelManager):
        """Initialize the text generator with a model manager."""
        self.model_manager = model_manager
    
    def generate_with_ollama(self, prompt: str, original_text: str) -> str:
        """Generate rewritten text using Ollama."""
        if not self.model_manager.use_ollama:
            logger.warning("Ollama not available for generation")
            return original_text
            
        try:
            # Conservative parameters but with sufficient length for full rewrites
            payload = {
                "model": self.model_manager.ollama_model,
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
                self.model_manager.ollama_url,
                json=payload
                # No timeout - let the model take the time it needs
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                logger.info(f"✅ Raw Ollama response: '{generated_text}'")
                logger.info(f"📊 Ollama response length: {len(generated_text)} chars vs original: {len(original_text)} chars")
                
                return generated_text if generated_text else original_text
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return original_text
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return original_text
    
    def generate_with_hf_model(self, prompt: str, original_text: str) -> str:
        """Generate rewritten text using Hugging Face model."""
        if not self.model_manager.generator:
            logger.warning("HuggingFace model not available for generation")
            return original_text
            
        try:
            # Check if tokenizer is available for eos_token_id
            pad_token_id = None
            if self.model_manager.tokenizer and hasattr(self.model_manager.tokenizer, 'eos_token_id'):
                pad_token_id = self.model_manager.tokenizer.eos_token_id
            
            # Generate text using the pipeline
            response = self.model_manager.generator(
                prompt,
                max_length=len(prompt.split()) + 100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=pad_token_id
            )
            
            # Handle the response - it should be a list of dictionaries
            if not response or not isinstance(response, list) or len(response) == 0:
                logger.warning("Empty or invalid response from HuggingFace model")
                return original_text
                
            generated_text = response[0].get('generated_text', '')
            
            # Ensure we have a string
            if not isinstance(generated_text, str):
                logger.warning("Generated text is not a string")
                return original_text
            
            if "Improved text:" in generated_text:
                rewritten = generated_text.split("Improved text:")[-1].strip()
            else:
                rewritten = generated_text.replace(prompt, "").strip()
            
            return rewritten if rewritten else original_text
            
        except Exception as e:
            logger.error(f"Hugging Face model generation failed: {e}")
            return original_text
    
    def generate_text(self, prompt: str, original_text: str) -> str:
        """
        Generate text using the available model.
        
        Args:
            prompt: The prompt to use for generation
            original_text: Original text as fallback
            
        Returns:
            Generated text or original text if generation fails
        """
        if self.model_manager.use_ollama:
            return self.generate_with_ollama(prompt, original_text)
        else:
            return self.generate_with_hf_model(prompt, original_text)
    
    def is_available(self) -> bool:
        """Check if text generation is available."""
        return self.model_manager.is_available()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current generation setup."""
        return {
            **self.model_manager.get_model_info(),
            'generation_available': self.is_available()
        } 