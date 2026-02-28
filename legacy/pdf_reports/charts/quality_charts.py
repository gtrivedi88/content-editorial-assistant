"""
Quality Charts Module

Professional chart generators for writing quality metrics.
Creates executive-ready visualizations with modern styling.
"""

import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from typing import Dict, Any, Optional, List
from reportlab.platypus import Image
from reportlab.lib.units import inch
import logging

from ..styles.chart_themes import ChartThemes

logger = logging.getLogger(__name__)


class QualityCharts:
    """Generate professional writing quality charts."""
    
    @classmethod
    def create_overall_score_card(cls, score: float,
                                  width: float = 3*inch,
                                  height: float = 3*inch) -> Optional[Image]:
        """Create a circular score card visualization."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(4, 4))
            
            # Create donut chart background
            colors_bg = ['#E8E8E8']
            colors_score = [ChartThemes.get_score_color(score)]
            
            # Background ring
            ax.pie([100], colors=colors_bg, radius=1, 
                  wedgeprops=dict(width=0.25, edgecolor='white'))
            
            # Score ring
            sizes = [score, 100 - score]
            colors = [colors_score[0], 'white']
            ax.pie(sizes, colors=colors, radius=1, 
                  startangle=90, counterclock=False,
                  wedgeprops=dict(width=0.25, edgecolor='white'))
            
            # Add score text in center
            ax.text(0, 0.1, f'{score:.0f}', ha='center', va='center',
                   fontsize=36, fontweight='bold', color='#26262E')
            ax.text(0, -0.2, 'Overall Score', ha='center', va='center',
                   fontsize=11, color='#666B73')
            
            # Get grade
            if score >= 90:
                grade = 'Exceptional'
            elif score >= 80:
                grade = 'Excellent'
            elif score >= 70:
                grade = 'Good'
            elif score >= 60:
                grade = 'Satisfactory'
            else:
                grade = 'Needs Work'
            
            ax.text(0, -0.4, grade, ha='center', va='center',
                   fontsize=10, fontweight='bold', color=colors_score[0])
            
            ax.set_xlim(-1.3, 1.3)
            ax.set_ylim(-1.3, 1.3)
            ax.axis('equal')
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating score card: {e}")
            return None
    
    @classmethod
    def create_quality_metrics_radar(cls, statistics: Dict[str, Any],
                                     width: float = 5*inch,
                                     height: float = 4*inch) -> Optional[Image]:
        """Create a radar chart for quality metrics."""
        try:
            ChartThemes.apply_executive_theme()
            
            # Prepare data
            categories = ['Readability', 'Clarity', 'Engagement', 'Structure', 'Precision']
            
            # Calculate scores for each category
            passive_pct = statistics.get('passive_voice_percentage', 0)
            avg_sentence = statistics.get('avg_sentence_length', 17)
            complex_pct = statistics.get('complex_words_percentage', 0)
            vocab_diversity = statistics.get('vocabulary_diversity', 0.5)
            
            readability = max(0, min(100, 100 - (complex_pct * 2.5)))
            clarity = max(0, min(100, 100 - (passive_pct * 3)))
            engagement = max(0, min(100, vocab_diversity * 100 + 20))
            structure = max(0, min(100, 100 - abs(avg_sentence - 17) * 4))
            precision = max(0, min(100, 100 - (complex_pct * 1.5) - (passive_pct * 1.5)))
            
            values = [readability, clarity, engagement, structure, precision]
            
            # Number of variables
            N = len(categories)
            
            # Compute angle for each category
            angles = [n / float(N) * 2 * np.pi for n in range(N)]
            values += values[:1]  # Complete the loop
            angles += angles[:1]
            
            # Create plot
            fig, ax = plt.subplots(figsize=(6, 5), subplot_kw=dict(polar=True))
            
            # Draw the polygon
            ax.fill(angles, values, color='#1C6BB0', alpha=0.25)
            ax.plot(angles, values, color='#1C6BB0', linewidth=2)
            
            # Draw circles
            for i in [20, 40, 60, 80, 100]:
                circle_angles = np.linspace(0, 2*np.pi, 100)
                circle_values = [i] * 100
                ax.plot(circle_angles, circle_values, color='#D1D6DE', 
                       linewidth=0.5, linestyle='--')
            
            # Add value markers
            for angle, value in zip(angles[:-1], values[:-1]):
                ax.scatter(angle, value, color='#1C6BB0', s=80, zorder=10)
                ax.annotate(f'{value:.0f}', xy=(angle, value), 
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=9, fontweight='bold', color='#26262E')
            
            # Customize
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=10)
            ax.set_ylim(0, 100)
            ax.set_yticks([])
            ax.spines['polar'].set_color('#D1D6DE')
            
            plt.title('Writing Quality Profile', fontsize=12, fontweight='bold',
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
            logger.error(f"Error creating quality radar chart: {e}")
            return None
    
    @classmethod
    def create_metrics_comparison_bars(cls, statistics: Dict[str, Any],
                                       width: float = 5.5*inch,
                                       height: float = 3*inch) -> Optional[Image]:
        """Create horizontal progress bars for key metrics."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, axes = plt.subplots(4, 1, figsize=(8, 4.5))
            plt.subplots_adjust(hspace=0.6)
            
            metrics = [
                {
                    'name': 'Passive Voice',
                    'value': statistics.get('passive_voice_percentage', 0),
                    'target': 15,
                    'max': 50,
                    'lower_is_better': True,
                    'unit': '%'
                },
                {
                    'name': 'Avg Sentence Length',
                    'value': statistics.get('avg_sentence_length', 17),
                    'target': 17,
                    'min': 12,
                    'max': 30,
                    'optimal': True,
                    'unit': ' words'
                },
                {
                    'name': 'Complex Words',
                    'value': statistics.get('complex_words_percentage', 0),
                    'target': 20,
                    'max': 50,
                    'lower_is_better': True,
                    'unit': '%'
                },
                {
                    'name': 'Vocabulary Diversity',
                    'value': statistics.get('vocabulary_diversity', 0.5) * 100,
                    'target': 70,
                    'max': 100,
                    'lower_is_better': False,
                    'unit': '%'
                }
            ]
            
            for ax, metric in zip(axes, metrics):
                value = metric['value']
                target = metric['target']
                max_val = metric['max']
                
                # Calculate score for color
                if metric.get('lower_is_better'):
                    score = max(0, 100 - (value / target) * 50)
                elif metric.get('optimal'):
                    distance = abs(value - target)
                    score = max(0, 100 - (distance / 10) * 50)
                else:
                    score = min(100, (value / target) * 100)
                
                color = ChartThemes.get_score_color(score)
                
                # Background bar
                ax.barh(0, max_val, height=0.4, color='#E8E8E8', zorder=1)
                
                # Value bar
                ax.barh(0, min(value, max_val), height=0.4, color=color, 
                       alpha=0.85, zorder=2)
                
                # Target marker
                ax.axvline(x=target, color='#26262E', linestyle='--', linewidth=2, zorder=3)
                
                # Labels
                ax.set_xlim(0, max_val * 1.1)
                ax.set_ylim(-0.5, 0.5)
                ax.set_yticks([])
                ax.set_xticks([])
                
                # Metric name
                ax.text(-max_val * 0.02, 0, metric['name'], ha='right', va='center',
                       fontsize=10, fontweight='bold', color='#26262E')
                
                # Value label
                ax.text(value + max_val * 0.02, 0, f'{value:.1f}{metric["unit"]}',
                       ha='left', va='center', fontsize=10, fontweight='bold', 
                       color=color)
                
                # Target label
                ax.text(target, 0.35, f'Target: {target}{metric["unit"]}',
                       ha='center', va='bottom', fontsize=8, color='#666B73')
                
                # Remove spines
                for spine in ax.spines.values():
                    spine.set_visible(False)
            
            plt.suptitle('Writing Quality Metrics vs Targets', fontsize=12,
                        fontweight='bold', color='#26262E', y=1.02)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating metrics comparison: {e}")
            return None
    
    @classmethod
    def create_document_overview_chart(cls, statistics: Dict[str, Any],
                                       width: float = 5.5*inch,
                                       height: float = 2*inch) -> Optional[Image]:
        """Create a document overview infographic."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, axes = plt.subplots(1, 4, figsize=(10, 2.5))
            
            metrics = [
                ('Words', statistics.get('word_count', 0), '#1C6BB0'),
                ('Sentences', statistics.get('sentence_count', 0), '#2E9E59'),
                ('Paragraphs', statistics.get('paragraph_count', 0), '#E89426'),
                ('Reading Time', f"{max(1, statistics.get('word_count', 0) // 250)}m", '#8B5CF6'),
            ]
            
            for ax, (label, value, color) in zip(axes, metrics):
                # Create circular background
                circle = plt.Circle((0.5, 0.55), 0.35, color=color, alpha=0.15)
                ax.add_patch(circle)
                
                # Add value
                ax.text(0.5, 0.6, str(value) if isinstance(value, int) else value,
                       ha='center', va='center', fontsize=20, fontweight='bold',
                       color=color)
                
                # Add label
                ax.text(0.5, 0.12, label, ha='center', va='center',
                       fontsize=10, color='#666B73')
                
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_aspect('equal')
                ax.axis('off')
            
            plt.suptitle('Document Overview', fontsize=12, fontweight='bold',
                        color='#26262E', y=1.05)
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating document overview: {e}")
            return None

