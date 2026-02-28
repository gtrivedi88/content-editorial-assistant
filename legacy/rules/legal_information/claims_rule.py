"""
Claims and Recommendations Rule — Deterministic YAML-based detection.
IBM Style Guide (Page 279): Do not make unsubstantiated claims.

Detects superlatives, subjective benefit claims, security claims,
environmental claims, and vague recommendations.

Configuration loaded from config/claims_config.yaml.
To add new claim phrases, edit the YAML file — no code changes needed.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule


def _load_config() -> List[Dict[str, Any]]:
    """Load and flatten claim phrases from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'claims_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return []

    phrases = []
    for _category, entries in config.get('claim_phrases', {}).items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and 'phrase' in entry:
                phrases.append(entry)
    return phrases


_CLAIM_PHRASES = _load_config()


class ClaimsRule(BaseLegalRule):
    """Detects unsubstantiated claims and recommendations."""

    def _get_rule_type(self) -> str:
        return 'claims'

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
            self._check_sentence(sent, i, text, context, errors)

        return errors

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context, errors: List[Dict[str, Any]]) -> None:
        """Find unsubstantiated claim phrases in a single sentence."""
        sent_lower = sent.text.lower()
        for entry in _CLAIM_PHRASES:
            phrase = entry['phrase']
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()
                suggestion = entry.get('suggestion', f"Avoid the claim '{found}'.")

                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=sent_index,
                    message=(
                        f"Unsubstantiated claim: '{found}'. "
                        f"{suggestion}"
                    ),
                    suggestions=[suggestion],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
