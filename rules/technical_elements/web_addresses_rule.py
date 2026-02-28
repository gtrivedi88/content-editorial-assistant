"""
Web Addresses Rule — Deterministic regex detection.
IBM Style Guide (p.274-278):
1. Include the protocol for non-HTTP web addresses.
2. Do not use a trailing slash for domain-only URLs.
3. Use lowercase for protocols and domain names.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Bare www URL without protocol: "www.example.com" → "https://www.example.com"
_BARE_WWW_RE = re.compile(
    r'(?<![/:])(?<!\w)\b(www\.[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}'
    r'(?:/[^\s,.)]*)?)\b',
)

# Uppercase protocol: "HTTP://", "HTTPS://" → lowercase
_UPPERCASE_PROTOCOL_RE = re.compile(
    r'\b(HTTPS?|FTP|FTPS)://',
)

# Trailing slash on domain-only URL: "https://example.com/" → no trailing slash
_TRAILING_SLASH_RE = re.compile(
    r'(https?://[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,})/(?=[\s,.)"\']|$)',
)


class WebAddressesRule(BaseTechnicalRule):
    """Flag web address formatting issues."""

    def _get_rule_type(self) -> str:
        return 'technical_web_addresses'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_bare_www(sentence, idx, text, context, errors, code_ranges, sent_start)
            self._check_uppercase_protocol(sentence, idx, text, context, errors, code_ranges, sent_start)
            self._check_trailing_slash(sentence, idx, text, context, errors, code_ranges, sent_start)
        return errors

    def _check_bare_www(self, sentence, idx, text, context, errors, code_ranges, sent_start):
        """Flag bare www URLs without protocol."""
        for match in _BARE_WWW_RE.finditer(sentence):
            url = match.group(1)
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Include the protocol for web addresses. "
                    f"Write 'https://{url}' instead of '{url}'."
                ),
                suggestions=[f"https://{url}"],
                severity='medium', text=text, context=context,
                flagged_text=url,
                span=(match.start(1), match.end(1)),
            )
            if error:
                errors.append(error)

    def _check_uppercase_protocol(self, sentence, idx, text, context, errors, code_ranges, sent_start):
        """Flag uppercase protocols: 'HTTP://' → 'http://'."""
        for match in _UPPERCASE_PROTOCOL_RE.finditer(sentence):
            protocol = match.group(1)
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use lowercase for protocols. "
                    f"Write '{protocol.lower()}://' instead of '{protocol}://'."
                ),
                suggestions=[f"{protocol.lower()}://"],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_trailing_slash(self, sentence, idx, text, context, errors, code_ranges, sent_start):
        """Flag trailing slash on domain-only URLs."""
        for match in _TRAILING_SLASH_RE.finditer(sentence):
            url_with_slash = match.group(0)
            url_without = match.group(1)
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    "Remove the trailing slash from the domain-only URL."
                ),
                suggestions=[url_without],
                severity='low', text=text, context=context,
                flagged_text=url_with_slash,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
