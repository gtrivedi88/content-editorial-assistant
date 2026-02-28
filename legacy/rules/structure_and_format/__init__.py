"""
Structure and Format Rules Package

Deterministic rules based on the IBM Style Guide (p. 167-217).
Covers headings, lists, messages, notes, procedures, paragraphs,
highlighting, glossaries, admonitions, indentation, and self-referential text.
"""

from .admonition_content_rule import AdmonitionContentRule
from .admonitions_rule import AdmonitionsRule
from .glossaries_rule import GlossariesRule
from .headings_rule import HeadingsRule
from .highlighting_rule import HighlightingRule
from .indentation_rule import IndentationRule
from .list_consistency_rule import ListConsistencyRule
from .list_parallelism_rule import ListParallelismRule
from .list_punctuation_rule import ListPunctuationRule
from .lists_rule import ListsRule
from .messages_rule import MessagesRule
from .notes_rule import NotesRule
from .paragraphs_rule import ParagraphsRule
from .procedures_rule import ProceduresRule
from .self_referential_text_rule import SelfReferentialTextRule

__all__ = [
    'AdmonitionContentRule',
    'AdmonitionsRule',
    'GlossariesRule',
    'HeadingsRule',
    'HighlightingRule',
    'IndentationRule',
    'ListConsistencyRule',
    'ListParallelismRule',
    'ListPunctuationRule',
    'ListsRule',
    'MessagesRule',
    'NotesRule',
    'ParagraphsRule',
    'ProceduresRule',
    'SelfReferentialTextRule',
]
