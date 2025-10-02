"""
Automated Test Runner
Orchestrates test execution, analysis, and reporting.
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict

from testing_agent.ai_test_analyzer import AITestAnalyzer
from testing_agent.report_generator import TestReportGenerator


@dataclass
class TestResult:
    """Represents a single test result."""
    name: str
    status: str  # 'passed', 'failed', 'skipped'
    duration: float
    message: Optional[str] = None
    traceback: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class AutomatedTestRunner:
    """
    Automated test runner that executes tests, collects results,
    analyzes with AI, and generates comprehensive reports.
    """
    
    def __init__(
        self,
        project_root: Path = Path("."),
        output_dir: Path = Path("testing_agent/reports")
    ):
        """Initialize the test runner."""
        self.project_root = project_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.analyzer = AITestAnalyzer()
        self.report_generator = TestReportGenerator(output_dir)
    
    def run_all_tests(
        self,
        test_categories: Optional[List[str]] = None,
        parallel: bool = True,
        coverage: bool = True
    ) -> Dict[str, Any]:
        """
        Run all tests and collect results.
        
        Args:
            test_categories: List of test categories to run (e.g., ['unit', 'integration', 'e2e', 'ui'])
            parallel: Whether to run tests in parallel
            coverage: Whether to collect code coverage
            
        Returns:
            Comprehensive test results
        """
        print("=" * 80)
        print("CONTENT EDITORIAL ASSISTANT - AUTOMATED TEST SUITE")
        print("=" * 80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        all_results = {
            'timestamp': datetime.now().isoformat(),
            'categories': {}
        }
        
        # Define test categories
        if test_categories is None:
            test_categories = [
                'unit',           # Unit tests
                'integration',    # Integration tests
                'api',           # API endpoint tests
                'database',      # Database tests
                'frontend',      # Frontend/UI tests
                'ui',            # Browser-based UI tests
                'websocket',     # WebSocket tests
                'validation',    # Validation tests
                'performance'    # Performance tests
            ]
        
        # Run each category
        for category in test_categories:
            print(f"\n{'='*80}")
            print(f"Running {category.upper()} tests...")
            print(f"{'='*80}")
            
            result = self._run_test_category(category, parallel, coverage)
            all_results['categories'][category] = result
        
        # Aggregate results
        aggregated = self._aggregate_results(all_results)
        
        # Run quality metrics
        print(f"\n{'='*80}")
        print("Running Quality Metrics...")
        print(f"{'='*80}")
        quality_metrics = self._run_quality_metrics()
        aggregated['quality_metrics'] = quality_metrics
        
        # Save raw results
        self._save_raw_results(aggregated)
        
        return aggregated
    
    def _run_test_category(
        self,
        category: str,
        parallel: bool,
        coverage: bool
    ) -> Dict[str, Any]:
        """Run tests for a specific category."""
        # Build pytest command - use directory-based selection instead of markers
        test_dir = f'tests/{category}/'
        
        # Check if test directory exists
        if not Path(test_dir).exists():
            print(f"⚠️  Skipping {category} tests - directory {test_dir} not found")
            return {
                'status': 'skipped',
                'reason': f'Directory {test_dir} does not exist',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0.0
            }
        
        cmd = ['python', '-m', 'pytest', test_dir]
        
        # Add options
        cmd.extend([
            '-v',  # Verbose
            '--tb=short',  # Short traceback
            f'--junit-xml=testing_agent/results/{category}_results.xml',
            '--json-report',
            f'--json-report-file=testing_agent/results/{category}_results.json',
        ])
        
        if coverage:
            cmd.extend([
                '--cov=.',
                '--cov-report=json',
                f'--cov-report=html:testing_agent/coverage/{category}'
            ])
        
        if parallel:
            cmd.extend(['-n', 'auto'])  # Use all available CPUs
        
        # Add timeout
        cmd.extend(['--timeout=300'])  # 5 minute timeout per test
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=3600  # 1 hour total timeout
            )
            
            # Parse results
            parsed = self._parse_test_results(category)
            parsed['exit_code'] = result.returncode
            parsed['stdout'] = result.stdout[-5000:] if result.stdout else ''  # Last 5000 chars
            parsed['stderr'] = result.stderr[-5000:] if result.stderr else ''
            
            return parsed
        
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'error': 'Test execution timed out',
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
    
    def _parse_test_results(self, category: str) -> Dict[str, Any]:
        """Parse test results from pytest output."""
        results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0.0,
            'tests': [],
            'passed_tests': [],
            'failed_tests': [],
            'failures': [],
            'test_durations': {}
        }
        
        # Try JSON report first
        json_path = Path(f'testing_agent/results/{category}_results.json')
        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)
                
                results['total'] = data.get('summary', {}).get('total', 0)
                results['passed'] = data.get('summary', {}).get('passed', 0)
                results['failed'] = data.get('summary', {}).get('failed', 0)
                results['skipped'] = data.get('summary', {}).get('skipped', 0)
                results['duration'] = data.get('duration', 0.0)
                
                # Parse individual tests
                for test in data.get('tests', []):
                    test_name = test.get('nodeid', '')
                    status = test.get('outcome', 'unknown')
                    duration = test.get('duration', 0.0)
                    
                    results['test_durations'][test_name] = duration
                    
                    if status == 'passed':
                        results['passed_tests'].append(test_name)
                    elif status == 'failed':
                        results['failed_tests'].append(test_name)
                        results['failures'].append({
                            'test_name': test_name,
                            'message': test.get('call', {}).get('longrepr', 'Unknown error'),
                            'type': 'AssertionError',  # Default
                            'traceback': test.get('call', {}).get('longrepr', '')
                        })
                
                return results
            except Exception as e:
                print(f"Error parsing JSON results: {e}")
        
        # Fallback to XML report
        xml_path = Path(f'testing_agent/results/{category}_results.xml')
        if xml_path.exists():
            try:
                tree = ET.parse(xml_path)
                root = tree.getroot()
                
                # Get summary from testsuite element
                testsuite = root.find('testsuite')
                if testsuite is not None:
                    results['total'] = int(testsuite.get('tests', 0))
                    results['passed'] = int(testsuite.get('tests', 0)) - int(testsuite.get('failures', 0)) - int(testsuite.get('skipped', 0))
                    results['failed'] = int(testsuite.get('failures', 0))
                    results['skipped'] = int(testsuite.get('skipped', 0))
                    results['duration'] = float(testsuite.get('time', 0.0))
                    
                    # Parse individual test cases
                    for testcase in testsuite.findall('testcase'):
                        test_name = f"{testcase.get('classname')}::{testcase.get('name')}"
                        duration = float(testcase.get('time', 0.0))
                        
                        results['test_durations'][test_name] = duration
                        
                        failure = testcase.find('failure')
                        if failure is not None:
                            results['failed_tests'].append(test_name)
                            results['failures'].append({
                                'test_name': test_name,
                                'message': failure.get('message', 'Unknown error'),
                                'type': failure.get('type', 'Error'),
                                'traceback': failure.text or ''
                            })
                        elif testcase.find('skipped') is not None:
                            pass  # Skipped
                        else:
                            results['passed_tests'].append(test_name)
            
            except Exception as e:
                print(f"Error parsing XML results: {e}")
        
        return results
    
    def _aggregate_results(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate results from all test categories."""
        aggregated = {
            'timestamp': all_results['timestamp'],
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0.0,
            'passed_tests': [],
            'failed_tests': [],
            'failures': [],
            'test_durations': {},
            'categories': all_results['categories']
        }
        
        for category, results in all_results['categories'].items():
            aggregated['total'] += results.get('total', 0)
            aggregated['passed'] += results.get('passed', 0)
            aggregated['failed'] += results.get('failed', 0)
            aggregated['skipped'] += results.get('skipped', 0)
            aggregated['duration'] += results.get('duration', 0.0)
            
            aggregated['passed_tests'].extend(results.get('passed_tests', []))
            aggregated['failed_tests'].extend(results.get('failed_tests', []))
            aggregated['failures'].extend(results.get('failures', []))
            aggregated['test_durations'].update(results.get('test_durations', {}))
        
        return aggregated
    
    def _run_quality_metrics(self) -> Dict[str, Any]:
        """Run quality metrics analysis."""
        try:
            # Try to import from validation.monitoring.metrics
            from validation.monitoring.metrics import QualityMetrics
            
            metrics = QualityMetrics()
            return metrics.generate_daily_report()
        except ImportError:
            # Module not found - return placeholder metrics
            print("Quality metrics module not found - using basic metrics")
            return {
                'metrics_available': False,
                'note': 'Install validation module for ML quality metrics',
                'false_positive_rate': None,
                'user_feedback_trends': None
            }
        except Exception as e:
            print(f"Could not run quality metrics: {e}")
            return {
                'error': str(e),
                'status': 'unavailable'
            }
    
    def _save_raw_results(self, results: Dict[str, Any]):
        """Save raw test results to file."""
        results_dir = Path('testing_agent/results')
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f'test_results_{timestamp}.json'
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Also save as latest
        latest_file = results_dir / 'latest_results.json'
        with open(latest_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def run_complete_suite(self) -> Dict[str, Any]:
        """
        Run complete test suite with analysis and reporting.
        This is the main entry point for automated daily runs.
        """
        print("🚀 Starting automated test suite...\n")
        
        # Step 1: Run all tests
        results = self.run_all_tests()
        
        # Step 2: Load historical data
        print("\n📊 Loading historical data...")
        historical_data = self._load_historical_data()
        
        # Step 3: AI Analysis
        print("\n🧠 Running AI analysis...")
        analysis = self.analyzer.analyze_test_results(results, historical_data)
        
        # Step 4: Save analysis to history
        self.analyzer.save_results(analysis)
        
        # Step 5: Generate reports
        print("\n📝 Generating reports...")
        html_report = self.report_generator.generate_report(
            analysis,
            historical_data,
            format='html'
        )
        print(f"✅ HTML report generated: {html_report}")
        
        try:
            pdf_report = self.report_generator.generate_report(
                analysis,
                historical_data,
                format='pdf'
            )
            print(f"✅ PDF report generated: {pdf_report}")
        except Exception as e:
            print(f"⚠️  Could not generate PDF report: {e}")
        
        # Step 6: Print summary
        self._print_summary(analysis)
        
        # Step 7: Send notifications (if configured)
        self._send_notifications(analysis, html_report)
        
        # Return exit code based on results
        summary = analysis.get('summary', {})
        if summary.get('status') == 'critical' or summary.get('failed', 0) > 0:
            return 1  # Failure
        return 0  # Success
    
    def _load_historical_data(self) -> List[Dict[str, Any]]:
        """Load historical test data."""
        history_path = Path('testing_agent/data/test_history.json')
        
        if not history_path.exists():
            return []
        
        try:
            with open(history_path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading historical data: {e}")
            return []
    
    def _print_summary(self, analysis: Dict[str, Any]):
        """Print a summary of test results."""
        summary = analysis.get('summary', {})
        
        print("\n" + "=" * 80)
        print("TEST SUITE SUMMARY")
        print("=" * 80)
        print(f"Status: {summary.get('status', 'unknown').upper()}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"Skipped: {summary.get('skipped', 0)}")
        print(f"Pass Rate: {summary.get('pass_rate', 0)}%")
        print(f"Duration: {summary.get('duration', 0):.2f}s")
        print(f"Health Score: {analysis.get('health_score', {}).get('grade', 'N/A')}")
        print("=" * 80)
        
        # Regressions
        regressions = analysis.get('regressions', [])
        if regressions:
            print(f"\n🔴 REGRESSIONS ({len(regressions)}):")
            for reg in regressions[:5]:
                print(f"  - {reg['test_name']}")
        
        # Action items
        actions = analysis.get('action_items', [])
        if actions:
            print(f"\n✅ TOP PRIORITY ACTIONS ({len(actions[:3])}):")
            for action in actions[:3]:
                print(f"  [{action['priority']}] {action['title']}")
        
        print()
    
    def _send_notifications(self, analysis: Dict[str, Any], report_path: Path):
        """Send notifications about test results."""
        # This would integrate with email, Slack, etc.
        # For now, just save notification data
        
        notification_data = {
            'timestamp': datetime.now().isoformat(),
            'status': analysis.get('summary', {}).get('status'),
            'pass_rate': analysis.get('summary', {}).get('pass_rate'),
            'report_url': str(report_path),
            'action_items': analysis.get('action_items', [])[:3]
        }
        
        notification_file = self.output_dir / 'latest_notification.json'
        with open(notification_file, 'w') as f:
            json.dump(notification_data, f, indent=2)


def main():
    """Main entry point for CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run automated test suite")
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['unit', 'integration', 'api', 'e2e', 'ui', 'performance'],
        help='Test categories to run'
    )
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel test execution'
    )
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable code coverage collection'
    )
    
    args = parser.parse_args()
    
    runner = AutomatedTestRunner()
    exit_code = runner.run_complete_suite()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

