"""
Appendix Section

Contains the full original content, technical details,
and AI-generated content disclaimer for reference purposes.
"""

from typing import Dict, Any, List
from datetime import datetime
from reportlab.platypus import Flowable, Paragraph, Spacer, KeepTogether, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from ..styles.corporate_styles import CorporateStyles


class AppendixSection:
    """Generate appendix section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
    
    def generate(self, content: str, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate appendix elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Appendix",
            self.styles.get_style('SectionTitle')
        ))
        
        # Original content
        content_section = self._create_original_content_section(content)
        elements.extend(content_section)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Technical details
        technical_section = self._create_technical_details(analysis_data)
        elements.extend(technical_section)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Report metadata and AI Disclaimer
        metadata_section = self._create_report_metadata(analysis_data)
        elements.extend(metadata_section)
        
        return elements
    
    def _create_original_content_section(self, content: str) -> List[Flowable]:
        """Create original content section."""
        elements = []
        
        elements.append(Paragraph("A.1 Original Content", self.styles.get_style('SubsectionTitle')))
        
        elements.append(Paragraph(
            "The complete original text that was analyzed:",
            self.styles.get_style('BodyText')
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Split content into chunks for better formatting
        max_chunk_size = 3000  # Characters per chunk
        content_chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
        
        for i, chunk in enumerate(content_chunks):
            if i > 0:
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph(
                    f"<i>--- Continued (Part {i+1} of {len(content_chunks)}) ---</i>",
                    self.styles.get_style('BodyText')
                ))
                elements.append(Spacer(1, 0.05 * inch))
            
            # Clean and format the chunk
            clean_chunk = self._clean_content_for_display(chunk)
            elements.append(Paragraph(
                f'<font size="8">{clean_chunk}</font>',
                self.styles.get_style('CodeText')
            ))
        
        return elements
    
    def _create_technical_details(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create technical details section."""
        elements = []
        
        elements.append(Paragraph("A.2 Technical Details", self.styles.get_style('SubsectionTitle')))
        
        # Analysis configuration - using separate paragraphs for spacing
        elements.append(Paragraph(
            "<b>Analysis Configuration:</b>",
            self.styles.get_style('BodyText')
        ))
        elements.append(Spacer(1, 0.08 * inch))
        
        analysis_mode = analysis_data.get('analysis_mode', 'Standard')
        spacy_status = 'Enabled' if analysis_data.get('spacy_available', True) else 'Disabled'
        rules_status = 'Enabled' if analysis_data.get('modular_rules_available', True) else 'Disabled'
        proc_time = analysis_data.get('processing_time', 'N/A')
        
        config_items = [
            f"•  Analysis Mode: {analysis_mode}",
            f"•  spaCy NLP: {spacy_status}",
            f"•  Modular Rules: {rules_status}",
            f"•  Processing Time: {proc_time}s"
        ]
        
        for item in config_items:
            elements.append(Paragraph(item, self.styles.get_style('BodyText')))
        
        elements.append(Spacer(1, 0.15 * inch))
        
        # Metrics summary
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        elements.append(Paragraph(
            "<b>Raw Metrics:</b>",
            self.styles.get_style('BodyText')
        ))
        elements.append(Spacer(1, 0.08 * inch))
        
        metric_items = [
            f"•  Flesch Reading Ease: {technical_metrics.get('flesch_reading_ease', 0):.2f}",
            f"•  Flesch-Kincaid Grade: {technical_metrics.get('flesch_kincaid_grade', 0):.2f}",
            f"•  Gunning Fog Index: {technical_metrics.get('gunning_fog_index', 0):.2f}",
            f"•  SMOG Index: {technical_metrics.get('smog_index', 0):.2f}",
            f"•  Coleman-Liau Index: {technical_metrics.get('coleman_liau_index', 0):.2f}",
            f"•  Automated Readability Index: {technical_metrics.get('automated_readability_index', 0):.2f}"
        ]
        
        for item in metric_items:
            elements.append(Paragraph(item, self.styles.get_style('BodyText')))
        
        return elements
    
    def _create_report_metadata(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create report metadata section with AI disclaimer."""
        elements = []
        
        elements.append(Paragraph("A.3 Report Information", self.styles.get_style('SubsectionTitle')))
        
        timestamp = datetime.now()
        
        # Report metadata with proper spacing
        elements.append(Paragraph("<b>Report Metadata:</b>", self.styles.get_style('BodyText')))
        elements.append(Spacer(1, 0.08 * inch))
        
        metadata_items = [
            f"•  Generated: {timestamp.strftime('%B %d, %Y at %I:%M %p')}",
            "•  Report Version: 2.0",
            "•  Generator: Content Editorial Assistant - PDF Report Generator",
            "•  Format: PDF/A Compliant"
        ]
        
        for item in metadata_items:
            elements.append(Paragraph(item, self.styles.get_style('BodyText')))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # =============================================================
        # AI DISCLAIMER - Human-in-the-loop notice (REQUIRED)
        # =============================================================
        elements.append(self._create_ai_disclaimer_box())
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # General disclaimer
        elements.append(Paragraph("<b>General Disclaimer:</b>", self.styles.get_style('BodyText')))
        elements.append(Spacer(1, 0.08 * inch))
        
        disclaimer_text = """This report is generated automatically based on algorithmic analysis 
of the provided content. Recommendations are suggestions based on industry best practices 
and may need adaptation for specific contexts, audiences, or requirements. The analysis 
should be used as guidance alongside human judgment and editorial review."""
        
        elements.append(Paragraph(disclaimer_text, self.styles.get_style('BodyTextJustified')))
        
        # Footer
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph(
            "<i>— End of Report —</i>",
            self.styles.get_style('FooterText')
        ))
        
        return elements
    
    def _create_ai_disclaimer_box(self) -> Table:
        """
        Create the AI-generated content disclaimer box.
        
        Human-in-the-loop requirement:
        "Always review AI-generated content prior to use."
        """
        # Title line
        title_para = Paragraph(
            '<font color="#CC6600" size="12"><b>⚠️ AI-GENERATED CONTENT DISCLAIMER</b></font>',
            self.styles.get_style('BodyText')
        )
        
        # Main disclaimer line (the required text)
        main_notice = Paragraph(
            '<font color="#CC6600" size="11"><b>Always review AI-generated content prior to use.</b></font>',
            self.styles.get_style('BodyText')
        )
        
        # Explanation
        explanation = Paragraph(
            """This report is generated automatically using artificial intelligence 
and machine learning algorithms. While we strive for accuracy, the analysis 
should be used as guidance alongside human judgment.""",
            self.styles.get_style('BodyText')
        )
        
        # Bullet points
        bullet_items = [
            "•  All recommendations are AI-generated suggestions based on industry best practices",
            "•  Human review and validation is required before implementing any suggested changes",
            "•  Results may need adaptation for specific contexts, audiences, or requirements",
            "•  The accuracy of AI-generated analysis may vary based on content complexity"
        ]
        
        bullet_paras = [Paragraph(item, self.styles.get_style('BodyText')) for item in bullet_items]
        
        # Build the content
        content = [[title_para]]
        content.append([Spacer(1, 0.1 * inch)])
        content.append([main_notice])
        content.append([Spacer(1, 0.1 * inch)])
        content.append([explanation])
        content.append([Spacer(1, 0.08 * inch)])
        for bullet in bullet_paras:
            content.append([bullet])
        
        table = Table(content, colWidths=[5.8 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(1.0, 0.97, 0.90)),  # Light orange/cream
            ('BOX', (0, 0), (-1, -1), 2, colors.Color(0.9, 0.6, 0.1)),  # Orange border
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            # Extra padding for first and last rows
            ('TOPPADDING', (0, 0), (0, 0), 15),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 15),
        ]))
        
        return table
    
    def _clean_content_for_display(self, content: str) -> str:
        """Clean content for safe PDF display."""
        # Escape special XML characters
        content = content.replace('&', '&amp;')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        
        # Normalize whitespace
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Convert newlines to breaks for display
        content = content.replace('\n', '<br/>')
        
        return content
