"""
Handles prompt generation by loading instructions from style guide
configuration files. This separates the prompt logic from the prompt content.
"""

import logging
import yaml
import os
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class PromptGenerator:
    """
    Generates prompts by dynamically loading instructions from a directory
    of configuration files (e.g., /ibm_style/*.yaml).
    """
    
    def __init__(self, style_guide: str = 'ibm_style', use_ollama: bool = True):
        """
        Initialize the prompt generator by loading a specific style guide config.
        
        Args:
            style_guide: The name of the style guide directory.
            use_ollama: Flag to determine which model to use.
        """
        self.use_ollama = use_ollama
        self.style_guide_name = style_guide
        self.prompt_config = self._load_prompt_config()

    def _load_prompt_config(self) -> Dict[str, Any]:
        """
        Loads and merges all YAML configuration files from a style guide's
        directory.
        """
        # Define the path to the specific style guide's directory
        style_guide_dir = os.path.join(os.path.dirname(__file__), 'prompt_configs', self.style_guide_name)
        
        if not os.path.isdir(style_guide_dir):
            logger.error(f"❌ Prompt configuration directory not found: {style_guide_dir}")
            return {}

        merged_config = {}
        try:
            # Iterate over all .yaml files in the directory
            for filename in os.listdir(style_guide_dir):
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    config_path = os.path.join(style_guide_dir, filename)
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)
                        if config and 'rules' in config:
                            # Merge the rules from this file into the main config
                            merged_config.update(config['rules'])
            
            logger.info(f"✅ Successfully loaded and merged prompt configurations for '{self.style_guide_name}'.")
            return merged_config
        except Exception as e:
            logger.error(f"❌ Error loading prompt configurations from {style_guide_dir}: {e}")
            return {}

    def generate_prompt(self, content: str, errors: List[Dict[str, Any]], context: str) -> str:
        """
        Generate a context-aware prompt by looking up instructions in the
        loaded configuration file based on the detected errors.
        """
        if not self.prompt_config:
            logger.warning("No prompt configuration loaded. Using a generic prompt.")
            return f"Improve this text for clarity and conciseness:\n\n{content}"

        error_groups = defaultdict(list)
        for error in errors:
            error_groups[error.get('type', 'unknown')].append(error)

        primary_command = ""
        specific_instructions = []

        # Dynamically build instructions from the merged config file
        for error_type, error_list in error_groups.items():
            rule_config = self.prompt_config.get(error_type)
            if rule_config:
                if 'primary_command' in rule_config and not primary_command:
                    primary_command = rule_config['primary_command']
                
                if 'instruction' in rule_config:
                    specific_instructions.append(rule_config['instruction'])
                
                if 'instructions' in rule_config:
                    specific_instructions.extend(rule_config['instructions'])
                
                if 'examples' in rule_config:
                    specific_instructions.extend(rule_config['examples'])

                # Special handling for passive voice to add dynamic sentence examples
                if error_type == 'passive_voice':
                    passive_sentences = {e.get('sentence', '') for e in error_list if e.get('sentence')}
                    for sentence in list(passive_sentences)[:3]:
                        specific_instructions.append(f"  Example: '{sentence[:50]}...' needs active voice")

        # Build the final prompt using a helper method
        if self.use_ollama:
            prompt = self._build_ollama_prompt_v3(content, primary_command, specific_instructions)
        else:
            prompt = self._build_hf_prompt_v3(content, primary_command, specific_instructions)
        
        return prompt
    
    def generate_self_review_prompt(self, first_rewrite: str, original_errors: List[Dict[str, Any]]) -> str:
        """
        Generate a prompt for the AI's second pass (self-review and refinement).
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