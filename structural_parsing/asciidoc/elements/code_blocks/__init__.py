"""
AsciiDoc Code Blocks Element Module

Handles parsing and processing of AsciiDoc code blocks:
- Listing blocks (----)
- Literal blocks (....)
- Source code blocks with syntax highlighting
- Code callouts and annotations
"""

from .parser import CodeBlockParser

__all__ = ['CodeBlockParser'] 