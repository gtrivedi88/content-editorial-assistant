"""
Abbreviations Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 84): Spell out abbreviations on first use.
Do not use Latin abbreviations. Do not use abbreviations as verbs.

Configuration loaded from config/abbreviations_config.yaml.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Set, Optional
from .base_language_rule import BaseLanguageRule


def _load_config() -> Dict[str, Any]:
    """Load abbreviations configuration from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'abbreviations_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        config = {}

    # Flatten universal abbreviations into single set for fast lookup
    universal = set()
    for category in config.get('universal_abbreviations', {}).values():
        universal.update(category)
    config['_universal_set'] = universal
    return config


_CONFIG = _load_config()


class AbbreviationsRule(BaseLanguageRule):
    """Checks Latin abbreviations, undefined abbreviations, and verb usage."""

    def __init__(self):
        super().__init__()
        self.defined_abbreviations: Set[str] = set()
        self._current_doc_id: Optional[str] = None

    def _get_rule_type(self) -> str:
        return 'abbreviations'

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []
        if not nlp:
            return []

        self._reset_state(context)

        # Pre-collect definitions: "Full Term (ABBR)"
        for m in re.finditer(
            r'\b([A-Za-z][a-z]*(?:[ -][A-Za-z][a-z]*)+)\s+\(([A-Z]{2,})\)', text
        ):
            self.defined_abbreviations.add(m.group(2))

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for sent_idx, sent in enumerate(doc.sents):
            self._check_latin(sent, sent_idx, text, context, doc, errors)
            self._check_undefined_and_verb(sent, sent_idx, text, context, doc, errors)

        return errors

    # ------------------------------------------------------------------
    # Check 1: Latin abbreviations (e.g., i.e., e.g., etc.)
    # ------------------------------------------------------------------

    def _check_latin(self, sent, sent_idx, text, context, doc, errors):
        for token in sent:
            if not self._is_latin_abbreviation(token, doc):
                continue
            replacement = _CONFIG.get('latin_equivalents', {}).get(
                token.text.lower().rstrip('.'), 'the English equivalent'
            )
            error = self._create_error(
                sentence=sent.text, sentence_index=sent_idx,
                message=f"Do not use the Latin abbreviation '{token.text}'. Use '{replacement}' instead.",
                suggestions=[f"Replace '{token.text}' with '{replacement}'."],
                severity='medium', text=text, context=context,
                flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 & 3: Undefined abbreviations + verb usage
    # ------------------------------------------------------------------

    def _check_undefined_and_verb(self, sent, sent_idx, text, context, doc, errors):
        for token in sent:
            if not self._is_abbreviation_candidate(token):
                continue
            if self._is_definition_pattern(token, doc):
                self.defined_abbreviations.add(token.text)
                continue
            self._flag_undefined(token, sent, sent_idx, text, context, errors)
            self._flag_verb_usage(token, sent, sent_idx, text, context, doc, errors)

    def _flag_undefined(self, token, sent, sent_idx, text, context, errors):
        """Flag an abbreviation that has not been defined on first use."""
        if token.text in self.defined_abbreviations:
            return
        if not self._should_skip_abbreviation(token, sent, context):
            expansion = self._get_expansion(token.text)
            suggestion = (
                f"Define on first use: '{expansion} ({token.text})'."
                if expansion else
                f"Define '{token.text}' on first use: 'Full Term ({token.text})'."
            )
            error = self._create_error(
                sentence=sent.text, sentence_index=sent_idx,
                message=f"Abbreviation '{token.text}' is used without being defined.",
                suggestions=[suggestion],
                severity='medium', text=text, context=context,
                flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)
        self.defined_abbreviations.add(token.text)

    def _flag_verb_usage(self, token, sent, sent_idx, text, context, doc, errors):
        """Flag an abbreviation that is used as a verb."""
        if not self._is_used_as_verb(token, doc):
            return
        error = self._create_error(
            sentence=sent.text, sentence_index=sent_idx,
            message=f"Do not use the abbreviation '{token.text}' as a verb.",
            suggestions=[f"Use a proper verb instead of '{token.text}'."],
            severity='medium', text=text, context=context,
            flagged_text=token.text,
            span=(token.idx, token.idx + len(token.text)),
        )
        if error:
            errors.append(error)

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    def _is_latin_abbreviation(self, token, doc) -> bool:
        """Detect Latin abbreviations using morphological patterns."""
        t = token.text.lower()
        if not t or not t.endswith('.'):
            return False
        # e.g., "e.g." / "i.e." patterns
        if len(t) == 4 and t.count('.') == 2 and t[0].isalpha() and t[2].isalpha():
            return True
        if len(t) >= 3 and self._has_latin_morphology(t):
            return True
        return False

    def _is_abbreviation_candidate(self, token) -> bool:
        """Return True for uppercase 2+ char tokens that may be abbreviations."""
        if not (token.is_upper and len(token.text) >= 2 and token.text.isalpha()):
            return False
        if token.is_stop:
            return False
        if token.ent_type_ in ('PERSON', 'GPE'):
            return False
        if token.is_title and not token.is_upper:
            return False
        return True

    def _should_skip_abbreviation(self, token, sentence, context) -> bool:
        """Guards that prevent false positives on undefined abbreviations."""
        text_upper = token.text.upper()

        # Universal or common technical abbreviation
        if text_upper in _CONFIG.get('_universal_set', set()):
            return True
        if text_upper in _CONFIG.get('common_technical_acronyms', set()):
            return True

        # Domain-specific acronym
        if context and self._is_domain_acronym(text_upper, context):
            return True

        # AsciiDoc metadata line (e.g., :_mod-docs-content-type: PROCEDURE)
        if sentence.text.strip().startswith(':') and token.text.isupper():
            return True

        return False

    def _is_domain_acronym(self, text_upper: str, context: dict) -> bool:
        """Check if abbreviation is well-known in the document's domain."""
        domains = context.get('domains', [])
        if 'domain' in context:
            domains = domains + [context['domain']]
        well_known = _CONFIG.get('well_known_technical_acronyms', {})
        return any(text_upper in well_known.get(d, []) for d in domains)

    def _is_used_as_verb(self, token, doc) -> bool:
        """Detect abbreviation used as a verb via POS/dep analysis."""
        if token.pos_ == 'VERB':
            return True
        if token.dep_ in ('ROOT', 'ccomp', 'xcomp'):
            if any(c.dep_ in ('dobj', 'iobj', 'nsubj') for c in token.children):
                return True
        if 0 < token.i < len(doc) - 1:
            prev, nxt = doc[token.i - 1], doc[token.i + 1]
            if prev.tag_ == 'MD' and nxt.pos_ in ('DET', 'NOUN', 'PRON'):
                return True
        return False

    def _is_definition_pattern(self, token, doc) -> bool:
        """Check if abbreviation is being defined inside parentheses."""
        if token.i == 0:
            return False
        open_paren_idx = self._find_open_paren_before(token, doc)
        if open_paren_idx is None:
            return False
        return self._has_close_paren_after(token, doc)

    @staticmethod
    def _find_open_paren_before(token, doc) -> Optional[int]:
        """Return index of '(' before token, or None if ')' found first."""
        for i in range(token.i - 1, -1, -1):
            if doc[i].text == ')':
                return None
            if doc[i].text == '(':
                return i
        return None

    @staticmethod
    def _has_close_paren_after(token, doc) -> bool:
        """Return True if ')' follows token within a short window."""
        for j in range(token.i + 1, min(len(doc), token.i + 5)):
            if doc[j].text == ')':
                return True
            if doc[j].text == '(':
                return False
        return False

    def _has_latin_morphology(self, text: str) -> bool:
        """Check if text starts with a known Latin prefix."""
        return any(text.startswith(p) for p in _CONFIG.get('latin_patterns', []))

    def _get_expansion(self, abbreviation: str) -> Optional[str]:
        """Look up the full expansion for an abbreviation from config."""
        expansions = _CONFIG.get('abbreviation_expansions', {})
        return expansions.get(abbreviation) or expansions.get(abbreviation.upper())

    def _reset_state(self, context) -> None:
        """Reset state when processing a new document."""
        doc_id = context.get('source_location', '') if context else ''
        if self._current_doc_id != doc_id:
            self.defined_abbreviations.clear()
            self._current_doc_id = doc_id
