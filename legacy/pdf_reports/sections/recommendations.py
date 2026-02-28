"""
Recommendations Section

Actionable recommendations with prioritization,
time estimates, and impact assessments.
"""

from typing import Dict, Any, List
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors

from ..styles.corporate_styles import CorporateStyles
from ..utils.metrics import MetricsCalculator
from ..utils.interpretations import MetricsInterpreter


class RecommendationsSection:
    """Generate recommendations section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate recommendations elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Recommendations & Action Plan",
            self.styles.get_style('SectionTitle')
        ))
        
        # Priority recommendations
        priority_section = self._create_priority_recommendations(analysis_data)
        elements.append(KeepTogether(priority_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Improvement roadmap
        roadmap_section = self._create_improvement_roadmap(analysis_data)
        elements.append(KeepTogether(roadmap_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Quick wins
        quick_wins = self._create_quick_wins(analysis_data)
        elements.append(KeepTogether(quick_wins))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Impact summary
        impact_section = self._create_impact_summary(analysis_data)
        elements.append(KeepTogether(impact_section))
        
        return elements
    
    def _create_priority_recommendations(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create high priority recommendations section."""
        elements = []
        
        elements.append(Paragraph("High Priority Actions", self.styles.get_style('SubsectionTitle')))
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        errors = analysis_data.get('errors', [])
        
        recommendations = []
        
        # Grade level recommendations
        grade_level = MetricsCalculator.extract_grade_level(analysis_data)
        if grade_level > 14:
            recommendations.append({
                'action': 'Simplify complex sentences to improve accessibility',
                'reason': f'Current grade level ({grade_level:.1f}) is too high for broad audiences',
                'impact': 'High',
                'effort': 'Medium'
            })
        elif grade_level < 8:
            recommendations.append({
                'action': 'Enhance vocabulary and sentence complexity',
                'reason': f'Current grade level ({grade_level:.1f}) may lack professional authority',
                'impact': 'Medium',
                'effort': 'Low'
            })
        
        # Sentence length recommendations
        avg_sentence = statistics.get('avg_sentence_length', 17)
        if avg_sentence > 25:
            recommendations.append({
                'action': 'Break down long sentences for better clarity',
                'reason': f'Average sentence length ({avg_sentence:.1f} words) exceeds recommended 20 words',
                'impact': 'High',
                'effort': 'Medium'
            })
        
        # Passive voice recommendations
        passive_pct = statistics.get('passive_voice_percentage', 0)
        if passive_pct > 25:
            recommendations.append({
                'action': 'Reduce passive voice usage for more engaging writing',
                'reason': f'Passive voice ({passive_pct:.0f}%) is too high for active, engaging content',
                'impact': 'High',
                'effort': 'Low'
            })
        
        # Error-based recommendations
        if len(errors) > 15:
            recommendations.append({
                'action': 'Systematic review to address multiple style issues',
                'reason': f'{len(errors)} issues identified require organized revision approach',
                'impact': 'High',
                'effort': 'High'
            })
        
        if not recommendations:
            elements.append(Paragraph(
                "✓ No critical actions required - your content meets professional standards.",
                self.styles.get_style('SuccessText')
            ))
            return elements
        
        # Create recommendations table
        table_data = [['Action', 'Reason', 'Impact', 'Effort']]
        
        for rec in recommendations[:4]:
            table_data.append([
                Paragraph(rec['action'], self.styles.get_style('TableCell')),
                Paragraph(rec['reason'], self.styles.get_style('TableCell')),
                self._create_impact_badge(rec['impact']),
                self._create_effort_badge(rec['effort'])
            ])
        
        table = Table(table_data, colWidths=[2*inch, 2.2*inch, 0.8*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (3, -1), 'CENTER'),
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
    
    def _create_improvement_roadmap(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create improvement roadmap section."""
        elements = []
        
        elements.append(Paragraph("Improvement Roadmap", self.styles.get_style('SubsectionTitle')))
        
        statistics = analysis_data.get('statistics', {})
        errors = analysis_data.get('errors', [])
        
        # Define phases based on analysis
        phases = []
        
        # Phase 1: Critical fixes
        if len(errors) > 0:
            phases.append({
                'phase': 'Phase 1: Critical Fixes',
                'timeline': 'Immediate',
                'tasks': ['Address high-priority style issues', 'Fix grammar and spelling errors'],
                'outcome': 'Eliminate major issues'
            })
        
        # Phase 2: Structure improvements
        avg_sentence = statistics.get('avg_sentence_length', 17)
        if avg_sentence > 22 or statistics.get('passive_voice_percentage', 0) > 20:
            phases.append({
                'phase': 'Phase 2: Structure',
                'timeline': '1-2 days',
                'tasks': ['Restructure long sentences', 'Convert passive to active voice'],
                'outcome': 'Improve readability by 20-30%'
            })
        
        # Phase 3: Polish
        phases.append({
            'phase': 'Phase 3: Polish',
            'timeline': '2-3 days',
            'tasks': ['Enhance vocabulary diversity', 'Optimize for AI processing'],
            'outcome': 'Publication-ready content'
        })
        
        for phase in phases:
            phase_text = f"""<b>{phase['phase']}</b> ({phase['timeline']})

<font color="#666B73">Tasks:</font> {', '.join(phase['tasks'])}

<font color="#2E9E59">Expected Outcome:</font> {phase['outcome']}"""
            elements.append(Paragraph(phase_text, self.styles.get_style('BodyText')))
            elements.append(Spacer(1, 0.2 * inch))
        
        return elements
    
    def _create_quick_wins(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create quick wins section."""
        elements = []
        
        elements.append(Paragraph("Quick Wins (Under 15 Minutes)", self.styles.get_style('SubsectionTitle')))
        
        quick_wins = [
            "Search and replace common wordy phrases (e.g., 'in order to' → 'to')",
            "Convert 'there is/are' constructions to direct statements",
            "Remove unnecessary adverbs (very, really, extremely)",
            "Replace passive constructions with active voice",
            "Break any sentence over 30 words into two sentences"
        ]
        
        for win in quick_wins:
            elements.append(Paragraph(
                f'<font color="#2E9E59">✓</font> {win}',
                self.styles.get_style('BulletText')
            ))
        
        return elements
    
    def _create_impact_summary(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create impact summary section."""
        elements = []
        
        elements.append(Paragraph("Expected Impact", self.styles.get_style('SubsectionTitle')))
        
        time_data = MetricsCalculator.calculate_time_savings(analysis_data)
        
        impact_text = f"""By implementing these recommendations, you can expect:

•  <b>Time Savings:</b> Up to {time_data['time_saved_minutes']:.0f} minutes of editing time saved

•  <b>Readability Improvement:</b> 20-40% increase in reader comprehension

•  <b>Professional Impact:</b> Enhanced credibility and authority

•  <b>AI Processing:</b> 40-60% improvement in LLM content processing

•  <b>Engagement:</b> Better reader engagement and retention

These improvements translate to more effective communication and reduced revision cycles."""
        
        elements.append(Paragraph(impact_text, self.styles.get_style('InsightText')))
        
        return elements
    
    def _create_impact_badge(self, impact: str) -> Paragraph:
        """Create impact badge."""
        colors_map = {'High': '#CC423D', 'Medium': '#E8A126', 'Low': '#2E9E59'}
        color = colors_map.get(impact, '#666B73')
        return Paragraph(
            f'<font color="{color}"><b>{impact}</b></font>',
            self.styles.get_style('TableCell')
        )
    
    def _create_effort_badge(self, effort: str) -> Paragraph:
        """Create effort badge."""
        colors_map = {'High': '#CC423D', 'Medium': '#E8A126', 'Low': '#2E9E59'}
        color = colors_map.get(effort, '#666B73')
        return Paragraph(
            f'<font color="{color}"><b>{effort}</b></font>',
            self.styles.get_style('TableCell')
        )

