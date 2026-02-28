"""
Orchestrates cross-references, templates, and inter-module analysis for comprehensive modular compliance.
"""
import re
from typing import List, Optional, Dict, Any, Set
from rules.modular_compliance.cross_reference_rule import CrossReferenceRule
from rules.modular_compliance.template_compliance_rule import TemplateComplianceRule
from rules.modular_compliance.inter_module_analysis_rule import InterModuleAnalysisRule
from rules.modular_compliance.concept_module_rule import ConceptModuleRule
from rules.modular_compliance.procedure_module_rule import ProcedureModuleRule
from rules.modular_compliance.reference_module_rule import ReferenceModuleRule
from rules.modular_compliance.assembly_module_rule import AssemblyModuleRule


class AdvancedModularAnalyzer:
    """
    Advanced analyzer that orchestrates all Phase 5 modular compliance features.
    
    This analyzer combines:
    - Basic modular compliance (concept, procedure, reference)
    - Cross-reference validation
    - Template compliance and suggestions
    - Inter-module relationship analysis
    """
    
    def __init__(self):
        """Initialize all advanced modular compliance analyzers."""
        # Basic modular compliance rules
        self.concept_rule = ConceptModuleRule()
        self.procedure_rule = ProcedureModuleRule()
        self.reference_rule = ReferenceModuleRule()
        self.assembly_rule = AssemblyModuleRule()
        
        # Phase 5 advanced features
        self.xref_rule = CrossReferenceRule()
        self.template_rule = TemplateComplianceRule()
        self.inter_module_rule = InterModuleAnalysisRule()
        
        # Rule mapping
        self.module_rules = {
            'concept': self.concept_rule,
            'procedure': self.procedure_rule,
            'reference': self.reference_rule,
            'assembly': self.assembly_rule
        }
    
    def analyze_comprehensive(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform comprehensive modular compliance analysis including all Phase 5 features.
        
        Args:
            text: Document text to analyze
            context: Analysis context including module type
            
        Returns:
            Comprehensive analysis results with all compliance aspects
        """
        if not text or not text.strip():
            return self._create_empty_result()
        
        context = context or {}
        module_type = context.get('content_type', 'concept')
        
        # Collect all analysis results
        results = {
            'module_type': module_type,
            'basic_compliance': [],
            'cross_references': [],
            'template_compliance': [],
            'inter_module_analysis': [],
            'template_suggestions': {},
            'comprehensive_score': 0.0,
            'total_issues': 0,
            'compliance_status': 'compliant'
        }
        
        try:
            # Basic modular compliance
            basic_rule = self.module_rules.get(module_type, self.concept_rule)
            results['basic_compliance'] = basic_rule.analyze(text, context)
            
            # Advanced Phase 5 analyses
            results['cross_references'] = self.xref_rule.analyze(text, context)
            results['template_compliance'] = self.template_rule.analyze(text, context)
            results['inter_module_analysis'] = self.inter_module_rule.analyze(text, context)
            
            # Generate template suggestions
            results['template_suggestions'] = self._generate_template_suggestions(text, context)
            
            # Calculate comprehensive metrics
            results.update(self._calculate_comprehensive_metrics(results))
            
        except Exception as e:
            # Graceful degradation
            results['analysis_error'] = f"Advanced analysis failed: {str(e)}"
            results['compliance_status'] = 'analysis_error'
        
        return results
    
    def analyze_basic_with_advanced_hints(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Perform basic analysis enhanced with Phase 5 insights for backward compatibility.
        
        This method maintains compatibility with the existing style analyzer while
        adding advanced Phase 5 features as additional context.
        
        Args:
            text: Document text to analyze
            context: Analysis context
            
        Returns:
            List of compliance issues in the standard format
        """
        if not text or not text.strip():
            return []
        
        context = context or {}
        module_type = context.get('content_type', 'concept')
        
        # Get basic compliance results
        basic_rule = self.module_rules.get(module_type, self.concept_rule)
        
        if basic_rule is None:
            return []
        
        basic_issues = basic_rule.analyze(text, context)
        
        # Add advanced insights as additional issues
        advanced_issues = []
        
        # High-confidence cross-reference issues
        xref_issues = self.xref_rule.analyze(text, context)
        high_confidence_xref = [issue for issue in xref_issues if issue.get('confidence', 0) >= 0.7]
        advanced_issues.extend(high_confidence_xref)
        
        # Critical template compliance issues
        template_issues = self.template_rule.analyze(text, context)
        critical_template = [issue for issue in template_issues if issue.get('confidence', 0) >= 0.8]
        advanced_issues.extend(critical_template)
        
        # Important inter-module relationship issues
        inter_module_issues = self.inter_module_rule.analyze(text, context)
        important_inter_module = [issue for issue in inter_module_issues if issue.get('confidence', 0) >= 0.6]
        advanced_issues.extend(important_inter_module)
        
        # Combine and return
        all_issues = basic_issues + advanced_issues
        return self._deduplicate_issues(all_issues)
    
    def get_template_for_module(self, module_type: str) -> Dict[str, Any]:
        """Get the complete template structure for a module type."""
        return self.template_rule.get_template(module_type)
    
    def generate_module_template(self, module_type: str, title: str) -> str:
        """Generate template content for a new module."""
        return self.template_rule.generate_template_content(module_type, title)
    
    def analyze_cross_references_only(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Analyze only cross-references for focused validation."""
        return self.xref_rule.analyze(text, context)
    
    def get_module_suggestions(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get suggestions for improving module structure and relationships."""
        context = context or {}
        
        # Get template suggestions
        template_suggestions = self.template_rule.analyze(text, context)
        template_improvements = [issue for issue in template_suggestions 
                               if 'suggestion' in issue.get('type', '')]
        
        # Get inter-module relationship suggestions
        relationship_suggestions = self.inter_module_rule.analyze(text, context)
        relationship_improvements = [issue for issue in relationship_suggestions
                                   if 'suggest' in issue.get('type', '')]
        
        return {
            'template_improvements': template_improvements,
            'relationship_improvements': relationship_improvements,
            'total_suggestions': len(template_improvements) + len(relationship_improvements)
        }
    
    def _generate_template_suggestions(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent template suggestions based on content analysis."""
        module_type = context.get('content_type', 'concept')
        
        # Get current template
        template = self.template_rule.get_template(module_type)
        
        # Analyze content gaps
        suggestions = {
            'missing_sections': [],
            'structural_improvements': [],
            'content_enhancements': [],
            'cross_reference_opportunities': []
        }
        
        # Template compliance analysis provides most suggestions
        template_issues = self.template_rule.analyze(text, context)
        for issue in template_issues:
            if 'missing' in issue.get('type', ''):
                suggestions['missing_sections'].append(issue.get('message', ''))
            elif 'suggest' in issue.get('type', ''):
                suggestions['structural_improvements'].append(issue.get('message', ''))
        
        # Cross-reference opportunities
        xref_issues = self.xref_rule.analyze(text, context)
        for issue in xref_issues:
            if 'missing' in issue.get('type', '') or 'suggest' in issue.get('type', ''):
                suggestions['cross_reference_opportunities'].append(issue.get('message', ''))
        
        return suggestions
    
    def _calculate_comprehensive_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive compliance metrics across all analyses."""
        # Count total issues
        total_issues = (
            len(results['basic_compliance']) +
            len(results['cross_references']) +
            len(results['template_compliance']) +
            len(results['inter_module_analysis'])
        )
        
        # Calculate weighted score (lower is better)
        issue_weights = {
            'basic_compliance': 1.0,      # Core compliance is most important
            'cross_references': 0.8,      # Cross-refs are important for navigation
            'template_compliance': 0.6,   # Templates help consistency
            'inter_module_analysis': 0.4  # Relationship analysis is suggestive
        }
        
        weighted_score = 0.0
        max_possible_score = 0.0
        
        for category, weight in issue_weights.items():
            issues = results.get(category, [])
            category_score = sum(issue.get('confidence', 0.5) for issue in issues)
            weighted_score += category_score * weight
            max_possible_score += len(issues) * weight  # Assume max confidence of 1.0
        
        # Normalize to 0-100 scale (higher is better)
        if max_possible_score > 0:
            comprehensive_score = max(0, 100 - (weighted_score / max_possible_score) * 100)
        else:
            comprehensive_score = 100  # No issues found
        
        # Determine compliance status
        if total_issues == 0:
            compliance_status = 'fully_compliant'
        elif comprehensive_score >= 80:
            compliance_status = 'mostly_compliant'
        elif comprehensive_score >= 60:
            compliance_status = 'partially_compliant'
        else:
            compliance_status = 'non_compliant'
        
        return {
            'total_issues': total_issues,
            'comprehensive_score': round(comprehensive_score, 1),
            'compliance_status': compliance_status
        }
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """Create an empty result structure."""
        return {
            'module_type': 'unknown',
            'basic_compliance': [],
            'cross_references': [],
            'template_compliance': [],
            'inter_module_analysis': [],
            'template_suggestions': {},
            'comprehensive_score': 100.0,
            'total_issues': 0,
            'compliance_status': 'compliant'
        }
    
    def _deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate issues based on message and line number."""
        seen = set()
        deduplicated = []
        
        for issue in issues:
            # Create a key for deduplication
            key = (
                issue.get('message', ''),
                issue.get('line_number', 0),
                issue.get('type', '')
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(issue)
        
        return deduplicated
