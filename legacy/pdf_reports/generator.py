"""
PDF Report Generator - Main Orchestrator

World-class PDF report generation for writing analytics.
Orchestrates all sections, charts, and styling into a professional report.

Usage:
    from pdf_reports import PDFReportGenerator
    
    generator = PDFReportGenerator()
    pdf_bytes = generator.generate_report(analysis_data, content, structural_blocks)
"""

import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Any, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, PageBreak, Spacer, Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from .styles.corporate_styles import CorporateStyles
from .sections.cover_page import CoverPageSection
from .sections.executive_summary import ExecutiveSummarySection
from .sections.writing_analytics import WritingAnalyticsSection
from .sections.document_structure import DocumentStructureSection
from .sections.error_analysis import ErrorAnalysisSection
from .sections.recommendations import RecommendationsSection
from .sections.appendix import AppendixSection
from .utils.metrics import MetricsCalculator

logger = logging.getLogger(__name__)

# AI Disclaimer - Human-in-the-loop notice
AI_DISCLAIMER = "⚠️ Always review AI-generated content prior to use."
AI_DISCLAIMER_FULL = """This report contains AI-generated analysis and recommendations. 
Always review AI-generated content prior to use. Human judgment should be applied 
before implementing any suggested changes."""


class PDFReportGenerator:
    """
    World-class PDF report generator for writing analytics.
    
    Creates comprehensive, executive-ready reports with:
    - Professional cover page with key metrics
    - Executive summary with actionable insights
    - Detailed writing analytics with visualizations
    - Document structure analysis
    - Error breakdown with examples
    - Prioritized recommendations
    - Full appendix with original content
    - Persistent AI disclaimer (Human-in-the-loop notice)
    """
    
    def __init__(self):
        """Initialize the PDF report generator."""
        self.styles = CorporateStyles()
        
        # Initialize section generators
        self.cover_section = CoverPageSection(self.styles)
        self.executive_summary_section = ExecutiveSummarySection(self.styles)
        self.writing_analytics_section = WritingAnalyticsSection(self.styles)
        self.document_structure_section = DocumentStructureSection(self.styles)
        self.error_analysis_section = ErrorAnalysisSection(self.styles)
        self.recommendations_section = RecommendationsSection(self.styles)
        self.appendix_section = AppendixSection(self.styles)
        
        # AI Disclaimer style
        self.disclaimer_style = ParagraphStyle(
            'AIDisclaimer',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.8, 0.4, 0.0),  # Orange warning color
            alignment=TA_CENTER,
            leading=12,
            spaceBefore=10,
            spaceAfter=10,
        )
        
        logger.info("PDFReportGenerator initialized with all sections")
    
    def _create_ai_disclaimer_box(self) -> Table:
        """Create a prominent AI disclaimer box."""
        disclaimer_text = Paragraph(
            f'<font color="#CC6600"><b>⚠️ AI-GENERATED CONTENT NOTICE</b></font><br/><br/>'
            f'<font color="#26262E">Always review AI-generated content prior to use. '
            f'This report contains automated analysis and recommendations that should be '
            f'verified by a human before implementation.</font>',
            ParagraphStyle(
                'DisclaimerBox',
                fontSize=10,
                fontName='Helvetica',
                alignment=TA_CENTER,
                leading=14,
                spaceBefore=0,
                spaceAfter=0,
            )
        )
        
        table = Table([[disclaimer_text]], colWidths=[5.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(1.0, 0.97, 0.90)),  # Light orange
            ('BOX', (0, 0), (-1, -1), 2, colors.Color(0.9, 0.6, 0.1)),  # Orange border
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def generate_report(self, analysis_data: Dict[str, Any], content: str,
                       structural_blocks: Optional[List[Dict]] = None) -> bytes:
        """
        Generate a comprehensive PDF report.
        
        Args:
            analysis_data: Complete analysis results dictionary
            content: Original content that was analyzed
            structural_blocks: Structural block analysis (optional)
        
        Returns:
            PDF content as bytes
        """
        try:
            logger.info("Starting PDF report generation...")
            
            # Ensure overall_score is calculated if not present
            if 'overall_score' not in analysis_data:
                analysis_data['overall_score'] = MetricsCalculator.calculate_overall_score(analysis_data)
            
            # Create PDF in memory
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.9 * inch,  # Extra space for disclaimer footer
                title="Writing Analytics Report",
                author="Content Editorial Assistant",
                subject="Comprehensive Writing Analysis",
                creator="PDF Report Generator v2.0"
            )
            
            # Build the report content
            story = []
            
            # 1. Cover Page (includes AI disclaimer at bottom)
            logger.debug("Generating cover page...")
            story.extend(self.cover_section.generate(analysis_data))
            story.append(PageBreak())
            
            # 2. Executive Summary (starts on page 2)
            logger.debug("Generating executive summary...")
            story.extend(self.executive_summary_section.generate(analysis_data))
            story.append(PageBreak())
            
            # 4. Writing Analytics
            logger.debug("Generating writing analytics section...")
            story.extend(self.writing_analytics_section.generate(analysis_data))
            story.append(PageBreak())
            
            # 5. Document Structure Analysis
            logger.debug("Generating document structure section...")
            story.extend(self.document_structure_section.generate(
                analysis_data, content, structural_blocks
            ))
            story.append(PageBreak())
            
            # 6. Detailed Error Analysis
            logger.debug("Generating error analysis section...")
            story.extend(self.error_analysis_section.generate(analysis_data))
            story.append(PageBreak())
            
            # 7. Recommendations
            logger.debug("Generating recommendations section...")
            story.extend(self.recommendations_section.generate(analysis_data))
            story.append(PageBreak())
            
            # 8. Appendix
            logger.debug("Generating appendix...")
            story.extend(self.appendix_section.generate(content, analysis_data))
            
            # Build PDF with page numbers and AI disclaimer footer
            doc.build(story, onFirstPage=self._add_page_footer, 
                     onLaterPages=self._add_page_footer)
            
            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"PDF report generated successfully ({len(pdf_bytes):,} bytes)")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}", exc_info=True)
            raise
    
    def _add_page_footer(self, canvas, doc):
        """Add page numbers, AI disclaimer, and footer to each page."""
        canvas.saveState()
        
        page_width = doc.pagesize[0]
        
        # AI Disclaimer line (persistent on every page)
        canvas.setFillColor(colors.Color(0.8, 0.4, 0.0))  # Orange
        canvas.setFont('Helvetica-Bold', 8)
        canvas.drawCentredString(
            page_width / 2,
            0.6 * inch,
            AI_DISCLAIMER
        )
        
        # Footer line
        canvas.setStrokeColor(self.styles.get_color('border'))
        canvas.setLineWidth(0.5)
        canvas.line(
            doc.leftMargin, 
            0.5 * inch,
            page_width - doc.rightMargin,
            0.5 * inch
        )
        
        # Page number
        page_num = canvas.getPageNumber()
        text = f"Page {page_num}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(self.styles.get_color('text_muted'))
        canvas.drawCentredString(
            page_width / 2,
            0.35 * inch,
            text
        )
        
        # Report title in footer
        canvas.drawString(
            doc.leftMargin,
            0.35 * inch,
            "Writing Analytics Report"
        )
        
        # Generated date
        timestamp = datetime.now().strftime("%Y-%m-%d")
        canvas.drawRightString(
            page_width - doc.rightMargin,
            0.35 * inch,
            timestamp
        )
        
        canvas.restoreState()
    
    def generate_summary_report(self, analysis_data: Dict[str, Any], content: str) -> bytes:
        """
        Generate a condensed summary report (2-3 pages).
        
        Args:
            analysis_data: Complete analysis results
            content: Original content
        
        Returns:
            PDF content as bytes
        """
        try:
            logger.info("Generating summary report...")
            
            # Ensure overall_score is calculated
            if 'overall_score' not in analysis_data:
                analysis_data['overall_score'] = MetricsCalculator.calculate_overall_score(analysis_data)
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.9 * inch,  # Extra space for disclaimer footer
                title="Writing Analytics Summary"
            )
            
            story = []
            
            # Cover (includes AI Disclaimer)
            story.extend(self.cover_section.generate(analysis_data))
            story.append(PageBreak())
            
            # Executive Summary (starts on page 2)
            story.extend(self.executive_summary_section.generate(analysis_data))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self.recommendations_section.generate(analysis_data))
            
            doc.build(story, onFirstPage=self._add_page_footer,
                     onLaterPages=self._add_page_footer)
            
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Summary report generated ({len(pdf_bytes):,} bytes)")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating summary report: {e}")
            raise


# Backwards compatibility - keep the old class name working
__all__ = ['PDFReportGenerator']
