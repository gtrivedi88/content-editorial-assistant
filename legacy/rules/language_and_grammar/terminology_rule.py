"""
Terminology Rule — Token-based detection for accuracy.
IBM Style Guide (Page 113): Use consistent, standardized terms.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule


def _load_config() -> Dict[str, str]:
    """Load terminology map from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'terminology_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return {k.lower(): v for k, v in config.get('term_map', {}).items()}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()
_SINGLE_TERMS = {k: v for k, v in _TERM_MAP.items() if ' ' not in k}
_PHRASE_TERMS = {k: v for k, v in _TERM_MAP.items() if ' ' in k}


class TerminologyRule(BaseLanguageRule):
    """Detects deprecated terms using linguistic tokens to minimize false positives."""

    def _get_rule_type(self) -> str:
        return 'terminology'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ('listing', 'literal', 'code_block', 'inline_code'):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for i, sent in enumerate(doc.sents):
            self._check_single_terms(sent, i, text, context, errors)
            self._check_phrase_terms(sent, i, text, context, errors)

        return errors

    def _check_single_terms(self, sent, sent_idx, text, context, errors):
        """Match single-word terms by token text or lemma."""
        for token in sent:
            if token.is_punct or token.is_space:
                continue

            match_key = None
            if token.lower_ in _SINGLE_TERMS:
                match_key = token.lower_
            elif token.lemma_.lower() in _SINGLE_TERMS:
                match_key = token.lemma_.lower()

            if not match_key:
                continue

            replacement = _SINGLE_TERMS[match_key]
            error = self._create_error(
                sentence=sent.text, sentence_index=sent_idx,
                message=f"Use '{replacement}' instead of '{token.text}'.",
                suggestions=[f"Change to '{replacement}'"],
                severity='medium', text=text, context=context,
                flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

    def _check_phrase_terms(self, sent, sent_idx, text, context, errors):
        """Match multi-word terms via regex."""
        for phrase, replacement in _PHRASE_TERMS.items():
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                found = match.group(0)
                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_idx,
                    message=f"Use '{replacement}' instead of '{found}'.",
                    suggestions=[f"Change to '{replacement}'"],
                    severity='medium', text=text, context=context,
                    flagged_text=found,
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                )
                if error:
                    errors.append(error)
