"""
Keyboard Keys Rule — Deterministic regex detection.
IBM Style Guide (p.249-252):
1. Use initial capitals for key names: 'Press Return' not 'Press return'.
2. Use 'press' for function keys (Enter, Esc, Shift, Tab).
3. Use 'type' or 'enter' for letter keys that produce output.
4. Use plus sign (+) without spaces for key combinations: 'Ctrl+C' not 'Ctrl + C'.
5. Do not highlight the names of keys.
"""
import os
import re
from typing import List, Dict, Any, Optional

import yaml

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'keyboard_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Key names that must be capitalized (from YAML or defaults)
_KEY_NAMES = set(_CONFIG.get('key_names', [
    'enter', 'return', 'tab', 'escape', 'esc', 'shift', 'control', 'ctrl',
    'alt', 'delete', 'del', 'backspace', 'insert', 'ins', 'home', 'end',
    'page up', 'page down', 'caps lock', 'num lock', 'scroll lock',
    'print screen', 'space', 'spacebar',
]))

# Words that look like key names but are common English verbs/nouns.
# Only flag in keyboard context (after "press", "hold", "hit").
_KEYBOARD_CONTEXT = re.compile(
    r'\b(?:press|hit|hold|hold\s+down|release)\b',
    re.IGNORECASE,
)

# Lowercase key name after a keyboard verb: "press return" → "Press Return"
# Build pattern from key names
_LOWER_KEY_NAMES = sorted(_KEY_NAMES, key=len, reverse=True)
_LOWER_KEY_PATTERN = '|'.join(re.escape(k) for k in _LOWER_KEY_NAMES)
_PRESS_LOWER_KEY_RE = re.compile(
    rf'\b(press|hit|hold)\s+({_LOWER_KEY_PATTERN})\b',
    re.IGNORECASE,
)

# Spaces around plus in key combination: "Ctrl + C" → "Ctrl+C"
_KEY_COMBO_SPACES_RE = re.compile(
    r'\b([A-Z][a-z]+(?:rl)?|Shift|Alt|Fn|Cmd|Command|Option|Meta)'
    r'\s*\+\s+'
    r'([A-Za-z0-9]+)\b',
)

# Also match: "key + key" with space before +
_KEY_COMBO_SPACES_BEFORE_RE = re.compile(
    r'\b([A-Z][a-z]+(?:rl)?|Shift|Alt|Fn|Cmd|Command|Option|Meta)'
    r'\s+\+\s*'
    r'([A-Za-z0-9]+)\b',
)


class KeyboardKeysRule(BaseTechnicalRule):
    """Flag keyboard key formatting issues."""

    def _get_rule_type(self) -> str:
        return 'technical_keyboard_keys'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_lowercase_key_name(sentence, idx, text, context, errors)
            self._check_combo_spaces(sentence, idx, text, context, errors)
        return errors

    def _check_lowercase_key_name(self, sentence, idx, text, context, errors):
        """Flag lowercase key names after keyboard verbs: 'press return'."""
        for match in _PRESS_LOWER_KEY_RE.finditer(sentence):
            verb = match.group(1)
            key = match.group(2)

            # Only flag if the key name is actually lowercase
            if key[0].isupper():
                continue

            # Guard: skip if not in keyboard context
            # (the regex already requires press/hit/hold, so this is inherent)

            # Guard: skip verb forms — "shifting", "tabbing" etc.
            if key.endswith(('ing', 'ed', 's')) and key.lower() not in _KEY_NAMES:
                continue

            # Guard: ambiguous words — only flag in clear keyboard context
            ambiguous = {'space', 'home', 'end', 'insert', 'delete', 'return'}
            if key.lower() in ambiguous:
                # Must have "press/hit/hold" immediately before
                if verb.lower() not in ('press', 'hit', 'hold'):
                    continue

            capitalized = key.capitalize()
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use initial capitals for key names. "
                    f"Write '{capitalized}' instead of '{key}'."
                ),
                suggestions=[f"{verb.capitalize()} {capitalized}."],
                severity='medium', text=text, context=context,
                flagged_text=f"{verb} {key}",
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_combo_spaces(self, sentence, idx, text, context, errors):
        """Flag spaces around + in key combinations: 'Ctrl + C' → 'Ctrl+C'."""
        for pattern in (_KEY_COMBO_SPACES_RE, _KEY_COMBO_SPACES_BEFORE_RE):
            for match in pattern.finditer(sentence):
                key1 = match.group(1)
                key2 = match.group(2)
                flagged = match.group(0)
                corrected = f"{key1}+{key2}"

                # Only flag if there actually are spaces around the +
                if flagged == corrected:
                    continue

                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=(
                        "Do not insert a space before or after the plus sign "
                        f"in key combinations. Write '{corrected}'."
                    ),
                    suggestions=[corrected],
                    severity='low', text=text, context=context,
                    flagged_text=flagged,
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)
