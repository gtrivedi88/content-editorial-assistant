"""
World-Class PDF Report Generator Package

A modular, professional-grade PDF report generation system for writing analytics.
Designed for executives and writers seeking actionable insights.

Architecture:
- sections/: Individual report sections (cover, executive summary, analytics, etc.)
- charts/: Professional chart generators with modern styling
- styles/: Corporate styling and typography
- utils/: Metric calculations and interpretations

Human-in-the-Loop Notice:
All generated reports include a persistent AI disclaimer:
"Always review AI-generated content prior to use."

Usage:
    from pdf_reports import PDFReportGenerator
    
    generator = PDFReportGenerator()
    pdf_bytes = generator.generate_report(analysis_data, content, structural_blocks)
"""

from .generator import PDFReportGenerator

__all__ = ['PDFReportGenerator']
__version__ = '2.0.0'
