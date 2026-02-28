"""
Modular Compliance Package

This package provides comprehensive validation for Red Hat Modular Documentation.

Based on Red Hat Modular Documentation Reference Guide:
https://redhat-documentation.github.io/modular-docs/

Core Module Rules:
- ConceptModuleRule: Validates concept modules
- ProcedureModuleRule: Validates procedure modules  
- ReferenceModuleRule: Validates reference modules
- AssemblyModuleRule: Validates assembly documents

Support Classes:
- ModularBaseRule: Shared validation utilities for all module types
- ModularStructureBridge: Bridges existing AsciiDoc parser (no duplication)

Phase 5 Advanced Features:
- CrossReferenceRule: Validates xref links and cross-reference best practices
- TemplateComplianceRule: Provides templates and validates against them
- InterModuleAnalysisRule: Analyzes relationships between modules
- AdvancedModularAnalyzer: Orchestrates all advanced compliance features
"""

from .modular_base_rule import ModularBaseRule
from .concept_module_rule import ConceptModuleRule
from .procedure_module_rule import ProcedureModuleRule
from .reference_module_rule import ReferenceModuleRule
from .assembly_module_rule import AssemblyModuleRule
from .modular_structure_bridge import ModularStructureBridge

from .cross_reference_rule import CrossReferenceRule
from .inter_module_analysis_rule import InterModuleAnalysisRule
from .template_compliance_rule import TemplateComplianceRule
from .advanced_modular_analyzer import AdvancedModularAnalyzer

__all__ = [
    # Base class
    'ModularBaseRule',
    # Core module rules
    'ConceptModuleRule',
    'ProcedureModuleRule',
    'ReferenceModuleRule',
    'AssemblyModuleRule',
    # Support
    'ModularStructureBridge',
    # Advanced features
    'CrossReferenceRule',
    'TemplateComplianceRule',
    'InterModuleAnalysisRule',
    'AdvancedModularAnalyzer',
]
