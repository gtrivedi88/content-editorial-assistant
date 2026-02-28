"""
Personal Information Rule — Deterministic YAML-based detection.
IBM Style Guide (Page 282): Use culturally neutral naming terminology.

Use "given name" and "surname" instead of culturally specific terms
like "first name", "last name", or "Christian name".

Configuration loaded from config/personal_info_config.yaml.
To add new term mappings, edit the YAML file — no code changes needed.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule


def _load_config() -> Dict[str, str]:
    """Load personal info term mappings from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'personal_info_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('term_map', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class PersonalInformationRule(BaseLegalRule):
    """Detects culturally specific naming terms and suggests neutral alternatives."""

    def _get_rule_type(self) -> str:
        return 'personal_information'

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
        """Find culturally specific naming terms in a single sentence."""
        sent_lower = sent.text.lower()
        for term, replacement in _TERM_MAP.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()

                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=sent_index,
                    message=(
                        f"Use '{replacement}' instead of '{found}'. "
                        f"The term '{found}' is culturally specific "
                        f"and may not apply globally."
                    ),
                    suggestions=[
                        f"Change '{found}' to '{replacement}'",
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
