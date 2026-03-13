"""
Highlighting Rule — Deterministic regex-based detection.
IBM Style Guide (p. 184-192): Highlighting and emphasis.

Checks:
  1. Do not use all uppercase letters for emphasis (use italic instead).
  2. Unformatted camelCase identifiers in prose — should use backticks.
  3. Do not wrap inline code in bold or italic — use monospace only.

Very conservative: only flags obvious all-caps emphasis words.
Guards: skip known acronyms (<=5 chars), skip headings, skip code blocks.
"""
import os
import re
from typing import List, Dict, Any, Optional, Set

import yaml

from rules.base_rule import in_code_range
from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
    'heading', 'title', 'section_title', 'document_title',
])

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
    'RHEL', 'SUSE', 'DITA', 'SCSI', 'BIOS', 'UEFI', 'NVIDIA', 'CUDA',
    'IMPORTANT', 'WARNING', 'CAUTION', 'DANGER', 'ATTENTION',
    'TIP', 'RESTRICTION', 'REQUIREMENT', 'EXCEPTION', 'REMEMBER',
])

# Check 2: camelCase identifiers that should be in backticks
_CAMEL_CASE_RE = re.compile(r'\b[a-z]+[A-Z]\w*\b')


def _load_camelcase_exceptions() -> Set[str]:
    """Load camelCase exception terms from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'camelcase_exceptions.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return set(config.get('exceptions', []))
    except (FileNotFoundError, yaml.YAMLError):
        return set()


_CAMELCASE_EXCEPTIONS: Set[str] = _load_camelcase_exceptions()


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

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_all_caps_emphasis(
                sentence, idx, text, context, code_ranges, sent_start, errors
            )
            self._check_camel_case(
                sentence, idx, text, context, code_ranges, sent_start, errors
            )
        # Check 3: bold or italic wrapping inline code
        self._check_bold_code(text, sentences, context, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — all-caps emphasis
    # ------------------------------------------------------------------
    def _check_all_caps_emphasis(
        self, sentence, idx, text, context, code_ranges, sent_start, errors
    ):
        for match in _ALL_CAPS_WORD.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
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

    # ------------------------------------------------------------------
    # Check 2 — camelCase identifiers in prose
    # ------------------------------------------------------------------
    def _check_camel_case(
        self, sentence, idx, text, context, code_ranges, sent_start, errors
    ):
        """Flag unformatted camelCase identifiers in prose.

        camelCase words (lowercase first letter + uppercase interior)
        are almost always code identifiers that should be wrapped in
        backticks for monospace formatting.

        Builds the error dict directly to bypass the base-class
        ``_is_technical_content()`` guard, which intentionally classifies
        camelCase as technical content to protect other rules.
        """
        for match in _CAMEL_CASE_RE.finditer(sentence):
            abs_pos = sent_start + match.start() if sent_start >= 0 else -1
            if abs_pos >= 0 and in_code_range(abs_pos, code_ranges):
                continue
            word = match.group(0)
            if word in _CAMELCASE_EXCEPTIONS:
                continue

            citation = self._ibm_style_citation or ''
            msg = (
                f"Wrap '{word}' in backticks for monospace formatting. "
                "CamelCase identifiers in prose should use code formatting."
            )
            if citation and 'IBM Style' not in msg:
                msg = f"{msg} Per {citation}."

            errors.append({
                'type': self.rule_type,
                'message': msg,
                'suggestions': [f'`{word}`'],
                'sentence': sentence,
                'sentence_index': idx,
                'severity': 'low',
                'style_guide_citation': citation,
                'flagged_text': word,
                'span': (match.start(), match.end()),
            })

    # ------------------------------------------------------------------
    # Check 3 — bold/italic wrapping inline code
    # ------------------------------------------------------------------
    def _check_bold_code(
        self,
        text: str,
        sentences: List[str],
        context: Dict[str, Any],
        errors: List[Dict[str, Any]],
    ) -> None:
        """Flag bold or italic formatting wrapped around inline code.

        IBM Style Guide (p. 184-192): code should use monospace formatting
        only, not monospace+bold or monospace+italic.

        Args:
            text: Full block text (content tier).
            sentences: Pre-split sentence list from ``analyze()``.
            context: Context dict containing ``bold_code_ranges``.
            errors: Accumulator list — errors are appended in place.
        """
        bold_code_ranges = context.get("bold_code_ranges", [])
        for c_start, c_end, fmt, code_text in bold_code_ranges:
            # Use the full wrapper as flagged_text (e.g., **`curl`**)
            # so the underline covers the entire markup pattern.
            # _is_technical_content() won't suppress this because it
            # starts with *, not backtick. The suggestion is a direct
            # replacement (`curl`) enabling instant Accept.
            sent_idx = 0
            sentence = text  # fallback
            for i, s in enumerate(sentences):
                if code_text in s:
                    sentence = s
                    sent_idx = i
                    break

            wrapper = '**' if fmt == 'bold' else '_'
            error = self._create_error(
                sentence=sentence,
                sentence_index=sent_idx,
                message=(
                    f"Do not apply {fmt} formatting to inline code "
                    f"'{code_text}'. Use monospace (backtick) formatting only."
                ),
                suggestions=[f"`{code_text}`"],
                severity='low',
                text=text,
                context=context,
                flagged_text=f"{wrapper}`{code_text}`{wrapper}",
                span=(c_start, c_end),
            )
            if error:
                errors.append(error)
