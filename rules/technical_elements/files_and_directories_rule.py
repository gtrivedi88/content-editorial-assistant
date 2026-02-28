"""
Files and Directories Rule — Deterministic regex detection.
IBM Style Guide (p.248-249):
1. Do not use a file extension, file type, or directory name as a noun.
   Follow with 'file', 'directory', etc.
2. Use the article 'a' (not 'an') before file extensions (the dot is
   pronounced, so '.exe' starts with a consonant sound).
3. Avoid placing the noun 'file' or 'directory' before the name.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Common file extensions for matching
_EXT_GROUP = (
    r'pdf|docx?|xlsx?|csv|txt|xml|json|yaml|yml|html?|css|js|py|java|'
    r'cpp|exe|zip|tar|gz|png|jpe?g|gif|svg|md|adoc|dita|log|conf|ini|'
    r'toml|rb|go|rs|swift|kt|ts|sh|bat|sql|war|jar|dll|so|rpm|deb'
)

# Extension used as standalone noun without 'file/format/type' after it.
# "Convert to .pdf", "Save as .docx", "Export .csv"
_EXT_AS_NOUN_RE = re.compile(
    r'(?:to|as|a|an|the|into)\s+'
    rf'(\.(?:{_EXT_GROUP}))'
    r'(?!\s*(?:file|format|type|extension|document))\b',
    re.IGNORECASE,
)

# Wrong article: "an .exe file" should be "a .exe file"
_AN_DOT_EXT_RE = re.compile(
    rf'\ban\s+(\.(?:{_EXT_GROUP}))\s+file\b',
    re.IGNORECASE,
)

# Noun 'file'/'directory' placed BEFORE the name:
# "the file readme.txt" → "the readme.txt file"
_NOUN_BEFORE_NAME_RE = re.compile(
    r'\b(?:the|a)\s+(file|directory)\s+(`?[\w][\w.-]+`?)\b',
    re.IGNORECASE,
)

# Compound nouns where "file X" or "directory X" is correct
_NOUN_BEFORE_SAFE = frozenset([
    'system', 'manager', 'structure', 'permissions', 'size', 'name',
    'path', 'type', 'format', 'extension', 'server', 'transfer',
    'descriptor', 'handle', 'lock', 'sharing', 'listing', 'browser',
    'explorer', 'service', 'hierarchy', 'tree', 'separator', 'access',
    'is', 'was', 'has', 'that', 'which', 'and', 'or', 'for', 'from',
    'to', 'in', 'on', 'at', 'by', 'with', 'into', 'can', 'must',
])


class FilesAndDirectoriesRule(BaseTechnicalRule):
    """Flag incorrect usage of file extensions and directory names."""

    def _get_rule_type(self) -> str:
        return 'technical_files_directories'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_ext_as_noun(sentence, idx, text, context, errors, code_ranges, sent_start)
            self._check_wrong_article(sentence, idx, text, context, errors)
            self._check_noun_before_name(sentence, idx, text, context, errors)
        return errors

    def _check_ext_as_noun(self, sentence, idx, text, context, errors, code_ranges, sent_start):
        """Flag file extensions used as nouns without 'file' after them."""
        for match in _EXT_AS_NOUN_RE.finditer(sentence):
            ext = match.group(1)
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the file extension '{ext}' as a noun. "
                    f"Follow it with 'file': '{ext} file'."
                ),
                suggestions=[f"a {ext} file"],
                severity='medium', text=text, context=context,
                flagged_text=ext,
                span=(match.start(1), match.end(1)),
            )
            if error:
                errors.append(error)

    def _check_wrong_article(self, sentence, idx, text, context, errors):
        """Flag 'an .ext file' — should be 'a .ext file'."""
        for match in _AN_DOT_EXT_RE.finditer(sentence):
            ext = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use 'a' before '{ext}', not 'an'. The period is "
                    f"pronounced 'dot' (consonant sound)."
                ),
                suggestions=[f"a {ext} file"],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_noun_before_name(self, sentence, idx, text, context, errors):
        """Flag 'the file readme.txt' — should be 'the readme.txt file'."""
        for match in _NOUN_BEFORE_NAME_RE.finditer(sentence):
            noun = match.group(1)
            name = match.group(2).strip('`')

            if name.lower() in _NOUN_BEFORE_SAFE:
                continue
            # Must look like a filename (contains dot, dash, or underscore)
            if not re.search(r'[.\-_]', name):
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Place '{noun}' after the name, not before. "
                    f"Write 'the {name} {noun}'."
                ),
                suggestions=[f"the {name} {noun}"],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)
