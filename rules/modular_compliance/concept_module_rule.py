"""
Concept Module Rule
Evidence-based validation for concept modules following established architectural patterns.

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


class ConceptModuleRule(BaseRule):
    """Evidence-based concept module validator following established patterns"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "modular_compliance"
        self.rule_subtype = "concept_module"
        self.parser = ModularStructureBridge()
        
        # Load configuration following established patterns
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "concept_module"
        
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
                config_thresholds = config.get('thresholds', {})
                # Override config thresholds with our fixed values
                config_thresholds.update({
                    'long_content_words': 300,          # Lowered from 400
                    'very_long_content_words': 350,     # Lowered from 500  
                })
                self.thresholds = config_thresholds
                self.evidence_scoring = config.get('evidence_scoring', {})
                self.module_types = config.get('module_types', {})
                
            except Exception:
                # Fallback to hardcoded values if config loading fails
                self._set_fallback_config()
        else:
            self._set_fallback_config()
    
    def _set_fallback_config(self):
        """Set fallback configuration if config file not available."""
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload',
            'navigate', 'scroll', 'press', 'choose', 'pick', 'add', 'remove'
        }
        self.thresholds = {
            'long_content_words': 300,          # Lowered from 400 - suggest images earlier
            'very_long_content_words': 350,     # Lowered from 500 - suggest structure earlier  
            'substantial_content_words': 100
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
        Analyze concept module compliance using direct compliance validation.
        
        Simple approach: Check structural requirements and content rules directly.
        No complex evidence scoring - compliance is binary (meets requirement or doesn't).
        """
        errors = []
        
        # Only analyze if this is a concept module
        if context and context.get('content_type') != 'concept':
            return errors  # Not a concept module, skip validation
            
        # Parse module structure
        structure = self.parser.parse(text)
        
        # Direct compliance checks - no evidence scoring complexity
        compliance_issues = []
        
        # Structural Requirements
        compliance_issues.extend(self._find_introduction_issues(structure))
        compliance_issues.extend(self._find_content_issues(structure))
        
        # Title Validation (MISSING - now added!)
        compliance_issues.extend(self._find_title_issues(structure))
        
        # Content Prohibitions  
        compliance_issues.extend(self._find_procedural_content(structure, text))
        
        # Content Recommendations
        compliance_issues.extend(self._find_improvement_opportunities(structure))
        
        # Create errors directly from compliance issues
        for issue in compliance_issues:
            error = self._create_error(
                sentence=issue.get('sentence', issue.get('flagged_text', '')),
                sentence_index=issue.get('line_number', 0),
                message=issue.get('message', ''),
                suggestions=issue.get('suggestions', []),
                severity=self._map_compliance_level_to_severity(issue.get('level')),
                text=text,      # Level 2 ✅
                context=context, # Level 2 ✅
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
    
    def _find_introduction_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check introduction requirements."""
        issues = []
        
        # [FAIL] No Introduction
        if not structure.get('introduction_paragraphs'):
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module must begin with at least one introductory paragraph immediately following the title",
                'flagged_text': "Missing introduction",
                'line_number': 2,  # Assume after title
                'span': (0, 0),
                'suggestions': [
                    "Add an introductory paragraph that explains what this concept is",
                    "Include why users should care about this concept",
                    "Keep the introduction concise and focused"
                ]
            })
        
        # [WARN] Multi-paragraph Introduction
        elif len(structure.get('introduction_paragraphs', [])) > 1:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'WARN',
                'message': "The introduction consists of more than one paragraph",
                'flagged_text': "Multi-paragraph introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Combine the introduction paragraphs into a single, concise paragraph",
                    "Move detailed explanations to the body of the concept module",
                    "Focus the introduction on what the concept is and why it matters"
                ]
            })
        
        return issues
    
    def _find_content_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for absence of descriptive content."""
        issues = []
        
        # [FAIL] Absence of Descriptive Content
        body_content_indicators = (
            len(structure.get('sections', [])) > 0 or  # Has sections beyond title
            len(structure.get('introduction_paragraphs', [])) > 1 or  # Multiple paragraphs
            structure.get('word_count', 0) > self.thresholds.get('substantial_content_words', 100)
        )
        
        if not body_content_indicators:
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module contains no body content after the introduction",
                'flagged_text': "Missing substantial content",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add detailed explanations of the concept",
                    "Include examples or use cases",
                    "Provide context about when and why this concept is relevant"
                ]
            })
        
        return issues
    
    def _find_procedural_content(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """Check for action-oriented steps (prohibited in concept modules)."""
        issues = []
        
        # Collect all action-oriented steps first
        action_steps = []
        for list_data in structure.get('ordered_lists', []):
            for item in list_data['items']:
                if self._starts_with_imperative(item['text']):
                    action_steps.append({
                        'text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span']
                    })
        
        # Create consolidated error if action-oriented steps found
        if action_steps:
            step_count = len(action_steps)
            examples = [step['text'][:60] + "..." if len(step['text']) > 60 else step['text'] 
                       for step in action_steps[:3]]  # Show up to 3 examples
            
            if step_count == 1:
                message = f"Contains action-oriented step: \"{examples[0]}\""
            else:
                message = f"Contains {step_count} action-oriented steps"
                if len(examples) < step_count:
                    message += f" (showing first {len(examples)})"
            
            # Use the first step's location for the error
            first_step = action_steps[0]
            
            issues.append({
                'type': 'prohibited_content',
                'level': 'FAIL',
                'message': message,
                'flagged_text': f"{step_count} procedural step(s) found",
                'line_number': first_step['line_number'],
                'span': first_step['span'],
                'suggestions': [
                    "Move procedural steps to a procedure module",
                    "Replace imperative instructions with descriptive explanations", 
                    "Focus on explaining concepts rather than giving commands",
                    f"Examples of problematic steps: {', '.join(examples)}" if step_count > 1 else None
                ]
            })
            
            # Remove None values from suggestions
            issues[0]['suggestions'] = [s for s in issues[0]['suggestions'] if s is not None]
        
        return issues
    
    def _find_title_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for title format issues - THIS WAS MISSING!"""
        issues = []
        
        title = structure.get('title', '')
        if not title:
            return issues
        
        # [WARN] Procedural Title - contains words ending with "-ing" 
        words = title.split()
        gerund_words = [word for word in words if word.lower().endswith('ing')]
        
        if gerund_words:
            issues.append({
                'type': 'title_format', 
                'level': 'WARN',
                'message': f'Title "{title}" appears procedural (contains gerund words: {", ".join(gerund_words)})',
                'flagged_text': title,
                'line_number': 1,
                'span': (0, len(title)),
                'suggestions': [
                    'Use a noun phrase instead of gerund words for concept titles',
                    f'Consider changing to: "Authentication Tokens" instead of "{title}"',
                    'Concept modules should describe "what" something is, not "how" to do it',
                    f'Remove procedural words like: {", ".join(gerund_words)}'
                ]
            })
        
        # [WARN] Question-style Title
        if title.endswith('?'):
            issues.append({
                'type': 'title_format',
                'level': 'WARN', 
                'message': f'Title "{title}" is question-style, not appropriate for concepts',
                'flagged_text': title,
                'line_number': 1,
                'span': (0, len(title)),
                'suggestions': [
                    'Use a declarative noun phrase instead of a question',
                    'Concept titles should state what the concept is',
                    'Questions are better suited for procedure or troubleshooting topics'
                ]
            })
        
        return issues
    
    def _find_improvement_opportunities(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for improvement opportunities."""
        issues = []
        
        word_count = structure.get('word_count', 0)
        
        # [INFO] Lacks Visuals
        if word_count > self.thresholds.get('long_content_words', 400) and len(structure.get('images', [])) == 0:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) lacks diagrams or images",
                'flagged_text': "Missing visual elements",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add diagrams to illustrate complex concepts",
                    "Include screenshots if relevant to the concept",
                    "Use flowcharts or process diagrams for multi-step concepts"
                ]
            })
        
        # [INFO] Lacks Structure for Long Content
        if (word_count > self.thresholds.get('very_long_content_words', 500) and 
            len(structure.get('sections', [])) <= 1):
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) lacks subheadings",
                'flagged_text': "Missing structural organization",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add subheadings to organize the content into logical sections",
                    "Break up long paragraphs into smaller, focused sections",
                    "Use heading hierarchy (==, ===) to structure the information"
                ]
            })
        
        return issues
    
    def _starts_with_imperative(self, text: str) -> bool:
        """Check if text starts with an imperative verb."""
        words = text.lower().split()
        if not words:
            return False
        
        first_word = words[0].strip('.,!?:;')
        return first_word in self.imperative_verbs
    
    # Simple compliance validation - messages and suggestions come directly from compliance issues
