"""
Format detection using simple regex patterns.
This module's sole purpose is quick format detection - NOT parsing.
"""

import re
from typing import Literal


class FormatDetector:
    """
    Simple format detector using regex patterns.
    
    This detector does NOT parse documents - it only makes a quick guess
    about the format based on simple patterns. The actual parsing is
    delegated to specialized parsers.
    """
    
    def __init__(self):
        # Simple patterns for format detection only
        self.asciidoc_patterns = [
            r'^=+\s+',  # AsciiDoc headings
            r'^\[(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]',  # Admonitions
            r'^:[\w-]+:\s*\w+',  # Document attributes
            r'^\*{4,}\s*$',  # Sidebar delimiters
            r'^={4,}\s*$',  # Example delimiters
            r'^-{4,}\s*$',  # Listing delimiters
            r'^\+{4,}\s*$',  # Passthrough delimiters
        ]
        
        self.markdown_patterns = [
            r'^#+\s+',  # Markdown headings
            r'^```',  # Code blocks
            r'^\*\s+',  # Unordered lists
            r'^\d+\.\s+',  # Ordered lists
            r'^>\s+',  # Blockquotes
            r'^\|\s*.*\s*\|',  # Tables
        ]
    
    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown']:
        """
        Detect document format using simple heuristics.
        
        This is a fast, simple check - NOT a full parse.
        The actual parsing is handled by specialized parsers.
        
        Args:
            content: Raw document content
            
        Returns:
            Detected format ('asciidoc' or 'markdown')
        """
        if not content.strip():
            return 'markdown'  # Default for empty content
        
        lines = content.split('\n')
        asciidoc_score = 0
        markdown_score = 0
        
        # Check first 20 lines for format indicators
        for line in lines[:20]:
            line = line.strip()
            if not line:
                continue
                
            # Check for AsciiDoc patterns
            for pattern in self.asciidoc_patterns:
                if re.match(pattern, line):
                    asciidoc_score += 1
                    break
            
            # Check for Markdown patterns
            for pattern in self.markdown_patterns:
                if re.match(pattern, line):
                    markdown_score += 1
                    break
        
        # Return format with higher score, default to markdown
        return 'asciidoc' if asciidoc_score > markdown_score else 'markdown' 