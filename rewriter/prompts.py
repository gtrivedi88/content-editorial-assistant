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

    def create_context_aware_assembly_line_prompt(self, target_sentence: str, context_sentences: List[str], 
                                                 errors: List[Dict[str, Any]], pass_number: int = 1) -> str:
        """
        Creates a context-aware prompt for fixing pronoun/ambiguity errors while maintaining assembly line precision.
        
        Args:
            target_sentence: The specific sentence to fix
            context_sentences: List of sentences providing context (includes target_sentence)
            errors: List of errors to fix in the target sentence
            pass_number: The pass number (1 for initial fix, 2 for refinement)
            
        Returns:
            A formatted prompt string for context-aware fixing
        """
        if pass_number == 1:
            return self._construct_context_aware_first_pass_prompt(target_sentence, context_sentences, errors)
        else:
            return self._construct_refinement_pass_prompt(target_sentence)

    def _construct_context_aware_first_pass_prompt(self, target_sentence: str, context_sentences: List[str], 
                                                  errors: List[Dict[str, Any]]) -> str:
        """
        Constructs a context-aware prompt for pronoun/ambiguity error fixing.
        Maintains surgical precision by only allowing changes to the target sentence.
        """
        # Build context text
        context_text = " ".join(context_sentences)
        
        # System-level instruction emphasizing surgical precision with context
        system_prompt = (
            "You are an expert technical editor with extreme precision. "
            "Your task is to fix ONLY the specific errors listed below in the TARGET sentence. "
            "Use the context ONLY to resolve pronouns and ambiguous references. "
            "Make NO changes to any text except the TARGET sentence. "
            "Apply fixes in the order listed, making only the specified changes. "
            "Preserve the original meaning and sentence structure."
        )

        # Format error list for the prompt
        error_list_str = self._format_error_list(errors)

        # The final context-aware prompt structure
        prompt = f"""{system_prompt}

**Context (for reference only - DO NOT modify):**
{context_text}

**TARGET Sentence (fix errors here):**
`{target_sentence}`

**Errors to Fix in TARGET Sentence (in order of priority):**
{error_list_str}

**CRITICAL RULES:**
- Fix ONLY the TARGET sentence shown above
- Use context ONLY to resolve pronouns (what does "this", "it", "that" refer to?)
- Make ONLY the specific changes listed in the errors
- Return ONLY the corrected TARGET sentence
- Do NOT modify any context sentences

**Corrected TARGET Sentence:**
"""
        return prompt.strip()

    def _construct_first_pass_prompt(self, original_text: str, errors: List[Dict[str, Any]]) -> str:
        """Constructs the prompt for the primary error-fixing pass."""
        
        # System-level instruction to set the context for the LLM
        system_prompt = (
            "You are an expert technical editor following a style guide with extreme precision. "
            "Your task is to rewrite the given text to fix the specific errors listed below. "
            "For each error, follow the exact fix instruction provided. "
            "Apply the fixes in the order they are listed, making only the specified changes. "
            "Preserve the original meaning and sentence structure. Make no other edits."
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
        """
        Format the list of errors for inclusion in the prompt.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Formatted string listing all errors with instructions
        """
        if not errors:
            return "No specific errors to fix."
        
        error_lines = []
        for i, error in enumerate(errors, 1):
            error_type = error.get('type', 'unknown')
            flagged_text = error.get('flagged_text', '')
            message = error.get('message', '')
            suggestions = error.get('suggestions', [])
            
            # Build error description
            line = f"{i}. {error_type.upper()}"
            if flagged_text:
                line += f" in '{flagged_text}'"
            if message:
                line += f": {message}"
            if suggestions:
                line += f" → {', '.join(suggestions[:2])}"  # Limit to first 2 suggestions
            
            error_lines.append(line)
        
        return "\n".join(error_lines)

    def create_simple_rewrite_prompt(self, text: str) -> str:
        """Creates a simple, general-purpose rewrite prompt (used for fallbacks)."""
        return f"""Rewrite the following text to improve its clarity, conciseness, and professional tone. Preserve the original meaning.

**Original:**
`{text}`

**Rewritten:**
"""

