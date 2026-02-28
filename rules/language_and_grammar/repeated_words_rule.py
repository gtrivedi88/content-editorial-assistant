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
    # Compound emphasis patterns
    'more', 'less', 'again', 'and', 'or', 'the',
    'step', 'end', 'one', 'side', 'bit', 'day',
})

_COMPOUND_REPEAT_RE = re.compile(
    r'\b(\w+)\s+(?:by|to|and|or|after|over|upon)\s+\1\b', re.IGNORECASE,
)


class RepeatedWordsRule(BaseLanguageRule):
    """Flag consecutive repeated words."""

    def _get_rule_type(self) -> str:
        return 'repeated_words'

    def _collect_sentence_errors(
        self, sent_text: str, index: int, text: str,
        context: Dict[str, Any], char_offset: int,
    ) -> List[Dict[str, Any]]:
        """Find repeated-word errors in a single sentence.

        Args:
            sent_text: The sentence text to scan.
            index: Sentence index in the document.
            text: Full document text.
            context: Analysis context dict.
            char_offset: Character offset of the sentence in the document.

        Returns:
            List of error dicts for this sentence.
        """
        errors: List[Dict[str, Any]] = []
        for match in _REPEATED_RE.finditer(sent_text):
            word = match.group(1)
            if word.lower() in _ALLOWED_REPEATS:
                continue
            # Guard: skip compound "X by/to/and X" patterns like "step by step"
            if _COMPOUND_REPEAT_RE.search(sent_text):
                continue
            error = self._create_error(
                sentence=sent_text,
                sentence_index=index,
                message=f"'{word}' is repeated. Remove the duplicate word.",
                suggestions=[f"Remove the repeated '{word}'"],
                severity='medium',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(char_offset + match.start(), char_offset + match.end()),
            )
            if error:
                errors.append(error)
        return errors

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for consecutive repeated words.

        Args:
            text: Full document text.
            sentences: Pre-split sentence list.
            nlp: SpaCy language model (optional).
            context: Analysis context dict (optional).
            spacy_doc: Pre-built SpaCy Doc (optional).

        Returns:
            List of error dicts for repeated words found.
        """
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        if spacy_doc is not None:
            doc = spacy_doc
        elif nlp:
            doc = nlp(text)
        else:
            doc = None
        errors: List[Dict[str, Any]] = []

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                errors.extend(self._collect_sentence_errors(
                    sent.text, i, text, context, sent.start_char,
                ))
        else:
            for i, sentence in enumerate(sentences):
                errors.extend(self._collect_sentence_errors(
                    sentence, i, text, context, 0,
                ))

        return errors
