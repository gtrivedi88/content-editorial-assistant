"""
Prepositions Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 108): Omit unnecessary prepositions in phrasal verbs.
Use prepositional phrases instead of possessive 's for abbreviations.

Configuration loaded from config/prepositions_config.yaml.
To add new phrasal verbs, edit the YAML file — no code changes needed.
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule


def _load_config() -> Dict[str, Any]:
    """Load prepositions configuration from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'prepositions_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()
UNNECESSARY_PHRASAL_VERBS: Dict[str, Dict[str, str]] = _CONFIG.get('unnecessary_phrasal_verbs', {})


class PrepositionsRule(BaseLanguageRule):
    """Detects unnecessary prepositions in phrasal verbs."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for token in doc:
            if token.pos_ not in ('ADP', 'PART'):
                continue

            verb = token.head
            if verb.pos_ != 'VERB':
                continue

            verb_lemma = verb.lemma_.lower()
            prep_text = token.lower_

            if verb_lemma in UNNECESSARY_PHRASAL_VERBS:
                prep_map = UNNECESSARY_PHRASAL_VERBS[verb_lemma]
                if prep_text in prep_map:
                    # Guard: if the preposition has a real object, it's meaningful
                    has_object = any(child.dep_ == 'pobj' for child in token.children)
                    if has_object:
                        continue

                    suggestion = prep_map[prep_text]
                    errors.append(self._create_error(
                        sentence=token.sent.text,
                        sentence_index=0,
                        message=f"Omit '{prep_text}' from '{verb.text} {prep_text}'. Use '{suggestion}' instead.",
                        suggestions=[f"Use '{suggestion}' instead of '{verb.text} {prep_text}'."],
                        severity='low',
                        text=text,
                        context=context,
                        flagged_text=f"{verb.text} {token.text}",
                        span=(verb.idx, token.idx + len(token.text))
                    ))

        return errors
