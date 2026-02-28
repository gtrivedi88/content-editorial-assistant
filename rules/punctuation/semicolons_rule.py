"""
Semicolons Rule — Deterministic regex-based detection.
IBM Style Guide (Page 139):
1. Use a semicolon between independent clauses connected by conjunctive
   adverbs (however, therefore, consequently, etc.).
2. Sentences longer than 32 words with semicolons may need splitting.
"""
import re
from typing import List, Dict, Any, Optional
from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Conjunctive adverbs that should be preceded by a semicolon, not a comma
_CONJUNCTIVE_ADVERBS = {
    'however', 'therefore', 'consequently', 'furthermore', 'moreover',
    'nevertheless', 'otherwise', 'meanwhile', 'instead', 'likewise',
    'similarly', 'specifically', 'still', 'subsequently', 'accordingly',
}

# Check: comma before conjunctive adverb (should be semicolon)
# Matches: ", however" or ", therefore" etc.
_COMMA_BEFORE_CONJ_ADV = re.compile(
    r',\s+(' + '|'.join(_CONJUNCTIVE_ADVERBS) + r')\b',
    re.IGNORECASE,
)

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


class SemicolonsRule(BasePunctuationRule):
    """Flag semicolon usage violations."""

    def _get_rule_type(self) -> str:
        return 'semicolons'

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
            for match in _COMMA_BEFORE_CONJ_ADV.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                adverb = match.group(1)
                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=(
                        f"Use a semicolon before the conjunctive adverb "
                        f"'{adverb}', not a comma."
                    ),
                    suggestions=[
                        f"Change ', {adverb}' to '; {adverb}'.",
                    ],
                    severity='medium', text=text, context=context,
                    flagged_text=match.group(0),
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)

        return errors
