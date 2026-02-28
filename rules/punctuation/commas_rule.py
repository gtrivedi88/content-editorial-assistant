"""
Commas Rule — Deterministic regex + SpaCy detection.
IBM Style Guide (Page 123):
1. Use a serial comma (Oxford comma) before the conjunction in a series of 3+.
2. Do not join independent clauses with 'then' without a comma or semicolon.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Check 2: "then" joining clauses without preceding comma/semicolon
# Matches: "word then word" where no comma or semicolon precedes "then"
_THEN_NO_COMMA = re.compile(r'(?<![,;])\s+then\s+(?!again\b)', re.IGNORECASE)

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


class CommasRule(BasePunctuationRule):
    """Flag comma usage violations."""

    def _get_rule_type(self) -> str:
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            self._check_then_without_comma(sentence, idx, text, context, errors)

        return errors

    def _check_then_without_comma(self, sentence, idx, text, context, errors):
        """Flag 'then' joining clauses without a preceding comma or semicolon."""
        code_ranges = context.get("inline_code_ranges", [])
        sent_start = text.find(sentence)
        for match in _THEN_NO_COMMA.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            # Guard: skip if "then" is at sentence start (introductory word)
            if match.start() < 2:
                continue
            # Guard: skip "if...then" conditional patterns
            sent_before = sentence[:match.start()].lower()
            if 'if ' in sent_before:
                continue
            if 'when ' in sent_before:
                continue
            if 'after ' in sent_before:
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    "'Then' is not a coordinating conjunction. "
                    "Use a semicolon or comma before 'then' when "
                    "joining independent clauses."
                ),
                suggestions=[
                    "Add a semicolon before 'then': '; then'",
                    "Add a comma and conjunction: ', and then'",
                ],
                severity='medium', text=text, context=context,
                flagged_text='then',
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
