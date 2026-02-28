"""
DITA structural parsing module.
Provides dedicated DITA XML parsing with topic-aware block detection.
"""

from .parser import DITAParser
from .types import DITADocument, DITABlock, DITAParseResult

__all__ = ['DITAParser', 'DITADocument', 'DITABlock', 'DITAParseResult']
