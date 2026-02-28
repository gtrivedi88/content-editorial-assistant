"""
Parentheses Rule — Deterministic regex-based detection.
IBM Style Guide (Page 132):
1. Use commas instead of parentheses to separate punctuation characters
   from surrounding text.
2. Avoid nested parentheses in technical documentation.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Check: Nested parentheses — "(... (...) ...)"
_NESTED_PARENS = re.compile(r'\([^)]*\([^)]*\)[^)]*\)')

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


class ParenthesesRule(BasePunctuationRule):
    """Flag parentheses usage violations."""

    def _get_rule_type(self) -> str:
        return 'parentheses'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            for match in _NESTED_PARENS.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=(
                        "Avoid nested parentheses. Rewrite the sentence "
                        "for clarity or use commas instead."
                    ),
                    suggestions=[
                        "Remove the inner parentheses and restructure.",
                    ],
                    severity='low', text=text, context=context,
                    flagged_text=match.group(0),
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)

        return errors
