"""
Language and Grammar Rules Package

This package contains all the individual language and grammar style rules.
By importing them here, they can be easily discovered and loaded
by the main application's rule engine.
"""

from .abbreviations_rule import AbbreviationsRule
from .adverbs_only_rule import AdverbsOnlyRule
from .anthropomorphism_rule import AnthropomorphismRule
from .articles_rule import ArticlesRule
from .capitalization_rule import CapitalizationRule
from .conjunctions_rule import ConjunctionsRule
from .contractions_rule import ContractionsRule
from .inclusive_language_rule import InclusiveLanguageRule
from .plurals_rule import PluralsRule
from .possessives_rule import PossessivesRule
from .prefixes_rule import PrefixesRule
from .prepositions_rule import PrepositionsRule
from .pronouns_rule import PronounsRule
from .spelling_rule import SpellingRule
from .terminology_rule import TerminologyRule
from .verbs_rule import VerbsRule


__all__ = [
    'AbbreviationsRule',
    'AdverbsOnlyRule',
    'AnthropomorphismRule',
    'ArticlesRule',
    'CapitalizationRule',
    'ConjunctionsRule',
    'ContractionsRule',
    'InclusiveLanguageRule',
    'PluralsRule',
    'PossessivesRule',
    'PrefixesRule',
    'PrepositionsRule',
    'PronounsRule',
    'SpellingRule',
    'TerminologyRule',
    'VerbsRule'
]
