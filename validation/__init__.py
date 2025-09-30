"""
Validation Module for Style Guide AI
Provides multi-layered confidence scoring and validation system.
"""

__version__ = "1.0.0"
__author__ = "Style Guide AI Team"

# Import main components for easy access
from .config import (
    BaseConfig, ConfidenceWeightsConfig, ValidationThresholdsConfig, LinguisticAnchorsConfig
)
from .confidence import (
    ConfidenceCalculator, LinguisticAnchors, ContextAnalyzer, DomainClassifier
)
from .multi_pass import (
    BasePassValidator, ValidationDecision, ValidationConfidence, ValidationEvidence,
    ValidationResult, ValidationContext, MorphologicalValidator, ContextValidator,
    DomainValidator, CrossRuleValidator, ValidationPipeline, PipelineConfiguration,
    PipelineResult, ConsensusStrategy, TerminationCondition, ValidatorWeight
)
# Import specialized validators
from .negative_example_validator import NegativeExampleValidator

__all__ = [
    # Configuration
    'BaseConfig',
    'ConfidenceWeightsConfig',
    'ValidationThresholdsConfig', 
    'LinguisticAnchorsConfig',
    # Confidence System
    'ConfidenceCalculator',
    'LinguisticAnchors',
    'ContextAnalyzer',
    'DomainClassifier',
    # Multi-Pass Validation
    'BasePassValidator',
    'ValidationDecision',
    'ValidationConfidence',
    'ValidationEvidence',
    'ValidationResult',
    'ValidationContext',
    'MorphologicalValidator',
    'ContextValidator',
    'DomainValidator',
    'CrossRuleValidator',
    'ValidationPipeline',
    'PipelineConfiguration',
    'PipelineResult',
    'ConsensusStrategy',
    'TerminationCondition',
    'ValidatorWeight',
    # Specialized Validators
    'NegativeExampleValidator'
]