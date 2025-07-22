"""
AI Output Enforcer
Prevents AI chatter at the source using structured output and intelligent prompting.
No more hard-coded pattern matching - stops the problem before it starts.
"""

import logging
import json
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OutputEnforcer:
    """
    Enforces clean AI output using structured responses and intelligent prompting.
    Prevents chatter at the source instead of filtering it afterward.
    """
    
    def __init__(self):
        """Initialize the output enforcer."""
        self.max_retries = 2
        self.clean_response_examples = [
            {
                "input": "This is an easy process.",
                "bad_output": "Here's the corrected text: This is a straightforward process. (I replaced 'easy' with 'straightforward' to avoid subjective claims.)",
                "good_output": "This is a straightforward process."
            },
            {
                "input": "Setup the server.",
                "bad_output": "Corrected text: Set up the server. I fixed the verb form as per your instruction.",
                "good_output": "Set up the server."
            },
            {
                "input": "The system wants you to input your first name.",
                "bad_output": "Here is the corrected sentence: The system requires you to enter your user name. (I removed anthropomorphism and personal information concerns.)",
                "good_output": "The system requires you to enter your user name."
            },
            {
                "input": "We will begin by having you click on the Start button.",
                "bad_output": "Corrected: You begin by selecting the Start button. I changed 'we will' to 'you' and 'click' to 'select'.",
                "good_output": "You begin by selecting the Start button."
            }
        ]
    
    def create_clean_prompt(self, content: str, instructions: str) -> str:
        """
        Create a prompt that enforces clean output using examples and structure.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt designed to prevent AI chatter
        """
        
        # Use few-shot examples to show exactly what we want
        examples_text = self._build_examples_section()
        
        prompt = f"""You are a text editor. Your job is to make ONLY the requested changes and output ONLY the corrected text.

{examples_text}

CRITICAL RULES:
1. Output ONLY the corrected text
2. NO prefixes like "Here is..." or "Corrected text:"
3. NO explanations, parentheses, or commentary
4. NO questions or offers to help
5. Make ONLY the specific changes requested

TASK:
{instructions}

INPUT TEXT:
{content}

OUTPUT (corrected text only):"""
        
        return prompt
    
    def create_structured_prompt(self, content: str, instructions: str) -> str:
        """
        Create a prompt that uses JSON structure to force clean output.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt that enforces JSON output structure
        """
        
        prompt = f"""You are a text editor. Apply the requested changes and respond in EXACT JSON format.

TASK: {instructions}

INPUT TEXT: {content}

Respond in this EXACT format (no other text):
{{"corrected_text": "your corrected text here"}}

JSON RESPONSE:"""
        
        return prompt
    
    def extract_clean_response(self, ai_response: str, original_text: str, 
                             use_structured: bool = False) -> str:
        """
        Extract clean text from AI response with validation and retry logic.
        
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
            # Try to extract from JSON structure
            extracted = self._extract_from_json(cleaned)
            if extracted:
                return self._validate_and_clean(extracted, original_text)
        
        # For non-structured responses, apply minimal cleaning
        cleaned = self._remove_obvious_prefixes(cleaned)
        
        # NEW: Extract good content even from chatty responses
        if self._is_chatty_response(cleaned):
            logger.warning(f"Detected chatty response, attempting to extract good content: '{cleaned[:100]}...'")
            extracted_content = self._extract_content_from_chatty_response(cleaned, original_text)
            if extracted_content and extracted_content != original_text:
                logger.info(f"✅ Successfully extracted content from chatty response: '{extracted_content[:50]}...'")
                return self._validate_and_clean(extracted_content, original_text)
            else:
                logger.warning("Failed to extract good content from chatty response, using original")
                return original_text
        
        return self._validate_and_clean(cleaned, original_text)
    
    def _build_examples_section(self) -> str:
        """Build few-shot examples section for the prompt."""
        examples_lines = ["EXAMPLES OF CORRECT BEHAVIOR:"]
        
        for i, example in enumerate(self.clean_response_examples, 1):
            examples_lines.extend([
                f"\nExample {i}:",
                f"INPUT: {example['input']}",
                f"BAD OUTPUT: {example['bad_output']}",
                f"GOOD OUTPUT: {example['good_output']}"
            ])
        
        examples_lines.append("\nYour output should be like the GOOD OUTPUT examples - just the corrected text.\n")
        return "\n".join(examples_lines)
    
    def _extract_from_json(self, response: str) -> Optional[str]:
        """Extract text from JSON response format."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{[^}]*"corrected_text"[^}]*\}', response)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return data.get('corrected_text', '').strip()
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
        
        return None
    
    def _remove_obvious_prefixes(self, text: str) -> str:
        """Remove only the most obvious AI prefixes quickly."""
        # Very minimal prefix removal - just the most common ones
        prefixes = [
            r'^corrected text:\s*',
            r'^here (?:is|\'s) the corrected text:\s*',
            r'^output:\s*'
        ]
        
        for prefix in prefixes:
            text = re.sub(prefix, '', text, flags=re.IGNORECASE).strip()
        
        return text
    
    def _is_chatty_response(self, text: str) -> bool:
        """
        Determine if response contains AI chatter using simple heuristics.
        
        Args:
            text: Text to check
            
        Returns:
            True if response appears chatty, False if clean
        """
        text_lower = text.lower()
        
        # Comprehensive checks for AI chatter patterns
        chatty_indicators = [
            # Commentary about changes
            'i fixed', 'i changed', 'i replaced', 'i applied', 'i won\'t make',
            'changes made:', 'change made:', 'corrected text remains',
            'the corrected text', 'correct usage of', 'phrasal verb',
            
            # Meta-commentary  
            'as per your', 'per your instruction', 'since there are',
            'there are no words', 'starting with', 'in the given text',
            
            # AI politeness/offers
            'let me know', 'is there anything', 'can help you',
            'here are the', 'would you like', 'feel free to',
            
            # Explanations in parentheses or bullets
            'correct usage', 'phrasal verb', '* "', '- "',
            'explanation:', 'note:', 'changes include'
        ]
        
        # Check for explicit chatter
        for indicator in chatty_indicators:
            if indicator in text_lower:
                return True
        
        # Check for bullet points or numbered explanations
        if re.search(r'[*•\-]\s*["\']', text_lower):
            return True
            
        # Check for parenthetical explanations about changes
        if re.search(r'\([^)]*(?:replaced|changed|fixed|correct)[^)]*\)', text_lower):
            return True
            
        return False
    
    def _extract_content_from_chatty_response(self, chatty_response: str, original_text: str) -> str:
        """
        Extract the actual corrected content from a chatty AI response.
        
        Args:
            chatty_response: The chatty AI response
            original_text: Original text for reference
            
        Returns:
            Extracted clean content or original text if extraction fails
        """
        try:
            # Strategy 1: Look for patterns like "The corrected text would be: [CONTENT]"
            patterns = [
                r'(?:the\s+)?corrected\s+text\s+(?:would\s+be|is):\s*(.+?)(?:\n|$|\.(?:\s|$))',
                r'here\s+is\s+the\s+corrected\s+(?:text|sentence):\s*(.+?)(?:\n|$)',
                r'(?:corrected|fixed|revised):\s*(.+?)(?:\n|$)',
                r'^(.+?)(?:\n|$|\.(?:\s*I\s+))',  # Take first sentence before explanation
            ]
            
            for pattern in patterns:
                match = re.search(pattern, chatty_response, re.IGNORECASE | re.DOTALL)
                if match:
                    extracted = match.group(1).strip()
                    # Remove trailing periods that might be part of the explanation
                    extracted = re.sub(r'\.\s*$', '', extracted).strip()
                    
                    # Validate it's different from original and reasonable
                    if extracted and extracted.lower() != original_text.lower() and len(extracted) > 3:
                        logger.info(f"Extracted using pattern '{pattern[:30]}...': '{extracted[:50]}...'")
                        return extracted
            
            # Strategy 2: Split by explanation markers and take the first meaningful sentence
            explanation_markers = [
                'I replaced', 'I changed', 'I fixed', 'I removed', 'I added',
                'In this correction', 'The change', 'This fixes', 'Note:'
            ]
            
            for marker in explanation_markers:
                if marker.lower() in chatty_response.lower():
                    parts = re.split(re.escape(marker), chatty_response, flags=re.IGNORECASE)
                    if len(parts) > 1:
                        candidate = parts[0].strip()
                        # Clean up any prefixes
                        candidate = self._remove_obvious_prefixes(candidate)
                        if candidate and candidate.lower() != original_text.lower():
                            logger.info(f"Extracted before explanation marker '{marker}': '{candidate[:50]}...'")
                            return candidate
            
            # Strategy 3: Take the longest sentence that's different from original
            sentences = re.split(r'[.!?]+', chatty_response)
            for sentence in sentences:
                cleaned = sentence.strip()
                cleaned = self._remove_obvious_prefixes(cleaned)
                if (cleaned and 
                    len(cleaned) > 5 and 
                    cleaned.lower() != original_text.lower() and
                    not any(marker.lower() in cleaned.lower() for marker in ['I replaced', 'I changed', 'I fixed'])):
                    logger.info(f"Extracted longest different sentence: '{cleaned[:50]}...'")
                    return cleaned
            
        except Exception as e:
            logger.error(f"Error extracting content from chatty response: {e}")
        
        return original_text

    def _validate_and_clean(self, text: str, original_text: str) -> str:
        """Final validation and minimal cleaning."""
        if len(text.strip()) < 2:
            return original_text
            
        if text.lower().strip() == original_text.lower().strip():
            return original_text
        
        # Ensure it ends properly
        cleaned = text.strip()
        if cleaned and not cleaned.endswith(('.', '!', '?')) and len(cleaned.split()) > 2:
            cleaned += '.'
            
        return cleaned


def create_output_enforcer() -> OutputEnforcer:
    """Factory function to create an output enforcer."""
    return OutputEnforcer() 