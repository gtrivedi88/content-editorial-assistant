"""
AsciiDoc Delimited Blocks Element Module

Handles parsing and processing of AsciiDoc delimited blocks:
- Sidebar blocks (****)
- Example blocks (====)
- Quote blocks (____)
- Verse blocks ([verse])
- Pass blocks (++++))
- Open blocks (--)
"""

from .parser import DelimitedBlockParser

__all__ = ['DelimitedBlockParser'] 