"""
Audience and Medium Rules Package

Rules based on the IBM Style Guide for audience-appropriate writing:
- AccessibilityRule: Flags all-caps words, color-only references, sensory directions
- ToneRule: Flags business jargon, marketing buzzwords, sports metaphors
- ConversationalStyleRule: Flags overly formal language, suggests conversational alternatives
- GlobalAudiencesRule: Flags negative constructions, long sentences, politeness terms,
  self-referential text, expletive constructions
- LLMConsumabilityRule: Flags tiny content blocks that LLMs struggle to consume
"""

from .base_audience_rule import BaseAudienceRule
from .accessibility_rule import AccessibilityRule
from .conversational_style_rule import ConversationalStyleRule
from .global_audiences_rule import GlobalAudiencesRule
from .llm_consumability_rule import LLMConsumabilityRule
from .obvious_terms_rule import ObviousTermsRule
from .tone_rule import ToneRule

__all__ = [
    'BaseAudienceRule',
    'AccessibilityRule',
    'ConversationalStyleRule',
    'GlobalAudiencesRule',
    'LLMConsumabilityRule',
    'ObviousTermsRule',
    'ToneRule',
]
