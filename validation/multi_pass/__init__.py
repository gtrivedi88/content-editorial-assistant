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
# from .validation_pipeline import ValidationPipeline  # Future step
# from .pass_validators import *  # Future steps

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
    # 'ValidationPipeline'
]

# Main validation pipeline will be imported here when implemented
# from .validation_pipeline import ValidationPipeline