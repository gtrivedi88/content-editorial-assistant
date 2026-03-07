"""
Case-Sensitive Terms Rule — Deterministic YAML lookup WITHOUT re.IGNORECASE.
Red Hat Vale CaseSensitiveTerms: Enforce correct capitalization for product names
and technical terms (e.g., kubernetes → Kubernetes, nodejs → Node.js).
"""
import os
import re
from typing import List, Dict, Any, Optional

import yaml

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])


def _load_config() -> Dict[str, str]:
    """Load case-sensitive term map from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config',
        'case_sensitive_terms_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('terms', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def _build_patterns(
    term_map: Dict[str, str],
) -> List[tuple]:
    """Pre-compile case-sensitive regex patterns.

    For dotted terms (e.g., Node.js), use lookaround anchors instead
    of \\b because '.' is not a word character and breaks \\b matching.
    """
    compiled = []
    for wrong, right in term_map.items():
        # Skip entries where wrong == right (already correct).
        if wrong == right:
            continue
        if '.' in wrong:
            pat = re.compile(
                r'(?<!\w)' + re.escape(wrong) + r'(?!\w)',
            )
        else:
            pat = re.compile(r'\b' + re.escape(wrong) + r'\b')
        compiled.append((wrong, right, pat))
    return compiled


_TERM_MAP = _load_config()
_PATTERNS = _build_patterns(_TERM_MAP)


class CaseSensitiveTermsRule(BaseTechnicalRule):
    """Flag incorrect capitalization of product and technology names."""

    def _get_rule_type(self) -> str:
        return 'case_sensitive_terms'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        """Analyze text for case-sensitive term violations."""
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            self._check_sent(sent, i, text, context, errors)

        return errors

    def _check_sent(
        self,
        sent,
        idx: int,
        text: str,
        context: Dict[str, Any],
        errors: List[Dict[str, Any]],
    ) -> None:
        """Check a single sentence against all case-sensitive patterns."""
        protected_ranges = self._get_protected_ranges(sent.text)
        for wrong, right, pattern in _PATTERNS:
            for match in pattern.finditer(sent.text):
                if self._is_in_protected_range(
                    match.start(), match.end(), protected_ranges,
                ):
                    continue
                found = match.group(0)
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=idx,
                    message=(
                        f"Use '{right}' instead of '{found}'."
                    ),
                    suggestions=[f"Change '{found}' to '{right}'"],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(
                        sent.start_char + match.start(),
                        sent.start_char + match.end(),
                    ),
                )
                if error:
                    errors.append(error)
