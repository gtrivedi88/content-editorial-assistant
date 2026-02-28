"""
Commands Rule — Deterministic regex detection.
IBM Style Guide (p.246):
1. Do not use a command name as a verb.
2. Specify the keyword type (command, parameter, option) after the name.
"""
import os
import re
from typing import List, Dict, Any, Optional

import yaml

from rules.base_rule import in_code_range
from .base_technical_rule import BaseTechnicalRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'commands_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()
_KNOWN_COMMANDS = {c.lower() for c in _CONFIG.get('known_commands', [])}

# ALL-CAPS word (3+ chars) used as if it were a verb:
# "REORG the database", "IMPORT the data", "DROP the object"
_ALLCAPS_VERB_RE = re.compile(
    r'\b([A-Z]{3,})\s+(?:the|a|an|this|that|all|some|your|my)\s+\w+',
)

# Common English abbreviations and acronyms — never command-as-verb
_ALLCAPS_SAFE = frozenset([
    'THE', 'AND', 'FOR', 'BUT', 'NOT', 'ALL', 'ARE', 'WAS', 'HAS', 'HAD',
    'CAN', 'MAY', 'USE', 'SET', 'GET', 'PUT', 'ADD', 'RUN', 'SEE', 'TRY',
    'LET', 'SAY', 'END', 'NEW', 'OLD', 'OUR', 'ANY', 'ITS', 'YOU', 'HOW',
    'WHO', 'API', 'SDK', 'URL', 'SQL', 'XML', 'CSS', 'HTML', 'JSON', 'YAML',
    'HTTP', 'HTTPS', 'REST', 'SOAP', 'DITA', 'IBM', 'CLI', 'GUI', 'IDE',
    'RAM', 'CPU', 'GPU', 'SSD', 'HDD', 'LAN', 'WAN', 'VPN', 'DNS', 'SSH',
    'FTP', 'PDF', 'CSV', 'TXT', 'NOTE', 'IMPORTANT', 'WARNING', 'CAUTION',
    'TIP', 'ATTENTION', 'DANGER', 'TODO', 'FIXME',
    # Additional common acronyms
    'TCP', 'UDP', 'TLS', 'SSL', 'JWT', 'RSA', 'AES', 'SHA',
    'LDAP', 'SMTP', 'IMAP', 'POP', 'AMQP', 'MQTT', 'GRPC',
    'RHEL', 'ROSA', 'RHOCP', 'RHOAI', 'FIPS', 'STIG',
    'RBAC', 'ABAC', 'SAML', 'OIDC', 'OAUTH', 'HMAC',
    'RAID', 'NVME', 'ISCSI', 'CIFS', 'NFS', 'EBS',
    'CICD', 'YAML', 'TOML', 'HELM', 'KUBE',
    'AWS', 'GCP', 'OCI', 'EKS', 'AKS', 'GKE',
])


class CommandsRule(BaseTechnicalRule):
    """Flag command names used as verbs."""

    def _get_rule_type(self) -> str:
        return 'technical_commands'

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
            self._check_allcaps_command_as_verb(sentence, idx, text, context, errors, code_ranges, sent_start)
        return errors

    def _check_allcaps_command_as_verb(self, sentence, idx, text, context, errors, code_ranges, sent_start):
        """Flag ALL-CAPS command names used as verbs: 'REORG the database'."""
        for match in _ALLCAPS_VERB_RE.finditer(sentence):
            cmd = match.group(1)

            if cmd in _ALLCAPS_SAFE:
                continue
            if in_code_range(sent_start + match.start(), code_ranges):
                continue

            error = self._create_error(
                sentence=sentence, sentence_index=idx,
                message=(
                    f"Do not use the command name '{cmd}' as a verb. "
                    f"Use a descriptive verb and refer to the {cmd} command."
                ),
                suggestions=[
                    f"Use the {cmd} command to ...",
                    f"Issue the {cmd} command.",
                    f"Run the {cmd} command.",
                ],
                severity='medium', text=text, context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)


