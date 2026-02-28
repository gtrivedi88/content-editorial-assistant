"""
Definitions Rule — Deterministic conditional detection.
Source: Red Hat Vale Definitions rule.
IBM Style Guide (p. 1): Define acronyms and abbreviations on first use.

Checks that 3-5 letter uppercase acronyms are defined in parentheses
somewhere in the text. For example, if "RBAC" appears, the text should
also contain "(RBAC)".
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

from .base_language_rule import BaseLanguageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Match uppercase acronyms 3-5 chars (with optional trailing 's')
_ACRONYM_USE = re.compile(r'\b([A-Z]{3,5}s?)\b')

# Match parenthetical definitions: (RBAC), (APIs), etc.
_ACRONYM_DEF = re.compile(r'\(([A-Z]{3,5}s?)\)')


def _load_exceptions() -> frozenset:
    """Load well-known acronyms that don't need definitions."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'definitions_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            items = config.get('well_known_acronyms', [])
            return frozenset(items)
    except (FileNotFoundError, yaml.YAMLError):
        return frozenset()


_WELL_KNOWN = _load_exceptions()


class DefinitionsRule(BaseLanguageRule):
    """Flag acronyms that are not defined on first occurrence."""

    def _get_rule_type(self) -> str:
        return 'definitions'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []

        # Find all defined acronyms in the text
        defined = {m.group(1) for m in _ACRONYM_DEF.finditer(text)}

        # Find all used acronyms
        seen_acronyms: set = set()
        doc = spacy_doc if (spacy_doc is not None) else (nlp(text) if nlp else None)

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                for match in _ACRONYM_USE.finditer(sent.text):
                    acronym = match.group(1)
                    if acronym in seen_acronyms:
                        continue
                    seen_acronyms.add(acronym)

                    if acronym in _WELL_KNOWN:
                        continue
                    if acronym in defined:
                        continue

                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"Define acronyms and abbreviations (such as "
                            f"'{acronym}') on first occurrence if they're "
                            f"likely to be unfamiliar."
                        ),
                        suggestions=[
                            f"Define '{acronym}' on first use, e.g., "
                            f"'Full Name ({acronym})'."
                        ],
                        severity='low',
                        text=text,
                        context=context,
                        flagged_text=acronym,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)
        else:
            for i, sentence in enumerate(sentences):
                for match in _ACRONYM_USE.finditer(sentence):
                    acronym = match.group(1)
                    if acronym in seen_acronyms:
                        continue
                    seen_acronyms.add(acronym)
                    if acronym in _WELL_KNOWN:
                        continue
                    if acronym in defined:
                        continue

                    error = self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=(
                            f"Define acronyms and abbreviations (such as "
                            f"'{acronym}') on first occurrence if they're "
                            f"likely to be unfamiliar."
                        ),
                        suggestions=[
                            f"Define '{acronym}' on first use, e.g., "
                            f"'Full Name ({acronym})'."
                        ],
                        severity='low',
                        text=text,
                        context=context,
                        flagged_text=acronym,
                        span=(match.start(), match.end()),
                    )
                    if error:
                        errors.append(error)

        return errors
