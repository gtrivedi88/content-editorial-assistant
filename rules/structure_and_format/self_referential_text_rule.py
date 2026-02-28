"""
Self-Referential Text Rule — Deterministic regex-based detection.
IBM Style Guide — References section.

Checks:
  1. Avoid "this document", "this section", "this chapter", "this topic", "this page".
  2. Avoid positional "above"/"below" as references to other content.
  3. Avoid "as follows" — use "the following" instead.
  4. Avoid "previous/next/preceding/following step/section" — use specific
     step numbers or section names.

Guards: skip code blocks. Skip "above" in non-positional contexts
(e.g. "degrees above", "above zero", "rise above").
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Check 1: self-referential document phrases
_SELF_REF_PHRASES = re.compile(
    r'\bthis\s+(document|section|chapter|topic|page|module|assembly|subsection)\b',
    re.IGNORECASE,
)

# Check 2: positional "above" / "below"
_ABOVE_RE = re.compile(r'\babove\b', re.IGNORECASE)
_BELOW_RE = re.compile(r'\bbelow\b', re.IGNORECASE)

# Non-positional contexts for "above" — skip these
_ABOVE_SAFE = re.compile(
    r'(degrees?\s+above|above\s+zero|rise\s+above|above\s+average|'
    r'above\s+and\s+beyond|over\s+and\s+above|above\s+all|'
    r'see\s+above|described\s+above|mentioned\s+above|noted\s+above)',
    re.IGNORECASE,
)
# Non-positional contexts for "below" — skip these
_BELOW_SAFE = re.compile(
    r'(degrees?\s+below|below\s+zero|fall\s+below|below\s+average|'
    r'see\s+below|described\s+below|mentioned\s+below|noted\s+below)',
    re.IGNORECASE,
)

# Check 3: "as follows"
_AS_FOLLOWS_RE = re.compile(r'\bas\s+follows\b', re.IGNORECASE)

# Check 4: "previous/next/preceding/following step/section"
_POSITIONAL_STEP_RE = re.compile(
    r'\b((?:the\s+)?(?:previous|preceding|next|following|earlier|later)'
    r'\s+(?:step|section|procedure|chapter|example|table|figure|command))\b',
    re.IGNORECASE,
)


class SelfReferentialTextRule(BaseStructureRule):
    """Flag self-referential phrases, positional references, and 'as follows'."""

    def _get_rule_type(self) -> str:
        return 'self_referential_text'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_self_ref(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_above_below(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_as_follows(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_positional_step(sentence, idx, text, context, code_ranges, sent_start, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — "this document/section/chapter/topic/page"
    # ------------------------------------------------------------------
    def _check_self_ref(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _SELF_REF_PHRASES.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid self-referential phrase '{found}'. "
                    "Use specific section names or descriptive references instead."
                ),
                suggestions=[
                    f"Replace '{found}' with the actual section or document name.",
                    "Example: 'the Installation section' instead of 'this section'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — positional "above" / "below"
    # ------------------------------------------------------------------
    def _check_above_below(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _ABOVE_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            if _ABOVE_SAFE.search(sentence):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid positional reference '{found}'. "
                    "Use specific section names that remain valid when content moves."
                ),
                suggestions=[
                    f"Replace '{found}' with a specific section reference.",
                    "Example: 'See the Configuration section' instead of 'see above'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

        for match in _BELOW_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            if _BELOW_SAFE.search(sentence):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid positional reference '{found}'. "
                    "Use specific section names that remain valid when content moves."
                ),
                suggestions=[
                    f"Replace '{found}' with a specific section reference.",
                    "Example: 'See the Troubleshooting section' instead of 'see below'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 3 — "as follows"
    # ------------------------------------------------------------------
    def _check_as_follows(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _AS_FOLLOWS_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="Use 'the following' instead of 'as follows'.",
                suggestions=[
                    "Replace 'as follows' with 'the following'.",
                    "Example: 'The required settings are the following:' "
                    "instead of 'The settings are as follows:'.",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 4 — "previous/next/preceding/following step/section"
    # ------------------------------------------------------------------
    def _check_positional_step(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _POSITIONAL_STEP_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid positional reference '{found}'. "
                    "Use a specific step number or section name instead."
                ),
                suggestions=[
                    f"Replace '{found}' with a specific reference.",
                    "Example: 'step 3' or 'the Configuration section' "
                    f"instead of '{found}'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
