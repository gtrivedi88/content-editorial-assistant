"""
Conjunctions Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 101): Use subordinating conjunctions correctly.
'since' for time only, 'while' for time only, avoid 'if...then'.
"""

from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule

# Linking/copular verbs — describe states, not actions.
# When these head a while-clause, the clause expresses a property/quality (contrastive).
_LINKING_VERBS = frozenset({
    'be', 'seem', 'appear', 'remain', 'become',
    'look', 'feel', 'sound', 'prove', 'stay',
})

# Adverbs in the main clause that signal contrast with the while-clause.
_CONTRASTIVE_ADVERBS = frozenset({
    'however', 'instead', 'nevertheless', 'nonetheless',
    'conversely', 'rather',
})


class ConjunctionsRule(BaseLanguageRule):
    """Detects misused subordinating conjunctions using SpaCy dependency parsing."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for sent in doc.sents:
            errors.extend(self._check_since(sent, text, context))
            errors.extend(self._check_while(sent, text, context))
            errors.extend(self._check_if_then(sent, text, context))

        return errors

    def _check_since(self, sent, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Flag 'since' when used as 'because' (non-temporal)."""
        errors = []
        for token in sent:
            if token.lemma_ != 'since' or token.dep_ != 'mark':
                continue

            # Check if temporal: look for time indicators in the clause
            clause_tokens = list(token.head.subtree)
            has_time_indicator = any(
                t.ent_type_ in ('DATE', 'TIME', 'CARDINAL')
                or t.lemma_ in (
                    'year', 'month', 'day', 'hour', 'week', 'minute', 'second',
                    'ago', 'yesterday', 'today', 'then', 'recently', 'earlier',
                    'version', 'release', 'update', 'upgrade', 'migration',
                    'inception', 'beginning', 'start', 'introduction', 'launch',
                )
                or t.like_num
                for t in clause_tokens
            )

            if not has_time_indicator:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=0,
                    message="Use 'because' instead of 'since' when expressing cause (not time).",
                    suggestions=["Replace 'since' with 'because' if you mean cause, not time."],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))

        return errors

    def _check_while(self, sent, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Flag 'while' only when positive contrastive evidence exists.

        Temporal 'while' (concurrent actions) is valid; contrastive 'while'
        (meaning 'although') should be replaced per IBM Style Guide.
        Ambiguous cases are left to the LLM granular pass.
        """
        errors = []
        for token in sent:
            if token.lemma_ != 'while' or token.dep_ != 'mark':
                continue

            clause_tokens = list(token.head.subtree)

            # Definite temporal signal — never flag
            if self._is_temporal_while(token, clause_tokens, sent):
                continue

            # Only flag when we have positive contrastive evidence
            if self._is_contrastive_while(token, clause_tokens, sent):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=0,
                    message="Use 'although' instead of 'while' when expressing "
                            "contrast (not time).",
                    suggestions=["although"],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))

            # Ambiguous — don't flag; LLM handles these

        return errors

    @staticmethod
    def _is_temporal_while(while_token, clause_tokens, sent) -> bool:
        """Detect positive temporal signals in a while-clause."""
        # DATE/TIME entities in the clause
        if any(t.ent_type_ in ('DATE', 'TIME') for t in clause_tokens):
            return True

        # Progressive aspect verb (-ing form) in the clause
        if any(
            t.pos_ == 'VERB' and t.morph.get('Aspect') == ['Prog']
            for t in clause_tokens
        ):
            return True

        # "either...while" structure implies simultaneity / choice of timing
        if any(
            t.lower_ == 'either' and t.i < while_token.i
            for t in sent
        ):
            return True

        return False

    @staticmethod
    def _is_contrastive_while(while_token, clause_tokens, sent) -> bool:
        """Detect positive contrastive signals — flag only when confident."""
        head = while_token.head

        # While-clause headed by a linking/copular verb describes a
        # state or quality, not an action — strong contrastive signal.
        # Guard: AUX with dep_='aux' is a true auxiliary ("is running"),
        # not copular ("is simple"), so exclude that.
        if head.lemma_ in _LINKING_VERBS:
            if not (head.pos_ == 'AUX' and head.dep_ == 'aux'):
                return True

        # Comparative adjectives/adverbs in the while-clause
        # (e.g., "simpler", "more portable", "less common")
        if any(
            t.tag_ in ('JJR', 'RBR') or t.lemma_ in ('more', 'less')
            for t in clause_tokens
        ):
            return True

        # Contrastive adverbs in the main clause (however, instead, etc.)
        clause_indices = frozenset(t.i for t in clause_tokens)
        if any(
            t.lemma_ in _CONTRASTIVE_ADVERBS
            for t in sent if t.i not in clause_indices
        ):
            return True

        return False

    def _check_if_then(self, sent, text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Flag unnecessary 'then' after 'if' clause."""
        errors = []
        has_if = False
        for token in sent:
            if token.lemma_ == 'if' and token.dep_ == 'mark':
                has_if = True
            elif has_if and token.lower_ == 'then' and token.dep_ == 'advmod':
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=0,
                    message="Omit 'then' after an 'if' clause.",
                    suggestions=["Remove 'then'. Example: 'If you set a password, access is restricted.'"],
                    severity='low',
                    text=text,
                    context=context,
                    flagged_text='then',
                    span=(token.idx, token.idx + len(token.text))
                ))
                break

        return errors
