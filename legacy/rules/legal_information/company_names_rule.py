"""
Company Names Rule — Deterministic SpaCy NER + YAML registry detection.
IBM Style Guide (Page 280): Use the full, official name of a company
or organization.

Uses SpaCy NER to find ORG entities, then checks against the company
registry in config/companies.yaml.
To add new companies, edit the YAML file — no code changes needed.
"""
import os
import yaml
from typing import List, Dict, Any, Optional
from .base_legal_rule import BaseLegalRule


def _load_registry() -> Dict[str, Dict[str, Any]]:
    """Load company registry from YAML and build a lookup dict."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'companies.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}

    registry = {}
    static = config.get('company_sources', {}).get('static', {})
    if not static.get('enabled', False):
        return {}

    for company in static.get('companies', []):
        name = company.get('name', '')
        if not name:
            continue
        entry = {
            'name': name,
            'aliases': [a.lower() for a in company.get('aliases', [])],
        }
        # Index by name and all aliases for fast lookup
        registry[name.lower()] = entry
        for alias in company.get('aliases', []):
            registry[alias.lower()] = entry
    return registry


_REGISTRY = _load_registry()


class CompanyNamesRule(BaseLegalRule):
    """Detects company name references and checks for official naming."""

    def _get_rule_type(self) -> str:
        return 'company_names'

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
            self._check_entities(sent, i, text, context, doc, errors)

        return errors

    def _check_entities(self, sent, sent_index: int, text: str,
                        context, doc, errors: List[Dict[str, Any]]) -> None:
        """Check ORG entities against the company registry."""
        for token in sent:
            if token.ent_type_ != 'ORG' or token.ent_iob_ != 'B':
                continue
            entity_text, end_idx = self._collect_entity_span(token, doc)
            self._flag_alias_usage(
                entity_text, end_idx, token, sent, sent_index,
                text, context, doc, errors)

    @staticmethod
    def _collect_entity_span(start_token, doc):
        """Collect the full text and end index of a multi-token ORG entity."""
        parts = [start_token.text]
        end_idx = start_token.i
        for j in range(start_token.i + 1, len(doc)):
            if doc[j].ent_type_ == 'ORG' and doc[j].ent_iob_ == 'I':
                parts.append(doc[j].text)
                end_idx = j
            else:
                break
        return ' '.join(parts), end_idx

    def _flag_alias_usage(self, entity_text: str, end_idx: int, token,
                          sent, sent_index: int, text: str, context,
                          doc, errors: List[Dict[str, Any]]) -> None:
        """Flag when a company alias is used instead of the official name."""
        entry = _REGISTRY.get(entity_text.lower())
        if not entry:
            return
        official_name = entry['name']
        if entity_text.lower() == official_name.lower():
            return
        # Only flag if it's a known alias
        if entity_text.lower() not in entry['aliases']:
            return

        last_token = doc[end_idx]
        error = self._create_error(
            sentence=sent.text,
            sentence_index=sent_index,
            message=(
                f"Use the full company name '{official_name}' "
                f"instead of the alias '{entity_text}'."
            ),
            suggestions=[
                f"Change '{entity_text}' to '{official_name}'",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=entity_text,
            span=(token.idx, last_token.idx + len(last_token.text)),
        )
        if error:
            errors.append(error)
