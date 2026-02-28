"""
Colons Rule — Deterministic regex-based detection.
IBM Style Guide (Page 121):
1. Do not insert a space before a colon.
2. Do not use a colon at the end of a heading or title.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Check 1: Space before colon (but not after http/https or time patterns)
_SPACE_BEFORE_COLON = re.compile(r'(?<!https)(?<!http)\s+:(?!\S*//)')

# Guard: time patterns (2:30, 18:00)
_TIME_RE = re.compile(r'\b\d{1,2}:\d{2}\b')

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


class ColonsRule(BasePunctuationRule):
    """Flag colon usage violations."""

    def _get_rule_type(self) -> str:
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            self._check_space_before_colon(
                sentence, idx, text, context, code_ranges, errors,
            )
        self._check_heading_colon(text, context, errors)
        return errors

    def _check_space_before_colon(self, sentence, idx, text, context,
                                  code_ranges, errors):
        """Check 1: Flag spaces before colons."""
        sent_start = text.find(sentence)
        for match in _SPACE_BEFORE_COLON.finditer(sentence):
            if _TIME_RE.search(
                sentence[max(0, match.start() - 3):match.end() + 3]
            ):
                continue
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Do not insert a space before a colon.",
                suggestions=["Remove the space before the colon."],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0).strip(),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_heading_colon(self, text, context, errors):
        """Check 2: Flag colons at end of headings."""
        if context.get('block_type') not in ('heading', 'title'):
            return
        stripped = text.rstrip()
        if stripped.endswith(':'):
            error = self._create_error(
                sentence=text, sentence_index=0,
                message="Do not use a colon at the end of a heading or title.",
                suggestions=["Remove the trailing colon from the heading."],
                severity='medium', text=text, context=context,
                flagged_text=':', span=(len(stripped) - 1, len(stripped)),
            )
            if error:
                errors.append(error)
