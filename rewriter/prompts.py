"""
Prompt Generation Module
Handles different prompt generation strategies for various AI models.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Generates context-aware prompts based on detected errors and model type."""
    
    def __init__(self, use_ollama: bool = True):
        """Initialize the prompt generator."""
        self.use_ollama = use_ollama
    
    def generate_prompt(self, content: str, errors: List[Dict[str, Any]], context: str) -> str:
        """
        Generate a context-aware prompt based on detected errors.
        
        Args:
            content: Original text content
            errors: List of detected errors
            context: Context level ('sentence' or 'paragraph')
            
        Returns:
            Generated prompt string
        """
        # Group errors by type and synthesize actionable instructions
        error_groups = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Generate specific instructions based on error analysis
        specific_instructions = []
        
        # Handle passive voice errors
        if 'passive_voice' in error_groups:
            passive_errors = error_groups['passive_voice']
            passive_sentences = set()
            for error in passive_errors:
                sentence = error.get('sentence', '')
                if sentence:
                    passive_sentences.add(sentence)
            
            if passive_sentences:
                specific_instructions.append("Convert ALL passive voice to active voice - identify who performs each action and make them the subject")
                for sentence in list(passive_sentences)[:3]:  # Limit examples
                    specific_instructions.append(f"  Example: '{sentence[:50]}...' needs active voice")
        
        # Handle second person errors
        if 'second_person' in error_groups:
            specific_instructions.append("Remove second person pronouns (you, your) - use third person or imperative form")
        
        # Handle article usage errors
        if 'article_usage' in error_groups:
            specific_instructions.append("Fix article usage - use 'a/an' for first mentions, 'the' only when specific item is clear")
        
        # Handle sentence length errors
        if 'sentence_length' in error_groups:
            long_sentences = [error.get('sentence', '') for error in error_groups['sentence_length']]
            if long_sentences:
                specific_instructions.append("Break overly long sentences into shorter, clearer ones (15-20 words each)")
        
        # Handle conciseness errors
        if 'conciseness' in error_groups:
            specific_instructions.append("Remove wordy phrases and unnecessary words")
        
        # Handle clarity errors
        if 'clarity' in error_groups:
            specific_instructions.append("Replace complex words with simpler alternatives")
        
        # Build the prompt with synthesized instructions
        if self.use_ollama:
            prompt = self._build_ollama_prompt_v2(content, specific_instructions)
        else:
            prompt = self._build_hf_prompt_v2(content, specific_instructions)
        
        return prompt
    
    def generate_self_review_prompt(self, first_rewrite: str, original_errors: List[Dict[str, Any]]) -> str:
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
    
    def _build_ollama_prompt_v2(self, content: str, specific_instructions: List[str]) -> str:
        """Build optimized prompt for Ollama/Llama models with synthesized instructions."""
        
        if specific_instructions:
            instructions_text = "\n".join(f"- {instruction}" for instruction in specific_instructions)
            prompt = f"""You are a professional technical writing editor. Rewrite the following text to address these specific style issues:

{instructions_text}

REWRITING GUIDELINES:
- Follow the specific instructions above precisely
- Use active voice throughout
- Use simple, direct language instead of corporate jargon
- Keep sentences short and clear (15-20 words each)
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
    
    def _build_hf_prompt_v2(self, content: str, specific_instructions: List[str]) -> str:
        """Build prompt for Hugging Face models with synthesized instructions."""
        if specific_instructions:
            instructions_text = "\n".join(f"- {instruction}" for instruction in specific_instructions)
            prompt_parts = [
                "Task: Improve the following text by addressing these specific issues:",
                instructions_text,
                f"\nOriginal text: {content}",
                "\nImproved text:"
            ]
        else:
            prompt_parts = [
                "Task: Improve the following text for clarity and conciseness:",
                f"\nOriginal text: {content}",
                "\nImproved text:"
            ]
        
        return "\n".join(prompt_parts) 