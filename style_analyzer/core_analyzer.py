"""
Core Analyzer Module (Refactored)
Main StyleAnalyzer class that coordinates all analysis with zero false positives.
This is now a thin wrapper around the modular components.
"""

# Import the new modular StyleAnalyzer
from .base_analyzer import StyleAnalyzer

# Re-export for backward compatibility
__all__ = ['StyleAnalyzer'] 