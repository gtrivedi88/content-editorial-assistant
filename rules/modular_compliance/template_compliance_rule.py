"""
Template Compliance Rule for Advanced Modular Documentation
Provides templates and validates document structure against modular documentation templates.
"""
import re
import os
from typing import List, Optional, Dict, Any, Set, Tuple
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
try:
    import yaml
except ImportError:
    yaml = None


class TemplateComplianceRule(BaseRule):
    """Advanced template validation and suggestion for modular documentation"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "template_compliance"
        self.rule_subtype = "structure_validation"
        self.parser = ModularStructureBridge()
        
        # Load templates and configuration
        self._load_templates()
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "template_compliance"
        
    def _load_templates(self):
        """Load modular documentation templates."""
        templates_path = os.path.join(
            os.path.dirname(__file__), 
            'templates'
        )
        
        # Default templates (embedded for reliability)
        self.templates = {
            'concept': {
                'title_pattern': r'^= (?:Understanding |About |What (?:is |are )|Overview of )?(.+)$',
                'required_sections': [
                    {'pattern': r'^== (?:Introduction|Overview|About).*', 'optional': True},
                    {'pattern': r'^== (?:Benefits?|Advantages?|Why use).*', 'optional': True},
                    {'pattern': r'^== (?:Key features?|Components?|Architecture).*', 'optional': True},
                    {'pattern': r'^== (?:Use cases?|When to use|Applications?).*', 'optional': True}
                ],
                'prohibited_sections': [
                    {'pattern': r'^== (?:Prerequisites?|Before you begin)', 'reason': 'Procedural content'},
                    {'pattern': r'^== (?:Steps?|Procedures?|Instructions?)', 'reason': 'Procedural content'},
                    {'pattern': r'^== (?:Installing?|Configuring?|Setting up)', 'reason': 'Procedural content'}
                ],
                'introduction_requirements': {
                    'min_paragraphs': 1,
                    'max_paragraphs': 3,
                    'should_define': True,
                    'should_contextualize': True
                },
                'content_guidelines': {
                    'focus': 'explanatory',
                    'avoid_imperatives': True,
                    'max_procedure_lists': 0,
                    'allow_examples': True
                }
            },
            'procedure': {
                'title_pattern': r'^= (?:How to |Installing?|Configuring?|Setting up|Creating?|Deploying?|Managing?)(.+)$',
                'required_sections': [
                    {'pattern': r'^== (?:Prerequisites?|Before you begin|Requirements?)', 'optional': False},
                    {'pattern': r'^== (?:Procedure|Steps?|Instructions?)', 'optional': False}
                ],
                'optional_sections': [
                    {'pattern': r'^== (?:Verification|Validating?|Testing?)', 'optional': True},
                    {'pattern': r'^== (?:Troubleshooting|Common issues?)', 'optional': True},
                    {'pattern': r'^== (?:Next steps?|Additional resources?)', 'optional': True}
                ],
                'prohibited_sections': [
                    {'pattern': r'^== (?:Introduction|Overview|About)', 'reason': 'Conceptual content - link to concept module instead'},
                    {'pattern': r'^== (?:Architecture|Components?)', 'reason': 'Conceptual content - link to concept module instead'}
                ],
                'step_requirements': {
                    'must_have_ordered_list': True,
                    'min_steps': 1,
                    'step_format': 'imperative',
                    'allow_substeps': True
                },
                'content_guidelines': {
                    'focus': 'action-oriented',
                    'use_imperatives': True,
                    'require_concrete_steps': True,
                    'allow_code_blocks': True
                }
            },
            'reference': {
                'title_pattern': r'^= (.+ (?:Reference|API|Parameters?|Options?|Configuration|Settings?))$',
                'required_sections': [
                    {'pattern': r'^== (?:Overview|Description|Summary)', 'optional': True}
                ],
                'typical_sections': [
                    {'pattern': r'^== (?:Parameters?|Options?|Arguments?|Fields?)', 'optional': True},
                    {'pattern': r'^== (?:Examples?|Usage)', 'optional': True},
                    {'pattern': r'^== (?:Return values?|Output|Response)', 'optional': True},
                    {'pattern': r'^== (?:See also|Related|Additional resources?)', 'optional': True}
                ],
                'prohibited_sections': [
                    {'pattern': r'^== (?:Prerequisites?|Before you begin)', 'reason': 'Procedural content'},
                    {'pattern': r'^== (?:Steps?|Procedure|Instructions?)', 'reason': 'Procedural content'},
                    {'pattern': r'^== (?:Architecture|How it works)', 'reason': 'Conceptual content - link to concept module instead'}
                ],
                'content_guidelines': {
                    'focus': 'factual',
                    'prefer_structured_data': True,
                    'allow_tables': True,
                    'allow_definition_lists': True,
                    'minimize_narrative': True
                }
            }
        }
        
        # Try to load templates from files if they exist
        if os.path.exists(templates_path):
            try:
                for module_type in ['concept', 'procedure', 'reference']:
                    template_file = os.path.join(templates_path, f'{module_type}_template.yaml')
                    if os.path.exists(template_file) and yaml:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            file_template = yaml.safe_load(f)
                            # Merge with defaults
                            if file_template:
                                self.templates[module_type].update(file_template)
            except Exception:
                pass  # Use embedded defaults
    
    def _load_config(self):
        """Load template validation configuration."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'template_compliance_types.yaml'
        )
        
        # Default configuration
        self.config = {
            'strict_mode': False,
            'suggest_improvements': True,
            'check_title_patterns': True,
            'validate_section_order': True,
            'confidence_thresholds': {
                'missing_required_section': 0.8,
                'prohibited_section': 0.9,
                'title_pattern_mismatch': 0.6,
                'structure_suggestion': 0.4,
                'content_guideline_violation': 0.5
            }
        }
        
        if yaml and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self.config.update(file_config)
            except Exception:
                pass  # Use defaults
    
    def analyze(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze document structure against modular documentation templates.
        
        Args:
            text: Document text to analyze
            context: Analysis context including module type
            
        Returns:
            List of template compliance issues and suggestions
        """
        if not text or not text.strip():
            return []
        
        errors = []
        context = context or {}
        module_type = context.get('content_type', 'concept')
        
        try:
            # Parse document structure
            structure = self.parser.parse(text)
            
            # Get template for this module type
            template = self.templates.get(module_type, self.templates['concept'])
            
            # Validate against template
            errors.extend(self._validate_title_pattern(text, template, context))
            errors.extend(self._validate_required_sections(structure, template, text, context))
            errors.extend(self._validate_prohibited_sections(structure, template, text, context))
            errors.extend(self._validate_content_guidelines(structure, template, text, context))
            errors.extend(self._suggest_template_improvements(structure, template, text, context))
            
        except Exception as e:
            # Graceful degradation
            errors.append(self._create_error(
                text[:50],  # sentence (first 50 chars)
                0,  # sentence_index
                "Template analysis failed due to parsing error",  # message
                [f"Unable to analyze template compliance: {str(e)}"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=0.2,
                error_type="template_analysis_error"
            ))
        
        return errors
    
    def _validate_title_pattern(self, text: str, template: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate document title against template pattern."""
        errors = []
        
        if not self.config['check_title_patterns']:
            return errors
        
        title_pattern = template.get('title_pattern')
        if not title_pattern:
            return errors
        
        # Extract title from text
        title_match = re.match(r'^= (.+)$', text.split('\n')[0] if text.split('\n') else '')
        if not title_match:
            return errors
        
        title = title_match.group(1).strip()
        
        # Check against pattern
        pattern = re.compile(title_pattern, re.IGNORECASE)
        if not pattern.match(f'= {title}'):
            module_type = context.get('content_type', 'concept')
            suggestions = self._get_title_suggestions(title, module_type)
            
            errors.append(self._create_error(
                title,  # sentence
                1,  # sentence_index
                f"Title doesn't follow {module_type} module pattern",  # message
                suggestions,  # suggestions
                severity="medium",
                text=text,
                context=context,
                confidence=self.config['confidence_thresholds']['title_pattern_mismatch'],
                error_type="title_pattern_mismatch"
            ))
        
        return errors
    
    def _validate_required_sections(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that required sections are present."""
        errors = []
        
        required_sections = template.get('required_sections', [])
        sections = structure.get('sections', [])
        
        for required in required_sections:
            if required.get('optional', False):
                continue
                
            pattern = re.compile(required['pattern'], re.IGNORECASE)
            found = any(pattern.match(f"={'=' * section['level']} {section['title']}") 
                       for section in sections)
            
            if not found:
                module_type = context.get('content_type', 'concept')
                errors.append(self._create_error(
                    required['pattern'],  # sentence
                    0,  # sentence_index
                    f"Missing required section for {module_type} module",  # message
                    [f"Add section: {self._suggest_section_title(required['pattern'])}"],  # suggestions
                    severity="high",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['missing_required_section'],
                    error_type="missing_required_section"
                ))
        
        return errors
    
    def _validate_prohibited_sections(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate that prohibited sections are not present."""
        errors = []
        
        prohibited_sections = template.get('prohibited_sections', [])
        sections = structure.get('sections', [])
        
        for section in sections:
            section_heading = f"={'=' * section['level']} {section['title']}"
            
            for prohibited in prohibited_sections:
                pattern = re.compile(prohibited['pattern'], re.IGNORECASE)
                if pattern.match(section_heading):
                    reason = prohibited.get('reason', 'Not appropriate for this module type')
                    module_type = context.get('content_type', 'concept')
                    
                    errors.append(self._create_error(
                        section['title'],  # sentence
                        section.get('line_number', 0),  # sentence_index
                        f"Prohibited section in {module_type} module: {section['title']}",  # message
                        [f"Consider moving this content to a separate {self._suggest_target_module_type(prohibited['pattern'])} module"],  # suggestions
                        severity="high",
                        text=text,
                        context=context,
                        confidence=self.config['confidence_thresholds']['prohibited_section'],
                        error_type="prohibited_section"
                    ))
        
        return errors
    
    def _validate_content_guidelines(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate content against template guidelines."""
        errors = []
        
        guidelines = template.get('content_guidelines', {})
        
        # Check for imperative usage based on module type
        if guidelines.get('avoid_imperatives') and self._has_imperatives(text):
            errors.append(self._create_error(
                text[:100],  # sentence (first 100 chars)
                0,  # sentence_index
                "Imperative language in concept module",  # message
                ["Use descriptive language: 'The system does...' instead of 'Do this...'"],  # suggestions
                severity="medium",
                text=text,
                context=context,
                confidence=self.config['confidence_thresholds']['content_guideline_violation'],
                error_type="imperative_in_concept"
            ))
        
        # Check for missing ordered lists in procedures
        if guidelines.get('focus') == 'action-oriented':
            ordered_lists = structure.get('ordered_lists', [])
            if not ordered_lists:
                errors.append(self._create_error(
                    text[:100],  # sentence (first 100 chars)
                    0,  # sentence_index
                    "Procedure module missing step-by-step instructions",  # message
                    ["Add numbered steps: 1. First step 2. Second step..."],  # suggestions
                    severity="high",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['content_guideline_violation'],
                    error_type="missing_procedure_steps"
                ))
        
        return errors
    
    def _suggest_template_improvements(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest improvements based on template best practices."""
        errors = []
        
        if not self.config['suggest_improvements']:
            return errors
        
        module_type = context.get('content_type', 'concept')
        
        # Suggest optional but recommended sections
        optional_sections = template.get('optional_sections', []) + template.get('typical_sections', [])
        sections = structure.get('sections', [])
        
        for optional in optional_sections[:2]:  # Limit suggestions
            pattern = re.compile(optional['pattern'], re.IGNORECASE)
            found = any(pattern.match(f"={'=' * section['level']} {section['title']}") 
                       for section in sections)
            
            if not found:
                errors.append(self._create_error(
                    optional['pattern'],  # sentence
                    0,  # sentence_index
                    f"Consider adding recommended section for {module_type} module",  # message
                    [f"Consider adding: {self._suggest_section_title(optional['pattern'])}"],  # suggestions
                    severity="low",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['structure_suggestion'],
                    error_type="suggested_section"
                ))
        
        return errors
    
    def _has_imperatives(self, text: str) -> bool:
        """Check if text contains imperative language patterns."""
        imperative_patterns = [
            r'\b(?:do|run|execute|install|configure|set|create|delete|remove|add|open|close|click|select|choose)\b',
            r'^\s*\d+\.\s+[A-Z]',  # Numbered steps starting with capital
            r'^\s*\*\s+[A-Z]'      # Bulleted steps starting with capital
        ]
        
        for pattern in imperative_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                return True
        
        return False
    
    def _get_title_suggestions(self, current_title: str, module_type: str) -> List[str]:
        """Generate title suggestions based on module type."""
        suggestions = []
        
        if module_type == 'concept':
            suggestions = [
                f"Understanding {current_title}",
                f"About {current_title}",
                f"What is {current_title}",
                f"Overview of {current_title}"
            ]
        elif module_type == 'procedure':
            suggestions = [
                f"Installing {current_title}",
                f"Configuring {current_title}",
                f"How to {current_title.lower()}",
                f"Setting up {current_title}"
            ]
        elif module_type == 'reference':
            suggestions = [
                f"{current_title} Reference",
                f"{current_title} Parameters",
                f"{current_title} API",
                f"{current_title} Configuration"
            ]
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _suggest_section_title(self, pattern: str) -> str:
        """Extract a suggested section title from a regex pattern."""
        # Simple extraction - remove regex syntax to get basic title
        title = re.sub(r'[\^$\(\)\[\]\{\}\*\+\?\|\\]', '', pattern)
        title = re.sub(r'\?:', '', title)  # Remove non-capturing groups
        title = title.replace('==', '').strip()
        
        return title or "Section"
    
    def _suggest_target_module_type(self, prohibited_pattern: str) -> str:
        """Suggest the appropriate module type for prohibited content."""
        if any(word in prohibited_pattern.lower() for word in ['step', 'procedure', 'install', 'configure']):
            return 'procedure'
        elif any(word in prohibited_pattern.lower() for word in ['parameter', 'option', 'api', 'reference']):
            return 'reference'
        else:
            return 'concept'
    
    def get_template(self, module_type: str) -> Dict[str, Any]:
        """Get the complete template for a module type."""
        return self.templates.get(module_type, self.templates['concept'])
    
    def generate_template_content(self, module_type: str, title: str) -> str:
        """Generate template content for a new module."""
        template = self.get_template(module_type)
        
        if module_type == 'concept':
            return f"""= Understanding {title}

[role="_abstract"]
Brief introduction explaining what {title} is and why it matters.

This section provides context and establishes the foundation for understanding {title}.

== Key Features

* Feature 1
* Feature 2  
* Feature 3

== Benefits

* Benefit 1
* Benefit 2
* Benefit 3

== Use Cases

Common scenarios where {title} is used:

* Use case 1
* Use case 2
* Use case 3

== Additional Resources

* xref:related-concept.adoc[Related Concept]
* xref:how-to-use-{title.lower().replace(' ', '-')}.adoc[How to Use {title}]
"""
        
        elif module_type == 'procedure':
            return f"""= Installing {title}

[role="_abstract"]
This procedure describes how to install and configure {title}.

== Prerequisites

Before you begin:

* Prerequisite 1
* Prerequisite 2

== Procedure

. First step with clear action
+
Additional details or code block if needed.

. Second step
. Third step

== Verification

To verify that {title} is working correctly:

. Verification step 1
. Verification step 2

== Next Steps

* xref:configuring-{title.lower().replace(' ', '-')}.adoc[Configure {title}]
* xref:understanding-{title.lower().replace(' ', '-')}.adoc[Learn more about {title}]
"""
        
        elif module_type == 'reference':
            return f"""= {title} Reference

[role="_abstract"]
Reference information for {title} including parameters, options, and examples.

== Overview

Brief description of {title} and its purpose.

== Parameters

[cols="1,1,1,2"]
|===
|Parameter |Type |Required |Description

|param1
|string
|Yes
|Description of parameter 1

|param2
|integer
|No
|Description of parameter 2

|===

== Examples

.Basic example
[source,bash]
----
# Example command or configuration
----

== See Also

* xref:understanding-{title.lower().replace(' ', '-')}.adoc[Understanding {title}]
* xref:related-reference.adoc[Related Reference]
"""
        
        return f"= {title}\n\n[role=\"_abstract\"]\nTemplate content for {module_type} module."
