"""
Prefixes Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 108): Close prefixes without hyphens unless exceptions apply.

Prefixes like re-, pre-, non-, un-, multi-, etc. should be closed (no hyphen) unless:
- The base word starts with a capital letter (e.g., non-IBM)
- The term is an established technical compound that keeps its hyphen

Configuration loaded from config/prefixes_config.yaml.
To add new exception terms, edit the YAML file — no code changes needed.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional, Set

from .base_language_rule import BaseLanguageRule


def _load_config() -> Set[str]:
    """Load standard hyphenated terms from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'prefixes_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return set(config.get('standard_hyphenated_terms', []))
    except (FileNotFoundError, yaml.YAMLError):
        return set()


_STANDARD_HYPHENATED_TERMS = _load_config()

# Regex to find hyphenated prefix patterns.
_PREFIX_PATTERN = re.compile(
    r'\b(re|pre|post|non|un|in|dis|multi|inter|over|under|sub|super|co|counter|anti|pro)-(\w+)\b',
    re.IGNORECASE,
)


class PrefixesRule(BaseLanguageRule):
    """Detect prefixes that should be closed (written without a hyphen)."""

    def _get_rule_type(self) -> str:
        return 'prefixes'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for hyphenated prefixes that should be closed."""
        if self._is_skippable_block(context):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for sent_index, sent in enumerate(doc.sents):
            self._check_sentence(sent, sent_index, text, context, errors)

        return errors

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_skippable_block(context: Optional[Dict[str, Any]]) -> bool:
        """Return True for code and literal blocks that should not be checked."""
        if not context:
            return False
        return context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        )

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context: Optional[Dict[str, Any]],
                        errors: List[Dict[str, Any]]) -> None:
        """Find prefix violations in a single sentence and append errors."""
        for match in _PREFIX_PATTERN.finditer(sent.text):
            full_word = match.group(0)
            prefix = match.group(1).lower()
            base_word = match.group(2)

            if self._should_skip_match(full_word, base_word, sent, match):
                continue

            closed_form = prefix + base_word
            char_start = sent.start_char + match.start()
            char_end = sent.start_char + match.end()

            error = self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message=(
                    f"Close the prefix: write '{closed_form}' "
                    f"instead of '{full_word}'."
                ),
                suggestions=[f"Change '{full_word}' to '{closed_form}'."],
                severity='low',
                text=text,
                context=context,
                flagged_text=full_word,
                span=(char_start, char_end),
            )
            if error:
                errors.append(error)

    @staticmethod
    def _should_skip_match(full_word: str, base_word: str,
                           sent, match) -> bool:
        """Return True when this match should be silently skipped."""
        # Established technical term that keeps its hyphen.
        if full_word.lower() in _STANDARD_HYPHENATED_TERMS:
            return True

        # Base word starts with a capital letter (e.g., non-IBM).
        if base_word[0].isupper():
            return True

        # Compound adjective modifying a noun — keep the hyphen.
        if _is_compound_modifier(sent, match):
            return True

        return False


def _is_compound_modifier(sent, match) -> bool:
    """Return True when the matched span is a compound modifier of a noun."""
    char_start = sent.start_char + match.start()
    char_end = sent.start_char + match.end()
    tokens_in_span = [
        t for t in sent
        if t.idx >= char_start and t.idx < char_end
    ]
    if not tokens_in_span:
        return False

    primary = tokens_in_span[0]
    dep = getattr(primary, 'dep_', '')
    if dep not in ('amod', 'compound'):
        return False
    head = getattr(primary, 'head', None)
    if head is None:
        return False
    return getattr(head, 'pos_', '') in ('NOUN', 'PROPN')
