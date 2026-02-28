"""
Contractions Rule
Based on IBM Style Guide (p.101): Do not use contractions in technical documentation.
Detects contractions using regex with SpaCy-based possessive filtering.
"""
import re
from typing import List, Dict, Any

from .base_language_rule import BaseLanguageRule


# Mapping of common contractions to their expanded forms.
CONTRACTION_EXPANSIONS = {
    "don't": "do not", "doesn't": "does not", "didn't": "did not",
    "can't": "cannot", "couldn't": "could not", "wouldn't": "would not",
    "shouldn't": "should not", "won't": "will not", "isn't": "is not",
    "aren't": "are not", "wasn't": "was not", "weren't": "were not",
    "hasn't": "has not", "haven't": "have not", "hadn't": "had not",
    "mustn't": "must not", "needn't": "need not",
    "it's": "it is", "that's": "that is", "there's": "there is",
    "here's": "here is", "what's": "what is", "who's": "who is",
    "he's": "he is", "she's": "she is",
    "i'm": "I am", "you're": "you are", "we're": "we are", "they're": "they are",
    "i've": "I have", "you've": "you have", "we've": "we have", "they've": "they have",
    "i'll": "I will", "you'll": "you will", "we'll": "we will", "they'll": "they will",
    "he'll": "he will", "she'll": "she will", "it'll": "it will",
    "i'd": "I would", "you'd": "you would", "we'd": "we would", "they'd": "they would",
    "he'd": "he would", "she'd": "she would",
    "let's": "let us",
}

# Regex pattern to find apostrophe-containing words (straight or curly quotes).
_CONTRACTION_RE = re.compile(r"\b\w+['\u2019]\w+\b")


class ContractionsRule(BaseLanguageRule):
    """Detects contractions in technical documentation."""

    def _get_rule_type(self) -> str:
        return 'contractions'

    # ------------------------------------------------------------------
    # Main analysis entry point
    # ------------------------------------------------------------------
    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """Scan *text* for contractions and return a list of error dicts."""

        # Guard: skip code blocks
        if context and context.get('block_type') in (
            'code_block', 'listing', 'literal', 'inline_code',
        ):
            return []

        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)

        errors: List[Dict[str, Any]] = []

        for match in _CONTRACTION_RE.finditer(text):
            match_text = match.group()
            start = match.start()
            end = match.end()

            # Find the corresponding SpaCy token(s) for this span.
            if self._is_possessive(doc, start, end):
                continue

            # Look up the expansion (normalise curly apostrophe first).
            key = match_text.lower().replace('\u2019', "'")

            # Guard: year abbreviations ('90s, '20s)
            if re.match(r"^'\d", key) or re.match(r"^\d+['\u2019]s$", key):
                continue

            expansion = CONTRACTION_EXPANSIONS.get(key)
            message, suggestions = self._build_message(match_text, expansion)

            # Find which sentence this contraction belongs to.
            sent_index = self._sentence_index_for_offset(doc, start)

            error = self._create_error(
                sentence=self._sentence_text_for_offset(doc, start) or text,
                sentence_index=sent_index,
                message=message,
                suggestions=suggestions,
                severity='low',
                text=text,
                context=context,
                flagged_text=match_text,
                span=(start, end),
            )
            if error is not None:
                errors.append(error)

        return errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _build_message(match_text: str, expansion: str) -> tuple:
        """Build the error message and suggestions for a contraction match.

        Args:
            match_text: The contraction text found in the document.
            expansion: The expanded form, or None if not in the lookup table.

        Returns:
            Tuple of (message, suggestions list).
        """
        if expansion:
            message = (
                f"Do not use the contraction '{match_text}'. "
                f"Use '{expansion}' instead."
            )
            suggestions = [match_text.replace(match_text, expansion)]
        else:
            message = (
                f"Do not use the contraction '{match_text}'. "
                f"Use the expanded form instead."
            )
            suggestions = ["Expand the contraction"]
        return message, suggestions

    @staticmethod
    def _is_possessive(doc, start: int, end: int) -> bool:
        """Return True if the span corresponds to a possessive, not a contraction."""
        for token in doc:
            # Check tokens that overlap with the match span.
            if token.idx >= end or token.idx + len(token.text) <= start:
                continue
            if token.tag_ == 'POS' or token.dep_ in ('case', 'poss'):
                return True
            # SpaCy sometimes splits "John's" into "John" + "'s"; check
            # following tokens within the span as well.
        return False

    @staticmethod
    def _sentence_index_for_offset(doc, offset: int) -> int:
        """Return the zero-based sentence index that contains *offset*."""
        for idx, sent in enumerate(doc.sents):
            if sent.start_char <= offset < sent.end_char:
                return idx
        return 0

    @staticmethod
    def _sentence_text_for_offset(doc, offset: int) -> str:
        """Return the sentence text that contains *offset*."""
        for sent in doc.sents:
            if sent.start_char <= offset < sent.end_char:
                return sent.text
        return ''
