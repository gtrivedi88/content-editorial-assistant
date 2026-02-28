"""
UI Elements Rule — Deterministic regex detection.
IBM Style Guide (p.255-273):
1. Do not use 'appears' or the active verb 'displays' for windows/dialogs.
   Use 'opens' or 'is displayed'.
2. Do not use food names for UI elements: 'hamburger menu', 'kebab icon',
   'toast notification'.
3. Use correct verbs per UI element type (click for buttons, select for
   checkboxes, etc.).
4. Do not use a label as a generic noun or verb.
"""
import os
import re
from typing import List, Dict, Any, Optional

import yaml

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'ui_elements_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# "window/dialog/wizard appears" → "opens" or "is displayed"
_APPEARS_RE = re.compile(
    r'\b(window|dialog|wizard|page|pane|panel|portal)\s+appears\b',
    re.IGNORECASE,
)

# "X displays" (active verb) → "X is displayed"
_DISPLAYS_ACTIVE_RE = re.compile(
    r'\b(window|dialog|wizard|page|pane|panel|portal)\s+displays\b',
    re.IGNORECASE,
)

# Food names for UI elements — always wrong per IBM Style
_FOOD_NAMES_RE = re.compile(
    r'\b(hamburger\s+menu|kebab\s+(?:icon|menu)|toast\s+notification)\b',
    re.IGNORECASE,
)

# Replacement map for food names
_FOOD_REPLACEMENTS = {
    'hamburger menu': 'main menu icon',
    'kebab icon': 'options icon',
    'kebab menu': 'options menu',
    'toast notification': 'notification',
}

# Wrong verb with checkboxes: "click the X checkbox" → "select"
_CLICK_CHECKBOX_RE = re.compile(
    r'\b(click)\s+(?:the\s+)?(\w+(?:\s+\w+)?)\s+(checkbox|check\s+box)\b',
    re.IGNORECASE,
)

# Wrong verb with buttons in some contexts: "select the X button" → "click"
_SELECT_BUTTON_RE = re.compile(
    r'\bselect\s+(?:the\s+)?(\w+)\s+button\b',
    re.IGNORECASE,
)


class UIElementsRule(BaseTechnicalRule):
    """Flag incorrect verbs and terminology with UI elements."""

    def _get_rule_type(self) -> str:
        return 'technical_ui_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_appears(sentence, idx, text, context, errors)
            self._check_displays_active(sentence, idx, text, context, errors)
            self._check_food_names(sentence, idx, text, context, errors)
            self._check_click_checkbox(sentence, idx, text, context, errors)
            self._check_select_button(sentence, idx, text, context, errors)
        return errors

    def _check_appears(self, sentence, idx, text, context, errors):
        """Flag 'window appears' — use 'opens' or 'is displayed'."""
        for match in _APPEARS_RE.finditer(sentence):
            element = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use 'appears' for a {element.lower()}. "
                    f"Use 'opens' or 'is displayed'."
                ),
                suggestions=[
                    f"The {element} opens.",
                    f"The {element} is displayed.",
                ],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_displays_active(self, sentence, idx, text, context, errors):
        """Flag 'window displays' (active) — use 'is displayed'."""
        for match in _DISPLAYS_ACTIVE_RE.finditer(sentence):
            element = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the active verb 'displays' for a "
                    f"{element.lower()}. Use 'is displayed'."
                ),
                suggestions=[f"The {element} is displayed."],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_food_names(self, sentence, idx, text, context, errors):
        """Flag food names for UI: 'hamburger menu', 'kebab icon', 'toast notification'."""
        for match in _FOOD_NAMES_RE.finditer(sentence):
            food_name = match.group(1).lower()
            replacement = _FOOD_REPLACEMENTS.get(food_name, food_name)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the food name '{match.group(1)}'. "
                    f"Use '{replacement}' instead."
                ),
                suggestions=[replacement],
                severity='medium', text=text, context=context,
                flagged_text=match.group(1),
                span=(match.start(1), match.end(1)),
            )
            if error:
                errors.append(error)

    def _check_click_checkbox(self, sentence, idx, text, context, errors):
        """Flag 'click the X checkbox' — use 'select' for checkboxes."""
        for match in _CLICK_CHECKBOX_RE.finditer(sentence):
            cb_name = match.group(2)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Use 'select' instead of 'click' for checkboxes.",
                suggestions=[f"Select the {cb_name} checkbox."],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_select_button(self, sentence, idx, text, context, errors):
        """Flag 'select the X button' — use 'click' for buttons."""
        for match in _SELECT_BUTTON_RE.finditer(sentence):
            if _in_quotes(sentence, match.start()):
                continue
            btn_name = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Use 'click' instead of 'select' for buttons.",
                suggestions=[f"Click the {btn_name} button."],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


def _in_quotes(text: str, pos: int) -> bool:
    before = text[:pos]
    return before.count('"') % 2 != 0 or before.count("'") % 2 != 0
