"""
AsciiDoc Titles Element Module

Handles parsing and processing of AsciiDoc titles:
- Document titles (= Title)
- Section headings (== Section, === Subsection, etc.)
- Title levels and hierarchy
"""

from .parser import TitleParser

__all__ = ['TitleParser'] 