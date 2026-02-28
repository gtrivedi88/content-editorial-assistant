"""
Source Map — tracks character position mappings through text transformations.

Used to convert error spans from cleaned-text coordinates back to raw-text
coordinates so underlines land precisely on the correct text in the editor.

Format: source_map[i] = position in raw text that produced character i in cleaned text.

Example:
    Raw:     "This is **bold** text"    (positions 0-21)
    Cleaned: "This is bold text"        (positions 0-17)
    Map:     [0,1,2,3,4,5,6,7, 10,11,12,13, 16,17,18,19]
"""

import re


class SourceMap:
    """Tracks character position mappings through sequential text transformations."""

    def __init__(self, text):
        self.text = text
        self.positions = list(range(len(text)))

    def apply_sub(self, pattern, replacement):
        """Apply regex substitution while tracking character positions.

        Handles two cases:
        - Group capture (e.g. r'\\1'): output chars inherit the captured group's positions
        - Fixed string (e.g. 'placeholder'): all output chars map to match start position
        """
        if not self.text:
            return

        is_group_ref = bool(re.match(r'^\\(\d+)$', replacement))
        group_num = int(replacement[1:]) if is_group_ref else 0

        compiled = re.compile(pattern)
        new_text = []
        new_positions = []
        last_end = 0

        for match in compiled.finditer(self.text):
            # Copy text before match (unchanged)
            new_text.append(self.text[last_end:match.start()])
            new_positions.extend(self.positions[last_end:match.start()])

            if is_group_ref:
                # Keep the captured group's text and positions
                group = match.group(group_num)
                group_start = match.start(group_num)
                group_end = match.end(group_num)
                if group is not None:
                    new_text.append(group)
                    new_positions.extend(self.positions[group_start:group_end])
            else:
                # Fixed replacement string — all chars map to match start
                match_start_pos = self.positions[match.start()] if match.start() < len(self.positions) else 0
                new_text.append(replacement)
                new_positions.extend([match_start_pos] * len(replacement))

            last_end = match.end()

        # Copy remaining text after last match
        new_text.append(self.text[last_end:])
        new_positions.extend(self.positions[last_end:])

        self.text = ''.join(new_text)
        self.positions = new_positions

    def apply_delete(self, pattern):
        """Delete all matches, removing their characters and position entries."""
        if not self.text:
            return

        compiled = re.compile(pattern)
        new_text = []
        new_positions = []
        last_end = 0

        for match in compiled.finditer(self.text):
            # Copy text before match
            new_text.append(self.text[last_end:match.start()])
            new_positions.extend(self.positions[last_end:match.start()])
            last_end = match.end()

        # Copy remaining text
        new_text.append(self.text[last_end:])
        new_positions.extend(self.positions[last_end:])

        self.text = ''.join(new_text)
        self.positions = new_positions

    def collapse_spaces(self):
        """Collapse runs of 2+ whitespace characters to a single space."""
        if not self.text:
            return

        new_text = []
        new_positions = []
        i = 0
        while i < len(self.text):
            if self.text[i] in ' \t' and i + 1 < len(self.text) and self.text[i + 1] in ' \t':
                # Start of a multi-space run — keep only the first space
                new_text.append(' ')
                new_positions.append(self.positions[i])
                # Skip all remaining spaces in this run
                while i < len(self.text) and self.text[i] in ' \t':
                    i += 1
            else:
                new_text.append(self.text[i])
                new_positions.append(self.positions[i])
                i += 1

        self.text = ''.join(new_text)
        self.positions = new_positions

    def clean_space_before_punct(self):
        """Remove spaces immediately before punctuation (.,;:).

        These are artifacts from prior deletions (e.g., removing a URL before a period).
        """
        if not self.text:
            return

        new_text = []
        new_positions = []
        i = 0
        while i < len(self.text):
            if self.text[i] in ' \t':
                # Look ahead for punctuation (skip all spaces before it)
                j = i
                while j < len(self.text) and self.text[j] in ' \t':
                    j += 1
                if j < len(self.text) and self.text[j] in '.,;:':
                    # Skip these spaces — they precede punctuation
                    i = j
                    continue
            new_text.append(self.text[i])
            new_positions.append(self.positions[i])
            i += 1

        self.text = ''.join(new_text)
        self.positions = new_positions

    def strip(self):
        """Strip leading and trailing whitespace, adjusting the position map."""
        if not self.text:
            return

        # Find first non-whitespace
        start = 0
        while start < len(self.text) and self.text[start] in ' \t\n\r':
            start += 1

        # Find last non-whitespace
        end = len(self.text)
        while end > start and self.text[end - 1] in ' \t\n\r':
            end -= 1

        self.text = self.text[start:end]
        self.positions = self.positions[start:end]

    @property
    def result(self):
        """Return (cleaned_text, source_map_array)."""
        return self.text, list(self.positions)
