"""
Audience and Medium Rules Package

This package contains all the individual audience and medium style rules,
based on the IBM Style Guide.
"""

from .base_audience_rule import BaseAudienceRule
from .conversational_style_rule import ConversationalStyleRule
from .global_audiences_rule import GlobalAudiencesRule
from .llm_consumability_rule import LLMConsumabilityRule
from .tone_rule import ToneRule

__all__ = [
    'BaseAudienceRule',
    'ConversationalStyleRule',
    'GlobalAudiencesRule',
    'LLMConsumabilityRule',
    'ToneRule',
]
