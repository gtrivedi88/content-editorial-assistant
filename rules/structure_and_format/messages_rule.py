"""
Messages Rule — Deterministic lookup-based detection.
IBM Style Guide (p. 200-203): Message language guidelines.

Checks:
  1. Exaggerated adjectives in messages (catastrophic, fatal, illegal).
  2. Casual expressions (oops, sorry, whoops).
  3. "please" in instructions.
  4. Blaming the user ("you failed", "you entered the wrong").
  5. "Congratulations!" in success messages.
  6. Unnecessary preamble phrases ("please note", "be aware that").

Configuration loaded from config/messages_config.yaml.
Guards: skip code blocks. For "fatal" guard against "fatal error" in code contexts.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_structure_rule import BaseStructureRule

# Block types that are never prose
_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Quoted text ranges — content inside quotes is UI/output text, not prose
_QUOTED_RE = re.compile(r'"[^"]*"|\'[^\']*\'')

# "please" at word boundary, case-insensitive
_PLEASE_RE = re.compile(r'\bplease\b', re.IGNORECASE)

# Unnecessary preamble phrases — state facts directly or use admonitions
_PREAMBLE_RE = re.compile(
    r'\b(?:'
    r'please\s+note(?:\s+that)?'
    r'|be\s+aware(?:\s+that)?'
    r'|keep\s+in\s+mind(?:\s+that)?'
    r'|it\s+should\s+be\s+noted(?:\s+that)?'
    r'|it\s+is\s+worth\s+noting(?:\s+that)?'
    r'|it\s+is\s+important\s+to\s+note(?:\s+that)?'
    r')\b',
    re.IGNORECASE,
)

# Technical contexts where "fatal" is legitimate
_FATAL_TECH_RE = re.compile(
    r'\bfatal\s+(error|exception|signal|crash|abort)\b', re.IGNORECASE
)
# Technical contexts where "illegal" is legitimate
_ILLEGAL_TECH_RE = re.compile(
    r'\billegal\s+(argument|operation|state|access|instruction|character)\b',
    re.IGNORECASE,
)


def _load_config() -> Dict[str, Any]:
    """Load messages config from YAML."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'messages_config.yaml'
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()
_EXAGGERATED = _CONFIG.get('exaggerated_adjectives', {})
_CASUAL = _CONFIG.get('casual_expressions', [])
_BLAMING = _CONFIG.get('blaming_phrases', [])
_SUCCESS = _CONFIG.get('success_phrases', [])


class MessagesRule(BaseStructureRule):
    """Flag exaggerated, casual, blaming, or inappropriate language in messages."""

    def _get_rule_type(self) -> str:
        return 'messages'

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
            quoted = [(m.start(), m.end()) for m in _QUOTED_RE.finditer(sentence)]
            self._check_exaggerated(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
            self._check_casual(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
            self._check_please(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
            self._check_blaming(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
            self._check_success(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
            self._check_preambles(sentence, idx, text, context, code_ranges, sent_start, quoted, errors)
        return errors

    @staticmethod
    def _in_quoted_range(pos: int, quoted_ranges: List[tuple]) -> bool:
        """Return True if *pos* falls inside any quoted text range."""
        return any(qs <= pos < qe for qs, qe in quoted_ranges)

    # ------------------------------------------------------------------
    # Check 1 — exaggerated adjectives
    # ------------------------------------------------------------------
    @staticmethod
    def _is_tech_context(found: str, sentence: str) -> bool:
        """Return True if *found* is used in a legitimate technical context."""
        lower = found.lower()
        if lower == 'fatal' and _FATAL_TECH_RE.search(sentence):
            return True
        if lower == 'illegal' and _ILLEGAL_TECH_RE.search(sentence):
            return True
        return False

    def _check_exaggerated(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        for word, replacement in _EXAGGERATED.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if self._in_quoted_range(match.start(), quoted):
                    continue
                found = match.group(0)
                if self._is_tech_context(found, sentence):
                    continue
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Avoid exaggerated adjective '{found}' in messages. "
                        f"Use '{replacement}' instead."
                    ),
                    suggestions=[
                        f"Replace '{found}' with '{replacement}'.",
                        "Use neutral, factual language in error messages.",
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
    # Check 2 — casual expressions
    # ------------------------------------------------------------------
    def _check_casual(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        for expr in _CASUAL:
            pattern = r'\b' + re.escape(expr) + r'\b'
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if self._in_quoted_range(match.start(), quoted):
                    continue
                found = match.group(0)
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=f"Avoid casual expression '{found}' in messages.",
                    suggestions=[
                        f"Remove '{found}' and describe the issue factually.",
                        "Use professional, neutral language.",
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
    # Check 3 — "please" in instructions
    # ------------------------------------------------------------------
    def _check_please(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        for match in _PLEASE_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            if self._in_quoted_range(match.start(), quoted):
                continue
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="Avoid 'please' in instructions; it is inappropriate in some cultures.",
                suggestions=[
                    "Remove 'please' and use a direct imperative.",
                    "Example: 'Enter your name' instead of 'Please enter your name'.",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 4 — blaming the user
    # ------------------------------------------------------------------
    def _check_blaming(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        sentence_lower = sentence.lower()
        for phrase in _BLAMING:
            pos = sentence_lower.find(phrase.lower())
            if pos == -1:
                continue
            if in_code_range(sent_start + pos, code_ranges):
                continue
            if self._in_quoted_range(pos, quoted):
                continue
            found = sentence[pos:pos + len(phrase)]
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=f"Avoid blaming the user: '{found}'.",
                suggestions=[
                    "Describe the problem without attributing fault to the user.",
                    "Focus on the action needed to resolve the issue.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(pos, pos + len(phrase)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 5 — "Congratulations!" in success messages
    # ------------------------------------------------------------------
    def _check_success(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        sentence_lower = sentence.lower()
        for phrase in _SUCCESS:
            pos = sentence_lower.find(phrase.lower())
            if pos == -1:
                continue
            if in_code_range(sent_start + pos, code_ranges):
                continue
            if self._in_quoted_range(pos, quoted):
                continue
            found = sentence[pos:pos + len(phrase)]
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=f"Avoid '{found}' in success messages.",
                suggestions=[
                    f"Remove '{found}' and state the result factually.",
                    "Example: 'The installation is complete' instead of 'Congratulations!'.",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=found,
                span=(pos, pos + len(phrase)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 6 — unnecessary preamble phrases
    # ------------------------------------------------------------------
    def _check_preambles(self, sentence, idx, text, context, code_ranges, sent_start, quoted, errors):
        """Flag 'please note', 'be aware that', and similar preambles."""
        for match in _PREAMBLE_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            if self._in_quoted_range(match.start(), quoted):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Avoid unnecessary preamble '{found}'. "
                    "State the fact directly or use a NOTE/IMPORTANT admonition."
                ),
                suggestions=[
                    f"Remove '{found}' and state the information directly.",
                    "Use a NOTE or IMPORTANT admonition for callout text.",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
