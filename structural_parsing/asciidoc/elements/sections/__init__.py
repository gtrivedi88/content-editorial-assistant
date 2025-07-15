"""
AsciiDoc Sections Element Module

Handles parsing and processing of AsciiDoc structural sections:
- Document sections (== Section, === Subsection, etc.)
- Preamble blocks (content before first section)
- Section hierarchy and organization
"""

from .parser import SectionParser

__all__ = ['SectionParser'] 