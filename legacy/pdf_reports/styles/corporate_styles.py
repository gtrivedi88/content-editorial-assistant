"""
Corporate Styles Module

Professional corporate styling for executive-ready PDF reports.
Features elegant typography, consistent branding, and sophisticated color palette.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY


class CorporateStyles:
    """Professional corporate styling for PDF reports."""
    
    # Premium Color Palette - Inspired by executive reports
    COLORS = {
        # Primary Brand Colors
        'primary': colors.Color(0.11, 0.42, 0.69),      # Deep Professional Blue #1C6BB0
        'primary_light': colors.Color(0.24, 0.56, 0.82), # Lighter Blue #3D8FD1
        'primary_dark': colors.Color(0.08, 0.31, 0.51),  # Darker Blue #144F82
        
        # Accent Colors
        'accent': colors.Color(0.91, 0.58, 0.15),       # Executive Gold #E89426
        'accent_light': colors.Color(0.96, 0.76, 0.42), # Light Gold #F5C26B
        
        # Status Colors
        'success': colors.Color(0.18, 0.62, 0.35),      # Professional Green #2E9E59
        'warning': colors.Color(0.91, 0.63, 0.15),      # Warm Amber #E8A126
        'danger': colors.Color(0.80, 0.26, 0.24),       # Refined Red #CC423D
        'info': colors.Color(0.20, 0.60, 0.86),         # Clear Blue #339ADB
        
        # Neutral Colors
        'text_primary': colors.Color(0.15, 0.15, 0.18), # Near Black #26262E
        'text_secondary': colors.Color(0.40, 0.42, 0.45),# Dark Gray #666B73
        'text_muted': colors.Color(0.60, 0.62, 0.65),   # Medium Gray #999EA6
        'border': colors.Color(0.82, 0.84, 0.87),       # Light Gray Border #D1D6DE
        'background': colors.Color(0.96, 0.97, 0.98),   # Off White Background #F5F7FA
        'white': colors.white,
        'black': colors.black,
        
        # Score Gradient Colors
        'score_excellent': colors.Color(0.10, 0.56, 0.34),  # Deep Green #1A8F57
        'score_good': colors.Color(0.40, 0.73, 0.42),       # Light Green #66BA6B
        'score_fair': colors.Color(0.95, 0.73, 0.30),       # Amber #F2BA4D
        'score_poor': colors.Color(0.89, 0.45, 0.37),       # Soft Red #E3735E
        'score_critical': colors.Color(0.75, 0.22, 0.22),   # Deep Red #BF3838
    }
    
    def __init__(self):
        """Initialize corporate styles."""
        self.base_styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self) -> dict:
        """Create comprehensive custom paragraph styles."""
        return {
            # Report Title - Large, impactful
            'ReportTitle': ParagraphStyle(
                'ReportTitle',
                parent=self.base_styles['Title'],
                fontSize=32,
                textColor=self.COLORS['primary'],
                spaceAfter=8,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold',
                leading=38
            ),
            
            # Report Subtitle
            'ReportSubtitle': ParagraphStyle(
                'ReportSubtitle',
                parent=self.base_styles['Normal'],
                fontSize=14,
                textColor=self.COLORS['text_secondary'],
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica',
                leading=18
            ),
            
            # Section Title - Clear hierarchy
            'SectionTitle': ParagraphStyle(
                'SectionTitle',
                parent=self.base_styles['Heading1'],
                fontSize=18,
                textColor=self.COLORS['primary'],
                spaceBefore=24,
                spaceAfter=12,
                fontName='Helvetica-Bold',
                borderColor=self.COLORS['primary'],
                borderWidth=0,
                borderPadding=0,
                leading=22,
                keepWithNext=1
            ),
            
            # Subsection Title
            'SubsectionTitle': ParagraphStyle(
                'SubsectionTitle',
                parent=self.base_styles['Heading2'],
                fontSize=14,
                textColor=self.COLORS['text_primary'],
                spaceBefore=16,
                spaceAfter=8,
                fontName='Helvetica-Bold',
                leading=18,
                keepWithNext=1
            ),
            
            # Executive Highlight - For key insights
            'ExecutiveHighlight': ParagraphStyle(
                'ExecutiveHighlight',
                parent=self.base_styles['Normal'],
                fontSize=12,
                textColor=self.COLORS['primary_dark'],
                backColor=self.COLORS['background'],
                borderColor=self.COLORS['primary'],
                borderWidth=2,
                borderPadding=12,
                spaceBefore=12,
                spaceAfter=12,
                fontName='Helvetica',
                leading=18,
                leftIndent=0,
                rightIndent=0
            ),
            
            # Body Text - Clean and readable
            'BodyText': ParagraphStyle(
                'BodyText',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                spaceBefore=4,
                spaceAfter=10,
                alignment=TA_LEFT,
                fontName='Helvetica',
                leading=16  # 1.6x line height for readability
            ),
            
            # Body Text Justified
            'BodyTextJustified': ParagraphStyle(
                'BodyTextJustified',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                spaceBefore=4,
                spaceAfter=10,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leading=16  # 1.6x line height
            ),
            
            # Bullet Text
            'BulletText': ParagraphStyle(
                'BulletText',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                leftIndent=20,
                bulletIndent=8,
                spaceBefore=4,
                spaceAfter=6,
                fontName='Helvetica',
                leading=15  # Good line spacing for bullets
            ),
            
            # Key Metric Value - Large numbers
            'MetricValueLarge': ParagraphStyle(
                'MetricValueLarge',
                parent=self.base_styles['Normal'],
                fontSize=36,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                textColor=self.COLORS['primary'],
                spaceAfter=4,
                leading=42
            ),
            
            # Metric Value Medium
            'MetricValueMedium': ParagraphStyle(
                'MetricValueMedium',
                parent=self.base_styles['Normal'],
                fontSize=24,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                textColor=self.COLORS['text_primary'],
                spaceAfter=4,
                leading=28
            ),
            
            # Metric Label
            'MetricLabel': ParagraphStyle(
                'MetricLabel',
                parent=self.base_styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=self.COLORS['text_muted'],
                fontName='Helvetica',
                spaceAfter=8,
                leading=11
            ),
            
            # Score Badge - For ratings
            'ScoreBadge': ParagraphStyle(
                'ScoreBadge',
                parent=self.base_styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                alignment=TA_CENTER,
                spaceAfter=4
            ),
            
            # Code/Content Text
            'CodeText': ParagraphStyle(
                'CodeText',
                parent=self.base_styles['Code'],
                fontSize=8,
                fontName='Courier',
                backColor=self.COLORS['background'],
                borderColor=self.COLORS['border'],
                borderWidth=1,
                borderPadding=8,
                spaceAfter=8,
                leading=11,
                textColor=self.COLORS['text_primary']
            ),
            
            # Insight Text - For recommendations
            'InsightText': ParagraphStyle(
                'InsightText',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                backColor=colors.Color(0.93, 0.96, 0.99),  # Light blue tint
                borderColor=self.COLORS['info'],
                borderWidth=1,
                borderPadding=14,
                spaceBefore=12,
                spaceAfter=12,
                fontName='Helvetica',
                leading=16,  # Better line height
                leftIndent=0
            ),
            
            # Warning Text
            'WarningText': ParagraphStyle(
                'WarningText',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                backColor=colors.Color(0.99, 0.96, 0.90),  # Light amber tint
                borderColor=self.COLORS['warning'],
                borderWidth=1,
                borderPadding=14,
                spaceBefore=12,
                spaceAfter=12,
                fontName='Helvetica',
                leading=16  # Better line height
            ),
            
            # Success Text
            'SuccessText': ParagraphStyle(
                'SuccessText',
                parent=self.base_styles['Normal'],
                fontSize=10,
                textColor=self.COLORS['text_primary'],
                backColor=colors.Color(0.92, 0.98, 0.94),  # Light green tint
                borderColor=self.COLORS['success'],
                borderWidth=1,
                borderPadding=14,
                spaceBefore=12,
                spaceAfter=12,
                fontName='Helvetica',
                leading=16  # Better line height
            ),
            
            # Footer Text
            'FooterText': ParagraphStyle(
                'FooterText',
                parent=self.base_styles['Normal'],
                fontSize=8,
                textColor=self.COLORS['text_muted'],
                alignment=TA_CENTER,
                fontName='Helvetica',
                leading=10
            ),
            
            # Table Header
            'TableHeader': ParagraphStyle(
                'TableHeader',
                parent=self.base_styles['Normal'],
                fontSize=9,
                textColor=self.COLORS['white'],
                fontName='Helvetica-Bold',
                alignment=TA_LEFT,
                leading=14,  # Better line height
                spaceBefore=2,
                spaceAfter=2
            ),
            
            # Table Cell
            'TableCell': ParagraphStyle(
                'TableCell',
                parent=self.base_styles['Normal'],
                fontSize=9,
                textColor=self.COLORS['text_primary'],
                fontName='Helvetica',
                alignment=TA_LEFT,
                leading=14,  # Better line height
                spaceBefore=2,
                spaceAfter=2
            ),
        }
    
    def get_style(self, name: str) -> ParagraphStyle:
        """Get a paragraph style by name."""
        if name in self.custom_styles:
            return self.custom_styles[name]
        return self.base_styles.get(name, self.base_styles['Normal'])
    
    def get_color(self, name: str) -> colors.Color:
        """Get a color by name."""
        return self.COLORS.get(name, self.COLORS['text_primary'])
    
    def get_score_color(self, score: float) -> colors.Color:
        """Get color based on score (0-100)."""
        if score >= 80:
            return self.COLORS['score_excellent']
        elif score >= 60:
            return self.COLORS['score_good']
        elif score >= 40:
            return self.COLORS['score_fair']
        elif score >= 20:
            return self.COLORS['score_poor']
        else:
            return self.COLORS['score_critical']
    
    def get_status_color(self, status: str) -> colors.Color:
        """Get color based on status string."""
        status_map = {
            'excellent': self.COLORS['score_excellent'],
            'good': self.COLORS['score_good'],
            'fair': self.COLORS['score_fair'],
            'poor': self.COLORS['score_poor'],
            'critical': self.COLORS['score_critical'],
            'success': self.COLORS['success'],
            'warning': self.COLORS['warning'],
            'danger': self.COLORS['danger'],
            'info': self.COLORS['info'],
        }
        return status_map.get(status.lower(), self.COLORS['text_primary'])

