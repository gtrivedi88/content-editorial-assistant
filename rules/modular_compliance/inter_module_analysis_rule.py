"""
Inter-Module Analysis Rule for Advanced Modular Compliance
Analyzes relationships between modules and validates modular documentation architecture.
"""
import re
import os
from typing import List, Optional, Dict, Any, Set, Tuple
from rules.base_rule import BaseRule
from .modular_structure_bridge import ModularStructureBridge
from .cross_reference_rule import CrossReferenceRule
try:
    import yaml
except ImportError:
    yaml = None


class InterModuleAnalysisRule(BaseRule):
    """Advanced inter-module relationship analysis for modular documentation"""
    
    def __init__(self):
        super().__init__()
        self.rule_type = "inter_module_analysis"
        self.rule_subtype = "relationship_validation"
        self.parser = ModularStructureBridge()
        self.xref_rule = CrossReferenceRule()
        
        # Module relationship patterns
        self.module_patterns = {
            'concept': r'^= (?:Understanding |About |What (?:is |are )|Overview of )?(.+)$',
            'procedure': r'^= (?:How to |Installing?|Configuring?|Setting up|Creating?|Deploying?|Managing?)(.+)$',
            'reference': r'^= (.+ (?:Reference|API|Parameters?|Options?|Configuration|Settings?))$'
        }
        
        # Load configuration
        self._load_config()
    
    def _get_rule_type(self) -> str:
        """Return the rule type for BaseRule compatibility."""
        return "inter_module_analysis"
        
    def _load_config(self):
        """Load inter-module analysis configuration."""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            'inter_module_types.yaml'
        )
        
        # Default configuration
        self.config = {
            'detect_missing_connections': True,
            'suggest_module_relationships': True,
            'validate_dependency_chains': True,
            'check_circular_dependencies': True,
            'max_dependency_depth': 5,
            'confidence_thresholds': {
                'missing_concept_link': 0.6,
                'missing_procedure_link': 0.7,
                'circular_dependency': 0.8,
                'incomplete_coverage': 0.5,
                'suggested_relationship': 0.3
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
        Analyze inter-module relationships and suggest improvements.
        
        Args:
            text: Document text to analyze
            context: Analysis context including module type and project context
            
        Returns:
            List of inter-module relationship issues and suggestions
        """
        if not text or not text.strip():
            return []
        
        errors = []
        context = context or {}
        
        try:
            # Parse document structure
            structure = self.parser.parse(text)
            
            # Extract cross-references
            xrefs = self.xref_rule._extract_cross_references(text)
            internal_links = self.xref_rule._extract_internal_links(text)
            
            # Analyze module relationships
            errors.extend(self._analyze_module_completeness(text, structure, context))
            errors.extend(self._check_missing_relationships(text, xrefs, context))
            errors.extend(self._validate_dependency_patterns(xrefs, text, context))
            errors.extend(self._suggest_complementary_modules(text, structure, context))
            errors.extend(self._check_content_distribution(text, structure, context))
            
        except Exception as e:
            # Graceful degradation
            errors.append(self._create_error(
                text[:50],  # sentence (first 50 chars)
                0,  # sentence_index
                "Inter-module analysis failed due to parsing error",  # message
                [f"Unable to analyze module relationships: {str(e)}"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=0.2,
                error_type="inter_module_analysis_error"
            ))
        
        return errors
    
    def _analyze_module_completeness(self, text: str, structure: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze if the current module is complete or needs supporting modules."""
        errors = []
        module_type = context.get('content_type', 'concept')
        
        # Check for content that suggests missing modules
        if module_type == 'concept':
            # Concept modules with procedural content should link to procedures
            if self._has_procedural_content(text):
                errors.append(self._create_error(
                    text[:100],  # sentence (first 100 chars)
                    0,  # sentence_index
                    "Concept module contains procedural content",  # message
                    [
                        "Create a 'How to...' procedure module",
                        "Add xref to procedure: xref:how-to-install-component.adoc[Installing Component]"
                    ],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['missing_procedure_link'],
                    error_type="concept_has_procedure_content"
                ))
        
        elif module_type == 'procedure':
            # Procedure modules should reference concepts if they lack context
            if not self._has_conceptual_references(text) and self._needs_conceptual_context(text):
                errors.append(self._create_error(
                    text[:100],  # sentence (first 100 chars)
                    0,  # sentence_index
                    "Procedure module lacks conceptual context",  # message
                    [
                        "Add link to concept module in introduction",
                        "Reference: xref:understanding-component.adoc[Understanding Component]"
                    ],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['missing_concept_link'],
                    error_type="procedure_missing_concept_link"
                ))
        
        elif module_type == 'reference':
            # Reference modules should have examples or usage procedures
            if not self._has_examples(text) and not self._has_usage_procedures(text):
                errors.append(self._create_error(
                    text[:100],  # sentence (first 100 chars)
                    0,  # sentence_index
                    "Reference module lacks usage examples",  # message
                    [
                        "Add examples section",
                        "Link to procedure: xref:using-api.adoc[Using the API]"
                    ],  # suggestions
                    severity="medium",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['incomplete_coverage'],
                    error_type="reference_missing_examples"
                ))
        
        return errors
    
    def _check_missing_relationships(self, text: str, xrefs: List[Dict[str, Any]], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for missing relationships between related modules."""
        errors = []
        
        if not self.config['detect_missing_connections']:
            return errors
        
        module_type = context.get('content_type', 'concept')
        title = self._extract_title(text)
        
        # Analyze content to suggest related modules
        suggested_modules = self._suggest_related_modules(text, title, module_type)
        
        # Check if these relationships already exist
        existing_refs = {xref['target'] for xref in xrefs}
        
        for suggestion in suggested_modules:
            if suggestion['filename'] not in ' '.join(existing_refs):
                errors.append(self._create_error(
                    suggestion['filename'],  # sentence
                    0,  # sentence_index
                    f"Consider linking to related {suggestion['type']} module",  # message
                    [suggestion['link_example']],  # suggestions
                    severity="low",
                    text=text,
                    context=context,
                    confidence=self.config['confidence_thresholds']['suggested_relationship'],
                    error_type="suggested_module_relationship"
                ))
        
        return errors
    
    def _validate_dependency_patterns(self, xrefs: List[Dict[str, Any]], text: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate dependency patterns and detect issues."""
        errors = []
        
        # Check for excessive dependencies
        if len(xrefs) > 10:  # Arbitrary threshold
            errors.append(self._create_error(
                text[:100],  # sentence (first 100 chars)
                0,  # sentence_index
                "Module has many external dependencies",  # message
                ["Consider splitting this module into smaller, focused modules"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=0.4,
                error_type="excessive_dependencies"
            ))
        
        # Check for dependency depth (simplified analysis)
        deep_deps = [xref for xref in xrefs if xref['target'].count('/') > 2]
        if deep_deps:
            errors.append(self._create_error(
                text[:100],  # sentence (first 100 chars)
                0,  # sentence_index
                "Deep dependency structure detected",  # message
                ["Review module organization and consider flattening structure"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=0.3,
                error_type="deep_dependencies"
            ))
        
        return errors
    
    def _suggest_complementary_modules(self, text: str, structure: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest complementary modules that would complete the documentation set."""
        errors = []
        
        if not self.config['suggest_module_relationships']:
            return errors
        
        module_type = context.get('content_type', 'concept')
        title = self._extract_title(text)
        
        # Generate suggestions based on content analysis
        suggestions = []
        
        if module_type == 'concept':
            # Suggest procedures and references
            if self._mentions_installation(text):
                suggestions.append({
                    'type': 'procedure',
                    'title': f"Installing {title}",
                    'filename': f"installing-{title.lower().replace(' ', '-')}.adoc",
                    'reason': 'Installation procedures would complement this concept'
                })
            
            if self._mentions_configuration(text):
                suggestions.append({
                    'type': 'procedure', 
                    'title': f"Configuring {title}",
                    'filename': f"configuring-{title.lower().replace(' ', '-')}.adoc",
                    'reason': 'Configuration procedures would be helpful'
                })
                
            if self._mentions_api_or_parameters(text):
                suggestions.append({
                    'type': 'reference',
                    'title': f"{title} Reference",
                    'filename': f"{title.lower().replace(' ', '-')}-reference.adoc",
                    'reason': 'A reference module would provide detailed parameter information'
                })
        
        # Present top suggestions
        for suggestion in suggestions[:2]:  # Limit to 2 suggestions
            errors.append(self._create_error(
                suggestion['title'],  # sentence
                0,  # sentence_index
                f"Consider creating complementary {suggestion['type']} module",  # message
                [f"Create: {suggestion['title']} ({suggestion['filename']})"],  # suggestions
                severity="low",
                text=text,
                context=context,
                confidence=self.config['confidence_thresholds']['suggested_relationship'],
                error_type="complementary_module_suggestion"
            ))
        
        return errors
    
    def _check_content_distribution(self, text: str, structure: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if content is properly distributed across module types."""
        errors = []
        
        module_type = context.get('content_type', 'concept')
        
        # Analyze content distribution
        content_analysis = self._analyze_content_types(text)
        
        # Check for misplaced content
        if module_type == 'concept' and content_analysis['procedural_ratio'] > 0.3:
            errors.append(self._create_error(
                text[:100],  # sentence (first 100 chars)
                0,  # sentence_index
                "High procedural content in concept module",  # message
                ["Consider moving step-by-step content to a procedure module"],  # suggestions
                severity="medium",
                text=text,
                context=context,
                confidence=0.6,
                error_type="content_type_mismatch"
            ))
        
        elif module_type == 'procedure' and content_analysis['conceptual_ratio'] > 0.4:
            errors.append(self._create_error(
                text[:100],  # sentence (first 100 chars)
                0,  # sentence_index
                "High conceptual content in procedure module",  # message
                ["Consider moving explanatory content to a concept module"],  # suggestions
                severity="medium",
                text=text,
                context=context,
                confidence=0.6,
                error_type="content_type_mismatch"
            ))
        
        return errors
    
    def _extract_title(self, text: str) -> str:
        """Extract the main title from text."""
        title_match = re.match(r'^= (.+)$', text.split('\n')[0] if text.split('\n') else '')
        return title_match.group(1).strip() if title_match else 'Unknown'
    
    def _has_procedural_content(self, text: str) -> bool:
        """Check if text contains procedural content patterns."""
        patterns = [
            r'\b(?:install|configure|setup|deploy|create|run|execute)\b',
            r'^\s*\d+\.\s+',  # Numbered steps
            r'\b(?:first|then|next|finally)\b.*(?:step|do|run)',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE | re.MULTILINE) for pattern in patterns)
    
    def _has_conceptual_references(self, text: str) -> bool:
        """Check if text references conceptual modules."""
        concept_patterns = [
            r'xref:[^[\]]*understanding[^[\]]*\.adoc',
            r'xref:[^[\]]*about[^[\]]*\.adoc',
            r'xref:[^[\]]*overview[^[\]]*\.adoc',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in concept_patterns)
    
    def _needs_conceptual_context(self, text: str) -> bool:
        """Check if procedure needs conceptual background."""
        # Simple heuristic: if procedure is complex or mentions unfamiliar concepts
        complex_indicators = [
            r'\b(?:architecture|components?|concepts?)\b',
            r'(?:advanced|complex|enterprise)',
            len(re.findall(r'^\s*\d+\.\s+', text, re.MULTILINE)) > 10  # Many steps
        ]
        
        return any(re.search(indicator, text, re.IGNORECASE) if isinstance(indicator, str) else indicator 
                  for indicator in complex_indicators)
    
    def _has_examples(self, text: str) -> bool:
        """Check if text contains examples."""
        example_patterns = [
            r'== Examples?',
            r'\.Example\b',
            r'\[source,',
            r'----\n',  # Code blocks
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in example_patterns)
    
    def _has_usage_procedures(self, text: str) -> bool:
        """Check if text links to usage procedures."""
        usage_patterns = [
            r'xref:[^[\]]*(?:how-to|using|usage)[^[\]]*\.adoc',
            r'xref:[^[\]]*procedure[^[\]]*\.adoc',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in usage_patterns)
    
    def _suggest_related_modules(self, text: str, title: str, module_type: str) -> List[Dict[str, Any]]:
        """Suggest related modules based on content analysis."""
        suggestions = []
        title_slug = title.lower().replace(' ', '-')
        
        if module_type == 'concept':
            if self._mentions_installation(text):
                suggestions.append({
                    'type': 'procedure',
                    'filename': f'installing-{title_slug}.adoc',
                    'reason': 'Installation procedures would help users implement this concept',
                    'link_example': f'xref:installing-{title_slug}.adoc[Installing {title}]'
                })
        
        elif module_type == 'procedure':
            # Check if concept module would be helpful
            if not self._has_conceptual_references(text):
                suggestions.append({
                    'type': 'concept',
                    'filename': f'understanding-{title_slug}.adoc',
                    'reason': 'A concept module would provide helpful background',
                    'link_example': f'xref:understanding-{title_slug}.adoc[Understanding {title}]'
                })
        
        return suggestions
    
    def _mentions_installation(self, text: str) -> bool:
        """Check if text mentions installation."""
        return bool(re.search(r'\b(?:install|installation|setup|deploy|deployment)\b', text, re.IGNORECASE))
    
    def _mentions_configuration(self, text: str) -> bool:
        """Check if text mentions configuration."""
        return bool(re.search(r'\b(?:configur|setting|option|parameter)\b', text, re.IGNORECASE))
    
    def _mentions_api_or_parameters(self, text: str) -> bool:
        """Check if text mentions APIs or parameters."""
        return bool(re.search(r'\b(?:api|parameter|option|field|property|attribute)\b', text, re.IGNORECASE))
    
    def _analyze_content_types(self, text: str) -> Dict[str, float]:
        """Analyze the distribution of content types in text."""
        total_sentences = len(re.findall(r'[.!?]+', text))
        if total_sentences == 0:
            return {'procedural_ratio': 0, 'conceptual_ratio': 0, 'reference_ratio': 0}
        
        # Count procedural content
        procedural_indicators = len(re.findall(r'\b(?:do|run|install|configure|create|execute|click|select)\b', text, re.IGNORECASE))
        procedural_steps = len(re.findall(r'^\s*\d+\.\s+', text, re.MULTILINE))
        
        # Count conceptual content
        conceptual_indicators = len(re.findall(r'\b(?:is|are|means|represents|consists of|includes)\b', text, re.IGNORECASE))
        
        # Count reference content  
        reference_indicators = len(re.findall(r'\b(?:parameter|option|field|returns?|syntax)\b', text, re.IGNORECASE))
        
        return {
            'procedural_ratio': min((procedural_indicators + procedural_steps * 2) / total_sentences, 1.0),
            'conceptual_ratio': min(conceptual_indicators / total_sentences, 1.0),
            'reference_ratio': min(reference_indicators / total_sentences, 1.0)
        }
