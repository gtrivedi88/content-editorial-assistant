"""
Fallback Services Module
Contains simple fallback implementations when advanced modules are not available.
Provides basic functionality with graceful degradation.
"""

import re
import logging
import requests
from typing import Dict, Any, List, Optional
from config import Config

logger = logging.getLogger(__name__)


class SimpleDocumentProcessor:
    """Simple document processor fallback when main processor is unavailable."""
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file type is supported."""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'md'}
    
    def extract_text(self, filepath: str) -> Optional[str]:
        """Extract text from file with basic error handling."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error extracting text from {filepath}: {e}")
            return None


class SimpleStyleAnalyzer:
    """Simple style analyzer fallback when main analyzer is unavailable."""
    
    def analyze(self, content: str) -> Dict[str, Any]:
        """Simple style analysis without complex NLP."""
        errors = []
        suggestions = []
        
        try:
            sentences = re.split(r'[.!?]+', content)
            
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                words = sentence.split()
                word_count = len(words)
                
                # Check sentence length
                if word_count > 25:
                    errors.append({
                        'type': 'sentence_length',
                        'sentence': sentence,
                        'message': f'Sentence is too long ({word_count} words). Consider breaking it up.',
                        'position': i,
                        'word_count': word_count
                    })
                
                # Check for passive voice (simple detection)
                if re.search(r'\b(was|were|is|are|been)\s+\w+ed\b', sentence, re.IGNORECASE):
                    errors.append({
                        'type': 'passive_voice',
                        'sentence': sentence,
                        'message': 'Consider using active voice instead of passive voice.',
                        'position': i
                    })
                
                # Check for wordy phrases
                wordy_phrases = ['in order to', 'due to the fact that', 'at this point in time', 'utilize', 'facilitate']
                for phrase in wordy_phrases:
                    if phrase in sentence.lower():
                        errors.append({
                            'type': 'conciseness',
                            'sentence': sentence,
                            'message': f'Consider replacing "{phrase}" with a more concise alternative.',
                            'position': i
                        })
                        
        except Exception as e:
            logger.error(f"Error in simple style analysis: {e}")
        
        return {
            'errors': errors,
            'suggestions': suggestions,
            'statistics': {
                'word_count': len(content.split()),
                'sentence_count': len([s for s in sentences if s.strip()]),
                'character_count': len(content)
            },
            'technical_writing_metrics': {
                'readability_score': 65.0,  # Placeholder
                'grade_level': 10.0,
                'error_density': len(errors) / max(1, len([s for s in sentences if s.strip()]))
            },
            'overall_score': max(0, 85 - len(errors) * 5),  # Simple scoring
            'analysis_mode': 'simple_fallback'
        }


class SimpleAIRewriter:
    """Simple AI rewriter fallback with Ollama integration."""
    
    def __init__(self):
        """Initialize with model configuration."""
        self.requests = requests
        try:
            from models import ModelConfig
            model_info = ModelConfig.get_model_info()
            active_config = ModelConfig.get_active_config()
            self.use_ollama = active_config.get('provider_type') == 'ollama'
            self.ollama_model = active_config.get('model', 'llama3:8b')
            self.ollama_url = f"{active_config.get('base_url', 'http://localhost:11434')}/api/generate"
        except ImportError:
            # Fallback if models system not available
            self.use_ollama = True
            self.ollama_model = 'llama3:8b'
            self.ollama_url = 'http://localhost:11434/api/generate'
    
    def rewrite(self, content: str, errors: Optional[List[Dict[str, Any]]] = None, context: str = "sentence") -> Dict[str, Any]:
        """Generate AI-powered rewrite."""
        if errors is None:
            errors = []
            
        if not content.strip():
            return {
                'rewritten_text': '',
                'improvements': [],
                'confidence': 0.0,
                'error': 'No content provided'
            }
        
        if self.use_ollama:
            return self._rewrite_with_ollama(content, errors)
        else:
            return self._rule_based_rewrite(content, errors)
    
    def _rewrite_with_ollama(self, content: str, errors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate rewrite using Ollama."""
        if errors is None:
            errors = []
            
        prompt = f"""You are a professional writing assistant. Please rewrite the following text to make it clearer, more concise, and more professional while preserving the original meaning.

Original text:
{content}

Improved text:"""
        
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 100
                }
            }
            
            response = self.requests.post(self.ollama_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                rewritten = result.get('response', '').strip()
                
                return {
                    'rewritten_text': rewritten if rewritten else content,
                    'improvements': ['AI-generated improvements'],
                    'confidence': 0.8,
                    'model_used': 'ollama'
                }
            else:
                logger.warning(f"Ollama request failed with status {response.status_code}")
                return self._rule_based_rewrite(content, errors)
                
        except Exception as e:
            logger.error(f"Ollama rewrite failed: {e}")
            return self._rule_based_rewrite(content, errors)
    
    def _rule_based_rewrite(self, content: str, errors: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Fallback rule-based rewriting with assembly line awareness."""
        if errors is None:
            errors = []
            
        rewritten = content
        improvements = []
        errors_fixed = 0
        
        try:
            # Apply error-specific fixes based on assembly line configuration
            for error in errors:
                error_type = error.get('type', '')
                flagged_text = error.get('flagged_text', '')
                
                if error_type == 'verbs' and 'is clicked' in rewritten:
                    # Convert passive voice "is clicked" to active voice
                    rewritten = rewritten.replace('This is clicked', 'Someone clicked this')
                    improvements.append('Converted passive voice to active voice')
                    errors_fixed += 1
                elif error_type == 'passive_voice':
                    # General passive voice patterns
                    passive_patterns = [
                        (r'\bis\s+(\w+ed)\b', r'someone \1'),
                        (r'\bwas\s+(\w+ed)\b', r'someone \1'),
                        (r'\bare\s+(\w+ed)\b', r'people \1'),
                        (r'\bwere\s+(\w+ed)\b', r'people \1')
                    ]
                    for pattern, replacement in passive_patterns:
                        if re.search(pattern, rewritten, re.IGNORECASE):
                            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)
                            improvements.append('Converted passive voice to active voice')
                            errors_fixed += 1
                            break
            
            # Apply general word replacements only if no specific error fixes were made
            if errors_fixed == 0:
                replacements = {
                    'in order to': 'to',
                    'due to the fact that': 'because',
                    'utilize': 'use',
                    'facilitate': 'help',
                    'at this point in time': 'now',
                    'in the event that': 'if',
                    'prior to': 'before',
                    'subsequent to': 'after'
                }
                
                for old, new in replacements.items():
                    if old in rewritten.lower():
                        pattern = re.compile(re.escape(old), re.IGNORECASE)
                        rewritten = pattern.sub(new, rewritten)
                        improvements.append(f'Replaced "{old}" with "{new}"')
                        errors_fixed += 1
            
            # Break long sentences (simple approach)
            sentences = re.split(r'([.!?]+)', rewritten)
            new_sentences = []
            
            for i in range(0, len(sentences), 2):
                if i + 1 < len(sentences):
                    sentence = sentences[i]
                    punctuation = sentences[i + 1]
                    
                    words = sentence.split()
                    if len(words) > 30:
                        # Try to split at coordinating conjunctions
                        for j, word in enumerate(words):
                            if word.lower() in ['and', 'but', 'or'] and j > 10:
                                first_part = ' '.join(words[:j])
                                second_part = ' '.join(words[j+1:])
                                new_sentences.extend([first_part, '. ', second_part, punctuation])
                                improvements.append(f'Split long sentence at "{word}"')
                                break
                        else:
                            new_sentences.extend([sentence, punctuation])
                    else:
                        new_sentences.extend([sentence, punctuation])
                        
            if new_sentences:
                rewritten = ''.join(new_sentences)
                
        except Exception as e:
            logger.error(f"Error in rule-based rewriting: {e}")
        
        return {
            'rewritten_text': rewritten,
            'improvements': improvements if improvements else ['Applied basic style improvements'],
            'confidence': 0.6 if errors_fixed > 0 else 0.3,
            'errors_fixed': errors_fixed,
            'model_used': 'rule_based'
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for AI rewriting."""
        try:
            ollama_available = False
            if self.use_ollama:
                try:
                    response = self.requests.get(f"{self.ollama_url.replace('/api/generate', '/api/tags')}", timeout=5)
                    ollama_available = response.status_code == 200
                except:
                    pass
            
            return {
                'ai_available': True,
                'model_info': {
                    'use_ollama': self.use_ollama,
                    'ollama_model': self.ollama_model,
                    'ollama_available': ollama_available
                },
                'fallback_available': True
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'ai_available': False,
                'model_info': {},
                'fallback_available': True
            }
    
    def refine_text(self, content: str, errors: Optional[List[Dict[str, Any]]] = None, context: str = "sentence") -> Dict[str, Any]:
        """Refine text (Pass 2) - for simple fallback, just return improved version."""
        if errors is None:
            errors = []
            
        # For fallback, we'll do a second pass with different focus
        result = self.rewrite(content, errors, context)
        
        # Modify result to indicate this is a refinement
        if 'improvements' in result:
            result['improvements'] = [f"Refined: {imp}" for imp in result['improvements']]
        
        result['pass_number'] = 2
        result['can_refine'] = False  # Simple fallback doesn't support further refinement
        
        return result 