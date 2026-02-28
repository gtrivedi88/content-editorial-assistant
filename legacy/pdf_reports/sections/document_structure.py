"""
Document Structure Section

Analyzes and presents document structure information
including statistics, error summaries, and structural block analysis.
"""

from typing import Dict, Any, List, Optional
from collections import Counter
from reportlab.platypus import Flowable, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.units import inch
from reportlab.lib import colors

from ..styles.corporate_styles import CorporateStyles
from ..utils.metrics import MetricsCalculator


class DocumentStructureSection:
    """Generate document structure section for PDF reports."""
    
    def __init__(self, styles: CorporateStyles):
        """Initialize with corporate styles."""
        self.styles = styles
    
    def generate(self, analysis_data: Dict[str, Any], content: str,
                 structural_blocks: Optional[List[Dict]] = None) -> List[Flowable]:
        """Generate document structure elements."""
        elements = []
        
        # Section title
        elements.append(Paragraph(
            "Document Structure Analysis",
            self.styles.get_style('SectionTitle')
        ))
        
        # Document statistics
        stats_section = self._create_statistics_section(analysis_data, content)
        elements.append(KeepTogether(stats_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Content preview
        preview_section = self._create_content_preview(content)
        elements.append(KeepTogether(preview_section))
        elements.append(Spacer(1, 0.3 * inch))
        
        # Error summary
        error_summary = self._create_error_summary(analysis_data)
        elements.append(KeepTogether(error_summary))
        
        # Structural blocks analysis (if available)
        if structural_blocks:
            elements.append(Spacer(1, 0.3 * inch))
            blocks_section = self._create_structural_blocks_section(structural_blocks)
            elements.append(KeepTogether(blocks_section))
        
        return elements
    
    def _create_statistics_section(self, analysis_data: Dict[str, Any], content: str) -> List[Flowable]:
        """Create document statistics section."""
        elements = []
        
        elements.append(Paragraph("Document Statistics", self.styles.get_style('SubsectionTitle')))
        
        statistics = analysis_data.get('statistics', {})
        
        # Statistics table
        stats_data = [
            ['Metric', 'Value', 'Metric', 'Value'],
            [
                'Total Characters', f"{len(content):,}",
                'Word Count', f"{statistics.get('word_count', 0):,}"
            ],
            [
                'Sentence Count', f"{statistics.get('sentence_count', 0):,}",
                'Paragraph Count', f"{statistics.get('paragraph_count', 0):,}"
            ],
            [
                'Avg Words/Sentence', f"{statistics.get('avg_sentence_length', 0):.1f}",
                'Avg Sentences/Para', f"{statistics.get('avg_paragraph_length', 0):.1f}"
            ],
            [
                'Reading Time', MetricsCalculator.estimate_reading_time(statistics.get('word_count', 0)),
                'Estimated Pages', f"{max(1, statistics.get('word_count', 0) // 250)}"
            ]
        ]
        
        table = Table(stats_data, colWidths=[1.5*inch, 1.2*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_content_preview(self, content: str) -> List[Flowable]:
        """Create content preview section."""
        elements = []
        
        elements.append(Paragraph("Content Preview", self.styles.get_style('SubsectionTitle')))
        
        # Show first 400 characters
        preview_length = min(400, len(content))
        preview = content[:preview_length]
        if len(content) > preview_length:
            preview += "..."
        
        # Clean up the preview for display
        preview = preview.replace('\n', ' ').replace('\r', ' ')
        preview = ' '.join(preview.split())  # Normalize whitespace
        
        elements.append(Paragraph(
            f'<font size="9" color="#26262E">{preview}</font>',
            self.styles.get_style('CodeText')
        ))
        
        return elements
    
    def _create_error_summary(self, analysis_data: Dict[str, Any]) -> List[Flowable]:
        """Create error summary section."""
        elements = []
        
        elements.append(Paragraph("Issue Summary", self.styles.get_style('SubsectionTitle')))
        
        errors = analysis_data.get('errors', [])
        
        if not errors:
            elements.append(Paragraph(
                "✓ No issues detected in the document. Excellent writing quality!",
                self.styles.get_style('SuccessText')
            ))
            return elements
        
        # Count errors by type
        error_counts = Counter([error.get('type', 'unknown') for error in errors])
        total_errors = len(errors)
        
        # Create summary table
        table_data = [['Issue Type', 'Count', 'Percentage', 'Priority']]
        
        for error_type, count in error_counts.most_common(8):  # Top 8 error types
            percentage = (count / total_errors) * 100
            priority = self._get_error_priority(error_type, count)
            priority_color = {'High': '#CC423D', 'Medium': '#E8A126', 'Low': '#2E9E59'}[priority]
            
            table_data.append([
                error_type.replace('_', ' ').title(),
                str(count),
                f"{percentage:.1f}%",
                Paragraph(f'<font color="{priority_color}">{priority}</font>',
                         self.styles.get_style('TableCell'))
            ])
        
        table = Table(table_data, colWidths=[2.5*inch, 0.8*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (2, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
        ]))
        
        elements.append(table)
        
        # Total summary
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(
            f"<b>Total Issues:</b> {total_errors} across {len(error_counts)} categories",
            self.styles.get_style('BodyText')
        ))
        
        return elements
    
    def _create_structural_blocks_section(self, structural_blocks: List[Dict]) -> List[Flowable]:
        """Create structural blocks analysis section."""
        elements = []
        
        elements.append(Paragraph("Structural Block Analysis", self.styles.get_style('SubsectionTitle')))
        
        intro_text = f"""
        The document was parsed into <b>{len(structural_blocks)} structural blocks</b> for detailed 
        analysis. This enables context-aware error detection and more precise recommendations.
        """
        elements.append(Paragraph(intro_text, self.styles.get_style('BodyText')))
        elements.append(Spacer(1, 0.1 * inch))
        
        # Block type summary
        block_types = Counter([block.get('block_type', 'unknown') for block in structural_blocks])
        
        if block_types:
            table_data = [['Block Type', 'Count']]
            for block_type, count in block_types.most_common():
                table_data.append([
                    block_type.replace('_', ' ').title(),
                    str(count)
                ])
            
            table = Table(table_data, colWidths=[3*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.11, 0.42, 0.69)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.82, 0.84, 0.87)),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.96, 0.97, 0.98)]),
            ]))
            
            elements.append(table)
        
        return elements
    
    def _get_error_priority(self, error_type: str, count: int) -> str:
        """Determine error priority based on type and count."""
        high_priority_types = ['passive_voice', 'sentence_length', 'readability']
        medium_priority_types = ['complex_words', 'word_choice', 'clarity']
        
        error_type_lower = error_type.lower()
        
        if any(t in error_type_lower for t in high_priority_types) or count >= 10:
            return 'High'
        elif any(t in error_type_lower for t in medium_priority_types) or count >= 5:
            return 'Medium'
        else:
            return 'Low'

