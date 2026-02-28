"""
Menus and Navigation Rule — Deterministic regex detection.
IBM Style Guide (p.252-253):
1. Refer to the choices on a menu as 'menu items', not 'menu choices'
   or 'menu options'.
2. Do not document ellipsis punctuation from menu labels:
   'Click Attach' not 'Click Attach...'
3. Use the greater-than symbol (>) with spaces to separate menu items:
   'Click File > Tools > User preferences'.
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# "menu choice(s)" or "menu option(s)" → "menu item(s)"
_MENU_CHOICE_RE = re.compile(
    r'\bmenu\s+(choice|choices|option|options)\b',
    re.IGNORECASE,
)

# Ellipsis in a UI label reference: "Click Attach..." or "Click Save As..."
# Only flag when preceded by a UI verb (Click, Select, From)
_MENU_ELLIPSIS_RE = re.compile(
    r'\b(?:click|select|choose|from)\s+(?:the\s+)?'
    r'([A-Z][\w\s]*?)(\.{3}|\u2026)\b',
    re.IGNORECASE,
)

# Menu path without > separator or using wrong separator:
# "click File, Tools" or "File -> Tools" (should be "File > Tools")
_WRONG_MENU_SEP_RE = re.compile(
    r'\b(?:click|select|choose|from\s+the)\s+'
    r'[A-Z]\w+\s*(-{1,2}>|>>|/)\s*[A-Z]\w+',
    re.IGNORECASE,
)


class MenusNavigationRule(BaseTechnicalRule):
    """Flag incorrect menu and navigation terminology."""

    def _get_rule_type(self) -> str:
        return 'technical_menus_navigation'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_menu_choice(sentence, idx, text, context, errors)
            self._check_menu_ellipsis(sentence, idx, text, context, errors)
            self._check_wrong_separator(sentence, idx, text, context, errors)
        return errors

    def _check_menu_choice(self, sentence, idx, text, context, errors):
        """Flag 'menu choice(s)' and 'menu option(s)' — use 'menu item(s)'."""
        for match in _MENU_CHOICE_RE.finditer(sentence):
            wrong_term = match.group(1)
            correct = 'items' if wrong_term.endswith('s') else 'item'
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Refer to the choices on a menu as 'menu {correct}', "
                    f"not 'menu {wrong_term}'."
                ),
                suggestions=[f"menu {correct}"],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_menu_ellipsis(self, sentence, idx, text, context, errors):
        """Flag ellipsis in menu label references: 'Click Attach...'."""
        for match in _MENU_ELLIPSIS_RE.finditer(sentence):
            label = match.group(1).strip()
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not document the ellipsis from the menu label. "
                    f"Write '{label}' without the ellipsis."
                ),
                suggestions=[label],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_wrong_separator(self, sentence, idx, text, context, errors):
        """Flag wrong menu path separators: '->' or '>>' — use ' > '."""
        for match in _WRONG_MENU_SEP_RE.finditer(sentence):
            sep = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use the greater-than symbol (>) with spaces to "
                    f"separate menu items. Do not use '{sep}'."
                ),
                suggestions=[
                    "Use ' > ' between menu items: File > Tools > Preferences.",
                ],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
