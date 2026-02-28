"""
Punctuation Rules Package

Deterministic rules based on the IBM Style Guide (p.117-140).
Covers all 12 punctuation topics.
"""

from .colons_rule import ColonsRule
from .commas_rule import CommasRule
from .compound_words_rule import CompoundWordsRule
from .dashes_rule import DashesRule
from .ellipses_rule import EllipsesRule
from .exclamation_points_rule import ExclamationPointsRule
from .hyphens_rule import HyphensRule
from .oxford_comma_rule import OxfordCommaRule
from .parentheses_rule import ParenthesesRule
from .periods_rule import PeriodsRule
from .punctuation_and_symbols_rule import PunctuationAndSymbolsRule
from .quotation_marks_rule import QuotationMarksRule
from .semicolons_rule import SemicolonsRule
from .slashes_rule import SlashesRule
from .spacing_rule import SpacingRule

__all__ = [
    'ColonsRule',
    'CommasRule',
    'CompoundWordsRule',
    'DashesRule',
    'EllipsesRule',
    'ExclamationPointsRule',
    'HyphensRule',
    'OxfordCommaRule',
    'ParenthesesRule',
    'PeriodsRule',
    'PunctuationAndSymbolsRule',
    'QuotationMarksRule',
    'SemicolonsRule',
    'SlashesRule',
    'SpacingRule',
]
