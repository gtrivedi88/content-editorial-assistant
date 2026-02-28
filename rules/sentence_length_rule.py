"""
Sentence Length Rule — Deterministic word-count detection.
IBM Style Guide (p.206, Paragraphs):
1. Keep sentences short for clarity and translatability.
2. Aim for 20-25 words per sentence.
3. Long sentences reduce readability and are harder to translate.
"""
from typing import List, Dict, Any, Optional

try:
    from .base_rule import BaseRule  # type: ignore
except ImportError:
    from rules.base_rule import BaseRule  # type: ignore

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Maximum recommended sentence length (IBM Style Guide)
_MAX_WORDS = 25

# Sentences shorter than this are never flagged
_MIN_WORDS_TO_CHECK = 10


class SentenceLengthRule(BaseRule):
    """Flag sentences that exceed the recommended word count."""

    def _get_rule_type(self) -> str:
        return 'sentence_length'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_length(sentence, idx, text, context, errors)
        return errors

    @staticmethod
    def _find_sentence_span(text, sentence):
        """Locate the sentence within the full text and return (start, end)."""
        pos = text.find(sentence)
        if pos >= 0:
            return (pos, pos + len(sentence))
        return (0, len(sentence))

    def _check_length(self, sentence, idx, text, context, errors):
        """Flag sentences exceeding the recommended word count."""
        words = sentence.split()
        word_count = len(words)

        if word_count <= _MAX_WORDS:
            return

        # Guard: skip headings (they can be fragments)
        if context.get('block_type') in ('heading', 'title'):
            return

        # Guard: skip sentences that are mostly code/paths
        if sentence.count('/') > 3 or sentence.count('`') > 2:
            return

        # Determine severity based on how far over the limit
        if word_count > 40:
            severity = 'high'
            guidance = 'Consider splitting into two or three sentences.'
        elif word_count > 30:
            severity = 'medium'
            guidance = 'Consider splitting into two sentences.'
        else:
            severity = 'low'
            guidance = 'Consider shortening for clarity.'

        error = self._create_error(
            sentence=sentence, sentence_index=idx,
            message=(
                f"This sentence has {word_count} words. "
                f"IBM Style recommends no more than {_MAX_WORDS} words "
                f"per sentence. {guidance}"
            ),
            suggestions=[
                f"Shorten to {_MAX_WORDS} words or fewer.",
                "Split into multiple shorter sentences.",
            ],
            severity=severity, text=text, context=context,
            flagged_text=sentence[:50] + ('...' if len(sentence) > 50 else ''),
            span=self._find_sentence_span(text, sentence),
        )
        if error:
            errors.append(error)
