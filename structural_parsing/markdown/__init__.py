"""
Markdown structural parsing module.
Uses markdown-it-py for CommonMark-compliant parsing.
"""

from .parser import MarkdownParser
from .types import MarkdownDocument, MarkdownBlock, MarkdownParseResult

__all__ = ['MarkdownParser', 'MarkdownDocument', 'MarkdownBlock', 'MarkdownParseResult'] 