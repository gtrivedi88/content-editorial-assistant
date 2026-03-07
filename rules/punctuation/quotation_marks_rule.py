"""
Quotation Marks Rule — Deterministic regex-based detection.
IBM Style Guide (Page 136):
1. Place periods and commas inside closing quotation marks.
2. Do not use curly/smart quotes — use straight quotes in all blocks.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Check 1: Period or comma placed OUTSIDE closing quotation mark
# Matches: "word". or "word",  (punctuation after the closing quote)
_PUNCT_OUTSIDE_QUOTE = re.compile(
    r'["\u201d\u2019]'   # closing double or single quote
    r'\s*'               # optional whitespace
    r'([.,])'            # period or comma outside
)

# Check 2: Curly/smart quotes (should be straight in code)
_SMART_QUOTES = re.compile(r'[\u201c\u201d\u2018\u2019]')

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


class QuotationMarksRule(BasePunctuationRule):
    """Flag quotation mark usage violations."""

    def _get_rule_type(self) -> str:
        return 'quotation_marks'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        block_type = context.get('block_type', '')
        errors: List[Dict[str, Any]] = []

        if block_type not in _SKIP_BLOCKS:
            self._check_punct_outside(sentences, text, context, errors)

        # Check 2: Smart/curly quotes should never appear in AsciiDoc source.
        # They cause rendering issues in all block types, not just code.
        self._check_smart_quotes(sentences, text, context, errors)

        return errors

    def _check_punct_outside(self, sentences, text, context, errors):
        """Check 1: Flag punctuation placed outside closing quotes."""
        code_ranges = context.get("inline_code_ranges", [])
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            for match in _PUNCT_OUTSIDE_QUOTE.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                punct = match.group(1)
                label = 'period' if punct == '.' else 'comma'
                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=(
                        f"Place the {label} inside the closing "
                        f"quotation mark."
                    ),
                    suggestions=[
                        "Move the punctuation mark inside the quotes."
                    ],
                    severity='medium', text=text, context=context,
                    flagged_text=match.group(0),
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)

    def _check_smart_quotes(self, sentences, text, context, errors):
        """Check 2: Flag curly/smart quotes in all blocks.

        Smart quotes cause rendering issues in AsciiDoc source and
        should always be replaced with straight quotes.
        """
        for idx, sentence in enumerate(sentences):
            for match in _SMART_QUOTES.finditer(sentence):
                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=(
                        "Use straight quotation marks in code, "
                        "not curly (smart) quotes."
                    ),
                    suggestions=[
                        "Replace smart quotes with straight quotes."
                    ],
                    severity='medium', text=text, context=context,
                    flagged_text=match.group(0),
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)
