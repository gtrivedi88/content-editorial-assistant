"""
Comprehensive Test Report Generator
Generates beautiful HTML and PDF reports with metrics, trends, and actionable insights.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from jinja2 import Template
import plotly.graph_objects as go  # type: ignore
import plotly.express as px  # type: ignore
from plotly.subplots import make_subplots  # type: ignore


class TestReportGenerator:
    """Generates comprehensive test reports."""
    
    def __init__(self, output_dir: Path = Path("testing_agent/reports")):
        """Initialize the report generator."""
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style for matplotlib
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def generate_report(
        self,
        analysis: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None,
        format: str = "html"
    ) -> Path:
        """
        Generate a comprehensive test report.
        
        Args:
            analysis: Test analysis results
            historical_data: Historical test data for trends
            format: Output format ('html' or 'pdf')
            
        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate charts
        charts = self._generate_charts(analysis, historical_data)
        
        # Create report data
        report_data = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            'analysis': analysis,
            'charts': charts,
            'historical_data': historical_data or []
        }
        
        if format == "html":
            return self._generate_html_report(report_data, timestamp)
        elif format == "pdf":
            return self._generate_pdf_report(report_data, timestamp)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_charts(
        self,
        analysis: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, str]:
        """Generate all charts for the report."""
        charts = {}
        
        # 1. Pass Rate Trend Chart
        if historical_data:
            charts['pass_rate_trend'] = self._create_pass_rate_trend_chart(historical_data, analysis)
        
        # 2. Performance Trend Chart
        if historical_data:
            charts['performance_trend'] = self._create_performance_trend_chart(historical_data, analysis)
        
        # 3. Test Category Breakdown
        charts['category_breakdown'] = self._create_category_breakdown_chart(analysis)
        
        # 4. Slowest Tests Chart
        charts['slowest_tests'] = self._create_slowest_tests_chart(analysis)
        
        # 5. Health Score Gauge
        charts['health_score'] = self._create_health_score_gauge(analysis)
        
        # 6. Failure Categories
        charts['failure_categories'] = self._create_failure_categories_chart(analysis)
        
        return charts
    
    def _create_pass_rate_trend_chart(
        self,
        historical_data: List[Dict[str, Any]],
        current: Dict[str, Any]
    ) -> str:
        """Create pass rate trend chart (last 30 days)."""
        # Prepare data
        data = historical_data[-30:] + [current]
        
        dates = []
        pass_rates = []
        
        for entry in data:
            timestamp = entry.get('timestamp', '')
            if timestamp:
                dates.append(datetime.fromisoformat(timestamp))
            summary = entry.get('summary', {})
            pass_rates.append(summary.get('pass_rate', 0))
        
        # Create interactive Plotly chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=pass_rates,
            mode='lines+markers',
            name='Pass Rate',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        # Add 95% threshold line
        fig.add_hline(
            y=95,
            line_dash="dash",
            line_color="green",
            annotation_text="Target: 95%"
        )
        
        fig.update_layout(
            title="Test Pass Rate Trend (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Pass Rate (%)",
            hovermode='x unified',
            template="plotly_white",
            height=400
        )
        
        # Save as HTML div
        chart_path = self.output_dir / "charts" / "pass_rate_trend.html"
        chart_path.parent.mkdir(exist_ok=True)
        fig.write_html(str(chart_path))
        
        return fig.to_html(include_plotlyjs='cdn', div_id='pass_rate_trend')
    
    def _create_performance_trend_chart(
        self,
        historical_data: List[Dict[str, Any]],
        current: Dict[str, Any]
    ) -> str:
        """Create performance trend chart."""
        data = historical_data[-30:] + [current]
        
        dates = []
        durations = []
        
        for entry in data:
            timestamp = entry.get('timestamp', '')
            if timestamp:
                dates.append(datetime.fromisoformat(timestamp))
            summary = entry.get('summary', {})
            durations.append(summary.get('duration', 0))
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=durations,
            mode='lines+markers',
            name='Duration',
            line=dict(color='#F77F00', width=3),
            fill='tozeroy',
            fillcolor='rgba(247, 127, 0, 0.2)'
        ))
        
        fig.update_layout(
            title="Test Suite Execution Time (Last 30 Days)",
            xaxis_title="Date",
            yaxis_title="Duration (seconds)",
            hovermode='x unified',
            template="plotly_white",
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='performance_trend')
    
    def _create_category_breakdown_chart(self, analysis: Dict[str, Any]) -> str:
        """Create test category breakdown pie chart."""
        summary = analysis.get('summary', {})
        
        categories = ['Passed', 'Failed', 'Skipped']
        values = [
            summary.get('passed', 0),
            summary.get('failed', 0),
            summary.get('skipped', 0)
        ]
        colors = ['#06D6A0', '#EF476F', '#FFD166']
        
        fig = go.Figure(data=[go.Pie(
            labels=categories,
            values=values,
            marker=dict(colors=colors),
            hole=0.4,
            textinfo='label+percent+value',
            textfont_size=14
        )])
        
        fig.update_layout(
            title="Test Results Breakdown",
            template="plotly_white",
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='category_breakdown')
    
    def _create_slowest_tests_chart(self, analysis: Dict[str, Any]) -> str:
        """Create chart showing slowest tests."""
        perf = analysis.get('performance_trends', {})
        slowest = perf.get('slowest_tests', [])[:10]
        
        if not slowest:
            return "<p>No performance data available</p>"
        
        test_names = [t['test'].split('::')[-1][:40] for t in slowest]
        durations = [t['duration'] for t in slowest]
        
        fig = go.Figure(data=[
            go.Bar(
                y=test_names,
                x=durations,
                orientation='h',
                marker=dict(
                    color=durations,
                    colorscale='Reds',
                    showscale=True,
                    colorbar=dict(title="Seconds")
                )
            )
        ])
        
        fig.update_layout(
            title="Top 10 Slowest Tests",
            xaxis_title="Duration (seconds)",
            yaxis_title="Test Name",
            template="plotly_white",
            height=500,
            yaxis=dict(autorange="reversed")
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='slowest_tests')
    
    def _create_health_score_gauge(self, analysis: Dict[str, Any]) -> str:
        """Create health score gauge chart."""
        health = analysis.get('health_score', {})
        score = health.get('overall_score', 0)
        grade = health.get('grade', 'N/A')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Health Score: {grade}"},
            delta={'reference': 95},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 70], 'color': "#EF476F"},
                    {'range': [70, 85], 'color': "#FFD166"},
                    {'range': [85, 95], 'color': "#26A69A"},
                    {'range': [95, 100], 'color': "#06D6A0"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        
        fig.update_layout(
            template="plotly_white",
            height=300
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='health_score')
    
    def _create_failure_categories_chart(self, analysis: Dict[str, Any]) -> str:
        """Create chart showing failure categories."""
        insights = analysis.get('insights', [])
        
        if not insights:
            return "<p>No failure insights available</p>"
        
        # Count by category
        categories = {}
        for insight in insights:
            if hasattr(insight, 'category'):
                cat = insight.category
            else:
                cat = insight.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(categories.keys()),
                y=list(categories.values()),
                marker=dict(
                    color=list(categories.values()),
                    colorscale='Blues'
                )
            )
        ])
        
        fig.update_layout(
            title="Issues by Category",
            xaxis_title="Category",
            yaxis_title="Count",
            template="plotly_white",
            height=400
        )
        
        return fig.to_html(include_plotlyjs='cdn', div_id='failure_categories')
    
    def _generate_html_report(self, report_data: Dict[str, Any], timestamp: str) -> Path:
        """Generate HTML report."""
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Report - {{ report_data.timestamp }}</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        h2 { color: #667eea; margin: 30px 0 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        h3 { color: #555; margin: 20px 0 10px; }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }
        
        .status-card .value {
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .status-card .label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-healthy { color: #06D6A0; }
        .status-degraded { color: #FFD166; }
        .status-critical { color: #EF476F; }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .insight {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .insight.priority-1 { border-left-color: #EF476F; }
        .insight.priority-2 { border-left-color: #FFD166; }
        .insight.priority-3 { border-left-color: #06D6A0; }
        
        .insight-title {
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .action-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #667eea;
        }
        
        .action-item.high { border-left-color: #EF476F; background: #FFF5F7; }
        .action-item.medium { border-left-color: #FFD166; background: #FFFBF0; }
        .action-item.low { border-left-color: #06D6A0; background: #F0FFF9; }
        
        .regression {
            background: #FFF5F7;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid #EF476F;
        }
        
        .flaky-test {
            background: #FFFBF0;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        th, td {
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #f0f0f0;
        }
        
        th {
            background: #667eea;
            color: white;
            font-weight: 600;
        }
        
        tr:hover { background: #f8f9fa; }
        
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-high { background: #EF476F; color: white; }
        .badge-medium { background: #FFD166; color: #333; }
        .badge-low { background: #06D6A0; color: white; }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #666;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Content Editorial Assistant</h1>
            <h2 style="color: white; border: none; margin: 0;">Daily Test Report</h2>
            <p style="margin-top: 10px; opacity: 0.9;">Generated: {{ report_data.timestamp }}</p>
        </header>
        
        <!-- Status Overview -->
        <div class="status-grid">
            <div class="status-card">
                <div class="label">Overall Status</div>
                <div class="value status-{{ report_data.analysis.summary.status }}">
                    {% if report_data.analysis.summary.status == 'healthy' %}🟢{% elif report_data.analysis.summary.status == 'degraded' %}🟡{% else %}🔴{% endif %}
                </div>
                <div class="label">{{ report_data.analysis.summary.status | upper }}</div>
            </div>
            
            <div class="status-card">
                <div class="label">Pass Rate</div>
                <div class="value status-{{ 'healthy' if report_data.analysis.summary.pass_rate >= 95 else 'degraded' if report_data.analysis.summary.pass_rate >= 85 else 'critical' }}">
                    {{ report_data.analysis.summary.pass_rate }}%
                </div>
                <div class="label">{{ report_data.analysis.summary.passed }}/{{ report_data.analysis.summary.total_tests }} Passed</div>
            </div>
            
            <div class="status-card">
                <div class="label">Health Score</div>
                <div class="value status-healthy">{{ report_data.analysis.health_score.grade }}</div>
                <div class="label">{{ report_data.analysis.health_score.overall_score }}/100</div>
            </div>
            
            <div class="status-card">
                <div class="label">Duration</div>
                <div class="value" style="color: #667eea; font-size: 2.5em;">{{ report_data.analysis.summary.duration }}</div>
                <div class="label">Seconds</div>
            </div>
        </div>
        
        <!-- Health Score Gauge -->
        <div class="chart-container">
            {{ report_data.charts.health_score | safe }}
        </div>
        
        <!-- Test Results Breakdown -->
        <div class="chart-container">
            {{ report_data.charts.category_breakdown | safe }}
        </div>
        
        <!-- Regressions -->
        {% if report_data.analysis.regressions %}
        <h2>🔴 Regressions ({{ report_data.analysis.regressions | length }})</h2>
        <p style="margin-bottom: 15px;">Tests that were passing yesterday but are failing today:</p>
        {% for regression in report_data.analysis.regressions %}
        <div class="regression">
            <strong>{{ regression.test_name }}</strong>
            <p style="margin-top: 5px; color: #666;">{{ regression.failure_message }}</p>
            <p style="margin-top: 5px;"><span class="badge badge-high">{{ regression.error_type }}</span></p>
        </div>
        {% endfor %}
        {% else %}
        <h2>✅ No Regressions</h2>
        <p style="color: green; margin-bottom: 20px;">All previously passing tests are still passing!</p>
        {% endif %}
        
        <!-- Performance Trends -->
        <h2>📈 Performance Trends</h2>
        <div class="chart-container">
            {{ report_data.charts.performance_trend | safe }}
        </div>
        
        <div class="chart-container">
            {{ report_data.charts.slowest_tests | safe }}
        </div>
        
        <!-- Pass Rate Trend -->
        <h2>📊 Pass Rate Trend (30 Days)</h2>
        <div class="chart-container">
            {{ report_data.charts.pass_rate_trend | safe }}
        </div>
        
        <!-- AI-Generated Insights -->
        <h2>🧠 AI-Generated Insights</h2>
        {% if report_data.analysis.insights %}
        {% for insight in report_data.analysis.insights %}
        <div class="insight priority-{{ insight.priority if insight.priority else insight['priority'] }}">
            <div class="insight-title">
                <span class="badge badge-{{ 'high' if (insight.priority if insight.priority else insight['priority']) <= 2 else 'medium' if (insight.priority if insight.priority else insight['priority']) == 3 else 'low' }}">
                    Priority {{ insight.priority if insight.priority else insight['priority'] }}
                </span>
                {{ insight.title if insight.title else insight['title'] }}
            </div>
            <p style="margin: 10px 0;">{{ insight.description if insight.description else insight['description'] }}</p>
            <p><strong>Suggested Actions:</strong></p>
            <ul style="margin-left: 20px;">
                {% for action in (insight.suggested_actions if insight.suggested_actions else insight['suggested_actions']) %}
                <li>{{ action }}</li>
                {% endfor %}
            </ul>
            {% set affected = insight.affected_tests if insight.affected_tests else insight.get('affected_tests', []) %}
            {% if affected %}
            <p style="margin-top: 10px; font-size: 0.9em; color: #666;">
                Affects: {{ affected | length }} tests
            </p>
            {% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p>No specific insights generated for this run.</p>
        {% endif %}
        
        <!-- Prioritized Action Items -->
        <h2>✅ Prioritized Action Items</h2>
        {% if report_data.analysis.action_items %}
        {% for action in report_data.analysis.action_items %}
        <div class="action-item {{ action.estimated_impact }}">
            <span class="badge badge-{{ action.estimated_impact }}">{{ action.type | upper }}</span>
            <strong>{{ action.title }}</strong>
            <p style="margin-top: 5px; color: #666;">{{ action.description }}</p>
        </div>
        {% endfor %}
        {% else %}
        <p style="color: green;">✅ No action items - everything is working well!</p>
        {% endif %}
        
        <!-- Flaky Tests -->
        {% if report_data.analysis.flaky_tests %}
        <h2>⚠️ Flaky Tests ({{ report_data.analysis.flaky_tests | length }})</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Failure Rate</th>
                    <th>Total Runs</th>
                    <th>Priority</th>
                </tr>
            </thead>
            <tbody>
                {% for test in report_data.analysis.flaky_tests[:10] %}
                <tr>
                    <td>{{ test.test_name }}</td>
                    <td>{{ test.failure_rate }}%</td>
                    <td>{{ test.total_runs }}</td>
                    <td><span class="badge badge-{{ test.priority }}">{{ test.priority | upper }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
        
        <!-- Failure Categories -->
        {% if report_data.analysis.insights %}
        <h2>📊 Issues by Category</h2>
        <div class="chart-container">
            {{ report_data.charts.failure_categories | safe }}
        </div>
        {% endif %}
        
        <footer>
            <p>Generated by Content Editorial Assistant Testing Agent</p>
            <p>Report Time: {{ report_data.timestamp }}</p>
        </footer>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        html_content = template.render(report_data=report_data)
        
        report_path = self.output_dir / f"test_report_{timestamp}.html"
        report_path.write_text(html_content)
        
        # Also create a 'latest' symlink
        latest_path = self.output_dir / "latest_report.html"
        if latest_path.exists():
            latest_path.unlink()
        latest_path.write_text(html_content)
        
        return report_path
    
    def _generate_pdf_report(self, report_data: Dict[str, Any], timestamp: str) -> Path:
        """Generate PDF report (simplified version)."""
        # For PDF, we'd use reportlab to create a similar report
        # This is a placeholder - full implementation would mirror HTML structure
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        pdf_path = self.output_dir / f"test_report_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("Content Editorial Assistant", title_style))
        story.append(Paragraph("Daily Test Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Generated: {report_data['timestamp']}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary Table
        summary = report_data['analysis']['summary']
        summary_data = [
            ['Metric', 'Value'],
            ['Total Tests', str(summary['total_tests'])],
            ['Passed', str(summary['passed'])],
            ['Failed', str(summary['failed'])],
            ['Pass Rate', f"{summary['pass_rate']}%"],
            ['Duration', f"{summary['duration']}s"],
            ['Status', summary['status'].upper()]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Test Summary", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*inch))
        
        # Regressions
        if report_data['analysis'].get('regressions'):
            story.append(Paragraph("Regressions", styles['Heading2']))
            for reg in report_data['analysis']['regressions']:
                story.append(Paragraph(f"• {reg['test_name']}: {reg['failure_message']}", styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
        
        # Action Items
        if report_data['analysis'].get('action_items'):
            story.append(Paragraph("Action Items", styles['Heading2']))
            for action in report_data['analysis']['action_items']:
                story.append(Paragraph(
                    f"[{action['priority']}] {action['title']}: {action['description']}",
                    styles['Normal']
                ))
            story.append(Spacer(1, 0.3*inch))
        
        doc.build(story)
        
        return pdf_path

