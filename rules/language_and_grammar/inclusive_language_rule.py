"""
Inclusive Language Rule — Token-based detection.
IBM Style Guide: Inclusive language.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule


def _load_config() -> List[Dict[str, Any]]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'inclusive_language_terms.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return []

    terms = []
    for category_terms in config.get('non_inclusive_terms', {}).values():
        for term, data in category_terms.items():
            terms.append({
                'term': term.lower(),
                'replacement': data.get('replacement', ''),
                'severity': data.get('severity_level', 'medium'),
                'is_phrase': ' ' in term
            })
    return terms


_TERMS = _load_config()
_SINGLE_TERMS = {t['term']: t for t in _TERMS if not t['is_phrase']}
_PHRASE_TERMS = [t for t in _TERMS if t['is_phrase']]


class InclusiveLanguageRule(BaseLanguageRule):
    """Detects non-inclusive terms using token lemmas to catch variations like 'mastering' or 'slaves'."""

    def _get_rule_type(self) -> str:
        return 'inclusive_language'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ('listing', 'code_block', 'inline_code'):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for i, sent in enumerate(doc.sents):
            self._check_single_terms(sent, i, text, context, errors)
            self._check_phrase_terms(sent, i, text, context, errors)

        return errors

    def _check_single_terms(self, sent, sent_idx, text, context, errors):
        """Check individual tokens by text or lemma."""
        for token in sent:
            term_data = _SINGLE_TERMS.get(token.lower_) or _SINGLE_TERMS.get(token.lemma_.lower())
            if not term_data:
                continue

            error = self._create_error(
                sentence=sent.text, sentence_index=sent_idx,
                message=f"Non-inclusive term '{token.text}' detected. Use '{term_data['replacement']}' instead.",
                suggestions=[f"Change to '{term_data['replacement']}'"],
                severity=term_data['severity'],
                text=text, context=context, flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

    def _check_phrase_terms(self, sent, sent_idx, text, context, errors):
        """Check multi-word phrases via regex."""
        for p_data in _PHRASE_TERMS:
            pattern = r'\b' + re.escape(p_data['term']) + r'\b'
            for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                found = match.group(0)
                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_idx,
                    message=f"Non-inclusive term '{found}' detected. Use '{p_data['replacement']}' instead.",
                    suggestions=[f"Change to '{p_data['replacement']}'"],
                    severity=p_data['severity'],
                    text=text, context=context, flagged_text=found,
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                )
                if error:
                    errors.append(error)
