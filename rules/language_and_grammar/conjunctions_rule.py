"""
Conjunctions Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 101): Use subordinating conjunctions correctly.
'since' for time only, 'while' for time only, avoid 'if...then'.
"""

from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule


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
        """Flag 'while' when used as 'although' (non-temporal)."""
        errors = []
        for token in sent:
            if token.lemma_ != 'while' or token.dep_ != 'mark':
                continue

            # Check if temporal: look for concurrent-action indicators
            clause_tokens = list(token.head.subtree)
            has_time_indicator = any(
                t.ent_type_ in ('DATE', 'TIME')
                or (t.pos_ == 'VERB' and t.morph.get('Aspect') == ['Prog'])
                or t.lemma_ in (
                    'wait', 'run', 'execute', 'process', 'download', 'upload',
                    'install', 'load', 'boot', 'compile', 'build', 'deploy',
                )
                for t in clause_tokens
            )

            if not has_time_indicator:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=0,
                    message="Use 'although' instead of 'while' when expressing contrast (not time).",
                    suggestions=["Replace 'while' with 'although' if you mean contrast, not concurrent actions."],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=token.text,
                    span=(token.idx, token.idx + len(token.text))
                ))

        return errors

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
