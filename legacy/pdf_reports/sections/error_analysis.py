"""
Error Analysis Section

Detailed error analysis with examples, suggestions,
and visualizations for actionable improvement.
"""

from typing import Dict, Any, List
from collections import Counter
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors

from ..styles.corporate_styles import CorporateStyles
from ..charts.error_charts import ErrorCharts


class ErrorAnalysisSection:
    """Generate error analysis section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
    
    def generate(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Generate error analysis elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Detailed Issue Analysis",
            self.styles.get_style('SectionTitle')
        ))
        
        errors = analysis_data.get('errors', [])
        
        if not errors:
            elements.append(self._create_no_errors_message())
            return elements
        
        # Error distribution chart
        chart = ErrorCharts.create_error_distribution_pie(errors)
        if chart:
            elements.append(chart)
            elements.append(Spacer(1, 0.3 * inch))
        
        # Error categories chart
        categories_chart = ErrorCharts.create_error_categories_chart(errors)
        if categories_chart:
            elements.append(categories_chart)
            elements.append(Spacer(1, 0.3 * inch))
        
        # Detailed error breakdown by type
        error_breakdown = self._create_error_breakdown(errors)
        elements.extend(error_breakdown)
        
        return elements
    
    def _create_no_errors_message(self) -> Flowable:
        """Create message for when no errors are found."""
        message = """
        <para alignment="CENTER">
            <font size="16" color="#2E9E59">✓ Excellent Writing!</font><br/><br/>
            <font size="11" color="#26262E">
                No style issues were detected in your document.<br/>
                Your content meets professional writing standards.
            </font>
        </para>
        """
        return Paragraph(message, self.styles.get_style('BodyText'))
    
    def _create_error_breakdown(self, errors: List[Dict]) -> List[Flowable]:
        """Create detailed breakdown by error type."""
        elements = []
        
        # Group errors by type
        error_groups = {}
        for error in errors:
            error_type = error.get('type', 'unknown')
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(error)
        
        # Sort by count (most common first)
        sorted_groups = sorted(error_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for error_type, error_list in sorted_groups[:6]:  # Top 6 error types
            section = self._create_error_type_section(error_type, error_list)
            elements.append(KeepTogether(section))
            elements.append(Spacer(1, 0.2 * inch))
        
        # Note if there are more error types
        if len(sorted_groups) > 6:
            remaining = len(sorted_groups) - 6
            remaining_count = sum(len(v) for _, v in sorted_groups[6:])
            elements.append(Paragraph(
                f"<i>...and {remaining} more issue types ({remaining_count} issues total)</i>",
                self.styles.get_style('BodyText')
            ))
        
        return elements
    
    def _create_error_type_section(self, error_type: str, errors: List[Dict]) -> List[Flowable]:
        """Create section for a specific error type."""
        elements = []
        
        # Title with count
        clean_type = error_type.replace('_', ' ').title()
        priority = self._get_priority(error_type, len(errors))
        priority_color = {'High': '#CC423D', 'Medium': '#E8A126', 'Low': '#2E9E59'}[priority]
        
        elements.append(Paragraph(
            f'<b>{clean_type}</b> <font color="{priority_color}" size="9">({len(errors)} issues - {priority} Priority)</font>',
            self.styles.get_style('SubsectionTitle')
        ))
        
        # Show examples (max 3)
        examples_to_show = min(3, len(errors))
        
        for i, error in enumerate(errors[:examples_to_show]):
            example = self._create_error_example(i + 1, error)
            elements.extend(example)
        
        # Note if there are more
        if len(errors) > examples_to_show:
            elements.append(Paragraph(
                f"<i>...and {len(errors) - examples_to_show} more similar issues</i>",
                self.styles.get_style('BodyText')
            ))
        
        return elements
    
    def _create_error_example(self, index: int, error: Dict) -> List[Flowable]:
        """Create a single error example."""
        elements = []
        
        sentence = error.get('sentence', '')
        message = error.get('message', '')
        suggestions = error.get('suggestions', [])
        flagged_text = error.get('flagged_text', '')
        
        # Example number and sentence
        if sentence:
            # Truncate long sentences
            display_sentence = sentence[:200] + '...' if len(sentence) > 200 else sentence
            elements.append(Paragraph(
                f'<b>Example {index}:</b> "{display_sentence}"',
                self.styles.get_style('BodyText')
            ))
        
        # Issue message
        if message:
            elements.append(Paragraph(
                f'<font color="#CC423D">Issue:</font> {message}',
                self.styles.get_style('BulletText')
            ))
        
        # Flagged text
        if flagged_text and flagged_text != sentence:
            elements.append(Paragraph(
                f'<font color="#E8A126">Flagged:</font> "{flagged_text}"',
                self.styles.get_style('BulletText')
            ))
        
        # Suggestions
        if suggestions:
            elements.append(Paragraph(
                '<font color="#2E9E59">Suggestions:</font>',
                self.styles.get_style('BulletText')
            ))
            for suggestion in suggestions[:2]:  # Max 2 suggestions
                elements.append(Paragraph(
                    f'  • {suggestion}',
                    self.styles.get_style('BulletText')
                ))
        
        elements.append(Spacer(1, 0.1 * inch))
        
        return elements
    
    def _get_priority(self, error_type: str, count: int) -> str:
        """Determine error priority."""
        high_priority_types = ['passive_voice', 'sentence_length', 'readability', 
                              'grammar', 'spelling']
        medium_priority_types = ['complex_words', 'word_choice', 'clarity',
                                'punctuation', 'style']
        
        error_type_lower = error_type.lower()
        
        if any(t in error_type_lower for t in high_priority_types) or count >= 10:
            return 'High'
        elif any(t in error_type_lower for t in medium_priority_types) or count >= 5:
            return 'Medium'
        else:
            return 'Low'

