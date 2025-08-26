"""
Prompt Generation Module for the AI Rewriter
"""
from typing import List, Dict, Any
import yaml
import os

class PromptGenerator:
    """
    Generates precise, structured JSON prompts for the AI model to ensure
    surgical, multi-level corrections with clean output.
    """
    
    def __init__(self):
        """Initialize with assembly line configuration."""
        self.instruction_templates = self._load_assembly_line_config()
    
    def _load_assembly_line_config(self) -> Dict[str, str]:
        """Load instruction templates from assembly_line_config.yaml."""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'assembly_line_config.yaml')
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('instruction_templates', {})
        except (FileNotFoundError, yaml.YAMLError) as e:
            print(f"Warning: Could not load assembly line config: {e}")
            return {}

    def create_assembly_line_prompt(self, original_text: str, errors: List[Dict[str, Any]], pass_number: int = 1) -> str:
        """
        Creates a single, comprehensive JSON-structured prompt for the assembly line rewriter.
        This prompt instructs the LLM to fix all provided errors in a prioritized order.

        Args:
            original_text: The original text block (sentence, heading, etc.) to be rewritten.
            errors: A list of error dictionaries, pre-sorted by priority.
            pass_number: The pass number (1 for initial fix, 2 for refinement).

        Returns:
            A formatted JSON prompt string for the LLM.
        """
        if pass_number == 1:
            return self._construct_first_pass_prompt(original_text, errors)
        else:
            return self._construct_refinement_pass_prompt(original_text)

    def create_context_aware_assembly_line_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                                 context: str = "", pass_number: int = 1) -> str:
        """
        Creates a context-aware JSON prompt that considers surrounding content.
        
        Args:
            original_text: The text to be rewritten
            errors: List of errors to fix
            context: Surrounding content for context
            pass_number: Pass number for processing
            
        Returns:
            JSON-structured prompt with context awareness
        """
        system_prompt = (
            "You are an expert technical editor following a style guide with extreme precision. "
            "Your task is to rewrite the given text to fix the specific errors listed below. "
            "For each error, follow the EXACT fix instruction provided - including any specific format examples given. "
            "If an instruction shows 'For example, change X to Y', use that exact format for the fix. "
            "Apply the fixes in the order they are listed, making only the specified changes. "
            "Preserve the original meaning and sentence structure. Make no other edits."
        )

        context_section = ""
        if context.strip():
            context_section = f"""
**Document Context:**
{context.strip()}
"""

        error_list_str = self._format_error_list(errors)

        prompt = f"""{system_prompt}

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.
{context_section}
**Original Text:**
`{original_text}`

**Errors to Fix (in order of priority):**
{error_list_str}

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your corrected text here"}}"""
        
        return prompt.strip()

    def _construct_first_pass_prompt(self, original_text: str, errors: List[Dict[str, Any]]) -> str:
        """Constructs the JSON prompt for the primary error-fixing pass."""
        
        system_prompt = (
            "You are an expert technical editor following a style guide with extreme precision. "
            "Your task is to rewrite the given text to fix the specific errors listed below. "
            "For each error, follow the EXACT fix instruction provided - including any specific format examples given. "
            "If an instruction shows 'For example, change X to Y', use that exact format for the fix. "
            "Apply the fixes in the order they are listed, making only the specified changes. "
            "Preserve the original meaning and sentence structure. Make no other edits."
        )

        error_list_str = self._format_error_list(errors)

        prompt = f"""{system_prompt}

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Original Text:**
`{original_text}`

**Errors to Fix (in order of priority):**
{error_list_str}

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your corrected text here"}}"""
        
        return prompt.strip()

    def _construct_refinement_pass_prompt(self, text_to_refine: str) -> str:
        """Constructs the JSON prompt for the second, holistic refinement pass."""
        
        system_prompt = (
            "You are an expert technical editor. Your task is to refine the following text, "
            "which has already had its primary grammatical and structural errors fixed. "
            "Improve its clarity, conciseness, and professional tone while strictly preserving the original meaning. "
            "Focus on flow and word choice. Do not introduce new information."
        )

        prompt = f"""{system_prompt}

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Text to Refine:**
`{text_to_refine}`

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your refined text here"}}"""
        
        return prompt.strip()

    def _format_error_list(self, errors: List[Dict[str, Any]]) -> str:
        """Formats the list of errors into a numbered string for the prompt."""
        if not errors:
            return "No specific errors to fix. Perform a general review for clarity and conciseness."

        formatted_errors = []
        for i, error in enumerate(errors):
            error_message = error.get('message', 'Unknown error')
            flagged_text = error.get('flagged_text', '')
            suggestions = error.get('suggestions', [])
            error_type = error.get('type', '')
            
            error_entry = f"{i + 1}. **Error:** {error_message}\n   **Text:** `{flagged_text}`"
            
            # Use assembly line config instruction templates for known error types
            # This overrides potentially problematic SpaCy suggestions with curated prompts
            config_instruction = self.instruction_templates.get(error_type)
            if config_instruction:
                error_entry += f"\n   **Fix:** {config_instruction}"
            elif suggestions:
                # Fallback to SpaCy suggestions for error types not in config
                if isinstance(suggestions, list) and suggestions:
                    error_entry += f"\n   **Fix:** {suggestions[0]}"
                elif isinstance(suggestions, str):
                    error_entry += f"\n   **Fix:** {suggestions}"
            
            formatted_errors.append(error_entry)
        
        return "\n".join(formatted_errors)

    def create_simple_rewrite_prompt(self, text: str) -> str:
        """Creates a simple, general-purpose JSON rewrite prompt (used for fallbacks)."""
        return f"""Rewrite the following text to improve its clarity, conciseness, and professional tone. Preserve the original meaning.

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Original:**
`{text}`

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your rewritten text here"}}"""

