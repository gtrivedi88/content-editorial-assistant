"""
Executive Summary Section

Creates a powerful one-page executive summary with key insights,
actionable recommendations, and visual scorecards.
"""

from typing import Dict, Any, List
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from ..styles.corporate_styles import CorporateStyles
from ..utils.metrics import MetricsCalculator
from ..utils.interpretations import MetricsInterpreter
from ..charts.quality_charts import QualityCharts


class ExecutiveSummarySection:
    """Generate executive summary section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
        self._create_local_styles()
    
    def _create_local_styles(self):
        """Create local styles for this section."""
        self.score_value_style = ParagraphStyle(
            'ScoreValue',
            fontSize=28,
            fontName='Helvetica-Bold',
            alignment=TA_CENTER,
            leading=34,
            spaceAfter=4,
        )
        
        self.score_label_style = ParagraphStyle(
            'ScoreLabel',
            fontSize=9,
            fontName='Helvetica',
            alignment=TA_CENTER,
            textColor=colors.Color(0.4, 0.42, 0.45),
            leading=12,
            spaceBefore=4,
            spaceAfter=4,
        )
        
        self.finding_style = ParagraphStyle(
            'Finding',
            fontSize=10,
            fontName='Helvetica',
            textColor=colors.Color(0.15, 0.15, 0.18),
            leading=16,
            spaceBefore=8,
            spaceAfter=8,
            leftIndent=0,
        )
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate executive summary elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Executive Summary",
            self.styles.get_style('SectionTitle')
        ))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Opening statement
        elements.append(self._create_opening_statement(analysis_data))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Score cards row
        elements.append(self._create_score_cards(analysis_data))
        elements.append(Spacer(1, 0.35 * inch))
        
        # Key findings
        key_findings = self._create_key_findings(analysis_data)
        elements.extend(key_findings)
        elements.append(Spacer(1, 0.35 * inch))
        
        # Priority actions
        priority_actions = self._create_priority_actions(analysis_data)
        elements.extend(priority_actions)
        elements.append(Spacer(1, 0.35 * inch))
        
        # Time savings
        elements.append(self._create_time_savings(analysis_data))
        
        return elements
    
    def _create_opening_statement(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create the opening executive statement."""
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        word_count = statistics.get('word_count', 0)
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        grade_info = MetricsInterpreter.interpret_grade_level(grade_level)
        flesch = technical_metrics.get('flesch_reading_ease', 0)
        flesch_info = MetricsInterpreter.interpret_readability(flesch)
        overall_score = MetricsCalculator.calculate_overall_score(analysis_data)
        score_info = MetricsInterpreter.interpret_overall_score(overall_score)
        
        statement = f"""This report analyzes a <b>{word_count:,}-word document</b> for writing quality, 
readability, and professional effectiveness. The content achieves a grade level of 
<b>{grade_level:.1f}</b>, making it appropriate for <b>{grade_info['audience']}</b>.

With a Flesch Reading Ease score of <b>{flesch:.1f}</b> ({flesch_info['category']}), 
the document receives an overall quality grade of <b>{score_info['grade']} ({score_info['category']})</b>. 
The analysis identified <b>{len(errors)} areas</b> for potential improvement."""
        
        return Paragraph(statement, self.styles.get_style('BodyTextJustified'))
    
    def _create_score_cards(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create horizontal score cards with proper spacing."""
        overall_score = MetricsCalculator.calculate_overall_score(analysis_data)
        llm_data = MetricsCalculator.calculate_llm_readiness_score(analysis_data)
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        
        # Create three score cards as nested tables for proper spacing
        scores = [
            ('Quality Score', f'{overall_score:.0f}', 
             MetricsInterpreter.interpret_overall_score(overall_score)['category'],
             self._get_score_hex(overall_score)),
            ('AI Readiness', f'{llm_data["score"]:.0f}', 
             llm_data['category'],
             self._get_score_hex(llm_data['score'])),
            ('Grade Level', f'{grade_level:.1f}', 
             'Target: 9-11',
             '#2E9E59' if 8 <= grade_level <= 12 else '#E8A126'),
        ]
        
        cards = []
        for title, value, subtitle, color in scores:
            card = self._create_single_score_card(title, value, subtitle, color)
            cards.append(card)
        
        # Arrange cards in a row
        table = Table([cards], colWidths=[2*inch, 2*inch, 2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        return table
    
    def _create_single_score_card(self, title: str, value: str, subtitle: str, color: str) -> Table:
        """Create a single score card as a table."""
        card_data = [
            [Paragraph(f'<font size="9" color="#666B73">{title}</font>', 
                      ParagraphStyle('CardTitle', alignment=TA_CENTER, leading=12, spaceBefore=4))],
            [Paragraph(f'<font color="{color}"><b>{value}</b></font>', self.score_value_style)],
            [Paragraph(f'<font size="9" color="#666B73">{subtitle}</font>', 
                      ParagraphStyle('CardSub', alignment=TA_CENTER, leading=12, spaceAfter=4))],
        ]
        
        card = Table(card_data, colWidths=[1.9*inch])
        card.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 2, colors.Color(0.11, 0.42, 0.69)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.96, 0.97, 0.98)),
        ]))
        
        return card
    
    def _create_key_findings(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create key findings section with proper spacing."""
        elements = []
        
        elements.append(Paragraph("Key Findings", self.styles.get_style('SubsectionTitle')))
        elements.append(Spacer(1, 0.1 * inch))
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        findings = []
        
        # Readability finding
        flesch = technical_metrics.get('flesch_reading_ease', 0)
        if flesch >= 60:
            findings.append(('✓', '#2E9E59', 'Readability is excellent - accessible to a broad professional audience.'))
        elif flesch >= 40:
            findings.append(('○', '#E8A126', 'Readability is moderate - consider simplifying for wider accessibility.'))
        else:
            findings.append(('△', '#CC423D', 'Readability needs improvement - content may be too complex for most readers.'))
        
        # Sentence structure finding
        avg_sentence = statistics.get('avg_sentence_length', 17)
        if 15 <= avg_sentence <= 20:
            findings.append(('✓', '#2E9E59', f'Sentence length ({avg_sentence:.1f} words avg) is optimal for comprehension.'))
        elif avg_sentence > 25:
            findings.append(('△', '#CC423D', f'Sentences are too long ({avg_sentence:.1f} words avg) - break into smaller units.'))
        else:
            findings.append(('○', '#E8A126', f'Sentence length ({avg_sentence:.1f} words avg) could be adjusted.'))
        
        # Passive voice finding
        passive_pct = statistics.get('passive_voice_percentage', 0)
        if passive_pct <= 15:
            findings.append(('✓', '#2E9E59', f'Active voice usage is excellent ({100-passive_pct:.0f}% active).'))
        elif passive_pct <= 25:
            findings.append(('○', '#E8A126', f'Some passive voice detected ({passive_pct:.0f}%) - consider revising.'))
        else:
            findings.append(('△', '#CC423D', f'High passive voice usage ({passive_pct:.0f}%) impacts engagement.'))
        
        # Error finding
        if len(errors) == 0:
            findings.append(('✓', '#2E9E59', 'No style issues detected - excellent writing quality!'))
        elif len(errors) < 10:
            findings.append(('○', '#339ADB', f'{len(errors)} minor issues identified - targeted improvements recommended.'))
        else:
            findings.append(('△', '#E8A126', f'{len(errors)} issues found - systematic revision recommended.'))
        
        for icon, color, text in findings:
            elements.append(Paragraph(
                f'<font color="{color}" size="12">{icon}</font>    {text}',
                self.finding_style
            ))
        
        return elements
    
    def _create_priority_actions(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create priority actions section with proper table spacing."""
        elements = []
        
        elements.append(Paragraph("Priority Actions", self.styles.get_style('SubsectionTitle')))
        elements.append(Spacer(1, 0.1 * inch))
        
        actions = MetricsInterpreter.generate_priority_actions(analysis_data)
        
        if not actions:
            elements.append(Paragraph(
                "No critical actions required - your content meets professional standards.",
                self.styles.get_style('SuccessText')
            ))
            return elements
        
        # Create action items table with better padding
        table_data = [['Priority', 'Action', 'Impact', 'Effort']]
        
        for action in actions[:4]:  # Top 4 actions
            priority_color = {
                'HIGH': '#CC423D',
                'MEDIUM': '#E8A126',
                'LOW': '#2E9E59'
            }.get(action['priority'], '#666B73')
            
            table_data.append([
                Paragraph(f'<font color="{priority_color}"><b>{action["priority"]}</b></font>',
                         self.styles.get_style('TableCell')),
                Paragraph(action['action'], self.styles.get_style('TableCell')),
                Paragraph(action['impact'], self.styles.get_style('TableCell')),
                Paragraph(action['effort'], self.styles.get_style('TableCell')),
            ])
        
        table = Table(table_data, colWidths=[0.8*inch, 2.4*inch, 1.7*inch, 0.9*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_time_savings(self, analysis_data: Dict[str, Any]) -> Flowable:
        """Create time savings callout with proper spacing."""
        time_data = MetricsCalculator.calculate_time_savings(analysis_data)
        
        savings_text = f"""<b>Estimated Time Savings with AI-Assisted Editing</b>

Manual editing estimate: {time_data['manual_edit_minutes']:.0f} minutes   •   AI-assisted: {time_data['ai_assisted_minutes']:.0f} minutes

<font color="#2E9E59"><b>Potential savings: {time_data['time_saved_minutes']:.0f} minutes ({time_data['productivity_gain_percent']:.0f}% productivity gain)</b></font>"""
        
        return Paragraph(savings_text, self.styles.get_style('InsightText'))
    
    def _get_score_hex(self, score: float) -> str:
        """Get hex color for a score."""
        if score >= 80:
            return '#1A8F57'
        elif score >= 60:
            return '#66BA6B'
        elif score >= 40:
            return '#F2BA4D'
        else:
            return '#CC423D'
