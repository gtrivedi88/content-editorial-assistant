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
    
    def analyze(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze procedure module compliance using direct compliance validation.
        
        Simple approach: Check structural requirements and procedure rules directly.
        No complex evidence scoring - compliance is binary (meets requirement or doesn't).
        """
        errors = []
        
        # Analyze if this is explicitly a procedure module OR if it contains procedural elements
        # This makes the rule more defensive and user-friendly
        if context and context.get('content_type'):
            content_type = context.get('content_type')
            if content_type not in ['procedure', 'auto', 'unknown']:
                # Skip analysis only if explicitly set to a different type
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
        """Check for improper subheadings and singular/plural issues."""
        issues = []
        
        for section in structure.get('sections', []):
            section_title_lower = section['title'].lower()
            
            # Skip the main title (level 0, document title)
            # Level 1 are the main sections (==) that we want to check
            if section['level'] == 0:
                continue
            
            # Check for singular vs plural heading issues
            if self._is_singular_plural_issue(section['title']):
                issues.append({
                    'type': 'optional_improvement',
                    'level': 'WARN',
                    'message': f"Heading should be plural: \"{section['title']}\"",
                    'flagged_text': section['title'],
                    'line_number': section['line_number'],
                    'span': section['span'],
                    'suggestions': [
                        f"Change '{section['title']}' to '{self._get_plural_form(section['title'])}'",
                        "Use plural forms for section headings that typically contain multiple items"
                    ]
                })
            
            # Check if subheading is approved
            elif not any(approved in section_title_lower for approved in self.approved_subheadings):
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
                            "Remove connecting words like 'and immediately' that combine actions"
                        ]
                    })
                
                # Check for conceptual explanations within steps
                if self._has_conceptual_explanation(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step contains conceptual explanation instead of direct action: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Remove explanatory content and focus on the specific action",
                            "Move detailed explanations to a Concept module",
                            "Keep steps concise and action-focused"
                        ]
                    })
                
                # Check for vague, non-action steps
                if self._is_vague_step(item['text']):
                    issues.append({
                        'type': 'step_validation',
                        'level': 'FAIL',
                        'message': f"Step is too vague and not actionable: \"{item['text'][:50]}...\"",
                        'flagged_text': item['text'],
                        'line_number': item['line_number'],
                        'span': item['span'],
                        'suggestions': [
                            "Make the step more specific and actionable",
                            "Replace vague instructions with concrete commands",
                            "Specify exactly what the user should do"
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
        # Enhanced detection for connecting words that suggest multiple actions
        multiple_action_indicators = [
            ' and then ', ' then ', ' and immediately ', ' and ', ' also ', ' next ',
            ', and ', '; ', ' after ', ' before ', ' while ', ' followed by ',
            ' subsequently ', ' afterwards ', ' immediately '
        ]
        
        text_lower = text.lower()
        
        # Count action verbs (enhanced detection)
        action_count = 0
        found_verbs = []
        for verb in self.imperative_verbs:
            # More precise verb detection with word boundaries
            import re
            pattern = r'\b' + re.escape(verb) + r'\b'
            matches = re.findall(pattern, text_lower)
            if matches:
                action_count += len(matches)
                found_verbs.extend(matches)
        
        # Enhanced compound sentence detection - specifically catch patterns like
        # "Log in to the server and navigate to the directory"
        compound_patterns = [
            r'\b(\w+)\s+[^.;]+\s+and\s+(?:immediately\s+)?(\w+)',  # "verb ... and verb"
            r'\b(\w+)\s+[^.;]+,\s*and\s+(\w+)',  # "verb ..., and verb"
        ]
        
        for pattern in compound_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                # Check if both parts contain action verbs
                if any(verb in match[0] for verb in self.imperative_verbs) and \
                   any(verb in match[1] for verb in self.imperative_verbs):
                    return True
        
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
    
    def _has_conceptual_explanation(self, text: str) -> bool:
        """Check if step contains conceptual explanations instead of direct actions."""
        # Indicators of conceptual content in steps
        conceptual_indicators = [
            'this is important because', 'this is crucial because', 'this is necessary because',
            'the reason for', 'this helps', 'this ensures', 'this provides', 'this allows',
            'memory leaks are', 'the script uses', 'providing a comprehensive', 'helping to',
            'over time', 'preemptively identify', 'commonly used for', 'typically used',
            'it is important to', 'note that', 'keep in mind', 'remember that',
            'this will', 'this can', 'this may', 'this might', 'because of', 'due to'
        ]
        
        text_lower = text.lower()
        
        # Check for long explanatory sentences (likely conceptual)
        if len(text.split()) > 30:  # Very long steps are likely explanatory
            # Look for explanatory patterns
            if any(indicator in text_lower for indicator in conceptual_indicators):
                return True
        
        # Check for technical explanations
        technical_explanation_patterns = [
            r'\b(uses?|utilizes?)\s+the\s+\w+\s+(command|tool|script)',
            r'\b(analyzes?|provides?|helps?|ensures?)\s+\w+',
            r'\b(comprehensive|detailed|thorough)\s+(overview|analysis)',
            r'\bpreemptively\s+identify\b',
            r'\bcommonly?\s+(source|cause)\s+of\b'
        ]
        
        import re
        for pattern in technical_explanation_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_vague_step(self, text: str) -> bool:
        """Check if step is too vague or non-actionable."""
        text_lower = text.lower().strip()
        
        # Vague action words that don't specify concrete actions
        vague_verbs = {
            'observe', 'watch', 'monitor', 'review', 'examine', 'consider',
            'think about', 'look at', 'see', 'notice', 'understand', 'realize',
            'be aware', 'make sure', 'ensure', 'confirm'
        }
        
        # Check if step starts with vague verbs
        words = text_lower.split()
        if words:
            first_word = words[0].strip('.,!?:;')
            if first_word in vague_verbs:
                return True
            
            # Check for multi-word vague phrases at the start
            if len(words) >= 2:
                two_word_start = f"{words[0]} {words[1]}"
                if two_word_start in vague_verbs:
                    return True
        
        # Check for vague patterns
        vague_patterns = [
            r'^observe\s+the\s+\w+',
            r'^watch\s+(for|the)',
            r'^monitor\s+\w+',
            r'^review\s+\w+',
            r'^examine\s+\w+',
            r'^check\s+(that|if)\s+\w+',  # "Check if" is vague vs "Check the log file"
            r'^make\s+sure\s+(that|\w+)',
            r'^ensure\s+(that|\w+)'
        ]
        
        import re
        for pattern in vague_patterns:
            if re.match(pattern, text_lower):
                return True
        
        return False
    
    def _is_singular_plural_issue(self, heading: str) -> bool:
        """Check if heading should be plural but is singular."""
        heading_lower = heading.lower().strip()
        
        # Known headings that should be plural
        should_be_plural = {
            'prerequisite': 'prerequisites',
            'limitation': 'limitations',
            'requirement': 'requirements',
            'resource': 'resources',
            'step': 'steps'
        }
        
        for singular, plural in should_be_plural.items():
            if singular in heading_lower and plural not in heading_lower:
                return True
        
        return False
    
    def _get_plural_form(self, heading: str) -> str:
        """Get the plural form of a heading."""
        heading_lower = heading.lower()
        
        # Known singular to plural conversions
        conversions = {
            'prerequisite': 'Prerequisites',
            'limitation': 'Limitations',
            'requirement': 'Requirements',
            'resource': 'Resources',
            'step': 'Steps'
        }
        
        for singular, plural in conversions.items():
            if singular in heading_lower:
                return heading.replace(singular.title(), plural)
        
        # Fallback: just add 's'
        return heading + 's'
