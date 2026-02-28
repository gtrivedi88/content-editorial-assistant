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

# Guard patterns: technical compound phrases where a claim keyword is part of a legitimate term
_TECHNICAL_COMPOUNDS: Dict[str, re.Pattern] = {
    'secure': re.compile(
        r'\bsecure\s+(?:shell|socket|connection|channel|boot|enclave|'
        r'element|token|hash|layer|copy)\b', re.IGNORECASE,
    ),
    'free': re.compile(
        r'\bfree\s+(?:up|of\s+charge|tier|trial|form|software)\b', re.IGNORECASE,
    ),
    'green': re.compile(
        r'\b(?:blue[- ])?green\s+(?:deployment|deploy|field|light)\b', re.IGNORECASE,
    ),
    'best': re.compile(
        r'\bbest[- ](?:effort|case|fit|match|of[- ]breed)\b', re.IGNORECASE,
    ),
}

# Sentences hedged with a modal qualifier before the claim phrase are not absolute claims
_MODAL_QUALIFIERS: re.Pattern = re.compile(
    r'\b(?:can|could|may|might|should)\b', re.IGNORECASE,
)

# Sentences with attribution markers are citing external sources, not making claims
_ATTRIBUTION_MARKERS: re.Pattern = re.compile(
    r'\b(?:according\s+to|as\s+described|per\s+the|based\s+on)\b', re.IGNORECASE,
)


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

    @staticmethod
    def _is_guarded_match(sent_text: str, sent_lower: str,
                          phrase: str, match_start: int) -> bool:
        """Check whether a claim match should be skipped by guard patterns.

        Args:
            sent_text: Original sentence text.
            sent_lower: Lowercased sentence text.
            phrase: The claim phrase being matched.
            match_start: Start offset of the match within the sentence.

        Returns:
            True if the match should be skipped.
        """
        if _ATTRIBUTION_MARKERS.search(sent_text):
            return True
        if _MODAL_QUALIFIERS.search(sent_lower[:match_start]):
            return True
        compound_re = _TECHNICAL_COMPOUNDS.get(phrase)
        if compound_re and compound_re.search(sent_text):
            return True
        return False

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context, errors: List[Dict[str, Any]]) -> None:
        """Find unsubstantiated claim phrases in a single sentence."""
        sent_lower = sent.text.lower()
        for entry in _CLAIM_PHRASES:
            phrase = entry['phrase']
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                if self._is_guarded_match(sent.text, sent_lower, phrase, match.start()):
                    continue

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
