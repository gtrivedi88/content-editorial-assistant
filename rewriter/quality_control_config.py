"""
Quality Control Configuration
Configurable AI output validation system.
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class QualityControlConfig:
    """Configuration for AI quality control system."""
    
    # Duplication detection patterns
    duplication_patterns: List[str] = None
    
    # Statistical anomaly thresholds
    max_length_ratio: float = 1.4
    max_word_ratio: float = 1.3
    max_short_word_repetition: int = 3
    repetition_multiplier_threshold: float = 2.0
    
    # Language validation
    valid_prefixes: List[str] = None
    min_word_length: int = 2
    max_simple_word_length: int = 6
    
    # Control flags
    enable_duplication_detection: bool = True
    enable_statistical_analysis: bool = True
    enable_structure_validation: bool = True
    enable_logging: bool = True
    
    def __post_init__(self):
        """Set default values for complex fields."""
        if self.duplication_patterns is None:
            self.duplication_patterns = [
                r'\b(\w+)(over|under|pre|post|re|de|un|in|out|up|down)\1\b',  # prefix duplications
                r'\b(\w+)\1\b',  # simple duplications (e.g., "thethe", "andand")
                r'\b(\w+)\s+\1\b',  # space-separated duplications
            ]
        
        if self.valid_prefixes is None:
            self.valid_prefixes = [
                'over', 'under', 'pre', 'post', 're', 'un', 'in', 'out',
                'anti', 'auto', 'co', 'de', 'dis', 'ex', 'inter', 'mis',
                'non', 'semi', 'sub', 'super', 'trans', 'ultra'
            ]

    @classmethod
    def from_env(cls) -> 'QualityControlConfig':
        """Create configuration from environment variables."""
        return cls(
            max_length_ratio=float(os.getenv('QC_MAX_LENGTH_RATIO', '1.4')),
            max_word_ratio=float(os.getenv('QC_MAX_WORD_RATIO', '1.3')),
            max_short_word_repetition=int(os.getenv('QC_MAX_SHORT_WORD_REP', '3')),
            repetition_multiplier_threshold=float(os.getenv('QC_REP_MULTIPLIER', '2.0')),
            enable_duplication_detection=os.getenv('QC_ENABLE_DUPLICATION', 'true').lower() == 'true',
            enable_statistical_analysis=os.getenv('QC_ENABLE_STATISTICAL', 'true').lower() == 'true',
            enable_structure_validation=os.getenv('QC_ENABLE_STRUCTURE', 'true').lower() == 'true',
            enable_logging=os.getenv('QC_ENABLE_LOGGING', 'true').lower() == 'true',
        )

    @classmethod
    def production(cls) -> 'QualityControlConfig':
        """Create production-optimized configuration."""
        return cls(
            max_length_ratio=1.2,  # Stricter in production
            max_word_ratio=1.15,   # Stricter in production
            max_short_word_repetition=2,  # More sensitive
            repetition_multiplier_threshold=1.5,  # More sensitive
            enable_duplication_detection=True,
            enable_statistical_analysis=True,
            enable_structure_validation=True,
            enable_logging=True,
        )

    @classmethod
    def development(cls) -> 'QualityControlConfig':
        """Create development configuration with relaxed constraints."""
        return cls(
            max_length_ratio=2.0,  # More lenient for testing
            max_word_ratio=1.8,    # More lenient for testing
            max_short_word_repetition=5,  # Less sensitive
            repetition_multiplier_threshold=3.0,  # Less sensitive
            enable_duplication_detection=True,
            enable_statistical_analysis=True,
            enable_structure_validation=True,
            enable_logging=True,
        )

# Global configuration instance
_config = None

def get_quality_control_config() -> QualityControlConfig:
    """Get the global quality control configuration."""
    global _config
    if _config is None:
        env = os.getenv('AI_ENVIRONMENT', 'production').lower()
        if env == 'development':
            _config = QualityControlConfig.development()
        elif env == 'testing':
            _config = QualityControlConfig.development()  # Use dev config for testing
        else:
            _config = QualityControlConfig.production()
    return _config

def set_quality_control_config(config: QualityControlConfig):
    """Set the global quality control configuration."""
    global _config
    _config = config
