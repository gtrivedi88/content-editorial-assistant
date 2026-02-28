"""
Numerals versus Words Rule
IBM Style Guide (p.157): "Always use words for the first number
if it occurs at the beginning of a sentence."

Checks for numerals at the start of a sentence and suggests spelling them out.
"""

import os
import re
import yaml
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule


class NumeralsVsWordsRule(BaseNumbersRule):
    """Flag sentences that begin with a bare numeral."""

    _config = None

    def _get_rule_type(self) -> str:
        return 'numerals_vs_words'

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        if cls._config is None:
            path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'config',
                'numerals_vs_words.yaml'
            )
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f) or {}
            except (OSError, yaml.YAMLError):
                cls._config = {}
        return cls._config

    def analyze(self, text: str, sentences: List[str],
                nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        cfg = self._load_config()
        skip_types = cfg.get('skip_block_types', [])
        numeral_words = cfg.get('numeral_words', {})
        list_patterns = [
            re.compile(p) for p in cfg.get('list_item_patterns', [])
        ]

        if context and context.get('block_type') in skip_types:
            return []

        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(sentences):
            stripped = sent.lstrip()
            if not stripped:
                continue

            # Skip numbered list items like "1. Click..." or "2) Open..."
            if any(p.match(stripped) for p in list_patterns):
                continue

            # Match a leading numeral (integer or decimal)
            m = re.match(r'^(\d+(?:\.\d+)?)\b', stripped)
            if not m:
                continue

            found = m.group(1)
            suggestion = numeral_words.get(found)
            if suggestion:
                hint = f"Spell out the number: '{suggestion} ...'"
            else:
                hint = "Rephrase so the sentence does not start with a numeral."

            error = self._create_error(
                sentence=sent,
                sentence_index=i,
                message=(
                    f"Do not start a sentence with a numeral. "
                    f"Spell out the number or rephrase: '{found}'."
                ),
                suggestions=[hint],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(sent.index(found), sent.index(found) + len(found)),
            )
            if error:
                errors.append(error)

        return errors
