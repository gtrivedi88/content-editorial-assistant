"""
AsciiDoc Procedures Element Module

Handles parsing and processing of AsciiDoc procedures:
- Numbered procedure steps
- Ordered lists that represent procedures
- Step-by-step instructions
- Procedure validation and numbering
"""

from .parser import ProcedureParser

__all__ = ['ProcedureParser'] 