"""
Model Management Module
Handles Ollama and HuggingFace model initialization and connectivity.
"""

import logging
import requests
from typing import Optional, Any

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages AI model initialization and connectivity."""
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium", 
                 use_ollama: bool = False, ollama_model: str = "llama3:8b"):
        """Initialize the model manager."""
        self.model_name = model_name
        self.use_ollama = use_ollama
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/generate"
        
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
    
    def is_available(self) -> bool:
        """Check if any model is available for use."""
        if self.use_ollama:
            return True  # Ollama connection was tested in init
        return self.generator is not None
    
    def get_model_info(self) -> dict:
        """Get information about the current model setup."""
        return {
            'use_ollama': self.use_ollama,
            'ollama_model': self.ollama_model if self.use_ollama else None,
            'hf_model': self.model_name if not self.use_ollama else None,
            'hf_available': HF_AVAILABLE,
            'is_available': self.is_available()
        } 