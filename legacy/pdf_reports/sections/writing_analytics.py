"""
Writing Analytics Section

Detailed writing analytics with professional visualizations,
benchmark comparisons, and actionable insights.
"""

from typing import Dict, Any, List
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors

from ..styles.corporate_styles import CorporateStyles
from ..utils.metrics import MetricsCalculator
from ..utils.interpretations import MetricsInterpreter
from ..charts.readability_charts import ReadabilityCharts
from ..charts.quality_charts import QualityCharts


class WritingAnalyticsSection:
    """Generate writing analytics section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate writing analytics elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Writing Analytics",
            self.styles.get_style('SectionTitle')
        ))
        
        # Grade level assessment
        grade_section = self._create_grade_level_section(analysis_data)
        elements.append(KeepTogether(grade_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Readability analysis
        readability_section = self._create_readability_section(analysis_data)
        elements.append(KeepTogether(readability_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Quality metrics
        quality_section = self._create_quality_metrics_section(analysis_data)
        elements.append(KeepTogether(quality_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # LLM readiness
        llm_section = self._create_llm_readiness_section(analysis_data)
        elements.append(KeepTogether(llm_section))
        
        return elements
    
    def _create_grade_level_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create grade level assessment section."""
        elements = []
        
        elements.append(Paragraph("Grade Level Assessment", self.styles.get_style('SubsectionTitle')))
        
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        grade_info = MetricsInterpreter.interpret_grade_level(grade_level)
        
        # Create assessment table
        assessment_data = [
            ['Metric', 'Value', 'Assessment'],
            ['Current Grade Level', f'{grade_level:.1f}', grade_info['category']],
            ['Target Range', '9-11', 'Professional Technical Writing'],
            ['Target Audience', grade_info['audience'], ''],
            ['Recommendation', '', grade_info['recommendation'][:60] + '...'] 
        ]
        
        table = Table(assessment_data, colWidths=[1.8*inch, 1.5*inch, 2.7*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
            ('SPAN', (1, 4), (2, 4)),  # Span recommendation across columns
        ]))
        
        elements.append(table)
        
        # Add interpretation
        elements.append(Spacer(1, 0.15 * inch))
        
        status_style = 'SuccessText' if 8 <= grade_level <= 12 else 'WarningText'
        elements.append(Paragraph(
            f"<b>Interpretation:</b> {grade_info['assessment']}",
            self.styles.get_style(status_style)
        ))
        
        return elements
    
    def _create_readability_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create readability analysis section."""
        elements = []
        
        elements.append(Paragraph("Readability Analysis", self.styles.get_style('SubsectionTitle')))
        
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        statistics = analysis_data.get('statistics', {})
        
        # Readability scores table
        metrics = [
            ('Flesch Reading Ease', 
             technical_metrics.get('flesch_reading_ease', 0),
             MetricsInterpreter.interpret_readability(technical_metrics.get('flesch_reading_ease', 0))['category'],
             '60-70'),
            ('Flesch-Kincaid Grade',
             technical_metrics.get('flesch_kincaid_grade', 0),
             f"Grade {technical_metrics.get('flesch_kincaid_grade', 0):.0f} level",
             '9-11'),
            ('Gunning Fog Index',
             technical_metrics.get('gunning_fog_index', 0),
             MetricsInterpreter.interpret_fog_index(technical_metrics.get('gunning_fog_index', 0))['assessment'],
             '< 12'),
            ('SMOG Index',
             technical_metrics.get('smog_index', 0),
             f"{technical_metrics.get('smog_index', 0):.0f} years education",
             '< 13'),
        ]
        
        table_data = [['Metric', 'Score', 'Interpretation', 'Target']]
        for name, value, interpretation, target in metrics:
            table_data.append([name, f'{value:.1f}', interpretation, target])
        
        table = Table(table_data, colWidths=[1.6*inch, 0.9*inch, 2.2*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_quality_metrics_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create writing quality metrics section."""
        elements = []
        
        elements.append(Paragraph("Writing Quality Metrics", self.styles.get_style('SubsectionTitle')))
        
        statistics = analysis_data.get('statistics', {})
        
        # Quality metrics with interpretations
        metrics = [
            {
                'name': 'Average Sentence Length',
                'value': f"{statistics.get('avg_sentence_length', 0):.1f} words",
                'target': '15-20 words',
                'interpretation': MetricsInterpreter.interpret_sentence_length(
                    statistics.get('avg_sentence_length', 0)
                )
            },
            {
                'name': 'Passive Voice Usage',
                'value': f"{statistics.get('passive_voice_percentage', 0):.1f}%",
                'target': '< 15%',
                'interpretation': MetricsInterpreter.interpret_passive_voice(
                    statistics.get('passive_voice_percentage', 0)
                )
            },
            {
                'name': 'Complex Words',
                'value': f"{statistics.get('complex_words_percentage', 0):.1f}%",
                'target': '< 20%',
                'interpretation': MetricsInterpreter.interpret_complex_words(
                    statistics.get('complex_words_percentage', 0)
                )
            },
            {
                'name': 'Vocabulary Diversity',
                'value': f"{statistics.get('vocabulary_diversity', 0):.2f}",
                'target': '> 0.7',
                'interpretation': MetricsInterpreter.interpret_vocabulary_diversity(
                    statistics.get('vocabulary_diversity', 0)
                )
            }
        ]
        
        for metric in metrics:
            interp = metric['interpretation']
            status_color = {'success': '#2E9E59', 'warning': '#E8A126', 'danger': '#CC423D'}.get(
                interp.get('status', 'warning'), '#666B73'
            )
            
            # Use separate lines instead of <br/> for proper spacing
            metric_text = f"""<b>{metric['name']}</b>: {metric['value']} (Target: {metric['target']})

<font color="{status_color}">{interp['assessment']}</font> - {interp['recommendation']}"""
            
            elements.append(Paragraph(metric_text, self.styles.get_style('BodyText')))
            elements.append(Spacer(1, 0.15 * inch))
        
        return elements
    
    def _create_llm_readiness_section(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create AI/LLM readiness section."""
        elements = []
        
        elements.append(Paragraph("AI & LLM Readiness", self.styles.get_style('SubsectionTitle')))
        
        llm_data = MetricsCalculator.calculate_llm_readiness_score(analysis_data)
        
        score_color = '#2E9E59' if llm_data['score'] >= 80 else '#E8A126' if llm_data['score'] >= 60 else '#CC423D'
        
        # LLM score display
        score_text = f"""<b>LLM Consumability Score:</b>  <font color="{score_color}" size="14">{llm_data['score']:.0f}/100</font>  <font color="#666B73">({llm_data['category']})</font>"""
        elements.append(Paragraph(score_text, self.styles.get_style('BodyText')))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Strengths
        if llm_data.get('strengths'):
            elements.append(Paragraph("<b>Strengths:</b>", self.styles.get_style('BodyText')))
            for strength in llm_data['strengths']:
                elements.append(Paragraph(
                    f'<font color="#2E9E59">✓</font> {strength}',
                    self.styles.get_style('BulletText')
                ))
        
        # Areas for improvement
        if llm_data.get('issues'):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("<b>Areas for Improvement:</b>", self.styles.get_style('BodyText')))
            for issue in llm_data['issues']:
                elements.append(Paragraph(
                    f'<font color="#E8A126">○</font> {issue}',
                    self.styles.get_style('BulletText')
                ))
        
        # AI benefits callout
        elements.append(Spacer(1, 0.2 * inch))
        benefits_text = """<b>Benefits of AI-Optimized Content:</b>

Well-structured content with clear readability metrics processes 40-60% more effectively through LLM systems, resulting in higher quality automated improvements and more accurate content generation."""
        elements.append(Paragraph(benefits_text, self.styles.get_style('InsightText')))
        
        return elements

