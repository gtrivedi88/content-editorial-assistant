"""
Headings Rule — Deterministic regex-based detection.
IBM Style Guide (p. 181-183):
1. Do not end a heading with a period or colon.
2. Do not use leading zeros in numbered headings (Chapter 02 → Chapter 2).
3. Do not use dashes or parentheses to separate heading from subheading;
   use a colon instead.

Guards: skip code blocks, inline code.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

_HEADING_BLOCKS = frozenset([
    'heading', 'heading1', 'heading2', 'heading3',
    'heading4', 'heading5', 'heading6',
    'title', 'section_title', 'document_title',
])

# Check 1: heading text ending with a period
_ENDS_WITH_PERIOD = re.compile(r'\.\s*$')

# Section numbering at start of heading (e.g. "5.2.", "1.3.1.", "Chapter 5.",
# "Appendix A.")
_SECTION_NUMBER_RE = re.compile(
    r'^(?:(?:Chapter|Appendix|Part|Section)\s+\w+\.(?:\s|$)|(?:\d+\.)+(?:\s|$))',
    re.IGNORECASE,
)

# Check 2: heading text ending with a colon
_ENDS_WITH_COLON = re.compile(r':\s*$')

# Check 3: leading zeros in numbered headings (Chapter 02, Step 01, 04.)
_LEADING_ZERO = re.compile(
    r'\b(Chapter|Step|Part|Section|Appendix|Lesson|Unit|Exercise)\s+0(\d)',
    re.IGNORECASE,
)
# Standalone leading-zero number at start (e.g., "04. AI solutions")
_LEADING_ZERO_START = re.compile(r'^0(\d+)\.\s+')

# Check 4: dash/parenthesis as heading-subheading separator
_DASH_SEPARATOR = re.compile(r'\s+[-–—]\s+')
_PAREN_SEPARATOR = re.compile(r'\s+\([^)]+\)\s*$')


class HeadingsRule(BaseStructureRule):
    """Flag heading formatting violations."""

    def _get_rule_type(self) -> str:
        return 'headings'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        block_type = context.get('block_type', 'paragraph')

        if block_type in _SKIP_BLOCKS:
            return []

        # Only apply to heading blocks
        if block_type not in _HEADING_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_trailing_period(sentence, idx, text, context, errors)
            self._check_trailing_colon(sentence, idx, text, context, errors)
            self._check_leading_zeros(sentence, idx, text, context, errors)
            self._check_dash_separator(sentence, idx, text, context, errors)
        return errors

    # ------------------------------------------------------------------
    def _check_trailing_period(self, sentence, idx, text, context, errors):
        if _ENDS_WITH_PERIOD.search(sentence):
            # Guard: skip URLs or file extensions at end
            if re.search(r'\.\w{2,4}\s*$', sentence):
                return
            # Guard: section numbering like "5.2. Configuring..."
            if _SECTION_NUMBER_RE.match(sentence):
                return
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Do not end a heading with a period.",
                suggestions=["Remove the period from the end of the heading."],
                severity='medium', text=text, context=context,
                flagged_text='.', span=(len(sentence.rstrip()) - 1, len(sentence.rstrip())),
            )
            if error:
                errors.append(error)

    def _check_trailing_colon(self, sentence, idx, text, context, errors):
        if _ENDS_WITH_COLON.search(sentence):
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Do not end a heading with a colon.",
                suggestions=["Remove the colon from the end of the heading."],
                severity='medium', text=text, context=context,
                flagged_text=':', span=(len(sentence.rstrip()) - 1, len(sentence.rstrip())),
            )
            if error:
                errors.append(error)

    def _check_leading_zeros(self, sentence, idx, text, context, errors):
        for match in _LEADING_ZERO.finditer(sentence):
            label = match.group(1)
            digit = match.group(2)
            found = match.group(0)
            corrected = f"{label} {digit}"
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=f"Do not use leading zeros in heading numbers: '{found}' → '{corrected}'.",
                suggestions=[f"Write '{corrected}' instead of '{found}'."],
                severity='medium', text=text, context=context,
                flagged_text=found, span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

        match = _LEADING_ZERO_START.match(sentence)
        if match:
            digit = match.group(1)
            found = f"0{digit}."
            corrected = f"{digit}."
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=f"Do not use leading zeros: '{found}' → '{corrected}'.",
                suggestions=[f"Write '{corrected}' without the leading zero."],
                severity='medium', text=text, context=context,
                flagged_text=found, span=(0, match.end()),
            )
            if error:
                errors.append(error)

    def _check_dash_separator(self, sentence, idx, text, context, errors):
        match = _DASH_SEPARATOR.search(sentence)
        if match:
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Use a colon to separate a heading from a subheading, not a dash.",
                suggestions=["Replace the dash with a colon: ': '."],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0).strip(),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
