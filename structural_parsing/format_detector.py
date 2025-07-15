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
            r'^\.{4,}\s*$',  # Literal delimiters (....)
            r'^_{4,}\s*$',  # Quote delimiters (____)
            r'^-{2}\s*$',  # Open block delimiters (--)
            r'^\.[A-Z]',  # Block titles (e.g., .Prerequisites)
            r'^\+\s*$',  # Continuation markers
            r'^\*{2,3}\s+',  # Multi-level list markers (** and ***)
            r'^\.\s+',  # Ordered lists with dots
            r'^\[\[.*\]\]',  # Anchors
            r'^include::', # Include directives
            r'^image::', # Image macros
            r'^link::', # Link macros
            r'link:.*\[.*\]', # Inline link macros
        ]
        
        self.markdown_patterns = [
            r'^#+\s+',  # Markdown headings
            r'^```',  # Code blocks
            r'^\*\s+',  # Unordered lists
            r'^\d+\.\s+',  # Ordered lists
            r'^>\s+',  # Blockquotes
            r'^\|\s*.*\s*\|',  # Tables
        ]
    
    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown', 'plaintext']:
        """
        Detect document format using simple heuristics.
        
        This is a fast, simple check - NOT a full parse.
        The actual parsing is handled by specialized parsers.
        
        Args:
            content: Raw document content
            
        Returns:
            Detected format ('asciidoc', 'markdown', or 'plaintext')
        """
        if not content or not content.strip():
            return 'plaintext'  # Default for empty or None content
        
        lines = content.split('\n')
        asciidoc_score = 0
        markdown_score = 0
        
        # Check first 50 lines for format indicators (increased from 20)
        # This helps catch indicators that appear later in the document
        scan_lines = min(50, len(lines))
        for line in lines[:scan_lines]:
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
        
        # If no markup patterns found, treat as plain text
        if asciidoc_score == 0 and markdown_score == 0:
            return 'plaintext'
        
        # Return format with higher score, default to markdown if tied
        return 'asciidoc' if asciidoc_score > markdown_score else 'markdown' 