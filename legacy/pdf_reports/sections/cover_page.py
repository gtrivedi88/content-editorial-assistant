"""
Cover Page Section

Creates a professional, executive-ready cover page for the PDF report.
Features elegant branding, key metrics at a glance, and professional styling.
"""

from datetime import datetime
from typing import Dict, Any, List
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from ..styles.corporate_styles import CorporateStyles
from ..utils.metrics import MetricsCalculator
from ..utils.interpretations import MetricsInterpreter


class CoverPageSection:
    """Generate professional cover page for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
        self._create_local_styles()
    
    def _create_local_styles(self):
        """Create local styles specific to cover page."""
        self.metric_value_style = ParagraphStyle(
            'MetricValue',
            fontSize=18,  # Slightly smaller for compact layout
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            leading=22,
            spaceAfter=2,
        )
        
        self.metric_label_style = ParagraphStyle(
            'MetricLabel',
            fontSize=8,  # Smaller labels
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.Color(0.4, 0.42, 0.45),
            leading=10,
            spaceBefore=1,
        )
        
        self.insight_bullet_style = ParagraphStyle(
            'InsightBullet',
            fontSize=9,  # Slightly smaller
            fontName='Helvetica',
            textColor=colors.Color(0.15, 0.15, 0.18),
            leading=13,
            spaceBefore=3,
            spaceAfter=3,
            leftIndent=8,
        )
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate cover page elements - optimized to fit all content on one page."""
        elements = []
        
        # Minimal top spacing
        elements.append(Spacer(1, 0.25 * inch))
        
        # Brand header line
        elements.append(self._create_brand_header())
        elements.append(Spacer(1, 0.2 * inch))
        
        # Main title
        elements.append(Paragraph(
            "Writing Analytics Report",
            self.styles.get_style('ReportTitle')
        ))
        
        # Subtitle with date
        timestamp = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(
            f"Comprehensive Analysis  •  Generated {timestamp}",
            self.styles.get_style('ReportSubtitle')
        ))
        
        elements.append(Spacer(1, 0.3 * inch))
        
        # Executive score card (compact)
        elements.append(self._create_executive_scorecard(analysis_data))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Key metrics grid
        elements.append(self._create_metrics_grid(analysis_data))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # Quick insights
        elements.extend(self._create_quick_insights(analysis_data))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # Analysis capabilities footer
        elements.append(self._create_capabilities_footer(analysis_data))
        
        elements.append(Spacer(1, 0.2 * inch))
        
        # AI Disclaimer box at bottom of cover page
        elements.append(self._create_ai_disclaimer_box())
        
        return elements
    
    def _create_brand_header(self) -> Flowable:
        """Create a subtle brand header."""
        header_data = [[
            Paragraph(
                '<font color="#1C6BB0">CONTENT EDITORIAL ASSISTANT</font>',
                self.styles.get_style('MetricLabel')
            ),
            Paragraph(
                '<font color="#666B73">AI-Powered Writing Analysis</font>',
                self.styles.get_style('MetricLabel')
            )
        ]]
        
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        return header_table
    
    def _create_executive_scorecard(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create a compact executive scorecard."""
        overall_score = MetricsCalculator.calculate_overall_score(analysis_data)
        badge = MetricsInterpreter.get_score_badge(overall_score)
        
        # Get color based on score
        score_color = self.styles.get_score_color(overall_score)
        hex_color = self._color_to_hex(score_color)
        
        # Compact horizontal layout: Score | Label | Badge
        score_para = Paragraph(
            f'<font size="42" color="{hex_color}"><b>{overall_score:.0f}</b></font>',
            ParagraphStyle('ScoreNum', alignment=TA_CENTER, leading=48)
        )
        label_para = Paragraph(
            'Overall Quality Score',
            ParagraphStyle('ScoreLabel', fontSize=11, alignment=TA_CENTER,
                          textColor=colors.Color(0.4, 0.42, 0.45), leading=14)
        )
        badge_para = Paragraph(
            f'<font color="{badge["color"]}"><b>{badge["label"]}</b></font>',
            ParagraphStyle('ScoreBadge', fontSize=12, alignment=TA_CENTER, leading=16)
        )
        
        # Stack vertically but compact
        score_data = [
            [score_para],
            [label_para],
            [badge_para],
        ]
        
        table = Table(score_data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        return table
    
    def _create_metrics_grid(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create a grid of key metrics with proper spacing."""
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        grade_info = MetricsInterpreter.interpret_grade_level(grade_level)
        
        flesch = technical_metrics.get('flesch_reading_ease', 0)
        flesch_info = MetricsInterpreter.interpret_readability(flesch)
        
        word_count = statistics.get('word_count', 0)
        reading_time = MetricsCalculator.estimate_reading_time(word_count)
        
        # Create metrics data with separate value and label rows
        metrics_data = [
            # Row 1 - Values
            [
                self._create_metric_cell(f"{word_count:,}", 'Word Count', '#1C6BB0'),
                self._create_metric_cell(f"{grade_level:.1f}", 'Grade Level', 
                    '#2E9E59' if 8 <= grade_level <= 12 else '#E8A126'),
                self._create_metric_cell(flesch_info['category'], 'Readability', 
                    '#2E9E59' if flesch_info['color'] == 'success' else '#E8A126'),
                self._create_metric_cell(str(len(errors)), 'Issues Found', 
                    '#2E9E59' if len(errors) < 5 else '#E8A126' if len(errors) < 15 else '#CC423D'),
            ],
            # Row 2 - Values
            [
                self._create_metric_cell(reading_time, 'Reading Time', '#666B73'),
                self._create_metric_cell(str(statistics.get('sentence_count', 0)), 'Sentences', '#666B73'),
                self._create_metric_cell(str(statistics.get('paragraph_count', 0)), 'Paragraphs', '#666B73'),
                self._create_metric_cell(f"{statistics.get('passive_voice_percentage', 0):.0f}%", 'Passive Voice', '#666B73'),
            ]
        ]
        
        table = Table(metrics_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 1, self.styles.get_color('border')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, self.styles.get_color('border')),
            ('BACKGROUND', (0, 0), (-1, -1), self.styles.get_color('background')),
        ]))
        
        return table
    
    def _create_metric_cell(self, value: str, label: str, color: str) -> Table:
        """Create a single metric cell as a mini table for proper spacing."""
        cell_data = [
            [Paragraph(f'<font color="{color}"><b>{value}</b></font>', self.metric_value_style)],
            [Paragraph(label, self.metric_label_style)]
        ]
        
        cell_table = Table(cell_data, colWidths=[1.4*inch])
        cell_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        return cell_table
    
    def _create_quick_insights(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create quick insights section with proper spacing."""
        elements = []
        insights = MetricsInterpreter.generate_executive_insights(analysis_data)
        
        if not insights:
            return elements
        
        # Title
        title_style = ParagraphStyle(
            'InsightTitle',
            fontSize=12,
            fontName='Helvetica-Bold',
            textColor=colors.Color(0.15, 0.15, 0.18),
            leading=16,
            spaceBefore=0,
            spaceAfter=10,
        )
        elements.append(Paragraph("Key Insights", title_style))
        
        # Each insight as separate paragraph with proper spacing
        for insight in insights[:3]:
            elements.append(Paragraph(f"•  {insight}", self.insight_bullet_style))
        
        return elements
    
    def _create_capabilities_footer(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create capabilities footer."""
        capabilities = []
        
        if analysis_data.get('spacy_available', True):
            capabilities.append("✓ Advanced NLP")
        if analysis_data.get('modular_rules_available', True):
            capabilities.append("✓ Style Analysis")
        capabilities.append("✓ Readability Metrics")
        capabilities.append("✓ AI/LLM Ready")
        
        cap_text = "   •   ".join(capabilities)
        
        footer_style = ParagraphStyle(
            'CapFooter',
            fontSize=8,
            fontName='Helvetica',
            textColor=colors.Color(0.4, 0.42, 0.45),
            alignment=TA_CENTER,
            leading=12,
        )
        
        return Paragraph(cap_text, footer_style)
    
    def _create_ai_disclaimer_box(self) -> Flowable:
        """
        Create AI disclaimer box for cover page.
        Human-in-the-loop requirement: Always review AI-generated content prior to use.
        """
        disclaimer_text = Paragraph(
            '<font color="#CC6600"><b>⚠️ Always review AI-generated content prior to use.</b></font><br/>'
            '<font size="8" color="#666B73">This report contains AI-generated analysis and recommendations '
            'that should be verified by a human before implementation.</font>',
            ParagraphStyle(
                'DisclaimerBox',
                fontSize=9,
                fontName='Helvetica',
                alignment=TA_CENTER,
                leading=13,
            )
        )
        
        table = Table([[disclaimer_text]], colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(1.0, 0.98, 0.94)),  # Very light orange
            ('BOX', (0, 0), (-1, -1), 1.5, colors.Color(0.9, 0.6, 0.1)),  # Orange border
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        return table
    
    def _color_to_hex(self, color: colors.Color) -> str:
        """Convert ReportLab color to hex string."""
        try:
            r = int(color.red * 255)
            g = int(color.green * 255)
            b = int(color.blue * 255)
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#26262E"
    
    def _status_to_hex(self, is_good: bool) -> str:
        """Get hex color based on status."""
        return '#2E9E59' if is_good else '#E8A126'
