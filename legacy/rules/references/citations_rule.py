"""
Citations and References Rule — Deterministic regex + YAML detection.
IBM Style Guide (p. 217-223):
1. Avoid generic link text like "click here" or "see here".
2. Use lowercase for cross-reference terms (chapter, section, figure, etc.)
   when referring to document parts generically or in cross-references.
3. Do not abbreviate chapter, part, or volume in cross-references.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional

from .base_references_rule import BaseReferencesRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Guard: inline code spans
_INLINE_CODE = re.compile(r'`[^`]+`')


def _load_config() -> Dict[str, Any]:
    """Load citations config from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'citations_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Check 1: Problematic link text phrases
_PROBLEMATIC_PHRASES = _CONFIG.get('problematic_link_phrases', [
    'click here', 'see here', 'go here', 'this link',
])

# Check 2: Cross-reference terms that should be lowercase
_XREF_TERMS = set(_CONFIG.get('cross_reference_terms', [
    'appendix', 'bibliography', 'chapter', 'contents', 'figure',
    'glossary', 'note', 'part', 'preface', 'table', 'volume',
]))

# Check 3: Abbreviations that should not be used in cross-references
_XREF_ABBREVS: Dict[str, str] = _CONFIG.get('cross_reference_abbreviations', {})

# Context indicators that signal a cross-reference
_XREF_INDICATORS = re.compile(
    r'\b(see|refer\s+to|shown\s+in|described\s+in|listed\s+in|'
    r'found\s+in|detailed\s+in|covered\s+in|as\s+in)\b',
    re.IGNORECASE,
)


def _inline_code_ranges(text: str) -> List[tuple]:
    return [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]


def _in_ranges(pos: int, ranges: List[tuple]) -> bool:
    for start, end in ranges:
        if start <= pos < end:
            return True
    return False


def _in_quotes(pos: int, text: str) -> bool:
    """Check if position is inside quotation marks."""
    for pattern in [r'"([^"]*)"', r"'([^']*)'", r'`([^`]*)`']:
        for m in re.finditer(pattern, text):
            if m.start() <= pos < m.end():
                return True
    return False


class CitationsRule(BaseReferencesRule):
    """Flag problematic link text, capitalized cross-reference terms,
    and abbreviated cross-reference words."""

    def _get_rule_type(self) -> str:
        return 'references_citations'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            code_ranges = _inline_code_ranges(sentence)
            self._check_problematic_link_text(sentence, idx, text, context, code_ranges, errors)
            self._check_xref_capitalization(sentence, idx, text, context, code_ranges, errors)
            self._check_xref_abbreviations(sentence, idx, text, context, code_ranges, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — problematic link text
    # ------------------------------------------------------------------
    def _check_problematic_link_text(self, sentence, idx, text, context,
                                     code_ranges, errors):
        for phrase in _PROBLEMATIC_PHRASES:
            pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(sentence):
                if _in_ranges(match.start(), code_ranges):
                    continue
                if _in_quotes(match.start(), sentence):
                    continue
                found = match.group(0)
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Avoid generic link text '{found}'. "
                        f"Use descriptive text that explains the destination."
                    ),
                    suggestions=[
                        "Use descriptive link text, e.g., 'See the Installation Guide'.",
                        "Link text should tell the reader what they will find.",
                    ],
                    severity='high',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(match.start(), match.end()),
                )
                if error is not None:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — cross-reference terms should be lowercase
    # ------------------------------------------------------------------
    def _check_xref_capitalization(self, sentence, idx, text, context,
                                   code_ranges, errors):
        if not _XREF_INDICATORS.search(sentence):
            return

        for term in _XREF_TERMS:
            # Match capitalized form followed by a number or letter
            pattern = re.compile(
                r'\b(' + re.escape(term.capitalize()) + r')\s+(\d+|[A-Z])\b'
            )
            for match in pattern.finditer(sentence):
                if _in_ranges(match.start(), code_ranges):
                    continue
                if _in_quotes(match.start(), sentence):
                    continue
                found = match.group(1)
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Use lowercase '{found.lower()}' in cross-references: "
                        f"'{found}' -> '{found.lower()}'."
                    ),
                    suggestions=[
                        f"Write '{found.lower()} {match.group(2)}' instead of "
                        f"'{found} {match.group(2)}'.",
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(match.start(), match.start() + len(found)),
                )
                if error is not None:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 3 — abbreviated cross-reference words
    # ------------------------------------------------------------------
    def _check_xref_abbreviations(self, sentence, idx, text, context,
                                  code_ranges, errors):
        for abbrev, full_word in _XREF_ABBREVS.items():
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\s*\d+', re.IGNORECASE)
            for match in pattern.finditer(sentence):
                if _in_ranges(match.start(), code_ranges):
                    continue
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Do not abbreviate '{full_word}' in cross-references. "
                        f"Write the full word."
                    ),
                    suggestions=[
                        f"Replace '{abbrev}' with '{full_word}'.",
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=abbrev,
                    span=(match.start(), match.start() + len(abbrev)),
                )
                if error is not None:
                    errors.append(error)
