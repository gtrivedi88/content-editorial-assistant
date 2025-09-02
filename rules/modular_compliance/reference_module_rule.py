"""
Reference Module Rule
Evidence-based validation for reference modules following established architectural patterns.

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


class ReferenceModuleRule(BaseRule):
    """Evidence-based reference module validator following established patterns"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "modular_compliance"
        self.rule_subtype = "reference_module"
        self.parser = ModularStructureBridge()
        
        # Load configuration following established patterns
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "reference_module"
        
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
    
    def _set_fallback_config(self):
        """Set fallback configuration if config file not available."""
        self.imperative_verbs = {
            'click', 'run', 'type', 'enter', 'execute', 'select', 'start', 'stop',
            'create', 'delete', 'install', 'configure', 'edit', 'open', 'save',
            'verify', 'check', 'test', 'copy', 'paste', 'download', 'upload'
        }
        self.thresholds = {
            'long_content_words': 500,
            'substantial_content_words': 200
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
        Analyze reference module compliance using direct compliance validation.
        
        Simple approach: Check structural requirements and reference rules directly.
        No complex evidence scoring - compliance is binary (meets requirement or doesn't).
        """
        errors = []
        
        # Only analyze if this is a reference module
        if context and context.get('content_type') != 'reference':
            return errors
            
        # Parse module structure
        structure = self.parser.parse(text)
        
        # Direct compliance checks - no evidence scoring complexity
        compliance_issues = []
        
        # Title and Introduction
        compliance_issues.extend(self._find_introduction_issues(structure))
        
        # Content and Structure
        compliance_issues.extend(self._find_structured_data_issues(structure))
        compliance_issues.extend(self._find_organization_issues(structure))
        compliance_issues.extend(self._find_structure_issues(structure))
        
        # Prohibited Content
        compliance_issues.extend(self._find_procedural_content_issues(structure))
        compliance_issues.extend(self._find_explanatory_content_issues(structure, text))
        
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
    
    def _find_introduction_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check introduction requirements."""
        issues = []
        
        # [FAIL] No Introduction
        if not structure.get('introduction_paragraphs'):
            issues.append({
                'type': 'critical_structural',
                'level': 'FAIL',
                'message': "Module lacks a brief, single-paragraph introduction after the title",
                'flagged_text': "Missing introduction",
                'line_number': 2,
                'span': (0, 0),
                'suggestions': [
                    "Add an introductory paragraph explaining what reference data is contained",
                    "Describe when users would consult this reference information",
                    "Keep the introduction brief and focused"
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
                    "Combine introduction paragraphs into a single, concise paragraph",
                    "Move detailed explanations to the reference data sections",
                    "Focus introduction on what reference information is provided"
                ]
            })
        
        return issues
    
    def _find_structured_data_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for presence of structured data."""
        issues = []
        
        # Check for structured data indicators
        has_tables = len(structure.get('tables', [])) > 0
        has_lists = len(structure.get('ordered_lists', [])) + len(structure.get('unordered_lists', [])) > 0
        
        # [FAIL] Lacks Structured Data
        if not (has_tables or has_lists):
            # Check if content is mostly prose
            total_words = structure.get('word_count', 0)
            intro_words = sum(len(para.split()) for para in structure.get('introduction_paragraphs', []))
            
            if total_words - intro_words > self.thresholds.get('substantial_content_words', 200):
                issues.append({
                    'type': 'critical_structural',
                    'level': 'FAIL',
                    'message': "Module's body contains no structured data",
                    'flagged_text': "Missing structured data",
                    'line_number': 0,
                    'span': (0, 0),
                    'suggestions': [
                        "Convert prose content into tables for quick scanning",
                        "Use bulleted lists for sets of related information",
                        "Use definition lists (Term::) for terminology or parameters",
                        "Structure information for easy lookup and reference"
                    ]
                })
        
        return issues
    
    def _find_organization_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if data appears to be logically organized."""
        issues = []
        
        # Check list organization (simple heuristic)
        for list_data in structure.get('unordered_lists', []):
            if len(list_data['items']) > 5:  # Only check larger lists
                item_texts = [item['text'].lower() for item in list_data['items']]
                
                # Check if items might benefit from alphabetization
                if self._could_be_alphabetized(item_texts):
                    issues.append({
                        'type': 'data_organization',
                        'level': 'WARN',
                        'message': "List content does not appear to be logically organized",
                        'flagged_text': "Unorganized list data",
                        'line_number': list_data['start_line'],
                        'span': (0, 0),
                        'suggestions': [
                            "Consider alphabetizing list items for easier lookup",
                            "Group related items together",
                            "Use consistent organization principles throughout the reference"
                        ]
                    })
        
        return issues
    
    def _find_structure_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check structure for long content."""
        issues = []
        
        word_count = structure.get('word_count', 0)
        
        # [INFO] Lacks Structure for Long Content
        if word_count > self.thresholds.get('long_content_words', 500) and len(structure.get('sections', [])) <= 1:
            issues.append({
                'type': 'improvement_suggestion',
                'level': 'INFO',
                'message': f"Long module ({word_count} words) does not use subheadings",
                'flagged_text': "Missing structural organization",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Add subheadings to group related reference information",
                    "Use heading hierarchy (==, ===) to organize content",
                    "Group similar types of reference data under common headings"
                ]
            })
        
        return issues
    
    def _find_procedural_content_issues(self, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for procedural content that doesn't belong."""
        issues = []
        
        # Look for numbered lists with action verbs
        for list_data in structure.get('ordered_lists', []):
            procedural_steps = 0
            for item in list_data['items']:
                if self._starts_with_action(item['text']):
                    procedural_steps += 1
            
            # [FAIL] Contains a Procedure
            if procedural_steps > 0:
                issues.append({
                    'type': 'prohibited_content',
                    'level': 'FAIL',
                    'message': "Module contains numbered list of instructional steps",
                    'flagged_text': "Procedural content detected",
                    'line_number': list_data['start_line'],
                    'span': (0, 0),
                    'suggestions': [
                        "Move procedural steps to a procedure module",
                        "Convert instructions to reference information",
                        "Focus on providing data that users can look up, not follow"
                    ]
                })
        
        return issues
    
    def _find_explanatory_content_issues(self, structure: Dict[str, Any], text: str) -> List[Dict[str, Any]]:
        """Check for explanatory concepts that belong in concept modules."""
        issues = []
        
        # Look for long explanatory paragraphs
        explanatory_indicators = [
            'understand', 'explanation', 'describes', 'overview', 'introduction to',
            'background', 'theory', 'concept', 'principles', 'fundamentals'
        ]
        
        content_lower = text.lower()
        explanatory_score = sum(1 for indicator in explanatory_indicators if indicator in content_lower)
        
        # Check paragraph length and explanatory content
        long_paragraphs = [para for para in structure.get('introduction_paragraphs', []) if len(para.split()) > 100]
        
        # [WARN] Contains Explanatory Concepts
        if explanatory_score >= 3 or len(long_paragraphs) > 0:
            issues.append({
                'type': 'prohibited_content',
                'level': 'WARN',
                'message': "Module contains long, conceptual explanations",
                'flagged_text': "Explanatory content detected",
                'line_number': 0,
                'span': (0, 0),
                'suggestions': [
                    "Move conceptual explanations to a concept module",
                    "Keep reference content concise and factual",
                    "Focus on providing data for quick lookup rather than detailed explanations"
                ]
            })
        
        return issues
    
    def _could_be_alphabetized(self, item_texts: List[str]) -> bool:
        """Simple heuristic to check if list could benefit from alphabetization."""
        # Check if items look like commands or parameters
        # that would benefit from alphabetical order
        
        command_like = sum(1 for text in item_texts if any(
            text.startswith(prefix) for prefix in ['--', '-', 'get', 'set', 'list', 'create', 'delete']
        ))
        
        if command_like > len(item_texts) * 0.5:  # More than half look like commands
            # Check if they're already roughly alphabetized
            sorted_texts = sorted(item_texts)
            
            # Simple check: if current order differs significantly from sorted
            misplaced = sum(1 for i, text in enumerate(item_texts) 
                          if i < len(sorted_texts) and text != sorted_texts[i])
            
            return misplaced > len(item_texts) * 0.3  # More than 30% out of order
        
        return False
    
    def _starts_with_action(self, text: str) -> bool:
        """Check if text starts with an action verb."""
        words = text.lower().split()
        if not words:
            return False
        
        first_word = words[0].strip('.,!?:;')
        return first_word in self.imperative_verbs
    
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
