"""
Modular Compliance Package

This package provides:
- ConceptModuleRule: Validates concept modules
- ProcedureModuleRule: Validates procedure modules  
- ReferenceModuleRule: Validates reference modules
- ModularStructureBridge: Bridges existing AsciiDoc parser (no duplication)
"""

from .concept_module_rule import ConceptModuleRule
from .procedure_module_rule import ProcedureModuleRule
from .reference_module_rule import ReferenceModuleRule
from .modular_structure_bridge import ModularStructureBridge

__all__ = [
    'ConceptModuleRule',
    'ProcedureModuleRule', 
    'ReferenceModuleRule',
    'ModularStructureBridge'
]
