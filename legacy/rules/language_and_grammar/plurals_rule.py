"""
Plurals Rule (YAML-based)
Based on IBM Style Guide topic: "Plurals" (p.106)

Checks for four common pluralization errors:
1. Do not use "(s)" to form plurals -- use either singular or plural.
2. Do not use plural nouns as adjectives (e.g., "systems administrator").
3. Incorrect plural forms (from YAML config).
4. Do not use apostrophe for acronym plurals (API's -> APIs).
"""
import os
import re
import yaml
from typing import List, Dict, Any

from .base_language_rule import BaseLanguageRule


def _load_config():
    """Load plurals corrections from YAML configuration."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'plurals_corrections.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()


class PluralsRule(BaseLanguageRule):
    """
    Checks for common pluralization errors in technical writing.
    """

    def _get_rule_type(self) -> str:
        return 'plurals'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for pluralization errors."""
        # Guard: skip code blocks
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code'
        ):
            return []

        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        # Rule 1: "(s)" patterns
        errors.extend(self._check_parenthetical_s(text, doc, context))

        # Rule 2: Plural nouns used as adjectives
        errors.extend(self._check_plural_adjectives(doc, text, context))

        # Rule 3: Incorrect plural forms from YAML config
        errors.extend(self._check_incorrect_plurals(doc, text, context))

        # Rule 4: Acronym apostrophe plurals (API's -> APIs)
        errors.extend(self._check_acronym_apostrophe_plurals(doc, text, context))

        return errors

    # ------------------------------------------------------------------
    # Rule 1: "(s)" patterns
    # ------------------------------------------------------------------

    def _check_parenthetical_s(self, text: str, doc, context) -> List[Dict[str, Any]]:
        """Detect word(s) patterns and suggest using singular or plural."""
        errors = []
        pattern = re.compile(r'\b(\w+)\(s\)', re.IGNORECASE)

        for match in pattern.finditer(text):
            base_word = match.group(1)

            # Find which sentence this belongs to
            sentence_index = 0
            sentence_text = text
            for i, sent in enumerate(doc.sents):
                if sent.start_char <= match.start() < sent.end_char:
                    sentence_index = i
                    sentence_text = sent.text
                    break

            error = self._create_error(
                sentence=sentence_text,
                sentence_index=sentence_index,
                message=(
                    f"Do not use '(s)' to indicate a plural. "
                    f"Use either '{base_word}' or '{base_word}s'."
                ),
                suggestions=[
                    f"Use '{base_word}' (singular) or '{base_word}s' (plural)",
                    "Rewrite to use 'one or more' or 'multiple' if both forms apply",
                ],
                severity='medium',
                text=text,
                context=context,
                span=(match.start(), match.end()),
                flagged_text=match.group(0),
            )
            if error:
                errors.append(error)

        return errors

    # ------------------------------------------------------------------
    # Rule 2: Plural nouns used as adjectives
    # ------------------------------------------------------------------

    def _check_plural_adjectives(self, doc, text: str, context) -> List[Dict[str, Any]]:
        """Detect plural nouns incorrectly used as adjectives."""
        errors = []

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if self._is_plural_adjective(token, doc):
                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"Use the singular form '{token.lemma_}' "
                            f"when modifying another noun."
                        ),
                        suggestions=[
                            f"Change '{token.text}' to '{token.lemma_}'",
                        ],
                        severity='low',
                        text=text,
                        context=context,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text,
                    )
                    if error:
                        errors.append(error)

        return errors

    def _is_plural_adjective(self, token, doc) -> bool:
        """Return True if token is a plural noun incorrectly modifying another noun."""
        # Must be tagged as plural noun acting as compound modifier or adjectival modifier
        if not (token.tag_ == 'NNS'
                and token.dep_ in ('compound', 'amod')
                and token.lemma_ != token.lower_):
            return False

        if self._fails_surface_guards(token, doc):
            return False

        if self._is_functioning_as_verb(token, doc):
            return False

        if self._is_compound_head_noun(token, doc):
            return False

        if self._is_yaml_exempted(token):
            return False

        return True

    def _fails_surface_guards(self, token, doc) -> bool:
        """Return True if the token should be skipped based on surface-level checks."""
        # Skip verbs (SpaCy sometimes mis-tags)
        if token.pos_ == 'VERB':
            return True

        # Skip all-caps acronyms (APIs, URLs, etc.)
        if token.text.isupper() and len(token.text) >= 2:
            return True

        # Skip tokens inside inline code (backticks)
        if self._is_in_backticks(token):
            return True

        # Skip technical identifiers (hyphens, underscores, dots, digits)
        if any(c in token.text for c in '-_./') or any(c.isdigit() for c in token.text):
            return True

        # Skip if part of a hyphenated compound (e.g., "cluster-csi-drivers")
        if token.i > 0 and doc[token.i - 1].text == '-':
            return True
        if token.i < len(doc) - 1 and doc[token.i + 1].text == '-':
            return True

        # Skip legitimate plural subjects (dep_ == 'nsubj')
        if token.dep_ == 'nsubj':
            return True

        return False

    def _is_yaml_exempted(self, token) -> bool:
        """Return True if the token is exempted by YAML configuration lists."""
        token_lower = token.text.lower()

        # Uncountable technical nouns (e.g., "data", "metadata")
        if token_lower in _CONFIG.get('uncountable_technical_nouns', {}):
            return True

        # Proper nouns ending in 's' (e.g., "kubernetes", "jenkins")
        if token_lower in _CONFIG.get('proper_nouns_ending_in_s', {}):
            return True

        # Acceptable plural compound phrases (e.g., "settings panel")
        acceptable = _CONFIG.get('plural_adjectives', {}).get('acceptable_compounds', [])
        if token.dep_ == 'compound' and token.head and token.head.pos_ == 'NOUN':
            compound = f"{token.text} {token.head.text}".lower()
            if compound in [a.lower() for a in acceptable]:
                return True

        return False

    # ------------------------------------------------------------------
    # Rule 3: Incorrect plural forms from YAML
    # ------------------------------------------------------------------

    def _check_incorrect_plurals(self, doc, text: str, context) -> List[Dict[str, Any]]:
        """Detect incorrect plural forms defined in YAML config."""
        errors = []

        for i, sent in enumerate(doc.sents):
            for token in sent:
                correct_form = self._get_correct_plural(token)
                if correct_form:
                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"'{token.text}' is not a correct plural form. "
                            f"Use '{correct_form}' instead."
                        ),
                        suggestions=[f"Change '{token.text}' to '{correct_form}'"],
                        severity='high',
                        text=text,
                        context=context,
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text,
                    )
                    if error:
                        errors.append(error)

        return errors

    def _get_correct_plural(self, token) -> str:
        """Return the correct form if token is an incorrect plural, else empty string."""
        if token.pos_ != 'NOUN':
            return ''

        token_lower = token.text.lower()

        # Check uncountable technical nouns (e.g., "datas" -> "data")
        uncountable = _CONFIG.get('uncountable_technical_nouns', {})
        for _noun, info in uncountable.items():
            incorrect_forms = [f.lower() for f in info.get('incorrect_forms', [])]
            if token_lower in incorrect_forms:
                return info.get('correct_plural_form', '')

        # Check traditional incorrect plurals (e.g., "informations" -> "information")
        incorrect_plurals = _CONFIG.get('incorrect_plurals', {})
        for category in incorrect_plurals.values():
            if isinstance(category, dict) and token_lower in category:
                return category[token_lower].get('correct_form', '')

        return ''

    # ------------------------------------------------------------------
    # Rule 4: Acronym apostrophe plurals
    # ------------------------------------------------------------------

    def _check_acronym_apostrophe_plurals(self, doc, text: str,
                                          context) -> List[Dict[str, Any]]:
        """Detect apostrophe plurals of acronyms (API's -> APIs)."""
        errors = []

        for i, sent in enumerate(doc.sents):
            for token in sent:
                result = self._detect_acronym_apostrophe(token, doc)
                if result is None:
                    continue

                acronym, span_start, span_end = result
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=(
                        f"Use '{acronym}s' instead of '{acronym}'s' "
                        f"for plural acronyms."
                    ),
                    suggestions=[
                        f"Change '{acronym}'s' to '{acronym}s'",
                        "Acronym plurals do not need an apostrophe",
                    ],
                    severity='medium',
                    text=text,
                    context=context,
                    span=(span_start, span_end),
                    flagged_text=f"{acronym}'s",
                )
                if error:
                    errors.append(error)

        return errors

    def _detect_acronym_apostrophe(self, token, doc):
        """Return (acronym, span_start, span_end) if token is an acronym with apostrophe plural, else None."""
        if not (token.text.isupper() and len(token.text) >= 2):
            return None
        if token.i + 1 >= len(doc):
            return None

        next_token = doc[token.i + 1]
        if next_token.text != "'s":
            return None

        if not self._is_likely_plural_context(token, doc):
            return None

        return (token.text, token.idx, next_token.idx + len(next_token.text))

    def _is_likely_plural_context(self, token, doc) -> bool:
        """Return True if context suggests plural rather than possessive."""
        # Check for plural verb indicators after the "'s" token
        if token.i + 2 < len(doc):
            after = doc[token.i + 2]
            plural_verbs = {
                'are', 'were', 'have', 'do', 'can', 'will',
                'may', 'must', 'should',
            }
            if after.text.lower() in plural_verbs:
                return True
            # List context (comma or conjunction after "'s")
            if after.text in (',', 'and', 'or'):
                return True
        return False

    # ------------------------------------------------------------------
    # Shared guard helpers
    # ------------------------------------------------------------------

    def _is_functioning_as_verb(self, token, doc) -> bool:
        """Detect when a token tagged NNS is actually functioning as a verb."""
        # ROOT dependency -> main predicate
        if token.dep_ == 'ROOT':
            return True

        # Has typical verb children (objects, adverbials, etc.)
        verb_child_deps = {'dobj', 'iobj', 'nsubjpass', 'advmod', 'aux', 'auxpass', 'prep'}
        if any(child.dep_ in verb_child_deps for child in token.children):
            return True

        # SpaCy POS says VERB
        if token.pos_ == 'VERB':
            return True

        # Subject + token + object/prep pattern
        if 0 < token.i < len(doc) - 1:
            prev = doc[token.i - 1]
            nxt = doc[token.i + 1]
            if prev.dep_ in ('nsubj', 'compound') and nxt.dep_ in ('dobj', 'attr', 'prep'):
                return True
            if prev.pos_ in ('NOUN', 'PROPN') and nxt.pos_ == 'ADP':
                return True

        return False

    def _is_compound_head_noun(self, token, doc) -> bool:
        """Return True if token is the head noun of a compound, not a modifier."""
        has_compound_children = any(
            child.dep_ == 'compound' and child.i < token.i
            for child in token.children
        )
        head = token.head
        is_head_position = (
            head.pos_ != 'NOUN'
            or head.i < token.i
            or head.dep_ == 'ROOT'
        )
        return has_compound_children and is_head_position

    @staticmethod
    def _is_in_backticks(token) -> bool:
        """Return True if token appears inside backtick-delimited inline code."""
        sent_text = token.sent.text
        offset = token.idx - token.sent.start_char
        depth = 0
        for idx, char in enumerate(sent_text):
            if char == '`':
                depth = 1 - depth
            if idx == offset:
                return depth == 1
        return False
