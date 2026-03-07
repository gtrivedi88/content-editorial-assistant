#!/usr/bin/env python3
"""
Vale-to-CEA comprehensive diff script.
Parses all Vale swap files and CEA config files, identifies missing entries.
"""

import re
import yaml
import sys
from collections import defaultdict


# --- File paths ---

VALE_DIR = "vale-at-red-hat/.vale/styles/RedHat"
VALE_FILES = {
    "TermsErrors": f"{VALE_DIR}/TermsErrors.yml",
    "TermsWarnings": f"{VALE_DIR}/TermsWarnings.yml",
    "TermsSuggestions": f"{VALE_DIR}/TermsSuggestions.yml",
    "SimpleWords": f"{VALE_DIR}/SimpleWords.yml",
    "DoNotUseTerms": f"{VALE_DIR}/DoNotUseTerms.yml",
    "Hyphens": f"{VALE_DIR}/Hyphens.yml",
}

CEA_FILES = {
    "word_usage": "rules/word_usage/config/word_usage_config.yaml",
    "terminology": "rules/language_and_grammar/config/terminology_config.yaml",
    "compound_words": "rules/punctuation/config/compound_words_config.yaml",
    "conversational": "rules/audience_and_medium/config/conversational_vocabularies.yaml",
    "do_not_use": "rules/word_usage/config/do_not_use_config.yaml",
    "simple_words": "rules/word_usage/config/simple_words_config.yaml",
}


# --- Regex simplification ---

def simplify_vale_key(key):
    """
    Simplify a Vale regex key to plain text entries.
    Returns a list of plain_text strings.
    """
    cleaned = str(key)

    # Step a: Remove lookbehinds: (?<!...) and (?<=...) entirely
    cleaned = re.sub(r'\(\?<[!=][^)]*\)', '', cleaned)

    # Step b: Remove lookaheads: (?!...) and (?=...) entirely
    cleaned = re.sub(r'\(\?[!=][^)]*\)', '', cleaned)

    # Step g: Remove \b word boundaries
    cleaned = cleaned.replace(r'\b', '')

    # Step h: Remove anchors
    cleaned = cleaned.lstrip('^').rstrip('$')

    # Step f: Replace \s with space
    cleaned = cleaned.replace(r'\s', ' ')

    # Remove regex escapes for literal chars
    cleaned = cleaned.replace(r'\/', '/')

    # Step c: Handle non-capturing groups (?:X|Y) -> take first alternative X
    max_iterations = 10
    for _ in range(max_iterations):
        new_cleaned = re.sub(r'\(\?:([^()]*)\)', lambda m: m.group(1).split('|')[0], cleaned)
        if new_cleaned == cleaned:
            break
        cleaned = new_cleaned

    # Step e: Remove optional quantifiers: ? after a char -> include the char
    cleaned = re.sub(r'(\w)\?', r'\1', cleaned)
    cleaned = re.sub(r'\)\?', ')', cleaned)
    # Remove standalone ?
    cleaned = cleaned.replace('?', '')

    # Step d: Handle character classes [bB] -> take first char
    cleaned = re.sub(r'\[([^\]]+)\]', lambda m: m.group(1)[0], cleaned)

    # Remove remaining parentheses
    cleaned = cleaned.replace('(', '').replace(')', '')

    # Clean up extra spaces
    cleaned = re.sub(r'  +', ' ', cleaned).strip()

    # Step i: Handle top-level alternation X|Y|Z -> split into separate entries
    if '|' in cleaned:
        parts = [p.strip() for p in cleaned.split('|') if p.strip()]
        return parts
    else:
        if cleaned.strip():
            return [cleaned.strip()]
        return []


def simplify_vale_replacement(replacement):
    """Convert Vale replacement format (pipe-separated) to CEA format (comma-separated)."""
    repl = str(replacement)
    if '|' in repl:
        parts = [p.strip() for p in repl.split('|')]
        return ', '.join(parts)
    return repl


# --- Parse Vale files ---

def parse_vale_file(filepath):
    """Parse a Vale YAML swap file and return entries."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    swap = data.get('swap', {})
    if not swap:
        return [], []

    entries = []
    pattern_entries = []

    for key, replacement in swap.items():
        key_str = str(key)
        repl_str = str(replacement)

        # Check if replacement uses backreferences ($1, $2)
        if re.search(r'\$\d', repl_str):
            pattern_entries.append((key_str, repl_str, "backreference in replacement"))
            continue

        plain_keys = simplify_vale_key(key_str)
        repl_cea = simplify_vale_replacement(repl_str)

        for pk in plain_keys:
            if pk:
                entries.append((pk, repl_cea, key_str))

    return entries, pattern_entries


def parse_vale_donotuse(filepath):
    """Parse DoNotUseTerms - swap value is error message, not replacement."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    swap = data.get('swap', {})
    if not swap:
        return [], []

    entries = []
    pattern_entries = []

    for key, message in swap.items():
        key_str = str(key)
        msg_str = str(message)

        plain_keys = simplify_vale_key(key_str)

        for pk in plain_keys:
            if pk:
                entries.append((pk, msg_str, key_str))

    return entries, pattern_entries


# --- Parse CEA config files ---

def parse_word_usage_config(filepath):
    """Parse word_usage_config.yaml - nested by letter sections."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    if data:
        for section_key, section_val in data.items():
            if isinstance(section_val, dict):
                for term in section_val:
                    keys.add(str(term).lower())
    return keys


def parse_terminology_config(filepath):
    """Parse terminology_config.yaml - flat term_map."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    term_map = data.get('term_map', {})
    if term_map:
        for term in term_map:
            keys.add(str(term).lower())
    return keys


def parse_compound_words_config(filepath):
    """Parse compound_words_config.yaml - flat compound_words map."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    compounds = data.get('compound_words', {})
    if compounds:
        for term in compounds:
            keys.add(str(term).lower())
    return keys


def parse_conversational_vocabularies(filepath):
    """Parse conversational_vocabularies.yaml - nested formal words."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    formal_to_conv = data.get('formal_to_conversational', {})
    if formal_to_conv:
        for category_name, category_list in formal_to_conv.items():
            if isinstance(category_list, list):
                for entry in category_list:
                    if isinstance(entry, dict) and 'formal' in entry:
                        keys.add(str(entry['formal']).lower())
    return keys


def parse_do_not_use_config(filepath):
    """Parse do_not_use_config.yaml - terms with messages."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    terms = data.get('terms', {})
    if terms:
        for term in terms:
            keys.add(str(term).lower())
    return keys


def parse_simple_words_config(filepath):
    """Parse simple_words_config.yaml - flat simple_words map."""
    with open(filepath, 'r') as f:
        data = yaml.safe_load(f)

    keys = set()
    words = data.get('simple_words', {})
    if words:
        for term in words:
            keys.add(str(term).lower())
    return keys


# --- Main analysis ---

def main():
    # Parse all CEA configs
    print("=" * 80)
    print("PARSING CEA CONFIG FILES")
    print("=" * 80)

    cea_word_usage = parse_word_usage_config(CEA_FILES["word_usage"])
    cea_terminology = parse_terminology_config(CEA_FILES["terminology"])
    cea_compound_words = parse_compound_words_config(CEA_FILES["compound_words"])
    cea_conversational = parse_conversational_vocabularies(CEA_FILES["conversational"])
    cea_do_not_use = parse_do_not_use_config(CEA_FILES["do_not_use"])
    cea_simple_words = parse_simple_words_config(CEA_FILES["simple_words"])

    print(f"  word_usage_config.yaml:            {len(cea_word_usage)} entries")
    print(f"  terminology_config.yaml:           {len(cea_terminology)} entries")
    print(f"  compound_words_config.yaml:        {len(cea_compound_words)} entries")
    print(f"  conversational_vocabularies.yaml:  {len(cea_conversational)} entries")
    print(f"  do_not_use_config.yaml:            {len(cea_do_not_use)} entries")
    print(f"  simple_words_config.yaml:          {len(cea_simple_words)} entries")

    # Combined lookups
    cea_terms_combined = cea_word_usage | cea_terminology
    cea_simple_combined = cea_simple_words | cea_conversational | cea_word_usage | cea_terminology
    cea_donotuse_combined = cea_do_not_use | cea_word_usage
    cea_hyphens_combined = cea_compound_words | cea_word_usage

    print(f"\n  Combined terms lookup (word_usage+terminology): {len(cea_terms_combined)} entries")
    print(f"  Combined simple lookup (simple+conv+wu+term):   {len(cea_simple_combined)} entries")
    print(f"  Combined donotuse lookup (dnu+wu):              {len(cea_donotuse_combined)} entries")
    print(f"  Combined hyphens lookup (compound+wu):          {len(cea_hyphens_combined)} entries")

    # Track results
    missing_for_word_usage = []
    missing_for_simple_words = []
    missing_for_do_not_use = []
    missing_for_compound_words = []
    all_pattern_entries = []

    # -- TermsErrors --
    print("\n" + "=" * 80)
    print("PROCESSING: TermsErrors.yml (level: error, ignorecase: true)")
    print("=" * 80)
    entries, patterns = parse_vale_file(VALE_FILES["TermsErrors"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, replacement, orig_key in entries:
        if plain_key.lower() not in cea_terms_combined:
            missing.append((plain_key, replacement, orig_key, "TermsErrors"))
    print(f"  Missing from CEA (word_usage+terminology): {len(missing)}")
    missing_for_word_usage.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "TermsErrors") for p in patterns])

    # -- TermsWarnings --
    print("\n" + "=" * 80)
    print("PROCESSING: TermsWarnings.yml (level: warning, ignorecase: true)")
    print("=" * 80)
    entries, patterns = parse_vale_file(VALE_FILES["TermsWarnings"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, replacement, orig_key in entries:
        if plain_key.lower() not in cea_terms_combined:
            missing.append((plain_key, replacement, orig_key, "TermsWarnings"))
    print(f"  Missing from CEA (word_usage+terminology): {len(missing)}")
    missing_for_word_usage.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "TermsWarnings") for p in patterns])

    # -- TermsSuggestions --
    print("\n" + "=" * 80)
    print("PROCESSING: TermsSuggestions.yml (level: suggestion, ignorecase: false)")
    print("=" * 80)
    entries, patterns = parse_vale_file(VALE_FILES["TermsSuggestions"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, replacement, orig_key in entries:
        if plain_key.lower() not in cea_terms_combined:
            missing.append((plain_key, replacement, orig_key, "TermsSuggestions"))
    print(f"  Missing from CEA (word_usage+terminology): {len(missing)}")
    missing_for_word_usage.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "TermsSuggestions") for p in patterns])

    # -- SimpleWords --
    print("\n" + "=" * 80)
    print("PROCESSING: SimpleWords.yml (level: suggestion, ignorecase: true)")
    print("=" * 80)
    entries, patterns = parse_vale_file(VALE_FILES["SimpleWords"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, replacement, orig_key in entries:
        if plain_key.lower() not in cea_simple_combined:
            missing.append((plain_key, replacement, orig_key, "SimpleWords"))
    print(f"  Missing from CEA (simple+conversational+wu+term): {len(missing)}")
    missing_for_simple_words.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "SimpleWords") for p in patterns])

    # -- DoNotUseTerms --
    print("\n" + "=" * 80)
    print("PROCESSING: DoNotUseTerms.yml (level: warning, ignorecase: false)")
    print("=" * 80)
    entries, patterns = parse_vale_donotuse(VALE_FILES["DoNotUseTerms"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, message, orig_key in entries:
        if plain_key.lower() not in cea_donotuse_combined:
            missing.append((plain_key, message, orig_key, "DoNotUseTerms"))
    print(f"  Missing from CEA (do_not_use+word_usage): {len(missing)}")
    missing_for_do_not_use.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "DoNotUseTerms") for p in patterns])

    # -- Hyphens --
    print("\n" + "=" * 80)
    print("PROCESSING: Hyphens.yml (level: warning, ignorecase: true)")
    print("=" * 80)
    entries, patterns = parse_vale_file(VALE_FILES["Hyphens"])
    print(f"  Total entries extracted: {len(entries)}")
    print(f"  Pattern entries (complex regex): {len(patterns)}")

    missing = []
    for plain_key, replacement, orig_key in entries:
        if plain_key.lower() not in cea_hyphens_combined:
            missing.append((plain_key, replacement, orig_key, "Hyphens"))
    print(f"  Missing from CEA (compound_words+word_usage): {len(missing)}")
    missing_for_compound_words.extend(missing)
    all_pattern_entries.extend([(p[0], p[1], p[2], "Hyphens") for p in patterns])

    # --- Dedup ---
    def dedup_entries(entries_list):
        seen = set()
        result = []
        for entry in entries_list:
            key_lower = entry[0].lower()
            if key_lower not in seen:
                seen.add(key_lower)
                result.append(entry)
        return result

    missing_for_word_usage = dedup_entries(missing_for_word_usage)
    missing_for_simple_words = dedup_entries(missing_for_simple_words)
    missing_for_do_not_use = dedup_entries(missing_for_do_not_use)
    missing_for_compound_words = dedup_entries(missing_for_compound_words)

    # --- Output Results ---

    # word_usage_config.yaml additions
    print("\n\n")
    print("#" * 80)
    print("# MISSING ENTRIES FOR: word_usage_config.yaml")
    print(f"# Source: TermsErrors + TermsWarnings + TermsSuggestions")
    print(f"# Total missing: {len(missing_for_word_usage)}")
    print("#" * 80)
    print()

    missing_for_word_usage.sort(key=lambda x: x[0].lower())

    for plain_key, replacement, orig_key, source in missing_for_word_usage:
        if orig_key != plain_key:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}, original: {orig_key}')
        else:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}')

    # simple_words_config.yaml additions
    print("\n\n")
    print("#" * 80)
    print("# MISSING ENTRIES FOR: simple_words_config.yaml")
    print(f"# Source: SimpleWords")
    print(f"# Total missing: {len(missing_for_simple_words)}")
    print("#" * 80)
    print()

    missing_for_simple_words.sort(key=lambda x: x[0].lower())

    for plain_key, replacement, orig_key, source in missing_for_simple_words:
        if orig_key != plain_key:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}, original: {orig_key}')
        else:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}')

    # do_not_use_config.yaml additions
    print("\n\n")
    print("#" * 80)
    print("# MISSING ENTRIES FOR: do_not_use_config.yaml")
    print(f"# Source: DoNotUseTerms")
    print(f"# Total missing: {len(missing_for_do_not_use)}")
    print("#" * 80)
    print()

    missing_for_do_not_use.sort(key=lambda x: x[0].lower())

    for plain_key, message, orig_key, source in missing_for_do_not_use:
        print(f'  "{plain_key}":')
        print(f'    message: "{message}"')
        print()

    # compound_words_config.yaml additions
    print("\n\n")
    print("#" * 80)
    print("# MISSING ENTRIES FOR: compound_words_config.yaml")
    print(f"# Source: Hyphens")
    print(f"# Total missing: {len(missing_for_compound_words)}")
    print("#" * 80)
    print()

    missing_for_compound_words.sort(key=lambda x: x[0].lower())

    for plain_key, replacement, orig_key, source in missing_for_compound_words:
        if orig_key != plain_key:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}, original: {orig_key}')
        else:
            print(f'  "{plain_key}": "{replacement}"  # Vale {source}')

    # Pattern entries
    print("\n\n")
    print("#" * 80)
    print("# PATTERN-BASED ENTRIES (need pattern_terms section)")
    print(f"# These have complex regex that cannot be simplified to plain text")
    print(f"# Total: {len(all_pattern_entries)}")
    print("#" * 80)
    print()

    for regex_key, replacement_or_reason, reason, source in all_pattern_entries:
        print(f"  # Source: Vale {source}")
        print(f"  # Reason: {reason}")
        print(f'  # Pattern: {regex_key}')
        print(f'  # Replacement: {replacement_or_reason}')
        print()

    # Summary
    print("\n")
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"  Missing for word_usage_config.yaml:     {len(missing_for_word_usage)} entries")
    print(f"  Missing for simple_words_config.yaml:   {len(missing_for_simple_words)} entries")
    print(f"  Missing for do_not_use_config.yaml:     {len(missing_for_do_not_use)} entries")
    print(f"  Missing for compound_words_config.yaml: {len(missing_for_compound_words)} entries")
    print(f"  Pattern-based entries:                  {len(all_pattern_entries)} entries")
    print(f"  -----------------------------------------------")
    total = (len(missing_for_word_usage) + len(missing_for_simple_words) +
             len(missing_for_do_not_use) + len(missing_for_compound_words) +
             len(all_pattern_entries))
    print(f"  TOTAL MISSING FROM CEA:                 {total} entries")


if __name__ == "__main__":
    main()
