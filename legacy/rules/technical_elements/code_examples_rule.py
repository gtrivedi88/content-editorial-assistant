"""
Code and Command Examples Rule — Deterministic regex detection.
IBM Style Guide (p.235-237):
1. If you use an inline example, ensure it is part of a complete sentence,
   not just a sentence fragment.
   WRONG: For example, ``db2 ping hostdb 5 times``.
   RIGHT: For example, enter ``db2 ping hostdb 5 times``.
2. Use a complete introductory sentence or an acceptable fragment like
   "For example:" with a colon to introduce examples.
3. Do not start a sentence before an example and continue it after.
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# "For example," directly followed by backtick code without a verb in between.
# WRONG: "For example, `db2 ping hostdb 5 times`."
# RIGHT: "For example, enter `db2 ping hostdb 5 times`."
_EXAMPLE_FRAGMENT_RE = re.compile(
    r'\b(for\s+example),?\s+`[^`]+`',
    re.IGNORECASE,
)

# Guard: legitimate forms that HAVE a verb between "For example" and the code.
_EXAMPLE_WITH_VERB_RE = re.compile(
    r'\bfor\s+example,?\s+'
    r'(?:enter|type|run|use|issue|specify|include|set|add|write|create|execute)\s',
    re.IGNORECASE,
)

# Sentence fragment ending with just "example:" without a descriptive verb.
# WRONG: "The following example:"
# RIGHT: "The following example demonstrates how to..."
# Guard: "For example:" IS acceptable per IBM (sentence fragment with colon).
_BARE_EXAMPLE_INTRO_RE = re.compile(
    r'^((?:the\s+)?following\s+(?:code\s+)?example)\s*:\s*$',
    re.IGNORECASE,
)

# Inline example not part of a complete sentence.
# Detects: "Such as `code`." or "Like `code`." — fragments, not complete sentences.
_INLINE_FRAGMENT_RE = re.compile(
    r'\b(such\s+as|like)\s+`[^`]+`\s*[.!]?\s*$',
    re.IGNORECASE,
)


class CodeExamplesRule(BaseTechnicalRule):
    """Flag code and command example formatting issues."""

    def _get_rule_type(self) -> str:
        return 'technical_code_examples'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_example_fragment(sentence, idx, text, context, errors)
            self._check_bare_example_intro(sentence, idx, text, context, errors)
        return errors

    def _check_example_fragment(self, sentence, idx, text, context, errors):
        """Flag 'For example, `code`.' without a verb — incomplete sentence."""
        for match in _EXAMPLE_FRAGMENT_RE.finditer(sentence):
            # Guard: skip if there IS a verb between "For example" and the code
            if _EXAMPLE_WITH_VERB_RE.search(sentence):
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    "An inline example must be part of a complete sentence. "
                    "Add a verb such as 'enter', 'type', or 'run' before the "
                    "inline code."
                ),
                suggestions=[
                    "For example, enter `...`.",
                    "For example, type `...`.",
                ],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_bare_example_intro(self, sentence, idx, text, context, errors):
        """Flag 'The following example:' — use a complete introductory sentence."""
        match = _BARE_EXAMPLE_INTRO_RE.match(sentence.strip())
        if not match:
            return

        intro = match.group(1)
        error = self._create_error(
            sentence=sentence, sentence_index=idx,
            message=(
                f"Use a complete introductory sentence instead of "
                f"'{intro}:'. Describe what the example demonstrates."
            ),
            suggestions=[
                f"The following example demonstrates how to ...",
                f"The following example shows ...",
            ],
            severity='low', text=text, context=context,
            flagged_text=sentence.strip(),
            span=(0, len(sentence.strip())),
        )
        if error:
            errors.append(error)
