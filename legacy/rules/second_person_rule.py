"""
Second Person Rule — Deterministic regex detection.
IBM Style Guide (p.109):
1. Use second person ('you') in user-facing content.
2. Avoid third-person substitutes like 'the user' in user guides
   when 'you' is more direct.

Note: First-person pronouns (we, our, us) are handled by the
pronouns rule in language_and_grammar/ to avoid duplicate flagging.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

try:
    from .base_rule import BaseRule  # type: ignore
except ImportError:
    from rules.base_rule import BaseRule  # type: ignore

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Any]:
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'second_person_patterns.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Build protected role set from YAML config
_PROTECTED_ROLES: frozenset = frozenset()
_raw_roles = _CONFIG.get('protected_role_terms', {})
if isinstance(_raw_roles, dict):
    _all_roles: list = []
    for val in _raw_roles.values():
        if isinstance(val, list):
            _all_roles.extend(val)
    _PROTECTED_ROLES = frozenset(r.lower() for r in _all_roles)

# Third-person substitutes — suggest 'you' in user-facing docs
_THIRD_PERSON_RE = re.compile(
    r'\bthe\s+(user|customer|reader|person|individual)\b',
    re.IGNORECASE,
)


class SecondPersonRule(BaseRule):
    """Flag third-person substitutes that should use 'you' instead."""

    def _get_rule_type(self) -> str:
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_third_person(sentence, idx, text, context, errors)
        return errors

    def _check_third_person(self, sentence, idx, text, context, errors):
        """Flag 'the user' when 'you' is more appropriate."""
        for match in _THIRD_PERSON_RE.finditer(sentence):
            role = match.group(1).lower()
            # Guard: protected role terms never suggest "you"
            if role in _PROTECTED_ROLES:
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use 'you' instead of 'the {role}' in user-facing "
                    f"documentation."
                ),
                suggestions=[f"Replace 'the {role}' with 'you'."],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
