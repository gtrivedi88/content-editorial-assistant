"""
Mouse Buttons Rule — Deterministic regex detection.
IBM Style Guide (p.253):
1. Do not use the preposition 'on' with mouse actions.
2. Use 'click', 'double-click', 'right-click' — not 'select' or 'press' for mouse.
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Pattern: "click on" / "Click on" / "right-click on" / "double-click on"
_CLICK_ON_RE = re.compile(
    r'\b((?:right[- ]|double[- ])?click)\s+on\b',
    re.IGNORECASE,
)

# Legitimate uses where "on" refers to a physical surface, not a UI target
_CLICK_ON_EXCEPTIONS = re.compile(
    r'\bon\s+(?:this\s+link|each\s|the\s+(?:screen|surface|touchpad|trackpad))',
    re.IGNORECASE,
)

# "select the X tab" — should be "click the X tab"
_SELECT_TAB_RE = re.compile(
    r'\bselect\s+(?:the\s+)?(\w+)\s+tab\b',
    re.IGNORECASE,
)

# "press the X button" — 'press' is for keyboard keys, not mouse
_PRESS_BUTTON_RE = re.compile(
    r'\bpress\s+(?:the\s+)?(\w+)\s+button\b',
    re.IGNORECASE,
)


class MouseButtonsRule(BaseTechnicalRule):
    """Flag incorrect preposition and verb usage with mouse actions."""

    def _get_rule_type(self) -> str:
        return 'technical_mouse_buttons'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_click_on(sentence, idx, text, context, errors)
            self._check_select_tab(sentence, idx, text, context, errors)
            self._check_press_button(sentence, idx, text, context, errors)
        return errors

    def _check_click_on(self, sentence, idx, text, context, errors):
        """Flag 'click on' — preposition 'on' is unnecessary with mouse actions."""
        for match in _CLICK_ON_RE.finditer(sentence):
            after_on = sentence[match.end() - 2:]
            if _CLICK_ON_EXCEPTIONS.match(after_on):
                continue
            if _in_quotes(sentence, match.start()):
                continue

            verb = match.group(1)
            flagged = match.group(0)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the preposition 'on' with mouse actions. "
                    f"Use '{verb}' instead of '{flagged}'."
                ),
                suggestions=[f"Remove 'on': use '{verb}' instead of '{flagged}'."],
                severity='medium', text=text, context=context,
                flagged_text=flagged,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_select_tab(self, sentence, idx, text, context, errors):
        """Flag 'select the X tab' — use 'click' for tabs."""
        for match in _SELECT_TAB_RE.finditer(sentence):
            if _in_quotes(sentence, match.start()):
                continue
            tab_name = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Use 'click' instead of 'select' for tabs.",
                suggestions=[f"Click the {tab_name} tab."],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_press_button(self, sentence, idx, text, context, errors):
        """Flag 'press the X button' — 'press' is for keyboard keys, not mouse."""
        for match in _PRESS_BUTTON_RE.finditer(sentence):
            if _in_quotes(sentence, match.start()):
                continue
            btn_name = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message="Use 'click' instead of 'press' for mouse buttons. "
                        "'Press' is for keyboard keys.",
                suggestions=[f"Click the {btn_name} button."],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


def _in_quotes(text: str, pos: int) -> bool:
    """Return True if position is inside single or double quotes."""
    before = text[:pos]
    return before.count('"') % 2 != 0 or before.count("'") % 2 != 0
