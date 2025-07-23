"""
Prompt Generation Module for the AI Rewriter
"""
from typing import List, Dict, Any

class PromptGenerator:
    """
    Generates precise, structured prompts for the AI model to ensure
    surgical, multi-level corrections in a single pass.
    """

    def create_assembly_line_prompt(self, original_text: str, errors: List[Dict[str, Any]], pass_number: int = 1) -> str:
        """
        Creates a single, comprehensive prompt for the assembly line rewriter.
        This prompt instructs the LLM to fix all provided errors in a prioritized order.

        Args:
            original_text: The original text block (sentence, heading, etc.) to be rewritten.
            errors: A list of error dictionaries, pre-sorted by priority.
            pass_number: The pass number (1 for initial fix, 2 for refinement).

        Returns:
            A formatted prompt string for the LLM.
        """
        if pass_number == 1:
            return self._construct_first_pass_prompt(original_text, errors)
        else:
            return self._construct_refinement_pass_prompt(original_text)

    def _construct_first_pass_prompt(self, original_text: str, errors: List[Dict[str, Any]]) -> str:
        """Constructs the prompt for the primary error-fixing pass."""
        
        # System-level instruction to set the context for the LLM
        system_prompt = (
            "You are an expert technical editor following a style guide with extreme precision. "
            "Your task is to rewrite the given text to fix a specific list of detected errors. "
            "Apply all corrections in the order they are listed. "
            "Preserve the original meaning and make no other stylistic changes."
        )

        # Dynamically build the list of errors for the prompt
        error_list_str = self._format_error_list(errors)

        # The final prompt structure
        prompt = f"""{system_prompt}

**Original Text:**
`{original_text}`

**Errors to Fix (in order of priority):**
{error_list_str}

**Rewritten Text:**
"""
        return prompt.strip()

    def _construct_refinement_pass_prompt(self, text_to_refine: str) -> str:
        """Constructs the prompt for the second, holistic refinement pass."""
        
        system_prompt = (
            "You are an expert technical editor. Your task is to refine the following text, "
            "which has already had its primary grammatical and structural errors fixed. "
            "Improve its clarity, conciseness, and professional tone while strictly preserving the original meaning. "
            "Focus on flow and word choice. Do not introduce new information."
        )

        prompt = f"""{system_prompt}

**Text to Refine:**
`{text_to_refine}`

**Refined Text:**
"""
        return prompt.strip()

    def _format_error_list(self, errors: List[Dict[str, Any]]) -> str:
        """Formats the list of errors into a numbered string for the prompt."""
        if not errors:
            return "No specific errors to fix. Perform a general review for clarity and conciseness."

        formatted_errors = []
        for i, error in enumerate(errors):
            # Providing the error message gives the LLM context on what to fix.
            # Including the flagged text helps it locate the error precisely.
            error_message = error.get('message', 'Unknown error')
            flagged_text = error.get('flagged_text', '')
            
            formatted_errors.append(
                f"{i + 1}. **Error:** {error_message}\n   **Text:** `{flagged_text}`"
            )
        
        return "\n".join(formatted_errors)

    def create_simple_rewrite_prompt(self, text: str) -> str:
        """Creates a simple, general-purpose rewrite prompt (used for fallbacks)."""
        return f"""Rewrite the following text to improve its clarity, conciseness, and professional tone. Preserve the original meaning.

**Original:**
`{text}`

**Rewritten:**
"""

