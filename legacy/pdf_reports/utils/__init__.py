"""
PDF Report Utilities Package

Metric calculations, interpretations, and helper functions
for generating meaningful insights from analysis data.
"""

from .metrics import MetricsCalculator
from .interpretations import MetricsInterpreter

__all__ = [
    'MetricsCalculator',
    'MetricsInterpreter'
]

