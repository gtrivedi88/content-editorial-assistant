"""
Command Syntax Rule — Deterministic regex detection.
IBM Style Guide (p.239-246):
1. When you specify a command, parameter, or option in text, specify the
   identifying noun (command, parameter, option) after the name.
   WRONG: You can use ``db2trc`` to record information.
   RIGHT: You can use the ``db2trc`` command to record information.
2. For multi-word variable names, remove spaces or use underscores.
   WRONG: <file name>   RIGHT: <filename> or <file_name>
3. Use consistent list style for parameter descriptions: start each
   description the same way (sentence fragment or full sentence).
"""
import re
from typing import List, Dict, Any, Optional

from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Backtick command in text without an identifying noun after it.
# "use the `db2trc` to record" → missing "command" after `db2trc`
# Guard: must look like a command name (lowercase, short, no spaces).
_CMD_WITHOUT_NOUN_RE = re.compile(
    r'\b(?:use|run|issue|execute|enter|type|invoke|start)\s+'
    r'(?:the\s+)?`([a-z][\w.-]{1,20})`'
    r'(?!\s+(?:command|utility|tool|program|script|function|statement'
    r'|parameter|option|API|method|macro))\b',
    re.IGNORECASE,
)

# Multi-word variable name inside angle brackets: <file name> → <filename>
# Detects spaces inside < > that should be removed or replaced with underscores.
_MULTI_WORD_VAR_RE = re.compile(
    r'<(\w+\s+\w+(?:\s+\w+)*)>',
)

# Guard: legitimate multi-word content inside angle brackets that is NOT a
# variable name (e.g., HTML tags, descriptive text).
_ANGLE_BRACKET_SAFE = frozenset([
    'see above', 'see below', 'not applicable', 'to be determined',
    'no value', 'any value', 'your value', 'default value',
])

# Bare command reference without backticks in instruction context.
# "run db2trc to" — should be "run the `db2trc` command to"
# Only flag well-known commands to avoid false positives.
_KNOWN_CLI_TOOLS = frozenset([
    'db2', 'db2trc', 'lssrc', 'mqsicreatebroker', 'mqsistart',
    'kubectl', 'docker', 'podman', 'helm', 'terraform',
    'ansible', 'vagrant', 'gradle', 'maven',
])

_BARE_CMD_RE = re.compile(
    r'\b(?:run|use|issue|execute|enter|type|invoke|start)\s+'
    r'(?:the\s+)?(\w+)\b'
    r'(?!\s+(?:command|utility|tool|program|script|function|statement'
    r'|parameter|option|API))',
    re.IGNORECASE,
)


class CommandSyntaxRule(BaseTechnicalRule):
    """Flag command syntax formatting and terminology issues."""

    def _get_rule_type(self) -> str:
        return 'technical_command_syntax'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_cmd_without_noun(sentence, idx, text, context, errors)
            self._check_multi_word_variable(sentence, idx, text, context, errors)
            self._check_bare_command(sentence, idx, text, context, errors)
        return errors

    def _check_cmd_without_noun(self, sentence, idx, text, context, errors):
        """Flag backtick command without identifying noun: 'use `cmd`' → 'use the `cmd` command'."""
        for match in _CMD_WITHOUT_NOUN_RE.finditer(sentence):
            cmd = match.group(1)
            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Specify the keyword type after '{cmd}'. "
                    f"Write 'the `{cmd}` command' to identify what '{cmd}' is."
                ),
                suggestions=[
                    f"the `{cmd}` command",
                    f"the `{cmd}` utility",
                ],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_multi_word_variable(self, sentence, idx, text, context, errors):
        """Flag multi-word variable names in angle brackets: <file name> → <filename>."""
        for match in _MULTI_WORD_VAR_RE.finditer(sentence):
            var_content = match.group(1)

            # Guard: skip known safe multi-word content
            if var_content.lower() in _ANGLE_BRACKET_SAFE:
                continue

            # Guard: skip if it looks like HTML or XML content
            if var_content.startswith('/') or '=' in var_content:
                continue

            no_spaces = var_content.replace(' ', '')
            with_underscores = var_content.replace(' ', '_')

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Remove spaces in variable names. "
                    f"Write '<{no_spaces}>' or '<{with_underscores}>' "
                    f"instead of '<{var_content}>'."
                ),
                suggestions=[
                    f"<{no_spaces}>",
                    f"<{with_underscores}>",
                ],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    def _check_bare_command(self, sentence, idx, text, context, errors):
        """Flag known CLI tools referenced without formatting or identifying noun."""
        for match in _BARE_CMD_RE.finditer(sentence):
            cmd = match.group(1)

            # Only flag known CLI tools
            if cmd.lower() not in _KNOWN_CLI_TOOLS:
                continue

            # Guard: skip if already in backticks (handled by _check_cmd_without_noun)
            if _in_backticks(sentence, match.start()):
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Use monospace formatting and specify the keyword type "
                    f"after '{cmd}'. Write 'the `{cmd}` command'."
                ),
                suggestions=[
                    f"the `{cmd}` command",
                ],
                severity='low', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


def _in_backticks(text: str, pos: int) -> bool:
    before = text[:pos]
    return before.count('`') % 2 != 0
