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
    
    def _detect_content_type_from_metadata(self, text: str) -> Optional[str]:
        """
        Detect content type from document metadata attributes.
        
        Looks for:
        - :_mod-docs-content-type: PROCEDURE|CONCEPT|REFERENCE
        - :_content-type: (deprecated but still supported)
        
        Returns lowercase type or None if not found.
        """
        # Check for new-style attribute
        new_style = re.search(r':_mod-docs-content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if new_style:
            return new_style.group(1).lower()
        
        # Check for old-style attribute (deprecated but still supported)
        old_style = re.search(r':_content-type:\s*(PROCEDURE|CONCEPT|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if old_style:
            return old_style.group(1).lower()
        
        return None
        
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
                # NOTE: Limitations section removed per Red Hat Apr 2025 update
                'deprecated_sections': [
                    {'pattern': r'^== (?:Limitations?)', 'reason': 'Removed per Apr 2025 - move to Prerequisites or intro'}
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
            except (yaml.YAMLError, OSError, ValueError):
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
            except (yaml.YAMLError, OSError, ValueError):
                pass  # Use defaults
    
    def analyze(self, text: str, sentences: List[str] = None, nlp=None, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze document structure against modular documentation templates.
        
        Args:
            text: Document text to analyze
            context: Analysis context including module type
            
        Returns:
            List of template compliance issues and suggestions
        """
        # === UNIVERSAL CODE CONTEXT GUARD ===
        # Skip analysis for code blocks, listings, and literal blocks (technical syntax, not prose)
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not text or not text.strip():
            return []
        
        errors = []
        context = context or {}
        
        # First try to detect content type from document metadata
        detected_type = self._detect_content_type_from_metadata(text)
        module_type = context.get('content_type', detected_type or 'concept')
        
        # Store the detected type back into context for use by validation methods
        context['content_type'] = module_type
        
        try:
            # Parse document structure
            structure = self.parser.parse(text)
            
            # Get template for this module type
            template = self.templates.get(module_type, self.templates['concept'])
            
            # Validate against template
            errors.extend(self._validate_title_pattern(text, template, context))
            errors.extend(self._validate_required_sections(structure, template, text, context))
            errors.extend(self._validate_prohibited_sections(structure, template, text, context))
            errors.extend(self._validate_deprecated_sections(structure, template, text, context))
            errors.extend(self._validate_content_guidelines(structure, template, text, context))
            errors.extend(self._suggest_template_improvements(structure, template, text, context))
            
        except (ValueError, TypeError, AttributeError) as e:
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
                error_type="template_analysis_error",
                flagged_text=text[:50]
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
                error_type="title_pattern_mismatch",
                flagged_text=title
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
            
            # Check section headings (== style)
            found = any(pattern.match(f"={'=' * section['level']} {section['title']}") 
                       for section in sections)
            
            # Also check for discrete headings (. style) in raw text
            # Red Hat modular docs use .Prerequisites, .Procedure, etc.
            if not found:
                discrete_pattern = required['pattern'].replace('^== ', '^\\.').replace('^=+', '\\.')
                found = bool(re.search(discrete_pattern, text, re.MULTILINE | re.IGNORECASE))
            
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
                    error_type="missing_required_section",
                    flagged_text=required['pattern']
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
                        error_type="prohibited_section",
                        flagged_text=section['title']
                    ))
        
        return errors
    
    def _validate_deprecated_sections(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Validate that deprecated sections are not present.
        
        Per Red Hat updates, certain sections have been deprecated:
        - Limitations: Removed per Apr 2025 update
        """
        errors = []
        
        deprecated_sections = template.get('deprecated_sections', [])
        sections = structure.get('sections', [])
        
        for section in sections:
            section_heading = f"={'=' * section['level']} {section['title']}"
            
            for deprecated in deprecated_sections:
                pattern = re.compile(deprecated['pattern'], re.IGNORECASE)
                if pattern.match(section_heading):
                    reason = deprecated.get('reason', 'This section has been deprecated')
                    module_type = context.get('content_type', 'concept')
                    
                    errors.append(self._create_error(
                        section['title'],  # sentence
                        section.get('line_number', 0),  # sentence_index
                        f"Deprecated section in {module_type} module: {section['title']}",  # message
                        [
                            reason,
                            "See: https://redhat-documentation.github.io/modular-docs/#whats-new"
                        ],  # suggestions
                        severity="medium",
                        text=text,
                        context=context,
                        confidence=0.8,
                        error_type="deprecated_section",
                        flagged_text=section['title']
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
                error_type="imperative_in_concept",
                flagged_text=text[:100]
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
                    error_type="missing_procedure_steps",
                    flagged_text=text[:100]
                ))
        
        return errors
    
    def _suggest_template_improvements(self, structure: Dict[str, Any], template: Dict[str, Any], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest improvements based on template best practices.

        Per Red Hat guidelines, optional sections should only be suggested when
        there's content that warrants them, not suggested unconditionally.

        Note: This method intentionally returns no suggestions. Per Red Hat modular
        documentation guidelines, optional sections should only be added when content
        warrants them, not suggested automatically.
        """
        # Don't suggest optional sections - they are truly OPTIONAL per Red Hat guidelines
        # The document is compliant as long as required sections are present
        # Optional sections like Troubleshooting, Next steps are only added when needed
        return []
    
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
        """
        Generate template content for a new module.

        NOTE: Templates updated per Red Hat guidelines:
        - Limitations section removed from procedures per Apr 2025 update
        - [discrete] tag not used per Oct 2025 update
        """
        template = self.get_template(module_type)
        title_slug = title.lower().replace(' ', '-')
        
        if module_type == 'concept':
            return f"""= Understanding {title}
:_mod-docs-content-type: CONCEPT

Brief introduction explaining what {title} is and why it matters.

This section provides context and establishes the foundation for understanding {title}.

== Key features

* Feature 1
* Feature 2  
* Feature 3

== Benefits

* Benefit 1
* Benefit 2
* Benefit 3

== Use cases

Common scenarios where {title} is used:

* Use case 1
* Use case 2
* Use case 3

== Additional resources

* xref:related-concept.adoc[Related Concept]
* xref:installing-{title_slug}.adoc[Installing {title}]
"""
        
        elif module_type == 'procedure':
            return f"""= Installing {title}
:_mod-docs-content-type: PROCEDURE

This procedure describes how to install and configure {title}.

.Prerequisites

* Prerequisite 1
* Prerequisite 2

.Procedure

. First step with clear action.
+
Additional details or code block if needed.

. Second step.
. Third step.

.Verification

To verify that {title} is working correctly:

. Verification step 1.
. Verification step 2.

.Next steps

* xref:configuring-{title_slug}.adoc[Configuring {title}]
* xref:understanding-{title_slug}.adoc[Understanding {title}]
"""
        
        elif module_type == 'reference':
            return f"""= {title} reference
:_mod-docs-content-type: REFERENCE

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

== Additional resources

* xref:understanding-{title_slug}.adoc[Understanding {title}]
* xref:related-reference.adoc[Related Reference]
"""
        
        elif module_type == 'assembly':
            return f"""= Getting started with {title}
:_mod-docs-content-type: ASSEMBLY

This assembly guides you through setting up and using {title}.

include::understanding-{title_slug}.adoc[leveloffset=+1]

include::installing-{title_slug}.adoc[leveloffset=+1]

include::configuring-{title_slug}.adoc[leveloffset=+1]

== Additional resources

* xref:{title_slug}-reference.adoc[{title} Reference]
"""
        
        return f"= {title}\n:_mod-docs-content-type: {module_type.upper()}\n\nTemplate content for {module_type} module."
