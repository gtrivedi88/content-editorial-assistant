"""
Geographic Locations Rule — Deterministic YAML-lookup detection.
IBM Style Guide (p. 225-227):
1. Use current geographic terminology (e.g., "Mumbai" not "Bombay").
2. Use correct geographical terms (e.g., "province" not "state" for Canada).

Guards: skip code blocks, inline code, and quoted text.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_references_rule import BaseReferencesRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

def _load_config() -> Dict[str, Any]:
    """Load geographic config from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'geographic_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Check 1: Outdated geographic terms -> preferred terms
_OUTDATED_TERMS: Dict[str, str] = _CONFIG.get('outdated_terms', {})

# Check 2: Misused geographic terms
_MISUSED_TERMS: Dict[str, Any] = _CONFIG.get('misused_geo_terms', {})


def _in_quotes(pos: int, text: str) -> bool:
    """Check if position is inside quotation marks."""
    for pattern in [r'"([^"]*)"', r"'([^']*)'"]:
        for m in re.finditer(pattern, text):
            if m.start() <= pos < m.end():
                return True
    return False


class GeographicLocationsRule(BaseReferencesRule):
    """Flag outdated and misused geographic terminology."""

    def _get_rule_type(self) -> str:
        return 'references_geographic'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_outdated_terms(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_misused_terms(sentence, idx, text, context, code_ranges, sent_start, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — outdated geographic terminology
    # ------------------------------------------------------------------
    def _check_outdated_terms(self, sentence, idx, text, context,
                              code_ranges, sent_start, errors):
        for outdated, preferred in _OUTDATED_TERMS.items():
            pattern = re.compile(r'\b' + re.escape(outdated) + r'\b', re.IGNORECASE)
            for match in pattern.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if _in_quotes(match.start(), sentence):
                    continue
                found = match.group(0)
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Use current geographic terminology: "
                        f"'{found}' -> '{preferred}'."
                    ),
                    suggestions=[
                        f"Replace '{found}' with '{preferred}'.",
                        "Use the most recent and appropriate geographic term.",
                    ],
                    severity='high',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(match.start(), match.end()),
                )
                if error is not None:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — misused geographic terms
    # ------------------------------------------------------------------
    def _check_misused_terms(self, sentence, idx, text, context,
                             code_ranges, sent_start, errors):
        for term, info in _MISUSED_TERMS.items():
            wrong_contexts = info.get('wrong_context', [])
            for wrong_ctx in wrong_contexts:
                # Match term within 5 words of wrong context (in either order)
                proximity = r'(?:\S+\s+){0,5}'
                pattern = re.compile(
                    r'\b' + re.escape(term) + r'\b\s+' + proximity +
                    r'\b' + re.escape(wrong_ctx) + r'\b'
                    r'|'
                    r'\b' + re.escape(wrong_ctx) + r'\b\s+' + proximity +
                    r'\b' + re.escape(term) + r'\b',
                    re.IGNORECASE,
                )
                for match in pattern.finditer(sentence):
                    if in_code_range(sent_start + match.start(), code_ranges):
                        continue
                    message = info.get('message', '')
                    correct = info.get('correct_term', '')
                    suggestions = []
                    if correct:
                        suggestions.append(f"Use '{correct}' instead of '{term}'.")
                    if message:
                        suggestions.append(message)
                    error = self._create_error(
                        sentence=sentence,
                        sentence_index=idx,
                        message=message or f"Incorrect use of '{term}' with '{wrong_ctx}'.",
                        suggestions=suggestions or [f"Check the correct geographic term for {wrong_ctx}."],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=term,
                        span=(match.start(), match.end()),
                    )
                    if error is not None:
                        errors.append(error)
