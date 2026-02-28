"""
Document extraction module for the structural parsing system.

This module handles text extraction from various document formats,
providing plain text output for documents that need basic text analysis
rather than structural parsing.
"""

from .document_processor import DocumentProcessor

__all__ = ['DocumentProcessor'] 