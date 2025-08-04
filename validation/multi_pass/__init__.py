"""
Multi-pass validation system.
Provides base classes and interfaces for multi-pass error validation.
"""

# Import base validation components
from .base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext,
    ValidationPerformanceMetrics, ValidationError, ValidationConfigError
)

# Import concrete validators
from .pass_validators import MorphologicalValidator, ContextValidator, DomainValidator, CrossRuleValidator

# Import validation pipeline
from .validation_pipeline import (
    ValidationPipeline, PipelineConfiguration, PipelineResult, 
    ConsensusStrategy, TerminationCondition, ValidatorWeight
)

__all__ = [
    'BasePassValidator',
    'ValidationDecision',
    'ValidationConfidence', 
    'ValidationEvidence',
    'ValidationResult',
    'ValidationContext',
    'ValidationPerformanceMetrics',
    'ValidationError',
    'ValidationConfigError',
    'MorphologicalValidator',
    'ContextValidator',
    'DomainValidator',
    'CrossRuleValidator',
    'ValidationPipeline',
    'PipelineConfiguration',
    'PipelineResult',
    'ConsensusStrategy',
    'TerminationCondition',
    'ValidatorWeight'
]