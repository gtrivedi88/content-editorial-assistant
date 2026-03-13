"""Unified term registry for LanguageTool false-positive suppression.

Builds a case-sensitive frozenset at module import from 7 YAML config files
(~7,500 correct-form domain terms).  Provides ``is_known_term`` for exact
matching and ``is_likely_code`` for heuristic code-pattern detection.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_RULES_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Heuristic code-pattern regexes (for terms not in any config)
# ---------------------------------------------------------------------------
_CODE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r'[a-z][A-Z]'),              # camelCase
    re.compile(r'^[A-Z][a-z]+[A-Z]'),       # PascalCase
    re.compile(r'_[a-z]'),                   # snake_case
    re.compile(r'^/[\w/]+'),                 # file paths /usr/bin/
    re.compile(r'^\w+[-]\w+[-]\w+'),         # hyphenated-multi-word
    re.compile(r'^v?\d+\.\d+'),              # version numbers v2.1.3
    re.compile(r'^[A-Z]{2,}$'),              # ALL-CAPS acronyms
    re.compile(r'[{}\[\]<>|&;$]'),           # shell/code characters
    re.compile(r'\.\w{1,4}$'),               # file extensions .yaml, .py
    re.compile(r'^--?\w'),                   # CLI flags --namespace, -v
]

# ---------------------------------------------------------------------------
# Registry construction
# ---------------------------------------------------------------------------


def _load_yaml(rel_path: str) -> Any:
    """Load a YAML file relative to the rules directory."""
    full = _RULES_DIR / rel_path
    if not full.exists():
        logger.warning("Term registry: config not found: %s", full)
        return None
    with open(full, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _build_registry() -> frozenset[str]:
    """Collect correct-form terms from all config sources."""
    terms: set[str] = set()

    # 1. Spelling allowlist — all terms as-is (curated lowercase domain terms)
    data = _load_yaml("config/spelling_allowlist.yaml")
    if data and isinstance(data.get("terms"), list):
        for t in data["terms"]:
            if isinstance(t, str) and t.strip():
                terms.add(t.strip())

    # 2. Case-sensitive terms — VALUES only (correct forms)
    data = _load_yaml(
        "technical_elements/config/case_sensitive_terms_config.yaml"
    )
    if data and isinstance(data.get("terms"), dict):
        for val in data["terms"].values():
            if isinstance(val, str) and val.strip():
                terms.add(val.strip())

    # 3. Product names — VALUES only (correct product names)
    data = _load_yaml("word_usage/config/product_names_config.yaml")
    if data and isinstance(data.get("simple_terms"), dict):
        for val in data["simple_terms"].values():
            if isinstance(val, str) and val.strip():
                terms.add(val.strip())

    # 4. Abbreviations — KEYS only (abbreviation forms: API, CLI, RBAC)
    data = _load_yaml(
        "language_and_grammar/config/abbreviations_config.yaml"
    )
    if data and isinstance(data.get("abbreviation_expansions"), dict):
        for key in data["abbreviation_expansions"]:
            if isinstance(key, str) and key.strip():
                terms.add(key.strip())

    # 5. Terminology — preferred terms (values) only
    data = _load_yaml(
        "language_and_grammar/config/terminology_config.yaml"
    )
    if data and isinstance(data.get("term_map"), dict):
        for val in data["term_map"].values():
            if isinstance(val, str) and val.strip():
                terms.add(val.strip())

    # 6. CamelCase exceptions — all terms as-is
    data = _load_yaml(
        "structure_and_format/config/camelcase_exceptions.yaml"
    )
    if data and isinstance(data.get("exceptions"), list):
        for t in data["exceptions"]:
            if isinstance(t, str) and t.strip():
                terms.add(t.strip())

    # 7. Companies — name, legal_names, aliases
    data = _load_yaml("legal_information/config/companies.yaml")
    if data:
        sources = data.get("company_sources", {})
        static = sources.get("static", {})
        if isinstance(static.get("companies"), list):
            for company in static["companies"]:
                if not isinstance(company, dict):
                    continue
                name = company.get("name")
                if isinstance(name, str) and name.strip():
                    terms.add(name.strip())
                for ln in company.get("legal_names") or []:
                    if isinstance(ln, str) and ln.strip():
                        terms.add(ln.strip())
                for alias in company.get("aliases") or []:
                    if isinstance(alias, str) and alias.strip():
                        terms.add(alias.strip())

    logger.info("Term registry: loaded %d terms from YAML configs", len(terms))
    return frozenset(terms)


# Module-level singleton — built once at import time
_REGISTRY: frozenset[str] = _build_registry()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def is_known_term(text: str) -> bool:
    """Return True if *text* is a recognized domain term.

    Uses case-sensitive exact matching against correct forms only.
    No substring matching — ``"Red"`` does NOT match
    ``"Red Hat Enterprise Linux"``.
    """
    return text in _REGISTRY


def is_likely_code(text: str) -> bool:
    """Return True if *text* looks like a code identifier or CLI fragment.

    Applies heuristic regex patterns for camelCase, snake_case, file paths,
    version numbers, CLI flags, etc.
    """
    if not text or len(text) < 2:
        return False
    for pattern in _CODE_PATTERNS:
        if pattern.search(text):
            return True
    return False
