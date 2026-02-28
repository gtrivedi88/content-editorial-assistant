"""
Repeated Words Rule — Deterministic regex-based detection.
Source: Red Hat Vale RepeatedWords rule.

Detects consecutive repeated words such as "the the", "a a", "is is".
"""
import re
from typing import List, Dict, Any, Optional

from .base_language_rule import BaseLanguageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

_REPEATED_RE = re.compile(r'\b(\w+)\s+\1\b', re.IGNORECASE)

# Words that are legitimately repeated in some constructs
_ALLOWED_REPEATS = frozenset({
    'had', 'that', 'can', 'do', 'will', 'very',
    'bye', 'no', 'so', 'much', 'far', 'long',
})


class RepeatedWordsRule(BaseLanguageRule):
    """Flag consecutive repeated words."""

    def _get_rule_type(self) -> str:
        return 'repeated_words'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        doc = spacy_doc if (spacy_doc is not None) else (nlp(text) if nlp else None)
        errors: List[Dict[str, Any]] = []

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                for match in _REPEATED_RE.finditer(sent.text):
                    word = match.group(1)
                    if word.lower() in _ALLOWED_REPEATS:
                        continue
                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"'{word}' is repeated. Remove the duplicate word.",
                        suggestions=[f"Remove the repeated '{word}'"],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)
        else:
            for i, sentence in enumerate(sentences):
                for match in _REPEATED_RE.finditer(sentence):
                    word = match.group(1)
                    if word.lower() in _ALLOWED_REPEATS:
                        continue
                    found = match.group(0)
                    error = self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"'{word}' is repeated. Remove the duplicate word.",
                        suggestions=[f"Remove the repeated '{word}'"],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(match.start(), match.end()),
                    )
                    if error:
                        errors.append(error)

        return errors
