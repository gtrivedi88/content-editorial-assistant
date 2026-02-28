"""
Programming Elements Rule — Deterministic regex detection.
IBM Style Guide (p.254-255):
1. Do not use a keyword as a verb: 'DROP the object' is wrong.
2. Do not add a verb ending to a keyword: 'LOADed', 'XCTLed' are wrong.
3. Specify the keyword type after the keyword: 'the DROP statement'.
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# ALL-CAPS keyword (3+ chars) used as a verb with an object after it.
# Same pattern as commands but specifically for programming keywords.
# "DROP the object", "LOAD the module", "SELECT the record"
_KEYWORD_AS_VERB_RE = re.compile(
    r'\b([A-Z]{3,})\s+(?:the|a|an|this|that|all|some|your|my)\s+\w+',
)

# ALL-CAPS keyword with verb ending: LOADed, XCTLed, DELETEd, CREATEing
_KEYWORD_VERB_SUFFIX_RE = re.compile(
    r'\b([A-Z]{3,})(ed|ing|s)\b',
)

# Common programming keywords that should NOT be used as verbs
_PROGRAMMING_KEYWORDS = frozenset([
    'DROP', 'LOAD', 'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE',
    'ALTER', 'EXECUTE', 'COMMIT', 'ROLLBACK', 'GRANT', 'REVOKE',
    'FETCH', 'MERGE', 'TRUNCATE', 'BACKUP', 'RESTORE', 'IMPORT',
    'EXPORT', 'COMPILE', 'XCTL', 'REORG', 'BIND', 'REBIND',
])

# Safe words that happen to be ALL-CAPS but are NOT programming keywords
_SAFE_WORDS = frozenset([
    'THE', 'AND', 'FOR', 'BUT', 'NOT', 'ALL', 'ARE', 'WAS', 'HAS', 'HAD',
    'CAN', 'MAY', 'USE', 'SET', 'GET', 'PUT', 'ADD', 'RUN', 'SEE', 'TRY',
    'LET', 'SAY', 'END', 'NEW', 'OLD', 'OUR', 'ANY', 'ITS', 'YOU', 'HOW',
    'API', 'SDK', 'URL', 'SQL', 'XML', 'CSS', 'HTML', 'JSON', 'YAML',
    'HTTP', 'HTTPS', 'REST', 'SOAP', 'IBM', 'CLI', 'GUI', 'IDE',
    'NOTE', 'IMPORTANT', 'WARNING', 'CAUTION', 'TIP', 'DANGER',
    'AND', 'ANDING', 'ORED',  # Boolean operators used as verbs are OK per IBM
])


class ProgrammingElementsRule(BaseTechnicalRule):
    """Flag programming keywords used as verbs or with verb endings."""

    def _get_rule_type(self) -> str:
        return 'technical_programming_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_keyword_as_verb(sentence, idx, text, context, errors)
            self._check_keyword_verb_suffix(sentence, idx, text, context, errors)
        return errors

    def _check_keyword_as_verb(self, sentence, idx, text, context, errors):
        """Flag ALL-CAPS programming keywords used as verbs."""
        for match in _KEYWORD_AS_VERB_RE.finditer(sentence):
            keyword = match.group(1)

            if keyword in _SAFE_WORDS:
                continue
            # Only flag known programming keywords to avoid false positives
            if keyword not in _PROGRAMMING_KEYWORDS:
                continue
            if _in_backticks(sentence, match.start()):
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the keyword '{keyword}' as a verb. "
                    f"Use a descriptive verb and refer to the {keyword} statement."
                ),
                suggestions=[
                    f"Issue the {keyword} statement.",
                    f"Use the {keyword} command to ...",
                ],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_keyword_verb_suffix(self, sentence, idx, text, context, errors):
        """Flag ALL-CAPS keywords with verb endings: 'LOADed', 'XCTLed'."""
        for match in _KEYWORD_VERB_SUFFIX_RE.finditer(sentence):
            keyword = match.group(1)
            suffix = match.group(2)

            if keyword in _SAFE_WORDS:
                continue
            if _in_backticks(sentence, match.start()):
                continue

            full_word = match.group(0)
            lower_form = keyword.lower() + suffix
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not add a verb ending to the keyword '{keyword}'. "
                    f"Write '{lower_form}' or rephrase the sentence."
                ),
                suggestions=[
                    lower_form,
                    f"Use the {keyword} command.",
                ],
                severity='medium', text=text, context=context,
                flagged_text=full_word,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


def _in_backticks(text: str, pos: int) -> bool:
    before = text[:pos]
    return before.count('`') % 2 != 0
