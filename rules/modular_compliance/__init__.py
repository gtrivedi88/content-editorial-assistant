"""
Modular Compliance Package

This package provides:
- ConceptModuleRule: Validates concept modules
- ProcedureModuleRule: Validates procedure modules  
- ReferenceModuleRule: Validates reference modules
- ModularStructureBridge: Bridges existing AsciiDoc parser (no duplication)

Phase 5 Advanced Features:
- CrossReferenceRule: Validates xref links and cross-reference best practices
- TemplateComplianceRule: Provides templates and validates against them
- InterModuleAnalysisRule: Analyzes relationships between modules
- AdvancedModularAnalyzer: Orchestrates all advanced compliance features
"""

from .concept_module_rule import ConceptModuleRule
from .procedure_module_rule import ProcedureModuleRule
from .reference_module_rule import ReferenceModuleRule
from .modular_structure_bridge import ModularStructureBridge

from .cross_reference_rule import CrossReferenceRule
from .template_compliance_rule import TemplateComplianceRule
from .inter_module_analysis_rule import InterModuleAnalysisRule
from .advanced_modular_analyzer import AdvancedModularAnalyzer

__all__ = [
    'ConceptModuleRule',
    'ProcedureModuleRule', 
    'ReferenceModuleRule',
    'ModularStructureBridge',
    'CrossReferenceRule',
    'TemplateComplianceRule', 
    'InterModuleAnalysisRule',
    'AdvancedModularAnalyzer'
]
