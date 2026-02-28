"""
Articles Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 91): Use 'a' before consonant sounds, 'an' before vowel sounds.
Choose based on pronunciation, not spelling.

Configuration loaded from config/articles_config.yaml.
To add new abbreviations, edit the YAML file — no code changes needed.
"""

import os
import yaml
from typing import List, Dict, Any, Optional, Set
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule


def _load_config() -> Dict[str, Any]:
    """Load articles configuration from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'articles_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()
VOWEL_SOUND_ABBREVS: Set[str] = set(_CONFIG.get('vowel_sound_abbreviations', []))
CONSONANT_SOUND_ABBREVS: Set[str] = set(_CONFIG.get('consonant_sound_abbreviations', []))
CONSONANT_SOUND_WORDS: Set[str] = set(_CONFIG.get('consonant_sound_words', []))
VOWEL_SOUND_WORDS: Set[str] = set(_CONFIG.get('vowel_sound_words', []))

# Letter names that start with a vowel sound (for unknown all-caps abbreviations)
_VOWEL_SOUND_LETTERS = set('AEFHILMNORSX')


class ArticlesRule(BaseLanguageRule):
    """Checks a/an usage based on pronunciation, not spelling."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for token in doc:
            if token.lower_ not in ('a', 'an') or token.pos_ != 'DET':
                continue

            next_token = None
            for j in range(token.i + 1, len(doc)):
                if not doc[j].is_space and not doc[j].is_punct:
                    next_token = doc[j]
                    break

            if next_token is None:
                continue

            expects_an = self._expects_an(next_token)
            actual_is_an = token.lower_ == 'an'

            if expects_an and not actual_is_an:
                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=0,
                    message=f"Use 'an' before '{next_token.text}' (vowel sound).",
                    suggestions=[f"Change 'a {next_token.text}' to 'an {next_token.text}'."],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=f"a {next_token.text}",
                    span=(token.idx, next_token.idx + len(next_token.text))
                ))
            elif not expects_an and actual_is_an:
                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=0,
                    message=f"Use 'a' before '{next_token.text}' (consonant sound).",
                    suggestions=[f"Change 'an {next_token.text}' to 'a {next_token.text}'."],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=f"an {next_token.text}",
                    span=(token.idx, next_token.idx + len(next_token.text))
                ))

        return errors

    def _expects_an(self, token) -> bool:
        """Determine if the token starts with a vowel sound."""
        word = token.text
        word_lower = word.lower()

        # Explicit lookup tables (from YAML config)
        if word_lower in VOWEL_SOUND_WORDS:
            return True
        if word_lower in CONSONANT_SOUND_WORDS:
            return False
        if word_lower in VOWEL_SOUND_ABBREVS:
            return True
        if word_lower in CONSONANT_SOUND_ABBREVS:
            return False

        # All-uppercase abbreviation not in tables: check first letter pronunciation
        if word.isupper() and len(word) >= 2:
            return word[0] in _VOWEL_SOUND_LETTERS

        # Default: first letter vowel → "an", consonant → "a"
        return word_lower[0] in 'aeiou' if word_lower else False
