"""
Prompt Generation Module for the AI Rewriter
Enhanced with multi-shot prompting for world-class performance.
"""
from typing import List, Dict, Any, Optional
import yaml
import os
from .example_selector import ExampleSelector

class PromptGenerator:
    """
    Generates precise, structured JSON prompts for the AI model to ensure
    surgical, multi-level corrections with clean output.
    """
    
    def __init__(self):
        """Initialize with assembly line configuration and example selector."""
        self.instruction_templates = self._load_assembly_line_config()
        self.example_selector = ExampleSelector()
        
        # Log initialization status
        example_stats = self.example_selector.get_example_stats()
        if 'error' not in example_stats:
            print(f"🎯 Multi-shot prompting enabled: {example_stats['total_examples']} examples across {example_stats['total_error_types']} error types")
    
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

    def create_assembly_line_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                  pass_number: int = 1, block_type: str = "text") -> str:
        """
        Creates a single, comprehensive JSON-structured prompt for the assembly line rewriter.
        This prompt instructs the LLM to fix all provided errors in a prioritized order.

        Args:
            original_text: The original text block (sentence, heading, etc.) to be rewritten.
            errors: A list of error dictionaries, pre-sorted by priority.
            pass_number: The pass number (1 for initial fix, 2 for refinement).
            block_type: Type of content block for contextual example selection.

        Returns:
            A formatted JSON prompt string for the LLM with multi-shot examples.
        """
        if pass_number == 1:
            return self._construct_first_pass_prompt(original_text, errors, block_type)
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
    
    def create_chain_of_thought_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                     block_type: str = "text") -> str:
        """
        Create a chain-of-thought prompt for complex reasoning cases.
        This improves AI performance on ambiguous or multi-step corrections.
        
        Args:
            original_text: Text to be corrected
            errors: List of errors requiring reasoning
            block_type: Type of content block (heading, paragraph, etc.)
            
        Returns:
            Chain-of-thought structured prompt
        """
        system_prompt = (
            "You are an expert technical editor. Use step-by-step reasoning to fix the text. "
            "Follow this reasoning process for each error, then provide the final corrected text."
        )
        
        reasoning_steps = []
        for i, error in enumerate(errors):
            error_type = error.get('type', 'unknown')
            error_message = error.get('message', 'Unknown error')
            flagged_text = error.get('flagged_text', '')
            
            step = f"""
**Step {i + 1} - Analyze {error_type.replace('_', ' ').title()} Issue:**
1. **Identify**: What is wrong with "{flagged_text}"?
   - Issue: {error_message}
2. **Understand Rule**: Why does this need to be fixed?
   - Rule: {self.instruction_templates.get(error_type, f'Fix {error_type} according to style guide')}
3. **Apply Fix**: How should it be corrected?
   - Examples: {self._get_rule_examples(error_type)}
4. **Verify**: Does the fix follow the pattern?"""
            
            reasoning_steps.append(step)
        
        reasoning_section = "\n".join(reasoning_steps)
        
        prompt = f"""{system_prompt}

**Original Text ({block_type}):**
`{original_text}`

**Reasoning Process:**
{reasoning_section}

**Final Step - Apply All Fixes:**
Based on your reasoning above, provide the corrected text that addresses all identified issues.

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your final corrected text here"}}"""
        
        return prompt.strip()

    def _construct_first_pass_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                   block_type: str = "text") -> str:
        """Constructs the JSON prompt for the primary error-fixing pass with multi-shot examples."""
        
        system_prompt = (
            "You are an expert technical editor following a style guide with extreme precision. "
            "Your task is to rewrite the given text to fix the specific errors listed below. "
            "For each error, follow the EXACT fix instruction provided and learn from the multi-shot examples. "
            "Apply the same patterns demonstrated in the examples to fix the current text. "
            "Apply the fixes in the order they are listed, making only the specified changes. "
            "Preserve the original meaning and sentence structure. Make no other edits."
        )

        error_list_str = self._format_error_list(errors, block_type)

        prompt = f"""{system_prompt}

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Content Type:** {block_type}
**Original Text:**
`{original_text}`

**Multi-Shot Error Analysis & Instructions:**
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

    def _format_error_list(self, errors: List[Dict[str, Any]], block_type: str = "text") -> str:
        """Formats the list of errors into a numbered string with multi-shot instructions."""
        if not errors:
            return "No specific errors to fix. Perform a general review for clarity and conciseness."

        formatted_errors = []
        for i, error in enumerate(errors):
            error_message = error.get('message', 'Unknown error')
            flagged_text = error.get('flagged_text', '')
            suggestions = error.get('suggestions', [])
            error_type = error.get('type', '')
            
            # Create enhanced instruction with multi-shot examples and context
            enhanced_instruction = self._create_enhanced_instruction(
                error_type, error_message, suggestions, flagged_text, block_type
            )
            
            error_entry = f"{i + 1}. **Error Type:** {error_type}\n   **Issue:** {error_message}\n   **Flagged Text:** `{flagged_text}`\n   **Instructions:** {enhanced_instruction}"
            
            formatted_errors.append(error_entry)
        
        return "\n".join(formatted_errors)
    
    def _create_enhanced_instruction(self, error_type: str, spacy_message: str, 
                                   spacy_suggestions: List[str], flagged_text: str,
                                   context: str = "text") -> str:
        """
        Create enhanced instruction with multi-shot examples and context.
        This is the KEY improvement that makes AI output world-class.
        
        Args:
            error_type: The type of error detected
            spacy_message: Specific message from SpaCy rule
            spacy_suggestions: Suggestions from SpaCy analysis
            flagged_text: The problematic text flagged by SpaCy
            context: Context type for example selection
            
        Returns:
            Rich, context-aware instruction with multi-shot examples
        """
        # Get base template guidance
        base_template = self.instruction_templates.get(error_type, "")
        
        # Get dynamic multi-shot examples
        examples = self.example_selector.select_examples(
            error_type, flagged_text, context, num_examples=3
        )
        examples_text = self.example_selector.format_examples_for_prompt(examples, error_type)
        
        # Create hybrid instruction with multi-shot learning
        if base_template:
            # Combine template + SpaCy context + multi-shot examples
            instruction_parts = []
            
            # Add rule guidance
            instruction_parts.append(f"**Rule**: {base_template}")
            
            # Add specific SpaCy context
            instruction_parts.append(f"**Specific Issue**: {spacy_message}")
            
            # Add SpaCy suggestions if available
            if spacy_suggestions:
                suggestion_text = spacy_suggestions[0] if isinstance(spacy_suggestions, list) else str(spacy_suggestions)
                instruction_parts.append(f"**SpaCy Guidance**: {suggestion_text}")
            
            # Add multi-shot examples for pattern learning
            if examples:
                instruction_parts.append(f"**Multi-Shot Examples**: {examples_text}")
            
            # Add flagged text context
            instruction_parts.append(f"**Apply to**: \"{flagged_text}\"")
            
            return " | ".join(instruction_parts)
        else:
            # Fallback with multi-shot examples
            fallback_parts = [f"Fix {error_type} issue: {spacy_message}"]
            
            if spacy_suggestions:
                suggestion_text = spacy_suggestions[0] if isinstance(spacy_suggestions, list) else str(spacy_suggestions) 
                fallback_parts.append(f"Guidance: {suggestion_text}")
            
            # Add multi-shot examples even for unknown error types
            if examples:
                fallback_parts.append(f"Examples: {examples_text}")
                
            fallback_parts.append(f"Apply to: \"{flagged_text}\"")
            
            return " | ".join(fallback_parts)
    
    def _get_rule_examples(self, error_type: str) -> str:
        """
        Get context-aware examples for specific error types.
        This provides few-shot learning for the AI.
        """
        examples_map = {
            'headings': "'Important Notes' → 'Important notes', 'API Configuration' → 'API configuration'",
            'word_usage_y': "'You must' → 'Users must', 'You can' → direct instruction",
            'technical_files_directories': "'/var/log/file.log' → '`/var/log/file.log`'",
            'contractions': "'you'll' → 'you will', 'can't' → 'cannot'",
            'legal_claims': "'easy' → 'straightforward', 'great' → 'useful'",
            'passive_voice': "'is clicked' → 'you click', 'was processed' → 'the system processes'",
            'ambiguity': "'this is clicked' → 'you click this button'",
            'capitalization': "'iPhone app' → 'iPhone App' (preserve brand)"
        }
        
        return examples_map.get(error_type, f"Follow standard {error_type} guidelines")

    def create_world_class_multi_shot_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                           block_type: str = "text") -> str:
        """
        Create world-class multi-shot prompt with extensive examples and reasoning.
        For the most challenging cases requiring maximum AI understanding.
        
        Args:
            original_text: Text to be corrected
            errors: List of errors with full context
            block_type: Content type for optimal example selection
            
        Returns:
            Comprehensive multi-shot prompt with adaptive examples
        """
        # Get comprehensive examples for each error type
        all_examples = []
        for error in errors:
            error_type = error.get('type', '')
            flagged_text = error.get('flagged_text', '')
            
            # Get 4-5 examples for intensive learning
            examples = self.example_selector.select_examples(
                error_type, flagged_text, block_type, num_examples=5
            )
            
            if examples:
                all_examples.extend(examples)
        
        # Create comprehensive example section
        examples_section = self._create_comprehensive_examples_section(all_examples, errors)
        
        # Enhanced system prompt for maximum understanding with negative example intelligence
        system_prompt = (
            "You are a world-class technical editor with deep expertise in style guide enforcement. "
            "Study the comprehensive examples below to understand BOTH when to make corrections AND when to leave text unchanged. "
            "Some examples show transformations (before ≠ after), others show when NO CHANGE is correct (before = after). "
            "Pay special attention to negative examples where the 'before' and 'after' are identical - these teach you "
            "when rules should NOT be applied due to contextual appropriateness. "
            "Use sophisticated judgment: apply corrections when needed, but preserve appropriate usage patterns. "
            "Context matters more than blind rule application. Show discernment, not just compliance."
        )
        
        error_analysis = self._create_detailed_error_analysis(errors, block_type)
        
        prompt = f"""{system_prompt}

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Content Analysis:**
- Type: {block_type}
- Complexity: {self.example_selector._assess_text_complexity(original_text)}
- Errors to address: {len(errors)}

**Comprehensive Learning Examples:**
{examples_section}

**Current Text Analysis:**
`{original_text}`

**Detailed Error Breakdown:**
{error_analysis}

**Your Task:**
Apply the patterns you learned from the examples above to transform the current text. Address all identified errors while maintaining the original meaning and appropriate tone for {block_type} content.

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your expertly corrected text here"}}"""
        
        return prompt.strip()
    
    def _create_comprehensive_examples_section(self, examples: List[Dict], errors: List[Dict]) -> str:
        """Create a comprehensive examples section for world-class prompting."""
        if not examples:
            return "No specific examples available for these error types."
        
        # Group examples by error type for organized learning
        examples_by_type = {}
        for example in examples:
            # Try to determine error type from context (simplified for now)
            example_key = f"pattern_{len(examples_by_type) + 1}"
            examples_by_type[example_key] = example
        
        formatted_sections = []
        
        for i, (pattern_key, example) in enumerate(examples_by_type.items(), 1):
            section = f"""**Learning Pattern {i}:**
- Situation: {example.get('context', 'text')} content
- Before: "{example.get('before', '')}"
- After: "{example.get('after', '')}"
- Reasoning: {example.get('reasoning', '')}
- Success Rate: {example.get('success_rate', 0.8):.1%}"""
            
            formatted_sections.append(section)
        
        return "\n\n".join(formatted_sections)
    
    def _create_detailed_error_analysis(self, errors: List[Dict], block_type: str) -> str:
        """Create detailed error analysis for world-class prompting."""
        if not errors:
            return "No specific errors identified."
        
        analysis_parts = []
        
        for i, error in enumerate(errors, 1):
            error_type = error.get('type', 'unknown')
            message = error.get('message', 'No message')
            flagged_text = error.get('flagged_text', '')
            suggestions = error.get('suggestions', [])
            
            # Get rule explanation
            rule_explanation = self.instruction_templates.get(error_type, f"Fix {error_type} issues")
            
            analysis = f"""Error {i}: {error_type.replace('_', ' ').title()}
- Flagged Text: "{flagged_text}"
- Issue: {message}
- Rule: {rule_explanation}
- Suggestions: {', '.join(suggestions) if suggestions else 'Apply standard pattern'}"""
            
            analysis_parts.append(analysis)
        
        return "\n\n".join(analysis_parts)

    def create_station_focused_prompt(self, original_text: str, errors: List[Dict[str, Any]], 
                                     station: str, station_name: str, block_type: str = "text") -> str:
        """
        Create a station-focused prompt for multi-pass assembly line processing.
        Each station gets a specialized prompt focused on its priority level.
        
        Args:
            original_text: Text to be corrected
            errors: Errors for this specific station
            station: Station identifier (urgent, high, medium, low)
            station_name: Human-readable station name
            block_type: Content type for context
            
        Returns:
            Focused prompt for the specific assembly line station
        """
        
        # Station-specific system prompts for focused processing
        station_prompts = {
            'urgent': (
                "You are a legal compliance and critical content specialist. "
                "Your ONLY focus is fixing critical issues that could cause legal problems or major content failures. "
                "Fix ONLY legal claims, compliance issues, and critical content problems. "
                "Ignore all other issues - they will be handled in subsequent passes."
            ),
            'high': (
                "You are a structural document editor specializing in organization and clarity. "
                "Your ONLY focus is fixing structural issues like passive voice, ambiguous actors, and document organization. "
                "Fix ONLY structural and organizational problems. "
                "Ignore grammar, word choice, and style issues - they will be handled in subsequent passes."
            ),
            'medium': (
                "You are a grammar and language specialist. "
                "Your ONLY focus is fixing grammar, word usage, contractions, and language correctness. "
                "Fix ONLY language and grammar issues. "
                "Ignore punctuation and style refinements - they will be handled in the final pass."
            ),
            'low': (
                "You are a style and polish specialist. "
                "Your ONLY focus is final style refinements, punctuation, citations, and formatting polish. "
                "This is the final pass - focus ONLY on style and formatting improvements."
            )
        }
        
        system_prompt = station_prompts.get(station, 
            f"You are processing the {station_name} stage. Focus only on {station}-priority issues.")
        
        # Get enhanced instructions for this station's errors
        error_list_str = self._format_error_list(errors, block_type)
        
        # Station-specific focus areas
        focus_areas = {
            'urgent': "legal compliance, critical content accuracy, and mandatory corrections",
            'high': "document structure, voice clarity, and organizational improvements", 
            'medium': "grammar correctness, word usage, and language precision",
            'low': "style consistency, punctuation accuracy, and formatting polish"
        }
        
        focus_area = focus_areas.get(station, f"{station} priority issues")
        
        prompt = f"""{system_prompt}

**ASSEMBLY LINE PASS: {station_name}**
**FOCUS AREA**: {focus_area}

CRITICAL INSTRUCTIONS:
- This is a multi-pass system. You are processing PASS {['urgent', 'high', 'medium', 'low'].index(station) + 1} of 4.
- Focus ONLY on {station}-priority issues listed below.
- Do NOT attempt to fix issues outside your station's scope.
- Other passes will handle remaining issues.
- Your response will be input to the next assembly line station.

**Content Type:** {block_type}
**Current Text:**
`{original_text}`

**{station_name} Issues to Fix:**
{error_list_str}

**Multi-Shot Examples for This Station:**
{self._get_station_examples(station, errors)}

Apply ONLY the {station}-priority fixes above. Make no other changes.

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your {station}-pass corrected text here"}}"""
        
        return prompt.strip()

    def _get_station_examples(self, station: str, errors: List[Dict[str, Any]]) -> str:
        """Get focused examples for a specific assembly line station."""
        if not errors:
            return f"Focus on {station}-priority patterns as demonstrated in your training."
        
        # Get examples for the first few error types at this station
        example_texts = []
        error_types_seen = set()
        
        for error in errors[:3]:  # Limit to avoid overwhelming prompt
            error_type = error.get('type', '')
            if error_type and error_type not in error_types_seen:
                error_types_seen.add(error_type)
                
                # Get examples for this error type
                examples = self.example_selector.select_examples(
                    error_type, error.get('flagged_text', ''), 'text', num_examples=1
                )
                
                if examples:
                    example = examples[0]
                    example_text = f"**{error_type}**: \"{example.get('before', '')}\" → \"{example.get('after', '')}\""
                    example_texts.append(example_text)
        
        if example_texts:
            return "Learn from these patterns:\n" + "\n".join(example_texts)
        else:
            return f"Apply {station}-priority fixes following standard patterns."

    def create_simple_rewrite_prompt(self, text: str) -> str:
        """Creates a simple, general-purpose JSON rewrite prompt (used for fallbacks)."""
        return f"""Rewrite the following text to improve its clarity, conciseness, and professional tone. Preserve the original meaning.

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

**Original:**
`{text}`

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your rewritten text here"}}"""

