"""
PDF Report Sections Package

Individual report sections that can be composed into complete reports.
Each section is self-contained and follows a consistent interface.
"""

from .cover_page import CoverPageSection
from .executive_summary import ExecutiveSummarySection
from .writing_analytics import WritingAnalyticsSection
from .document_structure import DocumentStructureSection
from .error_analysis import ErrorAnalysisSection
from .recommendations import RecommendationsSection
from .appendix import AppendixSection

__all__ = [
    'CoverPageSection',
    'ExecutiveSummarySection', 
    'WritingAnalyticsSection',
    'DocumentStructureSection',
    'ErrorAnalysisSection',
    'RecommendationsSection',
    'AppendixSection'
]

