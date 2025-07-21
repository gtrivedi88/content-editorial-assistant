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

        # AUTO-CATEGORIZE using existing rule severity (zero maintenance!)
        priority_groups = {'urgent': [], 'high': [], 'medium': [], 'low': []}
        for error in errors:
            severity = error.get('severity', 'medium')  # Rules already set this automatically
            priority = self._map_severity_to_priority(severity)  # Simple mapping, no hardcoded keywords
            if priority in priority_groups:
                priority_groups[priority].append(error)
        
        # SMART PRIORITIZATION: Process urgent first, then high, then medium, then low
        prioritized_errors = []
        for priority in ['urgent', 'high', 'medium', 'low']:
            prioritized_errors.extend(priority_groups[priority])
        
        # GROUP by error type to avoid duplication
        error_groups = defaultdict(list)
        for error in prioritized_errors:
            # Handle ambiguity errors by using their subtype
            if error.get('type') == 'ambiguity':
                error_type = error.get('subtype', 'unknown')
            else:
                error_type = error.get('type', 'unknown')
            error_groups[error_type].append(error)

        primary_command = ""
        specific_instructions = []
        current_prompt_length = 0
        MAX_PROMPT_LENGTH = 1500  # Automatic limit to prevent overwhelm

        # SMART PROMPT BUILDING with automatic length management - ENHANCED for systematic structure
        # CRITICAL FIX: Process high-severity errors FIRST to prevent them from being skipped
        high_priority_types = []
        other_types = []

        for error_type, error_list in error_groups.items():
            # Check if any errors in this group are high/urgent severity OR if it's a critical rule type
            has_high_severity = any(error.get('severity') in ['high', 'urgent'] for error in error_list)
            is_critical_rule = self._is_critical_rule_type(error_type)
            
            if has_high_severity or is_critical_rule:
                high_priority_types.append((error_type, error_list))
                if is_critical_rule:
                    logger.info(f"🚨 Critical rule type '{error_type}' prioritized for processing")
            else:
                other_types.append((error_type, error_list))

        # Process high-priority types FIRST (inclusive_language, second_person, etc.)
        processing_order = high_priority_types + other_types

        for error_type, error_list in processing_order:
            rule_config = self.prompt_config.get(error_type)
            if rule_config:
                # Calculate potential instruction length
                instruction_text = ""
                
                if 'primary_command' in rule_config and not primary_command:
                    primary_command = rule_config['primary_command']
                    instruction_text += primary_command + " "
                
                # SYSTEMATIC INSTRUCTION BUILDING - handles both old and new formats
                if 'instruction' in rule_config:
                    instruction_text += rule_config['instruction'] + " "
                
                # NEW: Process transformations with examples (systematic approach)
                if 'transformations' in rule_config:
                    for transformation in rule_config['transformations']:
                        if 'pattern' in transformation:
                            instruction_text += f"Apply: {transformation['pattern']}. "
                        if 'examples' in transformation:
                            # Add specific examples from transformations
                            examples_text = "; ".join(transformation['examples'][:3])  # Limit to 3 examples per pattern
                            instruction_text += f"Examples: {examples_text}. "
                
                # ENHANCED LENGTH CHECK: Reserve space for critical errors
                has_high_severity = any(error.get('severity') in ['high', 'urgent'] for error in error_list)
                is_critical_rule = self._is_critical_rule_type(error_type)
                is_critical_error = has_high_severity or is_critical_rule
                
                # Check length and break if a non-critical error exceeds the limit
                if not is_critical_error and (current_prompt_length + len(instruction_text) > MAX_PROMPT_LENGTH):
                    logger.info(f"⚠️ Prompt length limit reached. Skipping lower priority rule: {error_type}")
                    break
                
                # Add instructions
                if 'primary_command' in rule_config and not primary_command:
                    primary_command = rule_config['primary_command']
                
                # BUILD SYSTEMATIC INSTRUCTIONS
                instruction_parts = []
                
                # Add main instruction
                if 'instruction' in rule_config:
                    instruction_parts.append(rule_config['instruction'])
                
                # Add transformation patterns and examples
                if 'transformations' in rule_config:
                    for i, transformation in enumerate(rule_config['transformations'][:3]):  # Limit to 3 transformations
                        if 'pattern' in transformation:
                            pattern_text = f"Pattern {i+1}: {transformation['pattern']}"
                            if 'examples' in transformation:
                                examples = transformation['examples'][:2]  # Limit to 2 examples per pattern
                                pattern_text += f" (e.g., {'; '.join(examples)})"
                            instruction_parts.append(pattern_text)
                
                # Add fallback guidance
                if 'fallback' in rule_config:
                    instruction_parts.append(f"Fallback: {rule_config['fallback']}")
                
                # Combine all instruction parts
                if instruction_parts:
                    specific_instructions.extend(instruction_parts)
                
                # Legacy support for old format
                if 'instructions' in rule_config:
                    specific_instructions.extend(rule_config['instructions'])
                
                if 'examples' in rule_config:
                    specific_instructions.extend(rule_config['examples'])

                # Special handling for passive voice to add dynamic sentence examples
                if error_type == 'passive_voice':
                    passive_sentences = {e.get('sentence', '') for e in error_list if e.get('sentence')}
                    for sentence in list(passive_sentences)[:2]:  # Limit to 2 examples
                        specific_instructions.append(f"  Example: '{sentence[:50]}...' needs active voice")
                
                # Update current length after adding instructions
                current_prompt_length += len(" ".join(instruction_parts))

        # AUTOMATIC FALLBACK if no instructions found
        if not specific_instructions:
            specific_instructions = [
                "Apply standard corporate writing improvements",
                "Use active voice and clear, concise language"
            ]

        # Build the final prompt using a helper method
        if self.use_ollama:
            prompt = self._build_ollama_prompt_v3(content, primary_command, specific_instructions)
        else:
            prompt = self._build_hf_prompt_v3(content, primary_command, specific_instructions)
        
        # LOG SMART PROCESSING INFO
        total_errors = len(errors)
        processed_types = len(error_groups)
        critical_types = [error_type for error_type, _ in high_priority_types if self._is_critical_rule_type(error_type)]
        
        logger.info(f"🎯 Smart processing: {processed_types} rule types from {total_errors} errors")
        logger.info(f"📊 Priority distribution: U:{len(priority_groups['urgent'])} H:{len(priority_groups['high'])} M:{len(priority_groups['medium'])} L:{len(priority_groups['low'])}")
        logger.info(f"🚨 Critical rule types prioritized: {critical_types}")
        logger.info(f"📏 Final prompt length: {len(prompt)} characters (limit: {MAX_PROMPT_LENGTH})")
        
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

    def generate_multi_pass_prompts(self, content: str, errors: List[Dict[str, Any]], context: str) -> List[Dict[str, Any]]:
        """
        Generate multiple focused prompts for complex texts with many errors.
        This ensures no errors are left behind while keeping each prompt manageable.
        """
        if not errors:
            return [{'prompt': f"Improve this text for clarity and conciseness:\n\n{content}", 'pass_number': 1, 'error_count': 0}]
        
        # AUTO-CATEGORIZE using existing rule severity (zero maintenance!)
        priority_groups = {'urgent': [], 'high': [], 'medium': [], 'low': []}
        for error in errors:
            severity = error.get('severity', 'medium')  # Rules already set this automatically
            priority = self._map_severity_to_priority(severity)  # Simple mapping, no hardcoded keywords
            if priority in priority_groups:
                priority_groups[priority].append(error)
        
        passes = []
        
        # PASS 1: Urgent fixes (breaks professional standards)
        if priority_groups['urgent']:
            prompt = self.generate_prompt(content, priority_groups['urgent'], context)
            passes.append({
                'prompt': prompt,
                'pass_number': 1,
                'pass_type': 'urgent',
                'error_count': len(priority_groups['urgent']),
                'focus': 'Urgent fixes that break professional standards'
            })
        
        # PASS 2: High priority fixes (major readability impact)
        if priority_groups['high']:
            prompt = self.generate_prompt(content, priority_groups['high'], context)
            passes.append({
                'prompt': prompt,
                'pass_number': 2 if passes else 1,
                'pass_type': 'high',
                'error_count': len(priority_groups['high']),
                'focus': 'High priority fixes for major readability impact'
            })
        
        # PASS 3: Medium priority fixes (important improvements)
        if priority_groups['medium']:
            prompt = self.generate_prompt(content, priority_groups['medium'], context)
            passes.append({
                'prompt': prompt,
                'pass_number': len(passes) + 1,
                'pass_type': 'medium',
                'error_count': len(priority_groups['medium']),
                'focus': 'Medium priority fixes for important improvements'
            })
        
        # PASS 4: Low priority fixes (polish and refinement)
        if priority_groups['low']:
            prompt = self.generate_prompt(content, priority_groups['low'], context)
            passes.append({
                'prompt': prompt,
                'pass_number': len(passes) + 1,
                'pass_type': 'low',
                'error_count': len(priority_groups['low']),
                'focus': 'Low priority fixes for final polish and refinement'
            })
        
        # FALLBACK: If no passes were created, create a single general pass
        if not passes:
            prompt = self.generate_prompt(content, errors, context)
            passes.append({
                'prompt': prompt,
                'pass_number': 1,
                'pass_type': 'general',
                'error_count': len(errors),
                'focus': 'General style improvements'
            })
        
        logger.info(f"🎯 Multi-pass strategy: {len(passes)} passes planned")
        for i, pass_info in enumerate(passes):
            logger.info(f"  Pass {i+1}: {pass_info['pass_type']} ({pass_info['error_count']} errors)")
        
        return passes

    def get_optimal_processing_strategy(self, content: str, errors: List[Dict[str, Any]], context: str) -> Dict[str, Any]:
        """
        Automatically determine the optimal processing strategy based on error complexity.
        No manual configuration needed - uses intelligent heuristics.
        """
        if not errors:
            return {
                'strategy': 'single_pass',
                'reason': 'No errors detected',
                'passes': 1,
                'estimated_prompt_length': 200
            }
        
        # ANALYZE ERROR COMPLEXITY
        total_errors = len(errors)
        error_types = len(set(error.get('type', 'unknown') for error in errors))
        
        # Count by existing rule severity (zero maintenance!)
        priority_counts = {'urgent': 0, 'high': 0, 'medium': 0, 'low': 0}
        for error in errors:
            severity = error.get('severity', 'medium')  # Rules already set this automatically
            priority = self._map_severity_to_priority(severity)  # Simple mapping, no hardcoded keywords
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        # ESTIMATE PROMPT LENGTH (based on current system)
        estimated_length = 300  # Base prompt
        estimated_length += error_types * 80  # ~80 chars per rule type
        estimated_length += total_errors * 20  # ~20 chars per error
        
        # AUTOMATIC DECISION LOGIC
        if total_errors <= 15 and error_types <= 5 and estimated_length <= 1500:
            # Simple case: single pass handles it well
            return {
                'strategy': 'single_pass',
                'reason': f'Manageable complexity: {total_errors} errors, {error_types} types',
                'passes': 1,
                'estimated_prompt_length': estimated_length
            }
        
        elif priority_counts['urgent'] > 0 and (priority_counts['high'] > 0 or priority_counts['medium'] > 0 or priority_counts['low'] > 0):
            # Mixed priorities: multi-pass for better focus
            return {
                'strategy': 'multi_pass',
                'reason': f'Mixed priority levels: U:{priority_counts["urgent"]} H:{priority_counts["high"]} M:{priority_counts["medium"]} L:{priority_counts["low"]}',
                'passes': sum(1 for count in priority_counts.values() if count > 0),
                'estimated_prompt_length': estimated_length // 2  # Distributed across passes
            }
        
        elif total_errors > 20 or error_types > 8:
            # High complexity: definitely multi-pass
            return {
                'strategy': 'multi_pass',
                'reason': f'High complexity: {total_errors} errors, {error_types} types',
                'passes': max(2, min(3, error_types // 3)),
                'estimated_prompt_length': estimated_length // 2
            }
        
        else:
            # Moderate complexity: single pass with smart length management
            return {
                'strategy': 'single_pass_smart',
                'reason': f'Moderate complexity: {total_errors} errors, {error_types} types',
                'passes': 1,
                'estimated_prompt_length': min(estimated_length, 1500)
            }
        
    def generate_optimal_prompts(self, content: str, errors: List[Dict[str, Any]], context: str) -> List[Dict[str, Any]]:
        """
        Generate prompts using the optimal strategy automatically determined by analysis.
        This is the main entry point for smart, scalable prompt generation.
        """
        strategy_info = self.get_optimal_processing_strategy(content, errors, context)
        
        logger.info(f"🎯 Auto-selected strategy: {strategy_info['strategy']}")
        logger.info(f"📊 Reason: {strategy_info['reason']}")
        
        if strategy_info['strategy'] == 'multi_pass':
            return self.generate_multi_pass_prompts(content, errors, context)
        else:
            # Single pass (smart or regular)
            prompt = self.generate_prompt(content, errors, context)
            return [{
                'prompt': prompt,
                'pass_number': 1,
                'pass_type': 'comprehensive',
                'error_count': len(errors),
                'focus': 'Comprehensive style improvements',
                'strategy': strategy_info['strategy']
            }]

    def _map_severity_to_priority(self, severity: str) -> str:
        """
        Map the existing rule severity levels to processing priorities.
        Uses the automatic severity that each rule already sets - zero maintenance!
        """
        # Rules already decide their own severity automatically
        # We just map their decision to processing priority
        severity_to_priority = {
            'high': 'urgent',     # High severity = urgent processing  
            'medium': 'high',     # Medium severity = high priority processing
            'low': 'medium'       # Low severity = medium priority processing
        }
        
        return severity_to_priority.get(severity, 'medium')  # Safe default

    def _is_critical_rule_type(self, error_type: str) -> bool:
        """
        Identify rule types that are ALWAYS critical regardless of detected severity.
        These rules address legal/compliance issues and should never be skipped.
        """
        critical_rule_types = {
            'inclusive_language',  # Legal compliance - master/slave, whitelist/blacklist
            'second_person',       # Corporate style requirement - we/our removal
            'legal_claims',        # Legal risk - subjective claims like "secure", "easy"
            'unsupported_claims',  # Fabrication prevention
            'fabrication_risk'     # Information accuracy
        }
        
        return error_type in critical_rule_types