"""
Prompt Generation Module
Handles different prompt generation strategies for various AI models.
"""

import logging
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates context-aware prompts based on detected errors and model type.
    This class acts as a translator, converting structured error data from the
    analyzer into clear, human-readable instructions for the AI model.
    """
    
    def __init__(self, use_ollama: bool = True):
        """Initialize the prompt generator."""
        self.use_ollama = use_ollama
    
    def generate_prompt(self, content: str, errors: List[Dict[str, Any]], context: str) -> str:
        """
        Generate a context-aware prompt for the first rewrite pass.

        This method synthesizes a set of instructions from the detected errors.
        It identifies high-priority issues (like voice) to create a "primary command"
        and then lists other specific fixes, creating a highly targeted prompt.
        
        Args:
            content: Original text content.
            errors: A list of error dictionaries from the analyzer.
            context: The context level ('sentence' or 'paragraph').
            
        Returns:
            A formatted prompt string ready for the AI model.
        """
        # Group errors by their 'type' for easier processing.
        error_groups = defaultdict(list)
        for error in errors:
            error_groups[error.get('type', 'unknown')].append(error)
        
        primary_command = ""
        specific_instructions = []
        
        # --- Forceful and Specific Prompting Logic ---
        # This section creates a hierarchy of instructions to guide the AI.

        # If a 'second_person' error is found, it's treated as a high-priority
        # IBM Style rule. A strong primary command is created, and other
        # specific IBM style rules are added as explicit instructions.
        if 'second_person' in error_groups:
            primary_command = "Your primary goal is to rewrite this text entirely in the second person (using 'you' and 'your'). You MUST NOT use any first-person pronouns like 'we', 'our', or 'I'. Address the user directly."
            
            # Add other specific IBM Style word replacements to enforce consistency.
            specific_instructions.append("Replace 'legacy' with a neutral term like 'existing' or 'previous'.")
            specific_instructions.append("Replace 'leverage' or 'utilize' with a simpler verb like 'use'.")
            specific_instructions.append("Replace 'whitelist' with 'allowlist'.")
            specific_instructions.append("Replace 'IBM Knowledge Center' with 'IBM Documentation'.")
            specific_instructions.append("Do not use em dashes (—).")

        # Handle passive voice errors by providing specific examples from the analyzer.
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
        
        # --- Instructions for all the new punctuation rules ---
        
        if 'punctuation_and_symbols' in error_groups:
            specific_instructions.append("Do not use symbols like '&' or '+' in place of words like 'and'.")

        if 'colons' in error_groups:
            specific_instructions.append("Fix incorrect colon usage. Do not place a colon directly after a verb.")

        if 'commas' in error_groups:
            specific_instructions.append("Ensure all lists of three or more items use a serial (Oxford) comma before the final conjunction.")

        if 'dashes' in error_groups:
            specific_instructions.append("Do not use em dashes (—) in technical writing; rewrite the sentence using other punctuation.")

        if 'ellipses' in error_groups:
            specific_instructions.append("Remove ellipses (...) from the text.")

        if 'exclamation_points' in error_groups:
            specific_instructions.append("Remove all exclamation points and replace them with periods.")

        if 'hyphens' in error_groups:
            specific_instructions.append("Fix hyphenation errors, especially with common prefixes like 'pre', 'multi', and 'non'.")
        
        if 'parentheses' in error_groups:
            specific_instructions.append("Correct punctuation placement around parentheses.")

        if 'periods' in error_groups:
            specific_instructions.append("Remove periods from within uppercase abbreviations (e.g., change 'U.S.' to 'US').")

        if 'quotation_marks' in error_groups:
            specific_instructions.append("Ensure punctuation (like periods and commas) is placed inside closing quotation marks.")

        if 'semicolons' in error_groups:
            specific_instructions.append("Avoid semicolons; rewrite complex sentences into shorter, separate sentences.")

        if 'slashes' in error_groups:
            specific_instructions.append("Do not use a slash (/) to mean 'and/or'; rewrite to clarify the meaning.")
        
        if 'sentence_length' in error_groups:
            specific_instructions.append("Break overly long sentences into shorter, clearer ones (15-20 words each).")
        
        if 'conciseness' in error_groups:
            specific_instructions.append("Remove wordy phrases and unnecessary words.")
        
        if 'clarity' in error_groups:
            specific_instructions.append("Replace complex words with simpler alternatives.")

        # Build the final prompt using a helper method that structures the commands.
        if self.use_ollama:
            prompt = self._build_ollama_prompt_v3(content, primary_command, specific_instructions)
        else:
            prompt = self._build_hf_prompt_v3(content, primary_command, specific_instructions)
        
        return prompt
    
    def generate_self_review_prompt(self, first_rewrite: str, original_errors: List[Dict[str, Any]]) -> str:
        """
        Generate a prompt for the AI's second pass (self-review and refinement).

        This prompt asks the model to act as a senior editor reviewing its own
        work, encouraging it to find further opportunities for improvement beyond
        the initial error-fixing pass.
        
        Args:
            first_rewrite: The text generated during the first pass.
            original_errors: The list of errors from the initial analysis.
            
        Returns:
            A formatted prompt for the second rewrite pass.
        """
        
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
    
    def _build_ollama_prompt_v3(self, content: str, primary_command: str, specific_instructions: List[str]) -> str:
        """
        Builds a more forceful, structured prompt for Ollama/Llama models.
        This structured format with clear headings helps the model better
        understand the hierarchy and importance of the instructions.
        """
        
        instructions_text = "\n".join(f"- {instruction}" for instruction in specific_instructions)

        prompt = f"""You are a professional technical editor following a strict corporate style guide.

PRIMARY GOAL:
{primary_command}

ADDITIONAL INSTRUCTIONS:
{instructions_text}

GENERAL GUIDELINES:
- Use active voice.
- Keep sentences short and clear.
- Maintain the original meaning.

Rewrite the following text according to all the rules above.

Original text:
{content}

Improved text:"""
        
        return prompt
    
    def _build_hf_prompt_v3(self, content: str, primary_command: str, specific_instructions: List[str]) -> str:
        """
        Builds a more forceful, structured prompt for Hugging Face models.
        This format is similar to the Ollama version but adapted for general
        Hugging Face model conventions.
        """
        
        instructions_text = "\n".join(f"- {instruction}" for instruction in specific_instructions)

        prompt_parts = [
            "Task: Rewrite the following text according to a strict corporate style guide.",
            f"\nPRIMARY GOAL: {primary_command}",
            f"\nADDITIONAL INSTRUCTIONS:\n{instructions_text}",
            f"\nOriginal text: {content}",
            "\nImproved text:"
        ]
        
        return "\n".join(prompt_parts)
