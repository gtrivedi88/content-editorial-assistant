"""
Command Line Data Entry Rule — Deterministic regex detection.
IBM Style Guide (p.237-239):
1. Use 'type', 'enter', or 'specify' to instruct users to provide data.
   Do not use informal verbs like 'input', 'key in', or 'put in'.
2. In documentation for only Windows, use 'command prompt'.
   For other OS or mixed OS documentation, use 'command line'.
3. Spell and capitalize data the same way the user must provide it.
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Wrong verbs for data entry instructions.
# "Input your password" → "Type your password"
# "Key in the value" → "Type the value"
# "Put in your user ID" → "Enter your user ID"
_WRONG_ENTRY_VERBS = [
    (
        re.compile(
            r'\b(input)\s+(?:the|your|a|an)\s+\w+',
            re.IGNORECASE,
        ),
        'input',
        "Use 'type' or 'enter' instead of 'input' for data entry instructions.",
        ["Type", "Enter"],
    ),
    (
        re.compile(
            r'\b(key\s+in)\s+(?:the|your|a|an)\s+\w+',
            re.IGNORECASE,
        ),
        'key in',
        "Use 'type' instead of 'key in' for data entry instructions.",
        ["Type"],
    ),
    (
        re.compile(
            r'\b(put\s+in)\s+(?:the|your|a|an)\s+\w+',
            re.IGNORECASE,
        ),
        'put in',
        "Use 'enter' or 'type' instead of 'put in' for data entry instructions.",
        ["Enter", "Type"],
    ),
    (
        re.compile(
            r'\b(feed)\s+(?:the|your|a|an)\s+(?:data|information|input|value)',
            re.IGNORECASE,
        ),
        'feed',
        "Use 'enter' or 'provide' instead of 'feed' for data entry instructions.",
        ["Enter", "Provide"],
    ),
]

# "command prompt" used in non-Windows context.
# Guard: only flag if text also mentions non-Windows OS.
_COMMAND_PROMPT_RE = re.compile(r'\bcommand\s+prompt\b', re.IGNORECASE)
_NON_WINDOWS_OS_RE = re.compile(
    r'\b(?:linux|unix|aix|macos|mac\s+os|solaris|z/os|'
    r'operating\s+systems?|all\s+platforms?|mixed\s+(?:os|operating))\b',
    re.IGNORECASE,
)


class CommandLineEntryRule(BaseTechnicalRule):
    """Flag incorrect data entry terminology."""

    def _get_rule_type(self) -> str:
        return 'technical_command_line_entry'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_wrong_entry_verbs(sentence, idx, text, context, errors)
            self._check_command_prompt(sentence, idx, text, context, errors)
        return errors

    def _check_wrong_entry_verbs(self, sentence, idx, text, context, errors):
        """Flag informal verbs for data entry: 'input', 'key in', 'put in'."""
        for pattern, verb, message, replacements in _WRONG_ENTRY_VERBS:
            for match in pattern.finditer(sentence):
                if _in_quotes(sentence, match.start()):
                    continue

                suggestions = [
                    match.group(0).replace(
                        match.group(1), r, 1
                    ) for r in replacements
                ]
                error = self._create_error(
                    sentence=sentence, sentence_index=idx,
                    message=message,
                    suggestions=suggestions,
                    severity='medium', text=text, context=context,
                    flagged_text=match.group(0),
                    span=(match.start(), match.end()),
                )
                if error:
                    errors.append(error)

    def _check_command_prompt(self, sentence, idx, text, context, errors):
        """Flag 'command prompt' when the doc covers non-Windows OS."""
        match = _COMMAND_PROMPT_RE.search(sentence)
        if not match:
            return

        # Only flag if the full text mentions non-Windows OS
        if not _NON_WINDOWS_OS_RE.search(text):
            return

        error = self._create_error(
            sentence=sentence, sentence_index=idx,
            message=(
                "Use 'command line' instead of 'command prompt' when "
                "documenting for non-Windows or mixed operating systems."
            ),
            suggestions=["command line"],
            severity='low', text=text, context=context,
            flagged_text=match.group(0),
            span=(match.start(), match.end()),
        )
        if error:
            errors.append(error)


def _in_quotes(text: str, pos: int) -> bool:
    before = text[:pos]
    return before.count('"') % 2 != 0 or before.count("'") % 2 != 0
