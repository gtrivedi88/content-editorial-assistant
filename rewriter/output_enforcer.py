"""
AI Output Enforcer
Simple, production-ready solution to eliminate AI chatter using JSON structure.
"""

import logging
import json
import re
from typing import Optional

logger = logging.getLogger(__name__)


class OutputEnforcer:
    """
    Enforces clean AI output using JSON structure.
    Simple, reliable, production-ready.
    """
    
    def __init__(self):
        """Initialize the output enforcer."""
        self.max_retries = 2
    
    def create_structured_prompt(self, content: str, instructions: str) -> str:
        """
        Create a JSON-structured prompt that eliminates chatter.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt that enforces JSON output structure
        """
        
        prompt = f"""You are a text editor. Apply the requested changes and respond in EXACT JSON format.

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

TASK: {instructions}

INPUT TEXT: {content}

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your corrected text here"}}"""
        
        return prompt
    
    def create_clean_prompt(self, content: str, instructions: str) -> str:
        """
        Fallback: Create a prompt for models that struggle with JSON.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt designed to prevent AI chatter
        """
        
        prompt = f"""You are a text editor. Your job is to output ONLY the corrected text.

CRITICAL RULES:
- Output ONLY the corrected text
- NO explanations, prefixes, or commentary
- Your response goes directly into a document
- Make ONLY the specific changes requested

TASK: {instructions}

INPUT TEXT: {content}

CORRECTED TEXT:"""
        
        return prompt
    
    def extract_clean_response(self, ai_response: str, original_text: str, 
                             use_structured: bool = True) -> str:
        """
        Extract clean text from AI response.
        
        Args:
            ai_response: Raw AI response
            original_text: Original text for fallback
            use_structured: Whether to expect JSON format
            
        Returns:
            Clean corrected text
        """
        if not ai_response or not ai_response.strip():
            logger.warning("Empty AI response")
            return original_text
        
        cleaned = ai_response.strip()
        
        if use_structured:
            # Try JSON extraction first
            extracted = self._extract_from_json(cleaned)
            if extracted:
                return self._validate_response(extracted, original_text)
        
        # Fallback: simple cleaning
        cleaned = self._simple_clean(cleaned)
        return self._validate_response(cleaned, original_text)
    
    def _extract_from_json(self, response: str) -> Optional[str]:
        """Extract text from JSON response format."""
        try:
            # Handle responses that might have extra text around JSON
            json_match = re.search(r'\{[^}]*"corrected_text"[^}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return data.get('corrected_text', '').strip()
            
            # Try parsing the whole response as JSON
            data = json.loads(response)
            return data.get('corrected_text', '').strip()
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"JSON parsing failed: {e}")
        
        return None
    
    def _simple_clean(self, text: str) -> str:
        """Simple, reliable cleaning for non-JSON responses."""
        # Remove common prefixes
        text = re.sub(r'^(?:corrected text:|here (?:is|\'s) the corrected text:|output:)\s*', 
                     '', text, flags=re.IGNORECASE).strip()
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # If there's obvious explanation text, take just the first sentence
        if any(phrase in text.lower() for phrase in ['i replaced', 'i changed', 'i fixed', 'explanation:']):
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                return sentences[0].strip()
        
        return text.strip()
    
    def _validate_response(self, text: str, original_text: str) -> str:
        """Validate and return the response or fallback to original."""
        if not text or len(text.strip()) < 2:
            return original_text
            
        # FIXED: Don't revert case changes - case differences are valid corrections!
        # Only revert if text is EXACTLY the same (preserving intentional case fixes)
        if text.strip() == original_text.strip():
            return original_text
        
        return text.strip()


def create_output_enforcer() -> OutputEnforcer:
    """Factory function to create an output enforcer."""
    return OutputEnforcer() 