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
            (r'^\|={4,}\s*$', 5),        # AsciiDoc table delimiters (|====)
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
            (r'^\|\s*[^=].*\s*\|', 1),   # Tables (but not AsciiDoc table delimiters |====).
            (r'^[\*\-\+]\s+', 1),          # Unordered lists (*, -, +) (lower score due to AsciiDoc ambiguity).
            (r'^\d+\.\s+', 1),              # Ordered lists.
        ]
        
        self.dita_patterns = [
            (r'<!DOCTYPE\s+\w+\s+PUBLIC.*DITA', 10),  # DITA DOCTYPE - very strong signal
            (r'<(concept|task|reference|topic|troubleshooting)', 8),  # DITA topic types
            (r'<(conbody|taskbody|refbody|troublebody)', 6),  # DITA body elements
            (r'<(shortdesc|prereq|context|steps|result)', 4),  # DITA specific elements
            (r'<(step|cmd|info|stepresult)', 3),  # Task-specific elements
            (r'<?xml.*encoding=', 2),  # XML declaration
        ]

    def detect_format(self, content: str) -> Literal['asciidoc', 'markdown', 'plaintext']:
        """
        Detect document format using a weighted scoring system.
        Enhanced to handle content inside delimited blocks properly.
        """
        if not content or not content.strip():
            return 'plaintext'

        lines = content.split('\n')
        asciidoc_score = 0
        markdown_score = 0
        dita_score = 0
        
        # Check for DITA patterns first (check entire content for XML patterns)
        for pattern, weight in self.dita_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                dita_score += weight
        
        # Track if we're inside delimited blocks to avoid scoring their content
        inside_asciidoc_block = False
        asciidoc_block_delimiter = None

        scan_lines = min(50, len(lines))
        for line in lines[:scan_lines]:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Check for AsciiDoc delimited block start/end
            if re.match(r'^(={4,}|`{4,}|-{4,}|\*{4,}|\+{4,}|\.{4,})\s*$', stripped_line):
                if inside_asciidoc_block and stripped_line == asciidoc_block_delimiter:
                    # End of block
                    inside_asciidoc_block = False
                    asciidoc_block_delimiter = None
                elif not inside_asciidoc_block:
                    # Start of block
                    inside_asciidoc_block = True
                    asciidoc_block_delimiter = stripped_line
                # Always score delimiter lines as AsciiDoc
                asciidoc_score += 2
                continue

            # Skip scoring content inside AsciiDoc delimited blocks
            if inside_asciidoc_block:
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
        if asciidoc_score == 0 and markdown_score == 0 and dita_score == 0:
            return 'plaintext'

        # Enhanced decision logic with DITA support
        scores = {
            'dita': dita_score,
            'asciidoc': asciidoc_score,
            'markdown': markdown_score
        }
        
        # Return format with highest score
        max_format = max(scores, key=scores.get)
        max_score = scores[max_format]
        
        if max_score > 0:
            return max_format
        else:
            return 'plaintext'