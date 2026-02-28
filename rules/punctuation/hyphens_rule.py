"""
Hyphens Rule
IBM Style Guide (p. 129): Do not use a hyphen after an adverb ending in '-ly'.

Detects '-ly' adverb + hyphen + adjective patterns (e.g. "highly-parallel"
should be "highly parallel"). Prefix hyphenation is handled separately by
language_and_grammar/prefixes_rule.py.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Regex: word ending in 'ly' immediately followed by hyphen and another word
_LY_HYPHEN_RE = re.compile(r'\b(\w+ly)-(\w+)\b')

# Common words ending in -ly that are NOT adverbs (adjectives / nouns).
_NON_ADVERB_LY = frozenset({
    'ally', 'belly', 'billy', 'bully', 'chilly', 'costly', 'curly',
    'daily', 'deadly', 'early', 'elderly', 'family', 'fly', 'friendly',
    'ghastly', 'holy', 'homely', 'jelly', 'jolly', 'july', 'kindly',
    'lily', 'lively', 'lonely', 'lovely', 'manly', 'only', 'orderly',
    'rally', 'reply', 'silly', 'sly', 'supply', 'tally', 'ugly',
    'unlikely', 'weekly', 'woolly',
})

_SKIP_BLOCK_TYPES = ('code_block', 'listing', 'literal', 'inline_code')


class HyphensRule(BasePunctuationRule):
    """Flag '-ly' adverbs incorrectly hyphenated to the following word."""

    def _get_rule_type(self) -> str:
        return 'hyphens'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        """Check each sentence for -ly adverb + hyphen violations."""
        if context and context.get('block_type') in _SKIP_BLOCK_TYPES:
            return []

        ctx = context or {}
        code_ranges = ctx.get("inline_code_ranges", [])
        doc = self._build_doc(nlp, text, spacy_doc)
        errors: List[Dict[str, Any]] = []

        for i, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            for match in _LY_HYPHEN_RE.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                error = self._check_match(match, doc, sentence, i, text, ctx)
                if error is not None:
                    errors.append(error)

        return errors

    # ------------------------------------------------------------------
    def _check_match(self, match, doc, sentence, idx, text, ctx):
        """Validate a single regex match and return an error dict or None."""
        ly_word = match.group(1)
        if not self._is_ly_adverb(doc, ly_word):
            return None

        adj_word = match.group(2)
        found = f"{ly_word}-{adj_word}"
        corrected = f"{ly_word} {adj_word}"

        return self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message=(
                f"Do not use a hyphen after an adverb ending in "
                f"'-ly': '{found}' \u2192 '{corrected}'."
            ),
            suggestions=[f"Write '{corrected}' without the hyphen."],
            severity='medium',
            text=text,
            context=ctx,
            span=(match.start(), match.end()),
            flagged_text=found,
        )

    @staticmethod
    def _build_doc(nlp, text, spacy_doc):
        """Return the SpaCy doc if NLP is available, else None."""
        if not nlp:
            return None
        return spacy_doc if spacy_doc is not None else nlp(text)

    @staticmethod
    def _is_ly_adverb(doc, ly_word: str) -> bool:
        """Return True if *ly_word* is an adverb. Uses SpaCy when available."""
        if doc is None:
            return ly_word.lower() not in _NON_ADVERB_LY
        lower = ly_word.lower()
        for token in doc:
            if token.text.lower() == lower:
                return token.pos_ == 'ADV'
        return False
