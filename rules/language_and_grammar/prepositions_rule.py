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
from rules.base_rule import in_code_range
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
        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors = []

        for i, sent in enumerate(doc.sents):
            self._check_sentence(sent, i, text, context, code_ranges, errors)

        return errors

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context, code_ranges: list,
                        errors: List[Dict[str, Any]]) -> None:
        """Check a single sentence for unnecessary phrasal verb prepositions."""
        for token in sent:
            if token.pos_ not in ('ADP', 'PART'):
                continue
            if in_code_range(token.idx, code_ranges):
                continue

            verb = token.head
            if verb.pos_ != 'VERB':
                continue

            verb_lemma = verb.lemma_.lower()
            prep_text = token.lower_

            if verb_lemma not in UNNECESSARY_PHRASAL_VERBS:
                continue
            prep_map = UNNECESSARY_PHRASAL_VERBS[verb_lemma]
            if prep_text not in prep_map:
                continue

            # Guard: if the preposition has a real object, it's meaningful
            has_object = any(child.dep_ == 'pobj' for child in token.children)
            if has_object:
                continue

            suggestion = prep_map[prep_text]
            error = self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message=f"Omit '{prep_text}' from '{verb.text} {prep_text}'. Use '{suggestion}' instead.",
                suggestions=[f"Use '{suggestion}' instead of '{verb.text} {prep_text}'."],
                severity='low',
                text=text,
                context=context,
                flagged_text=f"{verb.text} {token.text}",
                span=(verb.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)
