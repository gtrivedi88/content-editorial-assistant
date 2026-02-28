"""
Messages Rule — Deterministic lookup-based detection.
IBM Style Guide (p. 200-203): Message language guidelines.

Checks:
  1. Exaggerated adjectives in messages (catastrophic, fatal, illegal).
  2. Casual expressions (oops, sorry, whoops).
  3. "please" in instructions.
  4. Blaming the user ("you failed", "you entered the wrong").
  5. "Congratulations!" in success messages.

Configuration loaded from config/messages_config.yaml.
Guards: skip code blocks. For "fatal" guard against "fatal error" in code contexts.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

# Block types that are never prose
_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_INLINE_CODE = re.compile(r'`[^`]+`')

# "please" at word boundary, case-insensitive
_PLEASE_RE = re.compile(r'\bplease\b', re.IGNORECASE)

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


def _code_ranges(text: str) -> List[tuple]:
    return [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]


def _in_ranges(pos: int, ranges: List[tuple]) -> bool:
    for start, end in ranges:
        if start <= pos < end:
            return True
    return False


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

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            code_spans = _code_ranges(sentence)
            self._check_exaggerated(sentence, idx, text, context, code_spans, errors)
            self._check_casual(sentence, idx, text, context, code_spans, errors)
            self._check_please(sentence, idx, text, context, code_spans, errors)
            self._check_blaming(sentence, idx, text, context, code_spans, errors)
            self._check_success(sentence, idx, text, context, code_spans, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — exaggerated adjectives
    # ------------------------------------------------------------------
    def _check_exaggerated(self, sentence, idx, text, context, code_spans, errors):
        for word, replacement in _EXAGGERATED.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                if _in_ranges(match.start(), code_spans):
                    continue
                found = match.group(0)
                # Guard: "fatal error" in technical context
                if found.lower() == 'fatal' and _FATAL_TECH_RE.search(sentence):
                    continue
                if found.lower() == 'illegal' and _ILLEGAL_TECH_RE.search(sentence):
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
    def _check_casual(self, sentence, idx, text, context, code_spans, errors):
        for expr in _CASUAL:
            pattern = r'\b' + re.escape(expr) + r'\b'
            for match in re.finditer(pattern, sentence, re.IGNORECASE):
                if _in_ranges(match.start(), code_spans):
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
    def _check_please(self, sentence, idx, text, context, code_spans, errors):
        for match in _PLEASE_RE.finditer(sentence):
            if _in_ranges(match.start(), code_spans):
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
    def _check_blaming(self, sentence, idx, text, context, code_spans, errors):
        sentence_lower = sentence.lower()
        for phrase in _BLAMING:
            pos = sentence_lower.find(phrase.lower())
            if pos == -1:
                continue
            if _in_ranges(pos, code_spans):
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
    def _check_success(self, sentence, idx, text, context, code_spans, errors):
        sentence_lower = sentence.lower()
        for phrase in _SUCCESS:
            pos = sentence_lower.find(phrase.lower())
            if pos == -1:
                continue
            if _in_ranges(pos, code_spans):
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
