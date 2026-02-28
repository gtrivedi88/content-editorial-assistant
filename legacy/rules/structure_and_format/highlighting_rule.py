"""
Highlighting Rule — Deterministic regex-based detection.
IBM Style Guide (p. 184-192): Highlighting and emphasis.

Checks:
  1. Do not use all uppercase letters for emphasis (use italic instead).

Check 2 (bold vs italic misuse) is skipped — too context-dependent
without markup parsing.

Very conservative: only flags obvious all-caps emphasis words.
Guards: skip known acronyms (<=5 chars), skip headings, skip code blocks.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
    'heading', 'title', 'section_title', 'document_title',
])

_INLINE_CODE = re.compile(r'`[^`]+`')

# All-caps word with 3+ alphabetic chars, surrounded by lowercase context
_ALL_CAPS_WORD = re.compile(r'\b([A-Z]{3,})\b')

# Common acronyms and technical terms that are legitimately all-caps
_KNOWN_ACRONYMS = frozenset([
    'API', 'SDK', 'HTTP', 'HTTPS', 'JSON', 'XML', 'HTML', 'CSS', 'SQL',
    'REST', 'SOAP', 'URL', 'URI', 'CLI', 'GUI', 'DNS', 'TCP', 'UDP',
    'SSH', 'SSL', 'TLS', 'FTP', 'SMTP', 'IMAP', 'POP', 'LDAP', 'SAML',
    'AWS', 'GCP', 'IBM', 'CPU', 'GPU', 'RAM', 'ROM', 'SSD', 'HDD',
    'PDF', 'CSV', 'YAML', 'TOML', 'UUID', 'GUID', 'CORS', 'CSRF',
    'CRUD', 'ACID', 'BASE', 'FIFO', 'LIFO', 'FQDN', 'CIDR', 'VLAN',
    'RBAC', 'ABAC', 'OIDC', 'JWT', 'RSA', 'AES', 'SHA', 'CRC',
    'TODO', 'FIXME', 'NOTE', 'HACK', 'INFO', 'WARN', 'FAIL',
    'NULL', 'TRUE', 'FALSE', 'ENUM', 'VOID', 'CHAR', 'BOOL',
    'NASA', 'NATO', 'OSHA', 'NIST', 'IEEE', 'IETF', 'RFC',
    'RHEL', 'SUSE', 'DITA', 'SCSI', 'BIOS', 'UEFI',
    'IMPORTANT', 'WARNING', 'CAUTION', 'DANGER', 'ATTENTION',
    'TIP', 'RESTRICTION', 'REQUIREMENT', 'EXCEPTION', 'REMEMBER',
])


def _code_ranges(text: str) -> list:
    return [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]


def _in_ranges(pos: int, ranges: list) -> bool:
    for s, e in ranges:
        if s <= pos < e:
            return True
    return False


def _is_surrounded_by_lowercase(text: str, start: int, end: int) -> bool:
    """Check if the all-caps word appears in a lowercase prose context."""
    before = text[max(0, start - 10):start].strip()
    after = text[end:min(len(text), end + 10)].strip()
    has_lower_before = bool(before) and any(c.islower() for c in before)
    has_lower_after = bool(after) and any(c.islower() for c in after)
    return has_lower_before or has_lower_after


class HighlightingRule(BaseStructureRule):
    """Flag all-caps words used for emphasis instead of proper formatting."""

    def _get_rule_type(self) -> str:
        return 'highlighting'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        context = context or {}
        block_type = context.get('block_type', '')

        if block_type in _SKIP_BLOCKS:
            return []
        # Also skip any heading variant
        if block_type.startswith('heading'):
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            code_spans = _code_ranges(sentence)
            self._check_all_caps_emphasis(
                sentence, idx, text, context, code_spans, errors
            )
        return errors

    # ------------------------------------------------------------------
    # Check 1 — all-caps emphasis
    # ------------------------------------------------------------------
    def _check_all_caps_emphasis(
        self, sentence, idx, text, context, code_spans, errors
    ):
        for match in _ALL_CAPS_WORD.finditer(sentence):
            if _in_ranges(match.start(), code_spans):
                continue
            word = match.group(1)
            # Guard: known acronyms
            if word in _KNOWN_ACRONYMS:
                continue
            # Guard: short words (<=5 chars) are likely acronyms
            if len(word) <= 5:
                continue
            # Guard: must be in lowercase prose context to be emphasis
            if not _is_surrounded_by_lowercase(sentence, match.start(), match.end()):
                continue

            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Do not use all uppercase '{word}' for emphasis. "
                    "Use italic formatting instead."
                ),
                suggestions=[
                    f"Change '{word}' to italic: '_{word.lower()}_'.",
                    "IBM Style Guide: use italic for emphasis, not all caps.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=word,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
