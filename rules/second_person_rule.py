"""
Second Person Rule — Deterministic regex detection with context awareness.

IBM Style Guide (p.109):
1. Use second person ('you') in user-facing content.
2. Avoid third-person substitutes like 'the user' in user guides
   when 'you' is more direct.

Context-aware features (from config YAML):
- Skips proper nouns (capitalized role terms like "the User dashboard").
- Skips technical compounds ("user interface", "user dashboard").
- Respects document type: third-person is preferred in API/reference docs.
- Checks nearby context indicators ("role", "permission", "account").

Note: First-person pronouns (we, our, us) are handled by the
pronouns rule in language_and_grammar/ to avoid duplicate flagging.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

try:
    from .base_rule import BaseRule  # type: ignore
except ImportError:
    from rules.base_rule import BaseRule  # type: ignore

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Any]:
    """Load the second person patterns configuration from YAML."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'second_person_patterns.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Build protected role set from YAML config
_PROTECTED_ROLES: frozenset = frozenset()
_raw_roles = _CONFIG.get('protected_role_terms', {})
if isinstance(_raw_roles, dict):
    _all_roles: list = []
    for val in _raw_roles.values():
        if isinstance(val, list):
            _all_roles.extend(val)
    _PROTECTED_ROLES = frozenset(r.lower() for r in _all_roles)

# Document type preferences from YAML — types where third person is preferred
_THIRD_PERSON_PREFERRED: frozenset = frozenset()
_doc_prefs = _CONFIG.get('document_type_preferences', {})
if isinstance(_doc_prefs, dict):
    _raw_third = _doc_prefs.get('third_person_preferred', [])
    if isinstance(_raw_third, list):
        _THIRD_PERSON_PREFERRED = frozenset(
            t.lower().replace('-', '_') for t in _raw_third
        )

# Technical compound patterns from YAML — "user interface", "user dashboard", etc.
_TECHNICAL_COMPOUNDS: frozenset = frozenset()
_context_rules = _CONFIG.get('context_rules', {})
if isinstance(_context_rules, dict):
    _raw_compounds = _context_rules.get('technical_compounds', [])
    if isinstance(_raw_compounds, list):
        _TECHNICAL_COMPOUNDS = frozenset(c.lower() for c in _raw_compounds)

# Context indicators — skip when these words appear near the role term
_CONTEXT_INDICATORS: frozenset = frozenset()
if isinstance(_context_rules, dict):
    _raw_indicators = _context_rules.get('role_context_indicators', [])
    if isinstance(_raw_indicators, list):
        _CONTEXT_INDICATORS = frozenset(w.lower() for w in _raw_indicators)

# Third-person substitutes — suggest 'you' in user-facing docs.
# Captures optional possessive 's so "the user's" → "your".
_THIRD_PERSON_RE = re.compile(
    r"\bthe\s+(user|customer|reader|person|individual)('s)?\b",
    re.IGNORECASE,
)


class SecondPersonRule(BaseRule):
    """Flag third-person substitutes that should use 'you' instead.

    Applies IBM Style Guide p.109 with context awareness: skips proper
    nouns, technical compounds, and document types where third person
    is preferred (API, reference docs).
    """

    def _get_rule_type(self) -> str:
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp: Any = None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc: Any = None) -> List[Dict[str, Any]]:
        """Analyze text for third-person substitutes.

        Args:
            text: Full document text.
            sentences: Pre-split sentence strings.
            nlp: SpaCy language model (unused).
            context: Block-level context dict with block_type and content_type.
            spacy_doc: SpaCy Doc object (unused).

        Returns:
            List of error dictionaries for each flagged occurrence.
        """
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        # Respect document type preferences: third person is preferred in
        # API docs, reference docs, admin guides, etc.
        content_type = str(context.get('content_type', '')).lower().replace('-', '_')
        if content_type in _THIRD_PERSON_PREFERRED:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_third_person(sentence, idx, text, context, errors)
        return errors

    def _check_third_person(
        self,
        sentence: str,
        idx: int,
        text: str,
        context: Dict[str, Any],
        errors: List[Dict[str, Any]],
    ) -> None:
        """Flag 'the user' when 'you' is more appropriate.

        Skips matches when:
        - The role term is a protected role (admin, developer, etc.)
        - The role term is capitalized (proper noun / component name)
        - The match is part of a technical compound (user interface, etc.)
        - A context indicator word appears nearby (role, permission, etc.)

        Args:
            sentence: The sentence to check.
            idx: Zero-based sentence index.
            text: Full document text for span calculation.
            context: Block-level context dict.
            errors: List to append detected errors to.
        """
        for match in _THIRD_PERSON_RE.finditer(sentence):
            role = match.group(1).lower()

            # Guard: protected role terms never suggest "you"
            if role in _PROTECTED_ROLES:
                continue

            # Guard: capitalized role term indicates a proper noun or
            # component name (e.g., "the User dashboard")
            if _is_proper_noun(match.group(1)):
                continue

            # Guard: technical compound (e.g., "the user interface")
            if _is_technical_compound(sentence, match):
                continue

            # Guard: context indicator nearby (e.g., "user role", "user account")
            if _has_context_indicator(sentence, match):
                continue

            is_possessive = match.group(2) is not None
            if is_possessive:
                replacement = "your"
                message = (
                    f"Use 'your' instead of 'the {role}'s' in user-facing "
                    f"documentation. Per IBM Style Guide (Page 119) [Verified]."
                )
                suggestions = [replacement]
            else:
                replacement = "you"
                message = (
                    f"Use 'you' instead of 'the {role}' in user-facing "
                    f"documentation. Per IBM Style Guide (Page 119) [Verified]."
                )
                suggestions = [
                    f"Rewrite using 'you' instead of 'the {role}', "
                    "adjusting verb agreement and possessives as needed"
                ]

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=message,
                suggestions=suggestions,
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


def _is_proper_noun(role_text: str) -> bool:
    """Check if the role term is capitalized, indicating a proper noun.

    Examples: "User" in "the User dashboard" is capitalized → proper noun.
    "user" in "the user should..." is lowercase → not a proper noun.

    Args:
        role_text: The role term as matched (preserving original case).

    Returns:
        True if the first character is uppercase.
    """
    return len(role_text) > 0 and role_text[0].isupper()


def _is_technical_compound(sentence: str, match: re.Match) -> bool:
    """Check if the match is part of a known technical compound.

    Looks at the word(s) following the matched role term in the sentence
    to form a compound (e.g., "user interface", "user dashboard").

    Args:
        sentence: The full sentence.
        match: The regex match object.

    Returns:
        True if the role + following word forms a known compound.
    """
    role = match.group(1).lower()
    end_pos = match.end()

    # Extract text after the match to check for compound
    rest = sentence[end_pos:].lstrip()
    if not rest:
        return False

    # Get the next word after the role term
    next_word_match = re.match(r'(\w+)', rest)
    if not next_word_match:
        return False

    compound = f"{role} {next_word_match.group(1).lower()}"
    return compound in _TECHNICAL_COMPOUNDS


def _has_context_indicator(sentence: str, match: re.Match) -> bool:
    """Check if a context indicator word appears near the role term.

    Context indicators (role, permission, access, account, etc.) signal
    that the term refers to a system concept, not the reader.

    Uses a window of 3 words before and after the match.

    Args:
        sentence: The full sentence.
        match: The regex match object.

    Returns:
        True if a context indicator is found in the surrounding window.
    """
    if not _CONTEXT_INDICATORS:
        return False

    # Build a window around the match
    start = max(0, match.start() - 50)
    end = min(len(sentence), match.end() + 50)
    window = sentence[start:end].lower()

    # Check for any indicator word in the window
    words_in_window = set(re.findall(r'\b\w+\b', window))
    return bool(words_in_window & _CONTEXT_INDICATORS)
