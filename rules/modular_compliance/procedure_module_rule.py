"""
Procedure Module Rule
Evidence-based validation for procedure modules following established architectural patterns.

"""
import re
import os
from typing import List, Optional, Dict, Any
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class ProcedureModuleRule(BaseRule):
    """Evidence-based procedure module validator following established patterns"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "modular_compliance"
        self.rule_subtype = "procedure_module"
        self.parser = ModularStructureBridge()
        
        # Load configuration following established patterns
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "procedure_module"
        
    def _load_config(self):
        """Load configuration following established patterns from other rules."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'modular_compliance_types.yaml'
        )
        
        if yaml and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                self.imperative_verbs = set(config.get('imperative_verbs', []))
                self.thresholds = config.get('thresholds', {})
                self.evidence_scoring = config.get('evidence_scoring', {})
                self.module_types = config.get('module_types', {})
                
            except Exception:
                self._set_fallback_config()
        else:
            self._set_fallback_config()
            
        # Procedure-specific configuration
        self.approved_subheadings = {
            'limitations', 'prerequisites', 'verification', 
            'troubleshooting', 'next steps', 'additional resources'
        }
    
    def _set_fallback_config(self):
        """Set fallback configuration if config file not available."""
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload',
            'navigate', 'scroll', 'press', 'choose', 'pick', 'add', 'remove'
        }
        self.evidence_scoring = {
            'base_scores': {
                'exact_violation_match': 0.9,
                'pattern_violation': 0.7,
                'generic_detection': 0.5
            }
        }
    
    def analyze(self, text: str, sentences, nlp=None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze procedure module compliance using direct compliance validation.
        
        Simple approach: Check structural requirements and procedure rules directly.
        No complex evidence scoring - compliance is binary (meets requirement or doesn't).
        """
        errors = []
        
        # Only analyze if this is a procedure module
        if context and context.get('content_type') != 'procedure':
            return errors
            
        # Parse module structure
        structure = self.parser.parse(text)
        
        # Direct compliance checks - no evidence scoring complexity
        compliance_issues = []
        
        # Title Requirements
        compliance_issues.extend(self._find_title_issues(structure))
        
        # Structural Requirements
        compliance_issues.extend(self._find_introduction_issues(structure))
        compliance_issues.extend(self._find_procedure_issues(structure))
        compliance_issues.extend(self._find_subheading_issues(structure))
        
        # Procedure Step Rules
        compliance_issues.extend(self._find_step_issues(structure))
        
        # Optional Section Rules
        compliance_issues.extend(self._find_section_order_issues(structure))
        
        # Create errors directly from compliance issues
        for issue in compliance_issues:
            error = self._create_error(
                sentence=issue.get('sentence', issue.get('flagged_text', '')),
                sentence_index=issue.get('line_number', 0),
                message=issue.get('message', ''),
                suggestions=issue.get('suggestions', []),
                severity=self._map_compliance_level_to_severity(issue.get('level')),
                text=text,
                context=context,
                flagged_text=issue.get('flagged_text', ''),
                span=issue.get('span', (0, 0))
            )
            errors.append(error)
        
        return errors
    
    # Simplified compliance validation - no complex evidence calculation needed
    
    def _map_compliance_level_to_severity(self, level: str) -> str:
        """Map compliance levels to standard severity levels."""
        mapping = {
            'FAIL': 'high',
            'WARN': 'medium',
            'INFO': 'low'
        }
        return mapping.get(level, 'medium')
    
    def _find_title_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if title is a gerund phrase (ending in -ing)."""
        issues = []
        
        title = structure.get('title')
        if title:
            title_words = title.strip().split()
            if title_words:
                last_word = title_words[-1].lower()
                
                # [FAIL] Improper Title Format
                if not last_word.endswith('ing'):
                    issues.append({
                        'type': 'title_format',
                        'level': 'FAIL',
                        'message': f"Title is not a gerund phrase: \"{title}\"",
                        'flagged_text': title,
                        'line_number': 1,
                        'span': (0, len(title)),
                        'suggestions': [
                            "Change title to a gerund form ending in '-ing'",
                            f"Example: '{self._suggest_gerund_title(title)}'",
                            "Remove phrases like 'How to' or 'Steps to'"
                        ]
                    })
        
        return issues
    
    def _find_introduction_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for required introduction."""
        issues = []
        
        # [FAIL] No Introduction
        if not structure.get('introduction_paragraphs'):
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module lacks a brief introductory paragraph after the title",
                'flagged_text': "Missing introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Add an introductory paragraph explaining what this procedure accomplishes",
                    "Include when or why someone would perform this procedure",
                    "Keep the introduction brief and focused"
                ]
            })
        
        return issues
    
    def _find_procedure_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for required procedure section with steps."""
        issues = []
        
        # Look for procedure section or steps
        has_procedure_section = any(
            'procedure' in section['title'].lower() 
            for section in structure.get('sections', [])
        )
        
        has_ordered_steps = len(structure.get('ordered_lists', [])) > 0
        
        # [FAIL] No Procedure Section
        if not has_procedure_section and not has_ordered_steps:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module does not contain a Procedure section with steps to follow",
                'flagged_text': "Missing procedure steps",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add a 'Procedure' section with numbered steps",
                    "Include clear, actionable steps that users can follow",
                    "Each step should be a single, direct action"
                ]
            })
        
        return issues
    
    def _find_subheading_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for improper subheadings."""
        issues = []
        
        for section in structure.get('sections', []):
            section_title_lower = section['title'].lower()
            
            # Skip the main title (level 1)
            if section['level'] == 1:
                continue
            
            # Check if subheading is approved
            if not any(approved in section_title_lower for approved in self.approved_subheadings):
                # [WARN] Improper Subheadings
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': f"Non-standard subheading: \"{section['title']}\"",
                    'flagged_text': section['title'],
                    'line_number': section['line_number'],
                    'span': section['span'],
                    'suggestions': [
                        f"Consider using one of the approved subheadings: {', '.join(self.approved_subheadings)}",
                        "Move content to the main Procedure section if it contains steps",
                        "Ensure subheadings add value and follow standard conventions"
                    ]
                })
        
        return issues
    
    def _find_step_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check step quality and format."""
        issues = []
        
        for list_data in structure.get('ordered_lists', []):
            # Check for single step using numbered list
            if len(list_data['items']) == 1:
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': "Single step uses numbered list format",
                    'flagged_text': "Single numbered step",
                    'line_number': list_data['start_line'],
                    'span': (0, 0),
                    'suggestions': [
                        "Change from numbered list (1.) to bullet point (*) for single steps",
                        "Reserve numbered lists for multi-step procedures"
                    ]
                })
            
            # Check each step
            for item in list_data['items']:
                if not self._starts_with_action(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step does not begin with an action: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Start the step with an action verb (click, type, select, etc.)",
                            "Make the step a clear, direct command",
                            "Remove explanatory text and focus on the action"
                        ]
                    })
                
                if self._has_multiple_actions(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step contains multiple actions: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Break this step into multiple, separate steps",
                            "Each step should have only one action",
                            "Use connecting words like 'then' to indicate separate steps"
                        ]
                    })
        
        return issues
    
    def _find_section_order_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check section ordering."""
        issues = []
        
        next_steps_index = None
        additional_resources_index = None
        
        for i, section in enumerate(structure.get('sections', [])):
            title_lower = section['title'].lower()
            if 'next steps' in title_lower:
                next_steps_index = i
            elif 'additional resources' in title_lower:
                additional_resources_index = i
        
        # [INFO] Incorrect Order
        if (next_steps_index is not None and 
            additional_resources_index is not None and 
            additional_resources_index < next_steps_index):
            
            issues.append({
                'type': 'optional_improvement',
                'level': 'INFO',
                'message': "Additional resources appears before Next steps",
                'flagged_text': "Section order",
                'line_number': structure['sections'][additional_resources_index]['line_number'],
                'span': (0, 0),
                'suggestions': [
                    "Move 'Additional resources' section after 'Next steps'",
                    "Follow the standard section order for procedure modules"
                ]
            })
        
        return issues
    
    def _suggest_gerund_title(self, title: str) -> str:
        """Suggest a gerund form of the title."""
        title_lower = title.lower()
        
        # Remove common prefixes
        if title_lower.startswith('how to '):
            base = title[7:]
        elif title_lower.startswith('steps to '):
            base = title[9:]
        elif title_lower.startswith('to '):
            base = title[3:]
        else:
            base = title
        
        # Simple gerund conversion
        words = base.split()
        if words:
            first_word = words[0].lower()
            if first_word == 'deploy':
                words[0] = 'Deploying'
            elif first_word == 'install':
                words[0] = 'Installing'
            elif first_word == 'configure':
                words[0] = 'Configuring'
            elif first_word == 'create':
                words[0] = 'Creating'
            elif first_word == 'delete':
                words[0] = 'Deleting'
            else:
                words[0] = first_word.capitalize() + 'ing'
        
        return ' '.join(words)
    
    def _starts_with_action(self, text: str) -> bool:
        """Check if text starts with an action verb."""
        words = text.lower().split()
        if not words:
            return False
        
        first_word = words[0].strip('.,!?:;')
        return first_word in self.imperative_verbs
    
    def _starts_with_imperative(self, text: str) -> bool:
        """Check if text starts with an imperative verb."""
        return self._starts_with_action(text)
    
    def _has_multiple_actions(self, text: str) -> bool:
        """Check if step contains multiple actions."""
        # Look for connecting words that suggest multiple actions
        multiple_action_indicators = [
            ' and then ', ' then ', ' and ', ' also ', ' next ',
            ', and ', '; ', ' after ', ' before ', ' while '
        ]
        
        text_lower = text.lower()
        
        # Count action verbs
        action_count = 0
        for verb in self.imperative_verbs:
            if f' {verb} ' in f' {text_lower} ':
                action_count += 1
        
        # If multiple action verbs or connecting words
        return (action_count > 1 or 
                any(indicator in text_lower for indicator in multiple_action_indicators))
    
    def _get_contextual_message(self, issue: Dict[str, Any], evidence_score: float) -> str:
        """Generate contextual error message based on evidence strength."""
        base_message = issue.get('message', '')
        
        if evidence_score > 0.85:
            return f"[CRITICAL] {base_message}"
        elif evidence_score > 0.6:
            return f"[WARNING] {base_message}"
        else:
            return f"[SUGGESTION] {base_message}"
    
    def _generate_smart_suggestions(self, issue: Dict[str, Any], context: Dict[str, Any] = None, evidence_score: float = 0.5) -> List[str]:
        """Generate evidence-aware smart suggestions."""
        suggestions = issue.get('suggestions', [])
        
        if evidence_score > 0.8:
            suggestions = [f"High priority: {s}" for s in suggestions]
        elif evidence_score > 0.6:
            suggestions = [f"Recommended: {s}" for s in suggestions]
        else:
            suggestions = [f"Optional: {s}" for s in suggestions]
        
        return suggestions[:3]
