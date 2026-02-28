"""
Spelling Rule — Deterministic lookup-based detection.
IBM Style Guide (Page 112): Use US English spelling.

Configuration loaded from config/spelling_config.yaml.
To add new non-US → US spelling pairs, edit the YAML file — no code changes needed.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule


def _load_config() -> Dict[str, str]:
    """Load spelling map from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'spelling_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('spelling_map', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_SPELLING_MAP = _load_config()


class SpellingRule(BaseLanguageRule):
    """Detects non-US spellings and suggests the preferred US English form."""

    def _get_rule_type(self) -> str:
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for i, sent in enumerate(doc.sents):
            for non_us, us_spelling in _SPELLING_MAP.items():
                pattern = r'\b' + re.escape(non_us) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"Use US spelling '{us_spelling}' instead of "
                            f"'{found}'."
                        ),
                        suggestions=[
                            f"Change '{found}' to '{us_spelling}'",
                        ],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)

        return errors
