"""
Chart Themes Module

Modern, professional color themes for matplotlib charts.
Ensures visual consistency across all report visualizations.
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
from typing import List, Tuple


class ChartThemes:
    """Professional chart themes for PDF reports."""
    
    # Executive Color Palette
    EXECUTIVE_COLORS = {
        'primary': '#1C6BB0',
        'primary_light': '#3D8FD1',
        'primary_dark': '#144F82',
        'accent': '#E89426',
        'accent_light': '#F5C26B',
        'success': '#2E9E59',
        'warning': '#E8A126',
        'danger': '#CC423D',
        'info': '#339ADB',
        'text': '#26262E',
        'text_light': '#666B73',
        'border': '#D1D6DE',
        'background': '#F5F7FA',
        'white': '#FFFFFF',
    }
    
    # Chart Color Sequences
    CHART_COLORS = [
        '#1C6BB0',  # Primary Blue
        '#E89426',  # Executive Gold
        '#2E9E59',  # Success Green
        '#CC423D',  # Refined Red
        '#8B5CF6',  # Purple
        '#339ADB',  # Info Blue
        '#F97316',  # Orange
        '#06B6D4',  # Cyan
    ]
    
    # Gradient Colors for Progress Bars
    GRADIENT_EXCELLENT = ['#1A8F57', '#2E9E59']
    GRADIENT_GOOD = ['#2E9E59', '#66BA6B']
    GRADIENT_FAIR = ['#E8A126', '#F2BA4D']
    GRADIENT_POOR = ['#CC423D', '#E3735E']
    
    @classmethod
    def apply_executive_theme(cls):
        """Apply executive theme to matplotlib."""
        plt.style.use('default')
        
        # Custom style parameters
        mpl.rcParams.update({
            # Figure
            'figure.facecolor': cls.EXECUTIVE_COLORS['white'],
            'figure.edgecolor': cls.EXECUTIVE_COLORS['border'],
            'figure.figsize': (10, 6),
            'figure.dpi': 150,
            
            # Axes
            'axes.facecolor': cls.EXECUTIVE_COLORS['white'],
            'axes.edgecolor': cls.EXECUTIVE_COLORS['border'],
            'axes.labelcolor': cls.EXECUTIVE_COLORS['text'],
            'axes.titlecolor': cls.EXECUTIVE_COLORS['text'],
            'axes.labelsize': 10,
            'axes.titlesize': 12,
            'axes.titleweight': 'bold',
            'axes.labelweight': 'normal',
            'axes.spines.top': False,
            'axes.spines.right': False,
            'axes.prop_cycle': mpl.cycler(color=cls.CHART_COLORS),
            'axes.grid': True,
            'axes.axisbelow': True,
            
            # Grid
            'grid.color': cls.EXECUTIVE_COLORS['border'],
            'grid.linestyle': '-',
            'grid.linewidth': 0.5,
            'grid.alpha': 0.7,
            
            # Ticks
            'xtick.color': cls.EXECUTIVE_COLORS['text_light'],
            'ytick.color': cls.EXECUTIVE_COLORS['text_light'],
            'xtick.labelsize': 9,
            'ytick.labelsize': 9,
            
            # Legend
            'legend.frameon': True,
            'legend.framealpha': 0.9,
            'legend.facecolor': cls.EXECUTIVE_COLORS['white'],
            'legend.edgecolor': cls.EXECUTIVE_COLORS['border'],
            'legend.fontsize': 9,
            
            # Font
            'font.family': 'sans-serif',
            'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
            'font.size': 10,
            
            # Savefig
            'savefig.dpi': 200,
            'savefig.facecolor': cls.EXECUTIVE_COLORS['white'],
            'savefig.edgecolor': 'none',
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.2,
        })
    
    @classmethod
    def get_chart_colors(cls, n: int = 8) -> List[str]:
        """Get n chart colors from the palette."""
        colors = cls.CHART_COLORS.copy()
        while len(colors) < n:
            colors.extend(cls.CHART_COLORS)
        return colors[:n]
    
    @classmethod
    def get_score_color(cls, score: float) -> str:
        """Get hex color based on score (0-100)."""
        if score >= 80:
            return '#1A8F57'  # Excellent - Deep Green
        elif score >= 60:
            return '#66BA6B'  # Good - Light Green
        elif score >= 40:
            return '#F2BA4D'  # Fair - Amber
        elif score >= 20:
            return '#E3735E'  # Poor - Soft Red
        else:
            return '#BF3838'  # Critical - Deep Red
    
    @classmethod
    def get_score_colors_list(cls, scores: List[float]) -> List[str]:
        """Get colors for a list of scores."""
        return [cls.get_score_color(s) for s in scores]
    
    @classmethod
    def get_status_colors(cls) -> dict:
        """Get status colors dictionary."""
        return {
            'excellent': '#1A8F57',
            'good': '#66BA6B',
            'fair': '#F2BA4D',
            'poor': '#E3735E',
            'critical': '#BF3838',
        }
    
    @classmethod
    def get_bar_gradient(cls, score: float) -> Tuple[str, str]:
        """Get gradient colors for a progress bar based on score."""
        if score >= 80:
            return tuple(cls.GRADIENT_EXCELLENT)
        elif score >= 60:
            return tuple(cls.GRADIENT_GOOD)
        elif score >= 40:
            return tuple(cls.GRADIENT_FAIR)
        else:
            return tuple(cls.GRADIENT_POOR)
    
    @classmethod
    def create_gauge_colors(cls) -> List[str]:
        """Get colors for gauge charts (from critical to excellent)."""
        return [
            '#BF3838',  # Critical
            '#E3735E',  # Poor
            '#F2BA4D',  # Fair
            '#66BA6B',  # Good
            '#1A8F57',  # Excellent
        ]

