"""
Legal Information Rules Package

This package contains all the individual legal information style rules,
based on the IBM Style Guide.
"""

from .base_legal_rule import BaseLegalRule
from .claims_rule import ClaimsRule
from .company_names_rule import CompanyNamesRule
from .personal_information_rule import PersonalInformationRule

__all__ = [
    'BaseLegalRule',
    'ClaimsRule',
    'CompanyNamesRule',
    'PersonalInformationRule',
]
