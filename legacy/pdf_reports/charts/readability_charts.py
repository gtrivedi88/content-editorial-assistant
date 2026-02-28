"""
Readability Charts Module

Professional chart generators for readability metrics.
Creates executive-ready visualizations with modern styling.
"""

import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from typing import Dict, Any, Optional
from reportlab.platypus import Image
from reportlab.lib.units import inch
import logging

from ..styles.chart_themes import ChartThemes

logger = logging.getLogger(__name__)


class ReadabilityCharts:
    """Generate professional readability charts."""
    
    @classmethod
    def create_grade_level_gauge(cls, grade_level: float, 
                                 width: float = 4*inch, 
                                 height: float = 2.5*inch) -> Optional[Image]:
        """Create a professional gauge chart for grade level."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(6, 3.5), subplot_kw={'projection': 'polar'})
            fig.patch.set_facecolor('white')
            
            # Configure gauge
            ax.set_theta_direction(-1)
            ax.set_theta_offset(np.pi)
            ax.set_thetamin(0)
            ax.set_thetamax(180)
            
            # Create gauge segments
            colors = ChartThemes.create_gauge_colors()[::-1]  # Reverse for gauge direction
            segments = [
                (0, 36, colors[0]),    # Grade 5-8: Very Easy
                (36, 72, colors[1]),   # Grade 8-10: Easy
                (72, 108, colors[2]),  # Grade 10-12: Standard
                (108, 144, colors[3]), # Grade 12-14: Difficult
                (144, 180, colors[4]), # Grade 14+: Very Difficult
            ]
            
            for start, end, color in segments:
                theta = np.linspace(np.radians(start), np.radians(end), 50)
                ax.fill_between(theta, 0.6, 1, color=color, alpha=0.8)
            
            # Calculate needle position (grade 5-18 mapped to 0-180 degrees)
            clamped_grade = max(5, min(18, grade_level))
            needle_angle = ((clamped_grade - 5) / 13) * 180
            needle_rad = np.radians(needle_angle)
            
            # Draw needle
            ax.annotate('', xy=(needle_rad, 0.95), xytext=(needle_rad, 0),
                       arrowprops=dict(arrowstyle='->', color='#26262E', lw=3))
            
            # Center circle
            circle = plt.Circle((0, 0), 0.15, transform=ax.transData._b, 
                               color='#26262E', zorder=10)
            ax.add_artist(circle)
            
            # Add grade level text in center
            ax.text(0, -0.4, f'{grade_level:.1f}', ha='center', va='center',
                   fontsize=24, fontweight='bold', color='#26262E',
                   transform=ax.transAxes)
            ax.text(0, -0.55, 'Grade Level', ha='center', va='center',
                   fontsize=10, color='#666B73', transform=ax.transAxes)
            
            # Add scale labels
            for grade, angle in [(6, 10), (9, 54), (11, 90), (13, 126), (16, 162)]:
                rad = np.radians(angle)
                ax.text(rad, 1.15, str(grade), ha='center', va='center',
                       fontsize=8, color='#666B73')
            
            # Clean up axes
            ax.set_ylim(0, 1.3)
            ax.axis('off')
            
            # Add title
            plt.title('Reading Level Assessment', fontsize=12, fontweight='bold',
                     color='#26262E', pad=20)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating grade level gauge: {e}")
            return None
    
    @classmethod
    def create_readability_scores_chart(cls, technical_metrics: Dict[str, Any],
                                        width: float = 5.5*inch,
                                        height: float = 2.5*inch) -> Optional[Image]:
        """Create horizontal bar chart comparing readability scores."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(8, 3.5))
            
            # Prepare data
            metrics = [
                ('Flesch Reading Ease', technical_metrics.get('flesch_reading_ease', 0), 100),
                ('Flesch-Kincaid Grade', technical_metrics.get('flesch_kincaid_grade', 0), 18),
                ('Gunning Fog Index', technical_metrics.get('gunning_fog_index', 0), 20),
                ('SMOG Index', technical_metrics.get('smog_index', 0), 20),
            ]
            
            labels = [m[0] for m in metrics]
            values = [m[1] for m in metrics]
            max_vals = [m[2] for m in metrics]
            
            # Normalize values for display (0-100 scale)
            normalized = [(v / m) * 100 for v, m in zip(values, max_vals)]
            
            # Get colors based on interpretation
            colors = []
            for i, (name, value, max_val) in enumerate(metrics):
                if name == 'Flesch Reading Ease':
                    colors.append(ChartThemes.get_score_color(value))
                else:
                    # For grade-based metrics, lower is better
                    score = max(0, 100 - (value / max_val) * 100)
                    colors.append(ChartThemes.get_score_color(score))
            
            y_pos = np.arange(len(labels))
            
            # Create horizontal bars
            bars = ax.barh(y_pos, normalized, color=colors, height=0.6, alpha=0.85)
            
            # Add value labels
            for i, (bar, value, norm) in enumerate(zip(bars, values, normalized)):
                ax.text(norm + 2, bar.get_y() + bar.get_height()/2, 
                       f'{value:.1f}', va='center', fontsize=10, fontweight='bold',
                       color='#26262E')
            
            # Customize appearance
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=10)
            ax.set_xlim(0, 110)
            ax.set_xlabel('Score (Normalized)', fontsize=10)
            ax.invert_yaxis()
            
            # Remove top and right spines
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#D1D6DE')
            ax.spines['left'].set_color('#D1D6DE')
            
            plt.title('Readability Metrics Comparison', fontsize=12, fontweight='bold',
                     color='#26262E', pad=15)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating readability scores chart: {e}")
            return None
    
    @classmethod
    def create_benchmark_comparison(cls, comparisons: Dict[str, Dict],
                                   width: float = 5.5*inch,
                                   height: float = 3*inch) -> Optional[Image]:
        """Create benchmark comparison chart."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(8, 4))
            
            metrics = []
            values = []
            benchmarks = []
            
            for key, data in comparisons.items():
                label = key.replace('_', ' ').title()
                metrics.append(label)
                values.append(data['value'])
                benchmarks.append(data['benchmark'].get('target', data['value']))
            
            x = np.arange(len(metrics))
            width_bar = 0.35
            
            # Create bars
            bars1 = ax.bar(x - width_bar/2, values, width_bar, label='Your Content',
                          color='#1C6BB0', alpha=0.85)
            bars2 = ax.bar(x + width_bar/2, benchmarks, width_bar, label='Target',
                          color='#E89426', alpha=0.85)
            
            # Add value labels
            for bar in bars1:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords='offset points',
                           ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            for bar in bars2:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width()/2, height),
                           xytext=(0, 3), textcoords='offset points',
                           ha='center', va='bottom', fontsize=9)
            
            ax.set_ylabel('Value', fontsize=10)
            ax.set_xticks(x)
            ax.set_xticklabels(metrics, fontsize=9)
            ax.legend(loc='upper right', fontsize=9)
            
            # Clean styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.title('Your Content vs Industry Benchmarks', fontsize=12, 
                     fontweight='bold', color='#26262E', pad=15)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating benchmark comparison: {e}")
            return None

