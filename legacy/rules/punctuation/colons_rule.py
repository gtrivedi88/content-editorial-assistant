"""
Colons Rule — Deterministic regex-based detection.
IBM Style Guide (Page 121):
1. Do not insert a space before a colon.
2. Do not use a colon at the end of a heading or title.
"""
import re
from typing import List, Dict, Any, Optional
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

        errors: List[Dict[str, Any]] = []

        # Check 1: Space before colon
        for idx, sentence in enumerate(sentences):
            for match in _SPACE_BEFORE_COLON.finditer(sentence):
                # Guard: skip time patterns
                if _TIME_RE.search(sentence[max(0, match.start()-3):match.end()+3]):
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

        # Check 2: Colon at end of heading
        if context.get('block_type') in ('heading', 'title'):
            stripped = text.rstrip()
            if stripped.endswith(':'):
                error = self._create_error(
                    sentence=text, sentence_index=0,
                    message="Do not use a colon at the end of a heading or title.",
                    suggestions=["Remove the trailing colon from the heading."],
                    severity='medium', text=text, context=context,
                    flagged_text=':', span=(len(stripped)-1, len(stripped)),
                )
                if error:
                    errors.append(error)

        return errors
