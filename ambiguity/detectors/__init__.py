"""
Ambiguity Detectors Package

This package contains specialized detectors for different types of ambiguity
in technical writing.
"""

try:
    from .missing_actor_detector import MissingActorDetector
    from .pronoun_ambiguity_detector import PronounAmbiguityDetector
    from .unsupported_claims_detector import UnsupportedClaimsDetector
    from .fabrication_risk_detector import FabricationRiskDetector
    
    __all__ = [
        'MissingActorDetector',
        'PronounAmbiguityDetector',
        'UnsupportedClaimsDetector',
        'FabricationRiskDetector'
    ]
    
except ImportError as e:
    print(f"Warning: Could not import all ambiguity detectors: {e}")
    __all__ = [] 