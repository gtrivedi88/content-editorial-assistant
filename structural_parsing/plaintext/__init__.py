"""
Plain text structural parsing module.
Provides dedicated plain text parsing with paragraph detection.
"""

from .parser import PlainTextParser
from .types import PlainTextDocument, PlainTextBlock, PlainTextParseResult

__all__ = ['PlainTextParser', 'PlainTextDocument', 'PlainTextBlock', 'PlainTextParseResult']
