"""Enumeration types for the Content Editorial Assistant.

Defines all enum classes used across the application for content types,
issue categorization, severity levels, issue statuses, and file types.
All enums inherit from (str, Enum) for direct JSON serialization.
"""

from enum import Enum


class ContentType(str, Enum):
    """Modular documentation content type classification.

    Categorizes documents according to modular documentation standards:
    concept, procedure, reference, or assembly modules.
    """

    CONCEPT = "concept"
    PROCEDURE = "procedure"
    REFERENCE = "reference"
    ASSEMBLY = "assembly"


class IssueCategory(str, Enum):
    """Categories for editorial issues found during analysis.

    Maps to rule categories from the IBM Style Guide, Red Hat Supplementary
    Style Guide, accessibility guidelines, and modular documentation standards.
    """

    STYLE = "style"
    GRAMMAR = "grammar"
    WORD_USAGE = "word-usage"
    PUNCTUATION = "punctuation"
    STRUCTURE = "structure"
    NUMBERS = "numbers"
    TECHNICAL = "technical"
    REFERENCES = "references"
    LEGAL = "legal"
    AUDIENCE = "audience"
    MODULAR = "modular"


class IssueSeverity(str, Enum):
    """Severity level for an editorial issue.

    Determines visual treatment in the UI and priority ordering:
    - LOW: informational suggestions
    - MEDIUM: recommended corrections
    - HIGH: critical style or compliance violations
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class IssueStatus(str, Enum):
    """Lifecycle status of an editorial issue.

    Tracks user interaction with each flagged issue:
    - OPEN: newly detected, awaiting user action
    - ACCEPTED: user accepted the suggested correction
    - DISMISSED: user chose to ignore the issue
    - MANUALLY_FIXED: user fixed the issue by hand (not via Accept)
    """

    OPEN = "open"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    MANUALLY_FIXED = "manually_fixed"


class FileType(str, Enum):
    """Supported input file formats for content analysis.

    Determines which parser and preprocessing pipeline to apply
    when processing uploaded files.
    """

    DITA = "dita"
    ASCIIDOC = "asciidoc"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    XML = "xml"
    PLAINTEXT = "plaintext"
