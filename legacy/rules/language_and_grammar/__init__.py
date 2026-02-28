"""
Language and Grammar Rules Package

All IBM Style Guide grammar rules implemented as deterministic SpaCy-based rules.
Each rule uses dependency parsing for detection — no LLM API calls.
Configuration for word lists is in config/*.yaml files.
"""

from .abbreviations_rule import AbbreviationsRule
from .adverbs_only_rule import AdverbsOnlyRule
from .anthropomorphism_rule import AnthropomorphismRule
from .articles_rule import ArticlesRule
from .capitalization_rule import CapitalizationRule
from .conjunctions_rule import ConjunctionsRule
from .contractions_rule import ContractionsRule
from .definitions_rule import DefinitionsRule
from .inclusive_language_rule import InclusiveLanguageRule
from .plurals_rule import PluralsRule
from .possessives_rule import PossessivesRule
from .prefixes_rule import PrefixesRule
from .prepositions_rule import PrepositionsRule
from .pronouns_rule import PronounsRule
from .repeated_words_rule import RepeatedWordsRule
from .spelling_rule import SpellingRule
from .terminology_rule import TerminologyRule
from .using_rule import UsingRule
from .verbs_rule import VerbsRule


__all__ = [
    'AbbreviationsRule',
    'AdverbsOnlyRule',
    'AnthropomorphismRule',
    'ArticlesRule',
    'CapitalizationRule',
    'ConjunctionsRule',
    'ContractionsRule',
    'DefinitionsRule',
    'InclusiveLanguageRule',
    'PluralsRule',
    'PossessivesRule',
    'PrefixesRule',
    'PrepositionsRule',
    'PronounsRule',
    'RepeatedWordsRule',
    'SpellingRule',
    'TerminologyRule',
    'UsingRule',
    'VerbsRule',
]
