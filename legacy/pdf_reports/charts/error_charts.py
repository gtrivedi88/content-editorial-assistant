"""
Error Charts Module

Professional chart generators for error analysis and distribution.
Creates executive-ready visualizations with modern styling.
"""

import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from typing import Dict, Any, Optional, List
from collections import Counter
from reportlab.platypus import Image
from reportlab.lib.units import inch
import logging

from ..styles.chart_themes import ChartThemes

logger = logging.getLogger(__name__)


class ErrorCharts:
    """Generate professional error analysis charts."""
    
    @classmethod
    def create_error_distribution_pie(cls, errors: List[Dict[str, Any]],
                                      width: float = 4*inch,
                                      height: float = 3.5*inch) -> Optional[Image]:
        """Create a donut chart showing error type distribution."""
        try:
            if not errors:
                return cls._create_no_errors_graphic(width, height)
            
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # Count error types
            error_types = [error.get('type', 'unknown') for error in errors]
            error_counts = Counter(error_types)
            
            # Get top 6 error types
            top_errors = error_counts.most_common(6)
            
            labels = []
            sizes = []
            for error_type, count in top_errors:
                # Clean up label
                label = error_type.replace('_', ' ').title()
                if len(label) > 18:
                    label = label[:16] + '...'
                labels.append(label)
                sizes.append(count)
            
            # Add "Other" category if needed
            if len(error_counts) > 6:
                other_count = sum(count for _, count in error_counts.most_common()[6:])
                labels.append('Other')
                sizes.append(other_count)
            
            colors = ChartThemes.get_chart_colors(len(labels))
            
            # Create donut chart
            wedges, texts, autotexts = ax.pie(
                sizes, 
                labels=labels,
                colors=colors,
                autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',
                pctdistance=0.75,
                startangle=90,
                wedgeprops=dict(width=0.5, edgecolor='white', linewidth=2)
            )
            
            # Style the labels
            for text in texts:
                text.set_fontsize(9)
                text.set_color('#26262E')
            
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_fontweight('bold')
                autotext.set_color('white')
            
            # Add center text
            ax.text(0, 0.05, str(len(errors)), ha='center', va='center',
                   fontsize=28, fontweight='bold', color='#26262E')
            ax.text(0, -0.15, 'Total Issues', ha='center', va='center',
                   fontsize=10, color='#666B73')
            
            ax.axis('equal')
            
            plt.title('Issue Distribution', fontsize=12, fontweight='bold',
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
            logger.error(f"Error creating error distribution chart: {e}")
            return None
    
    @classmethod
    def _create_no_errors_graphic(cls, width: float, height: float) -> Optional[Image]:
        """Create a graphic for when there are no errors."""
        try:
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(5, 4))
            
            # Create success circle
            circle = plt.Circle((0.5, 0.5), 0.3, color='#2E9E59', alpha=0.2)
            ax.add_patch(circle)
            
            # Checkmark
            ax.text(0.5, 0.55, '✓', ha='center', va='center',
                   fontsize=48, color='#2E9E59', fontweight='bold')
            
            ax.text(0.5, 0.2, 'No Issues Found!', ha='center', va='center',
                   fontsize=14, fontweight='bold', color='#2E9E59')
            
            ax.text(0.5, 0.08, 'Excellent writing quality', ha='center', va='center',
                   fontsize=10, color='#666B73')
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            plt.tight_layout()
            
            # Save to buffer
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
            img_buffer.seek(0)
            plt.close()
            
            return Image(img_buffer, width=width, height=height)
            
        except Exception as e:
            logger.error(f"Error creating no-errors graphic: {e}")
            return None
    
    @classmethod
    def create_error_severity_chart(cls, errors: List[Dict[str, Any]],
                                    width: float = 5*inch,
                                    height: float = 2.5*inch) -> Optional[Image]:
        """Create horizontal bar chart showing errors by severity."""
        try:
            if not errors:
                return None
            
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(7, 3.5))
            
            # Categorize errors by severity
            severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
            
            for error in errors:
                severity = error.get('severity', 'medium').lower()
                if severity in ['high', 'critical', 'urgent']:
                    severity_counts['High'] += 1
                elif severity in ['medium', 'moderate']:
                    severity_counts['Medium'] += 1
                else:
                    severity_counts['Low'] += 1
            
            # If no severity data, estimate from error types
            if all(v == 0 for v in severity_counts.values()):
                total = len(errors)
                severity_counts['High'] = int(total * 0.2)
                severity_counts['Medium'] = int(total * 0.5)
                severity_counts['Low'] = total - severity_counts['High'] - severity_counts['Medium']
            
            labels = list(severity_counts.keys())
            values = list(severity_counts.values())
            colors = ['#CC423D', '#E8A126', '#66BA6B']
            
            y_pos = np.arange(len(labels))
            
            bars = ax.barh(y_pos, values, color=colors, height=0.5, alpha=0.85)
            
            # Add value labels
            for bar, value in zip(bars, values):
                if value > 0:
                    ax.text(value + max(values) * 0.02, bar.get_y() + bar.get_height()/2,
                           str(value), va='center', fontsize=11, fontweight='bold',
                           color='#26262E')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=10)
            ax.set_xlim(0, max(values) * 1.2 if max(values) > 0 else 10)
            ax.invert_yaxis()
            
            # Clean styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#D1D6DE')
            ax.spines['left'].set_color('#D1D6DE')
            
            ax.set_xlabel('Number of Issues', fontsize=10)
            
            plt.title('Issues by Priority', fontsize=12, fontweight='bold',
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
            logger.error(f"Error creating severity chart: {e}")
            return None
    
    @classmethod
    def create_error_categories_chart(cls, errors: List[Dict[str, Any]],
                                      width: float = 5.5*inch,
                                      height: float = 3*inch) -> Optional[Image]:
        """Create horizontal bar chart showing top error categories."""
        try:
            if not errors:
                return None
            
            ChartThemes.apply_executive_theme()
            
            fig, ax = plt.subplots(figsize=(8, 4))
            
            # Count and sort error types
            error_types = [error.get('type', 'unknown') for error in errors]
            error_counts = Counter(error_types)
            top_errors = error_counts.most_common(8)
            
            if not top_errors:
                return None
            
            labels = [e[0].replace('_', ' ').title()[:25] for e in top_errors]
            values = [e[1] for e in top_errors]
            
            # Get colors based on count
            max_val = max(values)
            colors = [ChartThemes.get_score_color(100 - (v / max_val) * 60) for v in values]
            
            y_pos = np.arange(len(labels))
            
            bars = ax.barh(y_pos, values, color=colors, height=0.6, alpha=0.85)
            
            # Add value labels
            for bar, value in zip(bars, values):
                ax.text(value + max_val * 0.02, bar.get_y() + bar.get_height()/2,
                       str(value), va='center', fontsize=10, fontweight='bold',
                       color='#26262E')
            
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels, fontsize=9)
            ax.set_xlim(0, max_val * 1.15)
            ax.invert_yaxis()
            
            # Clean styling
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#D1D6DE')
            ax.spines['left'].set_color('#D1D6DE')
            
            ax.set_xlabel('Number of Occurrences', fontsize=10)
            
            plt.title('Top Issue Categories', fontsize=12, fontweight='bold',
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
            logger.error(f"Error creating categories chart: {e}")
            return None

