"""
Slashes Rule
Based on IBM Style Guide (p.139): Avoid slashes in general text.
Use "and" or "or" instead.

Deterministic rule: regex find "/" in prose, skip allowlisted terms,
skip code blocks, URLs, and file paths.
"""
import os
import re
from typing import List, Dict, Any, Optional, Set

import yaml

from .base_punctuation_rule import BasePunctuationRule

# Block types that are never prose
_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Regex for word/word patterns in text
_SLASH_PATTERN = re.compile(r'\b[\w]+/[\w]+\b')

# Patterns that indicate the sentence contains a URL or path
_URL_HINTS = re.compile(
    r'https?://|ftp://|www\.|\.com\b|\.org\b|\.net\b|\.gov\b|\.edu\b|\.io\b',
    re.IGNORECASE,
)
_PATH_HINTS = re.compile(
    r'/usr/|/bin/|/etc/|/var/|/home/|/opt/|/tmp/',
)

# Date-like slash usage (e.g. 01/15/2024)
_DATE_PATTERN = re.compile(r'^\d{1,4}/\d{1,4}(/\d{1,4})?$')


def _collect_yaml_strings(container) -> Set[str]:
    """Extract uppercase strings from a YAML dict-of-lists or list."""
    result: Set[str] = set()
    if isinstance(container, dict):
        for terms in container.values():
            if isinstance(terms, list):
                result.update(t.upper() for t in terms if isinstance(t, str))
    elif isinstance(container, list):
        result.update(t.upper() for t in container if isinstance(t, str))
    return result


class SlashesRule(BasePunctuationRule):
    """Flag ambiguous slash usage in general text."""

    _FALLBACK_ALLOWED: Set[str] = {
        'CI/CD', 'TCP/IP', 'I/O', 'INPUT/OUTPUT', 'CLIENT/SERVER',
        'READ/WRITE', 'R/W', 'N/A', 'W/O', 'C/O', 'ON/OFF',
        'TRUE/FALSE', 'HTTP/HTTPS', 'SSL/TLS', 'YES/NO', '24/7',
        'BLUE/GREEN', 'ACTIVE/PASSIVE', 'NBDE/CLEVIS', 'DNS/DHCP',
    }

    def __init__(self) -> None:
        super().__init__()
        self._allowed: Set[str] = self._load_allowlist()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_allowlist(self) -> Set[str]:
        config_path = os.path.join(
            os.path.dirname(__file__), 'config', 'slash_allowlist.yaml',
        )
        data = self._read_yaml(config_path)
        if not data:
            return {t.upper() for t in self._FALLBACK_ALLOWED}

        allowed = _collect_yaml_strings(data.get('built_in_categories', {}))
        allowed |= _collect_yaml_strings(data.get('user_defined_terms', []))
        return allowed if allowed else {t.upper() for t in self._FALLBACK_ALLOWED}

    @staticmethod
    def _read_yaml(path: str) -> Optional[dict]:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as fh:
                    return yaml.safe_load(fh)
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Rule interface
    # ------------------------------------------------------------------

    def _get_rule_type(self) -> str:
        return 'slashes'

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

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_sentence(sentence, idx, text, context, errors)
        return errors

    def _check_sentence(
        self,
        sentence: str,
        idx: int,
        text: str,
        context: Dict[str, Any],
        errors: List[Dict[str, Any]],
    ) -> None:
        # Skip sentences that are URLs or file paths
        if _URL_HINTS.search(sentence) or _PATH_HINTS.search(sentence):
            return

        for match in _SLASH_PATTERN.finditer(sentence):
            found = match.group(0)

            if _DATE_PATTERN.match(found):
                continue
            if found.upper() in self._allowed:
                continue

            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid using slashes in general text. "
                    f"Use 'and' or 'or' instead: '{found}'."
                ),
                suggestions=[
                    f"Replace '{found}' with "
                    f"'{found.replace('/', ' or ')}' or "
                    f"'{found.replace('/', ' and ')}'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)
