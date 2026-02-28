"""
Global Audiences Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 63): Write for a global audience.

Checks:
1. Negative constructions that confuse non-native readers
2. Sentences exceeding 32 words
3. Politeness terms ("please", "thank you") inappropriate in technical docs
4. Self-referential text ("This topic is about", "This section describes")
5. Expletive constructions ("It is important to", "There are two databases")
6. Double negatives ("not uncommon" → "common")

Configuration loaded from config/global_patterns.yaml.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Set
from .base_audience_rule import BaseAudienceRule


def _load_config() -> Dict[str, Any]:
    """Load global audience patterns from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'global_patterns.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Technical state words that legitimately use negation
_TECHNICAL_NEGATION_OBJECTS: Set[str] = {
    'available', 'supported', 'enabled', 'required', 'recommended',
    'allowed', 'permitted', 'configured', 'installed', 'running',
    'compatible', 'applicable', 'valid', 'found', 'defined',
    'encrypted', 'authenticated', 'authorized', 'connected',
    # Additional technical state words
    'exist', 'present', 'possible', 'necessary', 'empty',
    'null', 'set', 'active', 'visible', 'ready', 'complete',
    'match', 'equal', 'respond', 'succeed', 'work', 'apply',
    'specify', 'include', 'contain', 'start', 'stop', 'load',
    'save', 'delete', 'remove', 'modify', 'change', 'update',
    'use', 'need', 'want', 'have', 'do', 'know',
}

# Double negatives: "not" + un-/in-/im- adjective → positive form
_DOUBLE_NEGATIVES: Dict[str, str] = {
    'uncommon': 'common',
    'unlike': 'similar to',
    'unlikely': 'likely',
    'insignificant': 'significant',
    'unnecessary': 'necessary',
    'impossible': 'possible',
    'unclear': 'clear',
    'unusual': 'usual, typical',
}
_DOUBLE_NEG_RE = re.compile(
    r'\bnot\s+(' + '|'.join(re.escape(w) for w in _DOUBLE_NEGATIVES) + r')\b',
    re.IGNORECASE,
)
# Prevent generic negation check from also firing on these words
_TECHNICAL_NEGATION_OBJECTS.update(_DOUBLE_NEGATIVES)

_MAX_SENTENCE_WORDS = 32

# Self-referential phrases (IBM Style p.65)
_SELF_REFERENTIAL_PATTERNS = [
    r'\bthis topic\s+(is about|describes|discusses|explains|provides|covers|contains)',
    r'\bthis section\s+(is about|describes|discusses|explains|provides|covers|contains)',
    r'\bthis chapter\s+(is about|describes|discusses|explains|provides|covers)',
    r'\bthis document\s+(is about|describes|discusses|explains|provides|covers)',
    r'\bthis page\s+(is about|describes|discusses|explains|provides|covers)',
]


class GlobalAudiencesRule(BaseAudienceRule):
    """Detects constructs difficult for global audiences."""

    def _get_rule_type(self) -> str:
        return 'global_audiences'

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
            self._check_negation(sent, i, text, context, errors)
            self._check_sentence_length(sent, i, text, context, errors)
            self._check_politeness(sent, i, text, context, errors)
            self._check_self_referential(sent, i, text, context, errors)
            self._check_expletive(sent, i, text, context, doc, errors)
            self._check_double_negatives(sent, i, text, context, errors)

        return errors

    # ------------------------------------------------------------------
    # Check 1: Negative constructions
    # ------------------------------------------------------------------

    def _check_negation(self, sent, sent_index, text, context, errors):
        """Flag negative constructions that confuse non-native readers."""
        for token in sent:
            if token.dep_ != 'neg':
                continue
            head = token.head
            if head.lemma_.lower() in _TECHNICAL_NEGATION_OBJECTS:
                continue
            if any(c.lemma_.lower() in _TECHNICAL_NEGATION_OBJECTS
                   for c in head.children):
                continue

            # Guard: imperative instructions ("Do not...", "Don't...")
            # are legitimate in technical docs
            sent_stripped = sent.text.strip()
            if sent_stripped.lower().startswith('do not') or sent_stripped.lower().startswith("don't"):
                continue

            error = self._create_error(
                sentence=sent.text, sentence_index=sent_index,
                message=(
                    f"Negative construction '{token.text} {head.text}' "
                    f"can confuse non-native readers. "
                    f"Consider rephrasing positively."
                ),
                suggestions=["Rewrite using a positive construction"],
                severity='low', text=text, context=context,
                flagged_text=f"{token.text} {head.text}",
                span=(token.idx, head.idx + len(head.text)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2: Sentence length
    # ------------------------------------------------------------------

    def _check_sentence_length(self, sent, sent_index, text, context, errors):
        """Flag sentences exceeding the IBM-recommended word limit."""
        words = [t for t in sent if not t.is_punct and not t.is_space]
        if len(words) <= _MAX_SENTENCE_WORDS:
            return
        error = self._create_error(
            sentence=sent.text, sentence_index=sent_index,
            message=(
                f"Sentence has {len(words)} words. "
                f"Keep sentences under {_MAX_SENTENCE_WORDS} words "
                f"for global audiences."
            ),
            suggestions=["Split into two or more shorter sentences"],
            severity='low', text=text, context=context,
            flagged_text=sent.text,
            span=(sent.start_char, sent.end_char),
        )
        if error:
            errors.append(error)

    # ------------------------------------------------------------------
    # Check 3: Politeness terms in technical docs
    # ------------------------------------------------------------------

    def _check_politeness(self, sent, sent_index, text, context, errors):
        """Flag 'please' and 'thank you' in technical documentation."""
        sent_lower = sent.text.lower()
        for phrase, msg in [
            ('please', "Do not use 'please' in technical information. "
                       "It conveys the wrong tone for technical content."),
            ('thank you', "Do not use 'thank you' in technical information. "
                          "Terms of politeness are not regarded the same way "
                          "in all cultures."),
        ]:
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()
                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_index,
                    message=msg,
                    suggestions=[f"Remove '{found}' and rephrase directly"],
                    severity='low', text=text, context=context,
                    flagged_text=found, span=(start, end),
                )
                if error:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 4: Self-referential text
    # ------------------------------------------------------------------

    def _check_self_referential(self, sent, sent_index, text, context, errors):
        """Flag 'This topic is about' and similar self-referential phrases."""
        sent_lower = sent.text.lower()
        for pattern in _SELF_REFERENTIAL_PATTERNS:
            match = re.search(pattern, sent_lower)
            if match:
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()
                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_index,
                    message=(
                        f"Avoid self-referential text: '{found}'. "
                        f"Focus on the content, not on the document itself."
                    ),
                    suggestions=[
                        "Rewrite to focus on the subject matter directly"
                    ],
                    severity='low', text=text, context=context,
                    flagged_text=found, span=(start, end),
                )
                if error:
                    errors.append(error)
                break  # One match per sentence is enough

    # ------------------------------------------------------------------
    # Check 5: Expletive constructions
    # ------------------------------------------------------------------

    def _check_expletive(self, sent, sent_index, text, context, doc, errors):
        """Flag expletive 'it is' and 'there are' constructions."""
        for token in sent:
            if token.dep_ != 'expl':
                continue
            head = token.head
            flagged = f"{token.text} {head.text}"
            error = self._create_error(
                sentence=sent.text, sentence_index=sent_index,
                message=(
                    f"Avoid the expletive construction '{flagged}'. "
                    f"Make the real subject the grammatical subject."
                ),
                suggestions=[
                    "Rewrite with a concrete subject "
                    "(e.g., 'Two databases are in the table space' "
                    "instead of 'There are two databases...')"
                ],
                severity='low', text=text, context=context,
                flagged_text=flagged,
                span=(token.idx, head.idx + len(head.text)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 6: Double negatives
    # ------------------------------------------------------------------

    def _check_double_negatives(self, sent, sent_index, text, context, errors):
        """Flag 'not uncommon' → 'common' and similar double negatives."""
        for match in _DOUBLE_NEG_RE.finditer(sent.text):
            neg_word = match.group(1).lower()
            positive = _DOUBLE_NEGATIVES.get(neg_word, '')
            if not positive:
                continue
            found = match.group(0)
            start = sent.start_char + match.start()
            end = sent.start_char + match.end()
            error = self._create_error(
                sentence=sent.text, sentence_index=sent_index,
                message=(
                    f"Avoid double negative '{found}'. "
                    f"Use '{positive}' for clarity."
                ),
                suggestions=[
                    f"Replace '{found}' with '{positive}'.",
                ],
                severity='low', text=text, context=context,
                flagged_text=found, span=(start, end),
            )
            if error:
                errors.append(error)
