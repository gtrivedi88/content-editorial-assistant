"""
Structure and Format Rules Package

This package contains all the individual rules related to document
structure and formatting. By importing them here, they can be easily
discovered and loaded by the main application's rule engine.
"""

from .headings_rule import HeadingsRule
from .highlighting_rule import HighlightingRule
from .lists_rule import ListsRule
from .list_punctuation_rule import ListPunctuationRule
from .messages_rule import MessagesRule
from .notes_rule import NotesRule
from .paragraphs_rule import ParagraphsRule
from .procedures_rule import ProceduresRule
from .admonitions_rule import AdmonitionsRule
from .glossaries_rule import GlossariesRule
from .indentation_rule import IndentationRule
from .admonition_content_rule import AdmonitionContentRule

# Note: Rules for Books, Examples, Figures, Glossaries, Tables, and Type Size
# are omitted as they relate to document-level structure and layout, which
# cannot be effectively checked at the sentence/text level.

__all__ = [
    'HeadingsRule',
    'HighlightingRule',
    'ListsRule',
    'ListPunctuationRule',
    'MessagesRule',
    'NotesRule',
    'ParagraphsRule',
    'ProceduresRule',
    'AdmonitionsRule',
    'GlossariesRule',
    'IndentationRule',
    'AdmonitionContentRule'
]
