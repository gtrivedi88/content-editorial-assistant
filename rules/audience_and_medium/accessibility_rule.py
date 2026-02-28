"""
Accessibility Rule — Deterministic detection.
IBM Style Guide (Page 60): Ensure content is accessible to all users.

Checks:
1. All-caps words in prose (harder to read, challenge for dyslexia)
2. Color-only references (inaccessible to color-blind users)
3. Sensory-only directional references (inaccessible to screen reader users)

Configuration loaded from config/accessibility_config.yaml.
"""
import os
import re
import yaml
from typing import List, Dict, Any
from .base_audience_rule import BaseAudienceRule


def _load_config() -> Dict[str, Any]:
    """Load accessibility configuration from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'accessibility_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Known abbreviations/acronyms that are correctly all-caps (not flagged).
# Organized by category to aid maintenance. ~150+ entries.
_KNOWN_ACRONYMS: frozenset = frozenset({
    # Web / general tech
    'API', 'URL', 'HTTP', 'HTTPS', 'HTML', 'CSS', 'SQL', 'XML', 'JSON',
    'REST', 'CRUD', 'SSL', 'TLS', 'SSH', 'FTP', 'DNS', 'TCP', 'UDP',
    'CLI', 'GUI', 'SDK', 'JVM', 'JDK', 'IDE', 'YAML', 'PDF',
    # Cloud vendors / orgs
    'IBM', 'AWS', 'GCP',
    # Hardware
    'CPU', 'GPU', 'RAM', 'SSD', 'HDD',
    # Infrastructure / identity
    'NFS', 'LDAP', 'RBAC', 'CI', 'CD', 'VM', 'OS', 'IP',
    # UI/UX / misc short
    'UI', 'UX', 'ID', 'OK',
    # Admonition labels
    'NOTE', 'TIP', 'WARNING', 'IMPORTANT', 'CAUTION', 'DANGER',
    # Literals / mod-docs content types
    'TRUE', 'FALSE', 'NULL', 'PROCEDURE', 'CONCEPT', 'REFERENCE',
    # --- Red Hat products ---
    'RHEL', 'ROSA', 'OCP', 'ARO', 'RHOAI', 'RHOCP', 'RHODS', 'RHDH',
    'ANSIBLE', 'CEPH', 'QUAY',
    # --- Cloud / infra ---
    'KUBERNETES', 'OPENSHIFT', 'PODMAN', 'DOCKER', 'TERRAFORM',
    'VAGRANT', 'JENKINS',
    # --- Standards ---
    'ASCII', 'UTF', 'IEEE', 'POSIX', 'RFC', 'ISO', 'ANSI', 'OWASP', 'NIST',
    # --- Protocols ---
    'AMQP', 'MQTT', 'GRPC', 'QUIC', 'SCTP', 'IMAP', 'SMTP', 'POP',
    'SNMP', 'ICMP',
    # --- Storage / DB ---
    'RAID', 'ISCSI', 'CIFS', 'NVME', 'ETCD', 'REDIS', 'KAFKA',
    'ZOOKEEPER', 'MONGODB', 'MYSQL', 'POSTGRESQL',
    # --- Security ---
    'SAML', 'OIDC', 'OAUTH', 'HMAC', 'AES', 'RSA', 'FIPS', 'SIEM',
    'SOC', 'CVE', 'CVSS',
    # --- Misc tech ---
    'CORS', 'WASM', 'GRUB', 'BIOS', 'UEFI', 'NUMA', 'DPDK', 'SRIOV',
    'VXLAN', 'GENEVE',
})


class AccessibilityRule(BaseAudienceRule):
    """Detects accessibility issues in technical documentation."""

    def _get_rule_type(self) -> str:
        return 'accessibility'

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
            self._check_all_caps(sent, i, text, context, errors)
            self._check_color_references(sent, i, text, context, errors)
            self._check_sensory_directions(sent, i, text, context, errors)

        return errors

    def _check_all_caps(self, sent, sent_index, text, context, errors):
        """Flag all-caps words that are not acronyms (harder to read)."""
        for token in sent:
            if not token.text.isupper() or len(token.text) <= 1:
                continue
            if not token.text.isalpha():
                continue
            if token.text in _KNOWN_ACRONYMS:
                continue
            # Skip if short enough to be an acronym (8 chars or less)
            if len(token.text) <= 8:
                continue

            error = self._create_error(
                sentence=sent.text, sentence_index=sent_index,
                message=(
                    f"Avoid using all-caps '{token.text}'. "
                    f"All-caps text is harder to read and poses "
                    f"challenges for users with dyslexia."
                ),
                suggestions=[
                    f"Change '{token.text}' to '{token.text.capitalize()}' "
                    f"or '{token.text.lower()}'",
                ],
                severity='medium', text=text, context=context,
                flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

    def _check_color_references(self, sent, sent_index, text, context, errors):
        """Flag color-only references (inaccessible to color-blind users)."""
        sent_lower = sent.text.lower()
        for phrase in _CONFIG.get('color_indicator_phrases', []):
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()

                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_index,
                    message=(
                        f"Do not use color alone to convey information: "
                        f"'{found}'. Some users cannot perceive color."
                    ),
                    suggestions=[
                        "Add a non-color indicator (icon, label, or text) "
                        "alongside the color reference",
                    ],
                    severity='medium', text=text, context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)

    def _check_sensory_directions(self, sent, sent_index, text, context, errors):
        """Flag sensory-only directional references."""
        sent_lower = sent.text.lower()
        for phrase in _CONFIG.get('sensory_direction_phrases', []):
            pattern = r'\b' + re.escape(phrase) + r'\b'
            for match in re.finditer(pattern, sent_lower):
                found = sent.text[match.start():match.end()]
                start = sent.start_char + match.start()
                end = sent.start_char + match.end()

                error = self._create_error(
                    sentence=sent.text, sentence_index=sent_index,
                    message=(
                        f"Avoid using sensory direction '{found}' as the "
                        f"only way to identify a UI element. Screen reader "
                        f"users cannot perceive spatial location."
                    ),
                    suggestions=[
                        "Identify the element by its label or name "
                        "instead of its position",
                    ],
                    severity='low', text=text, context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
