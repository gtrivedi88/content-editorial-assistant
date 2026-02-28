"""
Punctuation and Symbols Rule
IBM Style Guide (p. 117): Do not use symbols instead of words in general text.

Flags '&' (use "and"), '#' (use "number sign"), and '+' used as "and".
Skips code blocks, proper nouns (R&D, AT&T), and HTML entities.
"""
import re
from typing import List, Dict, Any, Optional
from .base_punctuation_rule import BasePunctuationRule

# Each entry: (compiled regex, symbol display, replacement word)
_SYMBOL_CHECKS = [
    (re.compile(r'(?<!\w)&(?!\w*;)'), '&', 'and'),
    (re.compile(r'(?<![#\d])#(?!\d)'), '#', 'number sign'),
    (re.compile(r'(?<!\d)\+(?!\d)'), '+', 'and'),
]

# Known proper-noun patterns that legitimately contain symbols
_PROPER_NOUN_RE = re.compile(
    r'\b(?:AT&T|R&D|H&R|S&P|B&B|P&L|Q&A|C\+\+|G\+\+)\b', re.IGNORECASE
)

# HTML entity pattern: &amp; &lt; &#123; etc.
_HTML_ENTITY_RE = re.compile(r'&\w+;|&#\d+;|&#x[\da-fA-F]+;')

_SKIP_BLOCK_TYPES = ('code_block', 'listing', 'literal', 'inline_code')


class PunctuationAndSymbolsRule(BasePunctuationRule):
    """Flag symbols used in place of words in general text."""

    def _get_rule_type(self) -> str:
        return 'punctuation_and_symbols'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        """Check each sentence for discouraged symbol usage."""
        if context and context.get('block_type') in _SKIP_BLOCK_TYPES:
            return []

        ctx = context or {}
        errors: List[Dict[str, Any]] = []

        for i, sentence in enumerate(sentences):
            for pattern, symbol, word in _SYMBOL_CHECKS:
                for match in pattern.finditer(sentence):
                    error = self._check_match(
                        match, symbol, word, sentence, i, text, ctx,
                    )
                    if error is not None:
                        errors.append(error)

        return errors

    # ------------------------------------------------------------------
    def _check_match(self, match, symbol, word, sentence, idx, text, ctx):
        """Return an error dict for the match, or None if it should be skipped."""
        # Guard: proper nouns containing the symbol (AT&T, R&D, C++, etc.)
        for pn in _PROPER_NOUN_RE.finditer(sentence):
            if pn.start() <= match.start() < pn.end():
                return None

        # Guard: HTML entities (&amp; etc.)
        for ent in _HTML_ENTITY_RE.finditer(sentence):
            if ent.start() <= match.start() < ent.end():
                return None

        return self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message=(
                f"Do not use the symbol '{symbol}' in general text. "
                f"Use '{word}' instead."
            ),
            suggestions=[f"Replace '{symbol}' with '{word}'."],
            severity='medium',
            text=text,
            context=ctx,
            span=(match.start(), match.end()),
            flagged_text=symbol,
        )
