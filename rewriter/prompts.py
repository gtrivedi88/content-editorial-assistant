"""
Handles prompt generation by loading instructions from style guide
configuration files. This separates the prompt logic from the prompt content.
"""

import logging
import yaml
import os
from typing import List, Dict, Any
from collections import defaultdict
from .output_enforcer import create_output_enforcer

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates prompts by dynamically loading instructions from a directory
    of configuration files (e.g., /ibm_style/*.yaml).
    """
    
    def __init__(self, style_guide: str = 'ibm_style', use_ollama: bool = True):
        """
        Initialize the prompt generator.
        Now uses OutputEnforcer for all prompts - no dependency on prompt_configs directory.
        
        Args:
            style_guide: The name of the style guide (kept for compatibility).
            use_ollama: Flag to determine which model to use.
        """
        self.use_ollama = use_ollama
        self.style_guide_name = style_guide
        self.output_enforcer = create_output_enforcer()
        
        # No longer load prompt_config - use OutputEnforcer for all prompts
        logger.info("🎯 PromptGenerator initialized with OutputEnforcer (no prompt_configs dependency)")

    # _load_prompt_config method removed - no longer needed with OutputEnforcer approach

    def generate_prompt(self, content: str, errors: List[Dict[str, Any]], context: str) -> str:
        """
        Generate a context-aware prompt using OutputEnforcer to prevent AI chatter.
        Now independent of prompt configuration files.
        """
        # Build instruction summary from errors
        instructions_summary = self._build_instructions_summary(errors)
        
        # Always use OutputEnforcer for clean prompts
        if self.use_ollama:
            prompt = self.output_enforcer.create_clean_prompt(content, instructions_summary)
        else:
            # For more reliable models, can try structured output
            prompt = self.output_enforcer.create_structured_prompt(content, instructions_summary)
        
        logger.info(f"🎯 Generated {len(prompt)} char prompt using OutputEnforcer")
        return prompt

    def _build_instructions_summary(self, errors: List[Dict[str, Any]]) -> str:
        """
        Build instruction summary from detected errors.
        
        Args:
            errors: List of detected errors
            
        Returns:
            Instruction summary for OutputEnforcer
        """
        if not errors:
            return "Improve this text for clarity and style"
        
        # Group errors by type and priority
        error_types = set()
        high_priority_issues = []
        
        for error in errors:
            error_type = error.get('type', 'unknown')
            error_types.add(error_type)
            
            if error.get('severity') in ['high', 'urgent']:
                high_priority_issues.append(error.get('message', ''))
        
        # Build concise instruction
        if high_priority_issues:
            return f"Fix critical issues: {', '.join(high_priority_issues[:3])}"
        else:
            types_str = ', '.join(list(error_types)[:5])
            return f"Fix {len(errors)} style issues: {types_str}"

    # Old complex prompt building logic removed - now uses simple OutputEnforcer approach
    # All old complex methods removed - now using simplified OutputEnforcer approach