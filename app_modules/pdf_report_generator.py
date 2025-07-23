"""
Professional PDF Report Generator
Creates comprehensive writing analytics reports with charts, diagrams, and detailed explanations.

Recent Improvements (Text Overlapping Fixes):
- Increased chart figure size from 12x10 to 14x12 inches
- Added more spacing between chart subplots (hspace=0.5, wspace=0.4)
- Positioned chart labels further from bar tops to avoid title overlap
- Shortened chart labels to prevent x-axis crowding
- Limited pie chart to top 4 error types with truncated labels
- Improved table column width distribution for better text fit
- Reduced font sizes in tables (9pt vs 10pt) for better fit
- Added proper padding and alignment to table cells
- Shortened interpretation text for better table display
- Fixed chart value label positioning to prevent overlap with titles
"""

import os
import io
import logging
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

# PDF Generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether, Flowable
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics import renderPDF

# Chart Generation
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class PDFReportGenerator:
    """Generates comprehensive PDF reports for writing analytics."""
    
    def __init__(self):
        """Initialize the PDF report generator."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Color palette
        self.colors = {
            'primary': colors.Color(0, 0.4, 0.8),      # Blue
            'success': colors.Color(0.3, 0.7, 0.2),    # Green
            'warning': colors.Color(1.0, 0.6, 0.0),    # Orange
            'danger': colors.Color(0.8, 0.2, 0.2),     # Red
            'info': colors.Color(0.1, 0.7, 0.9),       # Light Blue
            'gray': colors.Color(0.5, 0.5, 0.5),       # Gray
            'light_gray': colors.Color(0.9, 0.9, 0.9), # Light Gray
            'dark_gray': colors.Color(0.3, 0.3, 0.3),  # Dark Gray
        }
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the report."""
        self.custom_styles = {
            'ReportTitle': ParagraphStyle(
                'ReportTitle',
                parent=self.styles['Title'],
                fontSize=24,
                textColor=colors.Color(0, 0.4, 0.8),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ),
            'SectionTitle': ParagraphStyle(
                'SectionTitle',
                parent=self.styles['Heading1'],
                fontSize=16,
                textColor=colors.Color(0, 0.4, 0.8),
                spaceBefore=20,
                spaceAfter=12,
                fontName='Helvetica-Bold',
                keepWithNext=1
            ),
            'SubsectionTitle': ParagraphStyle(
                'SubsectionTitle',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.Color(0.3, 0.3, 0.3),
                spaceBefore=15,
                spaceAfter=8,
                fontName='Helvetica-Bold',
                keepWithNext=1
            ),
            'MetricValue': ParagraphStyle(
                'MetricValue',
                parent=self.styles['Normal'],
                fontSize=28,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=5
            ),
            'MetricLabel': ParagraphStyle(
                'MetricLabel',
                parent=self.styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.Color(0.5, 0.5, 0.5),
                spaceAfter=15
            ),
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=self.styles['Normal'],
                fontSize=11,
                leading=14,
                spaceAfter=8,
                alignment=TA_JUSTIFY
            ),
            'BulletText': ParagraphStyle(
                'BulletText',
                parent=self.styles['Normal'],
                fontSize=10,
                leftIndent=20,
                bulletIndent=10,
                spaceAfter=4
            ),
            'CodeText': ParagraphStyle(
                'CodeText',
                parent=self.styles['Code'],
                fontSize=9,
                fontName='Courier',
                backColor=colors.Color(0.95, 0.95, 0.95),
                borderColor=colors.Color(0.8, 0.8, 0.8),
                borderWidth=1,
                borderPadding=5,
                spaceAfter=8
            )
        }
    
    def _extract_grade_level(self, analysis_data: Dict[str, Any]) -> float:
        """Extract grade level from analysis data, checking multiple possible sources."""
        try:
            # Check multiple possible sources for grade level data
            technical_metrics = analysis_data.get('technical_writing_metrics', {})
            statistics = analysis_data.get('statistics', {})
            
            # Priority order for grade level sources
            grade_level_sources = [
                technical_metrics.get('estimated_grade_level'),
                technical_metrics.get('flesch_kincaid_grade'),
                technical_metrics.get('text_standard'),
                statistics.get('flesch_kincaid_grade'),
                statistics.get('estimated_grade_level'),
                statistics.get('text_standard')
            ]
            
            # Return the first valid numeric value found
            for source in grade_level_sources:
                if source is not None and isinstance(source, (int, float)) and source > 0:
                    return float(source)
            
            # If no valid grade level found, estimate from Flesch Reading Ease
            flesch_score = technical_metrics.get('flesch_reading_ease') or statistics.get('flesch_reading_ease', 0)
            if flesch_score > 0:
                # Rough conversion from Flesch Reading Ease to grade level
                if flesch_score >= 90:
                    return 5.0
                elif flesch_score >= 80:
                    return 6.0
                elif flesch_score >= 70:
                    return 7.0
                elif flesch_score >= 60:
                    return 8.5
                elif flesch_score >= 50:
                    return 10.0
                elif flesch_score >= 30:
                    return 13.0
                else:
                    return 16.0
            
            # Default fallback
            return 10.0
            
        except Exception as e:
            logger.error(f"Error extracting grade level: {e}")
            return 10.0
    
    def generate_report(self, analysis_data: Dict[str, Any], content: str, 
                       structural_blocks: Optional[List[Dict]] = None) -> bytes:
        """
        Generate a comprehensive PDF report.
        
        Args:
            analysis_data: Complete analysis results
            content: Original content that was analyzed
            structural_blocks: Structural block analysis (optional)
        
        Returns:
            PDF content as bytes
        """
        try:
            # Create PDF in memory
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch,
                title="Writing Analytics Report"
            )
            
            # Build the report content
            story = []
            
            # Cover page
            story.extend(self._create_cover_page(analysis_data))
            story.append(PageBreak())
            
            # Executive summary
            story.extend(self._create_executive_summary(analysis_data))
            story.append(PageBreak())
            
            # Writing Analytics section with proper spacing
            story.extend(self._create_writing_analytics_section(analysis_data))
            story.append(PageBreak())
            
            # Document Structure Analysis
            story.extend(self._create_document_structure_section(analysis_data, content, structural_blocks))
            story.append(PageBreak())
            
            # Detailed Error Analysis
            story.extend(self._create_error_analysis_section(analysis_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations_section(analysis_data))
            story.append(PageBreak())
            
            # Appendix with original content
            story.extend(self._create_appendix_section(content))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Generated PDF report ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise
    
    def _create_cover_page(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create the cover page."""
        elements = []
        
        # Title
        elements.append(Spacer(1, inch))
        elements.append(Paragraph("Writing Analytics Report", self.custom_styles['ReportTitle']))
        elements.append(Spacer(1, 0.5 * inch))
        
        # Subtitle
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        elements.append(Paragraph(f"Generated on {timestamp}", self.styles['Normal']))
        elements.append(Spacer(1, inch))
        
        # Key metrics overview
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        # Extract grade level properly
        grade_level = self._extract_grade_level(analysis_data)
        
        # Create metrics table
        metrics_data = [
            ['Document Statistics', '', 'Quality Metrics', ''],
            [f"Words: {statistics.get('word_count', 0):,}", '', 
             f"Grade Level: {grade_level:.1f}", ''],
            [f"Sentences: {statistics.get('sentence_count', 0):,}", '', 
             f"Readability: {self._get_readability_category(technical_metrics.get('flesch_reading_ease', 0))}", ''],
            [f"Paragraphs: {statistics.get('paragraph_count', 0):,}", '', 
             f"Issues Found: {len(errors)}", ''],
            [f"Reading Time: {self._estimate_reading_time(statistics.get('word_count', 0))}", '', 
             f"Overall Score: {analysis_data.get('overall_score', 0):.0f}/100", '']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.2*inch, 0.3*inch, 2.8*inch, 0.3*inch])
        metrics_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),  # Slightly smaller font
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['primary']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 15),  # More space after headers
            ('TOPPADDING', (0, 1), (-1, -1), 10),  # More padding for content rows
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, inch))
        
        # Analysis capabilities
        elements.append(Paragraph("Analysis Capabilities", self.custom_styles['SubsectionTitle']))
        
        capabilities = []
        if analysis_data.get('spacy_available', False):
            capabilities.append("✓ Advanced NLP Processing")
        if analysis_data.get('modular_rules_available', False):
            capabilities.append("✓ Comprehensive Style Rules")
        capabilities.extend([
            "✓ Readability Analysis",
            "✓ Technical Writing Metrics",
            "✓ Error Detection & Suggestions",
            "✓ AI/LLM Compatibility Assessment"
        ])
        
        for capability in capabilities:
            elements.append(Paragraph(capability, self.custom_styles['BulletText']))
        
        return elements
    
    def _create_executive_summary(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create executive summary section."""
        elements = []
        
        # Use KeepTogether for title and content
        title_and_intro = []
        title_and_intro.append(Paragraph("Executive Summary", self.custom_styles['SectionTitle']))
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        # Key findings
        word_count = statistics.get('word_count', 0)
        grade_level = self._extract_grade_level(analysis_data)
        flesch_score = technical_metrics.get('flesch_reading_ease', 0)
        overall_score = analysis_data.get('overall_score', 0)
        
        summary_text = f"""
        This report analyzes a {word_count:,}-word document for writing quality, readability, and technical effectiveness. 
        The analysis reveals a grade level of {grade_level:.1f}, indicating content appropriate for 
        {self._interpret_grade_level(grade_level)}. 
        
        With a Flesch Reading Ease score of {flesch_score:.1f}, the text is classified as 
        "{self._get_readability_category(flesch_score)}" and receives an overall quality score of {overall_score:.0f}/100.
        
        The analysis identified {len(errors)} areas for improvement across various writing dimensions including 
        sentence structure, word choice, and technical clarity. Key strengths and opportunities are detailed 
        in the sections that follow.
        """
        
        title_and_intro.append(Paragraph(summary_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(title_and_intro))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Key metrics visualization with better spacing
        chart_section = []
        chart_section.append(Paragraph("Key Metrics Overview", self.custom_styles['SubsectionTitle']))
        chart_section.append(self._create_metrics_chart(analysis_data))
        elements.append(KeepTogether(chart_section))
        
        return elements
    
    def _create_writing_analytics_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create detailed writing analytics section with better spacing."""
        elements = []
        
        # Section title
        elements.append(Paragraph("Writing Analytics", self.custom_styles['SectionTitle']))
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        # Grade Level Analysis with KeepTogether
        grade_section = []
        grade_section.append(Paragraph("Grade Level Assessment", self.custom_styles['SubsectionTitle']))
        
        grade_level = self._extract_grade_level(analysis_data)
        grade_text = f"""
        <b>Current Grade Level:</b> {grade_level:.1f}<br/>
        <b>Target Range:</b> 9-11 (Professional Technical Writing)<br/>
        <b>Interpretation:</b> {self._interpret_grade_level(grade_level)}<br/>
        <b>Recommendation:</b> {self._get_grade_level_recommendation(grade_level)}
        """
        
        grade_section.append(Paragraph(grade_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(grade_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Readability Scores with KeepTogether
        readability_section = []
        readability_section.append(Paragraph("Readability Analysis", self.custom_styles['SubsectionTitle']))
        
        readability_data = [
            ['Metric', 'Score', 'Interpretation', 'Target'],
            ['Flesch Reading Ease', f"{technical_metrics.get('flesch_reading_ease', 0):.1f}", 
             self._get_readability_category(technical_metrics.get('flesch_reading_ease', 0)), '60-70'],
            ['Flesch-Kincaid Grade', f"{technical_metrics.get('flesch_kincaid_grade', grade_level):.1f}", 
             f"Grade {technical_metrics.get('flesch_kincaid_grade', grade_level):.0f} level", '9-11'],
            ['Gunning Fog Index', f"{technical_metrics.get('gunning_fog_index', 0):.1f}", 
             self._interpret_fog_index(technical_metrics.get('gunning_fog_index', 0)), '< 12'],
            ['SMOG Index', f"{technical_metrics.get('smog_index', 0):.1f}", 
             f"{technical_metrics.get('smog_index', 0):.0f} years education", '< 13']
        ]
        
        readability_table = Table(readability_data, colWidths=[1.6*inch, 1.0*inch, 2.6*inch, 0.8*inch])
        readability_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['dark_gray']),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),  # Smaller font to fit content
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.colors['light_gray']]),
            ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # More padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical center alignment
        ]))
        
        readability_section.append(readability_table)
        elements.append(KeepTogether(readability_section))
        elements.append(Spacer(1, 0.4 * inch))
        
        # Writing Quality Metrics with KeepTogether
        quality_section = []
        quality_section.append(Paragraph("Writing Quality Metrics", self.custom_styles['SubsectionTitle']))
        
        quality_text = f"""
        <b>Sentence Length:</b> {statistics.get('avg_sentence_length', 0):.1f} words (Target: 15-20 words)<br/>
        This measures the average length of sentences. {self._interpret_sentence_length(statistics.get('avg_sentence_length', 0))}<br/><br/>
        
        <b>Passive Voice:</b> {statistics.get('passive_voice_percentage', 0):.1f}% (Target: < 15%)<br/>
        Percentage of sentences using passive voice. {self._interpret_passive_voice(statistics.get('passive_voice_percentage', 0))}<br/><br/>
        
        <b>Complex Words:</b> {statistics.get('complex_words_percentage', 0):.1f}% (Target: < 20%)<br/>
        Percentage of words with 3+ syllables. {self._interpret_complex_words(statistics.get('complex_words_percentage', 0))}<br/><br/>
        
        <b>Vocabulary Diversity:</b> {statistics.get('vocabulary_diversity', 0):.2f} (Target: > 0.7)<br/>
        Ratio of unique words to total words. {self._interpret_vocabulary_diversity(statistics.get('vocabulary_diversity', 0))}
        """
        
        quality_section.append(Paragraph(quality_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(quality_section))
        elements.append(Spacer(1, 0.4 * inch))
        
        # AI/LLM Compatibility with KeepTogether
        llm_section = []
        llm_section.append(Paragraph("AI & LLM Compatibility", self.custom_styles['SubsectionTitle']))
        
        llm_score = self._calculate_llm_score(statistics, technical_metrics)
        
        llm_text = f"""
        <b>LLM Consumability Score:</b> {llm_score:.0f}/100<br/>
        <b>Category:</b> {self._get_llm_category(llm_score)}<br/>
        <b>Assessment:</b> {self._interpret_llm_score(llm_score)}<br/><br/>
        
        <b>Time Savings with AI:</b> This analysis helps optimize content for AI processing, potentially saving 
        2-4 hours of manual editing time by identifying specific areas for improvement before AI rewriting.<br/><br/>
        
        <b>AI Processing Benefits:</b> Well-structured content with clear readability metrics processes 40-60% 
        more effectively through LLM systems, resulting in higher quality automated improvements.
        """
        
        llm_section.append(Paragraph(llm_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(llm_section))
        
        return elements
    
    def _create_document_structure_section(self, analysis_data: Dict[str, Any], content: str, 
                                         structural_blocks: Optional[List[Dict]] = None) -> List[Flowable]:
        """Create document structure analysis section."""
        elements = []
        
        elements.append(Paragraph("Document Structure Analysis", self.custom_styles['SectionTitle']))
        
        # Original content preview with KeepTogether
        content_section = []
        content_section.append(Paragraph("Original Content (First 500 characters)", self.custom_styles['SubsectionTitle']))
        
        content_preview = content[:500] + "..." if len(content) > 500 else content
        content_section.append(Paragraph(content_preview, self.custom_styles['CodeText']))
        elements.append(KeepTogether(content_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Document statistics with KeepTogether
        stats_section = []
        stats_section.append(Paragraph("Document Statistics", self.custom_styles['SubsectionTitle']))
        
        statistics = analysis_data.get('statistics', {})
        stats_text = f"""
        <b>Total Character Count:</b> {len(content):,}<br/>
        <b>Word Count:</b> {statistics.get('word_count', 0):,}<br/>
        <b>Sentence Count:</b> {statistics.get('sentence_count', 0):,}<br/>
        <b>Paragraph Count:</b> {statistics.get('paragraph_count', 0):,}<br/>
        <b>Average Words per Sentence:</b> {statistics.get('avg_sentence_length', 0):.1f}<br/>
        <b>Average Sentences per Paragraph:</b> {statistics.get('avg_paragraph_length', 0):.1f}<br/>
        <b>Estimated Reading Time:</b> {self._estimate_reading_time(statistics.get('word_count', 0))}
        """
        
        stats_section.append(Paragraph(stats_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(stats_section))
        elements.append(Spacer(1, 0.4 * inch))
        
        # Error summary by type with KeepTogether
        error_summary_section = []
        error_summary_section.append(Paragraph("Error Analysis Summary", self.custom_styles['SubsectionTitle']))
        
        errors = analysis_data.get('errors', [])
        error_counts = Counter([error.get('type', 'unknown') for error in errors])
        
        if error_counts:
            error_data = [['Error Type', 'Count', 'Percentage']]
            total_errors = len(errors)
            
            for error_type, count in error_counts.most_common():
                percentage = (count / total_errors) * 100
                error_data.append([
                    error_type.replace('_', ' ').title(),
                    str(count),
                    f"{percentage:.1f}%"
                ])
            
            error_table = Table(error_data, colWidths=[3.2*inch, 1.0*inch, 1.0*inch])
            error_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
                ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['dark_gray']),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align count and percentage
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),  # Smaller font for better fit
                ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
                ('TOPPADDING', (0, 0), (-1, -1), 10),  # More padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            error_summary_section.append(error_table)
        else:
            error_summary_section.append(Paragraph("No errors detected in the document.", self.custom_styles['BodyText']))
        
        elements.append(KeepTogether(error_summary_section))
        elements.append(Spacer(1, 0.4 * inch))
        
        # Structural blocks analysis (if available) with KeepTogether
        if structural_blocks:
            blocks_section = []
            blocks_section.append(Paragraph("Structural Block Analysis", self.custom_styles['SubsectionTitle']))
            
            blocks_text = f"""
            The document was parsed into {len(structural_blocks)} structural blocks for detailed analysis. 
            This allows for context-aware error detection and more precise recommendations.
            """
            
            blocks_section.append(Paragraph(blocks_text, self.custom_styles['BodyText']))
            
            # Block type summary
            block_types = Counter([block.get('block_type', 'unknown') for block in structural_blocks])
            
            if block_types:
                block_data = [['Block Type', 'Count']]
                for block_type, count in block_types.most_common():
                    block_data.append([
                        block_type.replace('_', ' ').title(),
                        str(count)
                    ])
                
                block_table = Table(block_data, colWidths=[3.8*inch, 1.2*inch])
                block_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['light_gray']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), self.colors['dark_gray']),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align count
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),  # Smaller font for better fit
                    ('GRID', (0, 0), (-1, -1), 1, self.colors['gray']),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),  # More padding
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                blocks_section.append(block_table)
            
            elements.append(KeepTogether(blocks_section))
        
        return elements
    
    def _create_error_analysis_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create detailed error analysis section."""
        elements = []
        
        elements.append(Paragraph("Detailed Error Analysis", self.custom_styles['SectionTitle']))
        
        errors = analysis_data.get('errors', [])
        
        if not errors:
            elements.append(Paragraph("No errors were detected in the document. Excellent work!", 
                                    self.custom_styles['BodyText']))
            return elements
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Display each error type with KeepTogether
        for error_type, error_list in error_groups.items():
            error_type_section = []
            error_type_section.append(Paragraph(f"{error_type.replace('_', ' ').title()} ({len(error_list)} issues)", 
                                              self.custom_styles['SubsectionTitle']))
            
            # Show first few examples
            examples_to_show = min(3, len(error_list))
            for i, error in enumerate(error_list[:examples_to_show]):
                sentence = error.get('sentence', '')
                message = error.get('message', '')
                suggestions = error.get('suggestions', [])
                
                if sentence:
                    error_type_section.append(Paragraph(f"<b>Example {i+1}:</b> {sentence}", 
                                                      self.custom_styles['BodyText']))
                
                error_type_section.append(Paragraph(f"<b>Issue:</b> {message}", self.custom_styles['BodyText']))
                
                if suggestions:
                    error_type_section.append(Paragraph("<b>Suggestions:</b>", self.custom_styles['BodyText']))
                    for suggestion in suggestions[:2]:  # Show max 2 suggestions
                        error_type_section.append(Paragraph(f"• {suggestion}", self.custom_styles['BulletText']))
                
                if i < examples_to_show - 1:
                    error_type_section.append(Spacer(1, 0.1 * inch))
            
            if len(error_list) > examples_to_show:
                error_type_section.append(Paragraph(f"... and {len(error_list) - examples_to_show} more similar issues.", 
                                                  self.custom_styles['BodyText']))
            
            elements.append(KeepTogether(error_type_section))
            elements.append(Spacer(1, 0.3 * inch))
        
        return elements
    
    def _create_recommendations_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create recommendations section."""
        elements = []
        
        elements.append(Paragraph("Recommendations & Action Items", self.custom_styles['SectionTitle']))
        
        suggestions = analysis_data.get('suggestions', [])
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        # Priority recommendations with KeepTogether
        priority_section = []
        priority_section.append(Paragraph("High Priority Actions", self.custom_styles['SubsectionTitle']))
        
        high_priority_recs = self._generate_priority_recommendations(statistics, technical_metrics, analysis_data.get('errors', []))
        
        for rec in high_priority_recs:
            priority_section.append(Paragraph(f"• {rec}", self.custom_styles['BulletText']))
        
        elements.append(KeepTogether(priority_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # General suggestions with KeepTogether
        if suggestions:
            suggestions_section = []
            suggestions_section.append(Paragraph("Additional Suggestions", self.custom_styles['SubsectionTitle']))
            
            for suggestion in suggestions[:5]:  # Show top 5 suggestions
                message = suggestion.get('message', '')
                suggestions_section.append(Paragraph(f"• {message}", self.custom_styles['BulletText']))
            
            elements.append(KeepTogether(suggestions_section))
            elements.append(Spacer(1, 0.3 * inch))
        
        # Time savings potential with KeepTogether
        time_savings_section = []
        time_savings_section.append(Paragraph("Potential Time Savings", self.custom_styles['SubsectionTitle']))
        
        time_savings_text = f"""
        <b>Editing Time Reduction:</b> Implementing these recommendations could save 2-4 hours of manual editing time.<br/>
        <b>AI Processing Improvement:</b> Optimized content processes 40-60% more effectively through AI tools.<br/>
        <b>Reader Comprehension:</b> Improved readability can increase reader understanding by 25-40%.<br/>
        <b>Professional Impact:</b> Higher quality writing enhances credibility and professional image.
        """
        
        time_savings_section.append(Paragraph(time_savings_text, self.custom_styles['BodyText']))
        elements.append(KeepTogether(time_savings_section))
        
        return elements
    
    def _create_appendix_section(self, content: str) -> List[Flowable]:
        """Create appendix with full original content."""
        elements = []
        
        elements.append(Paragraph("Appendix: Original Content", self.custom_styles['SectionTitle']))
        
        appendix_intro = []
        appendix_intro.append(Paragraph("Complete original text as analyzed:", self.custom_styles['BodyText']))
        elements.append(KeepTogether(appendix_intro))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Split content into chunks for better formatting
        max_chunk_size = 4000  # Characters per chunk
        content_chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
        
        for i, chunk in enumerate(content_chunks):
            if i > 0:
                elements.append(Paragraph(f"--- Continued (Part {i+1}) ---", self.custom_styles['BodyText']))
                elements.append(Spacer(1, 0.1 * inch))
            
            elements.append(Paragraph(chunk, self.custom_styles['CodeText']))
            
            if i < len(content_chunks) - 1:
                elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_metrics_chart(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create a well-spaced metrics visualization chart."""
        try:
            # Set up matplotlib for PDF generation with larger figure
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(14, 12))  # Even larger figure size
            fig.suptitle('Writing Analytics Overview', fontsize=18, fontweight='bold', y=0.96)
            
            # Add more spacing between subplots to prevent overlapping
            plt.subplots_adjust(hspace=0.5, wspace=0.4, top=0.88, bottom=0.12, left=0.08, right=0.95)
            
            statistics = analysis_data.get('statistics', {})
            technical_metrics = analysis_data.get('technical_writing_metrics', {})
            errors = analysis_data.get('errors', [])
            
            # Chart 1: Grade Level vs Target (top left)
            ax1 = axes[0, 0]
            grade_level = self._extract_grade_level(analysis_data)
            bars1 = ax1.bar(['Current', 'Target\nMin', 'Target\nMax'], [grade_level, 9, 11], 
                           color=['#1f77b4', '#2ca02c', '#2ca02c'], alpha=0.8)
            ax1.set_title('Grade Level Assessment', fontsize=13, fontweight='bold', pad=25)
            ax1.set_ylabel('Grade Level', fontsize=11)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, max(16, grade_level + 2))  # Dynamic y-limit to prevent cramping
            
            # Add value labels on bars with better positioning
            for bar in bars1:
                height = bar.get_height()
                # Position labels further from bar tops to avoid title overlap
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                        f'{height:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
            
            # Chart 2: Readability Scores (top right)
            ax2 = axes[0, 1]
            readability_scores = [
                technical_metrics.get('flesch_reading_ease', 0),
                max(0, 100 - technical_metrics.get('gunning_fog_index', 0) * 8),
                max(0, 100 - technical_metrics.get('smog_index', 0) * 7)
            ]
            # Shorter labels to prevent overlap
            bars2 = ax2.bar(['Flesch\nEase', 'Gunning\nFog', 'SMOG\nIndex'], 
                           readability_scores, color=['#ff7f0e', '#2ca02c', '#d62728'], alpha=0.8)
            ax2.set_title('Readability Metrics', fontsize=13, fontweight='bold', pad=25)
            ax2.set_ylabel('Score (0-100)', fontsize=11)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 110)  # Fixed y-limit to prevent label overlap
            
            # Add value labels with better spacing
            for bar in bars2:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 3,
                        f'{height:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
            
            # Chart 3: Error Distribution (bottom left)
            ax3 = axes[1, 0]
            if errors:
                error_types = [error.get('type', 'unknown') for error in errors]
                error_counts = Counter(error_types)
                if error_counts:
                    # Limit to top 4 error types for better label spacing
                    top_errors = error_counts.most_common(4)
                    labels, values = zip(*top_errors)
                    
                    # Shorten labels to prevent overlap
                    short_labels = []
                    for label in labels:
                        clean_label = label.replace('_', ' ').title()
                        if len(clean_label) > 12:
                            # Truncate long labels
                            clean_label = clean_label[:10] + '...'
                        short_labels.append(clean_label)
                    
                    wedges, texts, autotexts = ax3.pie(values, labels=short_labels, 
                                                      autopct='%1.1f%%', startangle=90,
                                                      pctdistance=0.85)  # Move percentages inward
                    ax3.set_title('Top Error Types', fontsize=13, fontweight='bold', pad=25)
                    
                    # Improve text readability and positioning
                    for text in texts:
                        text.set_fontsize(9)  # Smaller font for labels
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        autotext.set_fontsize(9)
            else:
                ax3.text(0.5, 0.5, 'No Errors Found!\n✓ Excellent Writing', ha='center', va='center', 
                        transform=ax3.transAxes, fontsize=14, color='green', fontweight='bold')
                ax3.set_title('Error Analysis', fontsize=13, fontweight='bold', pad=25)
                ax3.set_xlim(-1, 1)
                ax3.set_ylim(-1, 1)
            
            # Chart 4: Quality Metrics (bottom right)
            ax4 = axes[1, 1]
            quality_metrics = [
                min(100, 100 - statistics.get('passive_voice_percentage', 0) * 4),
                min(100, 100 - abs(statistics.get('avg_sentence_length', 18) - 18) * 3),
                min(100, 100 - statistics.get('complex_words_percentage', 0) * 3),
                min(100, statistics.get('vocabulary_diversity', 0.5) * 100)
            ]
            
            # Shorter labels to prevent x-axis overlap
            labels = ['Passive\nVoice', 'Sentence\nLength', 'Complex\nWords', 'Vocab\nDiversity']
            bars4 = ax4.bar(labels, quality_metrics, 
                           color=['#9467bd', '#8c564b', '#e377c2', '#7f7f7f'], alpha=0.8)
            ax4.set_title('Writing Quality Metrics', fontsize=13, fontweight='bold', pad=25)
            ax4.set_ylabel('Quality Score (0-100)', fontsize=11)
            ax4.grid(True, alpha=0.3)
            ax4.set_ylim(0, 110)  # Fixed y-limit to prevent overlap
            
            # Add value labels with proper spacing
            for bar in bars4:
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height + 3,
                        f'{height:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
            
            # Rotate x-axis labels to prevent overlap
            for ax in [ax1, ax2, ax4]:
                ax.tick_params(axis='x', labelsize=9)
                plt.setp(ax.get_xticklabels(), rotation=0, ha='center')
            
            # Save to bytes with higher DPI for better quality
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none', pad_inches=0.2)
            img_buffer.seek(0)
            plt.close()
            
            # Create ReportLab Image with appropriate sizing
            img = Image(img_buffer, width=7.5*inch, height=6.5*inch)
            return img
            
        except Exception as e:
            logger.error(f"Error creating metrics chart: {e}")
            return Paragraph("Chart generation failed", self.custom_styles['BodyText'])
    
    # Helper methods for interpretation
    def _get_readability_category(self, flesch_score: float) -> str:
        """Get readability category from Flesch score."""
        if flesch_score >= 90: return "Very Easy"
        elif flesch_score >= 80: return "Easy"
        elif flesch_score >= 70: return "Fairly Easy"
        elif flesch_score >= 60: return "Standard"
        elif flesch_score >= 50: return "Fairly Difficult"
        elif flesch_score >= 30: return "Difficult"
        else: return "Very Difficult"
    
    def _interpret_grade_level(self, grade_level: float) -> str:
        """Interpret grade level."""
        if grade_level < 6: return "Elementary school level - may be too simple for professional content"
        elif grade_level < 9: return "Middle school level - accessible but may lack authority"
        elif grade_level <= 11: return "High school level - ideal for most professional audiences"
        elif grade_level <= 13: return "College level - appropriate for technical content"
        elif grade_level <= 16: return "College/Graduate level - may be challenging for general readers"
        else: return "Graduate/Professional level - very challenging for most readers"
    
    def _get_grade_level_recommendation(self, grade_level: float) -> str:
        """Get recommendation based on grade level."""
        if grade_level < 9: 
            return "Consider adding more sophisticated vocabulary and sentence structures for professional credibility."
        elif grade_level > 13:
            return "Consider simplifying complex sentences and reducing jargon for better accessibility."
        else:
            return "Grade level is appropriate for professional technical writing."
    
    def _interpret_fog_index(self, fog_index: float) -> str:
        """Interpret Gunning Fog index."""
        if fog_index <= 12: return "Good for technical docs"
        elif fog_index <= 15: return "Moderately complex"
        else: return "Too complex"
    
    def _interpret_sentence_length(self, avg_length: float) -> str:
        """Interpret average sentence length."""
        if avg_length < 15: return "Sentences are appropriately concise for technical writing."
        elif avg_length <= 20: return "Sentence length is ideal for professional communication."
        elif avg_length <= 25: return "Sentences are getting lengthy - consider breaking some down."
        else: return "Sentences are too long - break into shorter, clearer statements."
    
    def _interpret_passive_voice(self, percentage: float) -> str:
        """Interpret passive voice percentage."""
        if percentage <= 15: return "Excellent use of active voice promotes clarity and engagement."
        elif percentage <= 25: return "Acceptable level, but consider converting some to active voice."
        else: return "Too much passive voice - actively rewrite for stronger impact."
    
    def _interpret_complex_words(self, percentage: float) -> str:
        """Interpret complex words percentage."""
        if percentage <= 20: return "Good balance of accessible vocabulary."
        elif percentage <= 30: return "Moderate complexity - consider simplifying some terms."
        else: return "High complexity - consider simpler alternatives where possible."
    
    def _interpret_vocabulary_diversity(self, diversity: float) -> str:
        """Interpret vocabulary diversity."""
        if diversity >= 0.7: return "Excellent vocabulary variety keeps readers engaged."
        elif diversity >= 0.5: return "Good vocabulary diversity with room for improvement."
        else: return "Limited vocabulary diversity - consider varying word choices."
    
    def _calculate_llm_score(self, statistics: Dict, technical_metrics: Dict) -> float:
        """Calculate LLM compatibility score."""
        score = 100
        
        # Word count factor
        word_count = statistics.get('word_count', 0)
        if word_count < 50: score -= 30
        elif word_count < 100: score -= 15
        
        # Sentence length factor
        avg_sentence_length = statistics.get('avg_sentence_length', 0)
        if avg_sentence_length > 30: score -= 20
        elif avg_sentence_length < 8: score -= 10
        
        # Readability factor
        flesch_score = technical_metrics.get('flesch_reading_ease', 0)
        if flesch_score < 30: score -= 15
        
        # Complex words factor
        complex_words = statistics.get('complex_words_percentage', 0)
        if complex_words > 40: score -= 10
        
        return max(0, min(100, score))
    
    def _get_llm_category(self, score: float) -> str:
        """Get LLM compatibility category."""
        if score >= 80: return "Excellent"
        elif score >= 60: return "Good"
        elif score >= 40: return "Fair"
        else: return "Needs Improvement"
    
    def _interpret_llm_score(self, score: float) -> str:
        """Interpret LLM compatibility score."""
        if score >= 80:
            return "Content is highly compatible with AI/LLM processing and will yield excellent automated improvements."
        elif score >= 60:
            return "Content works well with AI tools with minor optimization opportunities."
        elif score >= 40:
            return "Content needs some structural improvements for optimal AI processing."
        else:
            return "Significant improvements needed for effective AI/LLM compatibility."
    
    def _estimate_reading_time(self, word_count: int) -> str:
        """Estimate reading time based on word count."""
        minutes = max(1, word_count // 250)  # 250 words per minute average
        if minutes == 1:
            return "1 minute"
        elif minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''} {remaining_minutes} minutes"
    
    def _generate_priority_recommendations(self, statistics: Dict, technical_metrics: Dict, errors: List) -> List[str]:
        """Generate priority recommendations based on analysis."""
        recommendations = []
        
        # Grade level recommendations
        grade_level = self._extract_grade_level({'statistics': statistics, 'technical_writing_metrics': technical_metrics})
        if grade_level > 13:
            recommendations.append("Simplify complex sentences to improve accessibility (current grade level too high)")
        elif grade_level < 9:
            recommendations.append("Enhance vocabulary and sentence complexity for professional credibility")
        
        # Sentence length recommendations
        avg_sentence_length = statistics.get('avg_sentence_length', 0)
        if avg_sentence_length > 25:
            recommendations.append("Break down long sentences for better clarity and readability")
        
        # Passive voice recommendations
        passive_voice = statistics.get('passive_voice_percentage', 0)
        if passive_voice > 25:
            recommendations.append("Reduce passive voice usage to create more engaging, direct writing")
        
        # Error-based recommendations
        if len(errors) > 10:
            recommendations.append("Address the most frequent error types first for maximum impact")
        
        # LLM compatibility
        llm_score = self._calculate_llm_score(statistics, technical_metrics)
        if llm_score < 60:
            recommendations.append("Optimize content structure for better AI/LLM processing capabilities")
        
        return recommendations[:5]  # Return top 5 priority recommendations 