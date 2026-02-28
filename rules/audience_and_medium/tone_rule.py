"""
Tone Rule — Deterministic YAML-based detection.
IBM Style Guide: Use a professional tone. Avoid business jargon,
sports metaphors, marketing buzzwords, and colloquialisms.

Configuration loaded from config/tone_vocabularies.yaml.
To add new phrases, edit the YAML file — no code changes needed.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from rules.base_rule import in_code_range
from .base_audience_rule import BaseAudienceRule


def _load_config() -> List[Dict[str, Any]]:
    """Load and flatten tone phrases from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'tone_vocabularies.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return []

    phrases = []
    for _section, categories in config.get('business_jargon', {}).items():
        if not isinstance(categories, list):
            continue
        for entry in categories:
            if not isinstance(entry, dict) or 'phrase' not in entry:
                continue
            phrases.append(entry)
            # Add declared variants as separate lookup entries
            for variant in entry.get('variants', []):
                phrases.append({
                    'phrase': variant,
                    'category': entry.get('category', 'jargon'),
                })
    return phrases


_PHRASES = _load_config()

# Matches single-quoted and double-quoted text spans
_QUOTED_RANGES_RE: re.Pattern = re.compile(r"""(['"]).*?\1""")


class ToneRule(BaseAudienceRule):
    """Detects business jargon, marketing buzzwords, and informal phrases."""

    def _get_rule_type(self) -> str:
        return 'tone'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors = []

        for i, sent in enumerate(doc.sents):
            self._check_sentence(sent, i, text, context, code_ranges, errors)

        return errors

    @staticmethod
    def _get_quoted_ranges(text: str) -> List[tuple]:
        """Return list of (start, end) tuples for quoted text spans.

        Args:
            text: The text to scan for quoted ranges.

        Returns:
            List of (start, end) tuples marking quoted spans.
        """
        return [(m.start(), m.end()) for m in _QUOTED_RANGES_RE.finditer(text)]

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context, code_ranges: list,
                        errors: List[Dict[str, Any]]) -> None:
        """Find jargon/buzzword phrases in a single sentence."""
        sent_lower = sent.text.lower()
        for entry in _PHRASES:
            phrase = entry['phrase']
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                # Guard: skip matches inside quoted text
                quoted_ranges = self._get_quoted_ranges(sent.text)
                if any(qs <= match.start() < qe for qs, qe in quoted_ranges):
                    continue
                # Guard: skip matches inside inline code
                if in_code_range(sent.start_char + match.start(), code_ranges):
                    continue

                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()
                category = entry.get('category', 'jargon')

                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=sent_index,
                    message=(
                        f"Avoid the {category.replace('_', ' ')} "
                        f"'{found}'. Use plain language instead."
                    ),
                    suggestions=[
                        f"Replace '{found}' with a clearer, "
                        f"more direct phrase",
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
