"""
Ambiguity Detectors Package

This package contains specific detectors for different types of ambiguity
in technical writing.
"""

# Detectors will be imported as they are created
__all__ = []

# Try to import available detectors
try:
    from .missing_actor_detector import MissingActorDetector
    __all__.append('MissingActorDetector')
except ImportError:
    pass

try:
    from .pronoun_ambiguity_detector import PronounAmbiguityDetector
    __all__.append('PronounAmbiguityDetector')
except ImportError:
    pass

try:
    from .unsupported_claims_detector import UnsupportedClaimsDetector
    __all__.append('UnsupportedClaimsDetector')
except ImportError:
    pass

try:
    from .fabrication_risk_detector import FabricationRiskDetector
    __all__.append('FabricationRiskDetector')
except ImportError:
    pass 