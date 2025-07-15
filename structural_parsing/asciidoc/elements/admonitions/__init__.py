"""
AsciiDoc Admonitions Element Module

Handles parsing and processing of AsciiDoc admonitions:
- NOTE blocks
- TIP blocks
- IMPORTANT blocks
- WARNING blocks
- CAUTION blocks
"""

from .parser import AdmonitionParser

__all__ = ['AdmonitionParser'] 