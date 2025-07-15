"""
AsciiDoc Tables Element Module

Handles parsing and processing of AsciiDoc tables:
- Table structures with headers and rows
- Table cells and cell content
- Table formatting and attributes
- Column specifications and alignment
"""

from .parser import TableParser

__all__ = ['TableParser'] 