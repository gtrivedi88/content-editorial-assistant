"""
Format detection using simple regex patterns.
This module's sole purpose is quick format detection - NOT parsing.
"""

import re
from typing import Literal

class FormatDetector:
    """
    Simple format detector using regex patterns.
    This version has improved heuristics to better distinguish AsciiDoc from Markdown.
    """

    def __init__(self):
        # Patterns are now tuples with a pattern and a score weight.
        # More unique patterns get a higher score.
        self.asciidoc_patterns = [
            (r'^=+\s+', 5),              # AsciiDoc headings are a very strong signal.
            (r'^:[\w-]+:', 5),           # Document attributes are unique to AsciiDoc.
            (r'^\[(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]', 4), # Admonitions.
            (r'^\.(.+)', 3),             # Block titles are a strong signal.
            (r'^(include|image|link)::', 3), # AsciiDoc macros.
            (r'^\*{4,}\s*$', 2),          # Delimiter lines.
            (r'^={4,}\s*$', 2),
            (r'^-{4,}\s*$', 2),
            (r'^\.{2,}\s*$', 2),          # Literal block delimiters (at least 2 dots)
            (r'^\*{1,5}\s+', 1),          # AsciiDoc lists (lower score due to Markdown ambiguity).
        ]

        self.markdown_patterns = [
            (r'^#+\s+', 5),              # Markdown headings are a very strong signal.
            (r'^```', 4),                # Code fences.
            (r'^>\s+', 2),                # Blockquotes.
            (r'^\|\s*.*\s*\|', 2),          # Tables.
            (r'^\*\s+', 1),                # Unordered lists (lower score due to AsciiDoc ambiguity).
            (r'^\d+\.\s+', 1),              # Ordered lists.
        ]

    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown', 'plaintext']:
        """
        Detect document format using a weighted scoring system.
        """
        if not content or not content.strip():
            return 'plaintext'

        lines = content.split('\n')
        asciidoc_score = 0
        markdown_score = 0

        scan_lines = min(50, len(lines))
        for line in lines[:scan_lines]:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Check for AsciiDoc patterns and add their weight to the score
            for pattern, weight in self.asciidoc_patterns:
                if re.search(pattern, stripped_line):
                    asciidoc_score += weight
                    break # Only score the first match per line

            # Check for Markdown patterns
            for pattern, weight in self.markdown_patterns:
                if re.search(pattern, stripped_line):
                    markdown_score += weight
                    break

        # If no markup patterns found, treat as plain text
        if asciidoc_score == 0 and markdown_score == 0:
            return 'plaintext'

        # The final decision is based on the weighted score.
        # This is much more reliable than a simple count.
        if asciidoc_score > markdown_score:
            return 'asciidoc'
        else:
            return 'markdown'