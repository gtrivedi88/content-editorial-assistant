"""
AI-Powered Test Analysis Agent
Uses LLM to analyze test results, identify patterns, and provide actionable insights.
Supports multiple AI providers: Ollama, OpenAI, Anthropic, and custom APIs.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict

from testing_agent.config import TestingConfig


@dataclass
class TestFailure:
    """Represents a test failure."""
    test_name: str
    failure_message: str
    error_type: str
    file_path: str
    duration: float
    timestamp: datetime
    traceback: Optional[str] = None


@dataclass
class AnalysisInsight:
    """Represents an AI-generated insight."""
    priority: int  # 1-5, where 1 is highest
    title: str
    description: str
    affected_tests: List[str]
    suggested_actions: List[str]
    category: str  # 'regression', 'performance', 'flaky', 'infrastructure', 'code_quality'
    confidence: float  # 0.0-1.0


class AITestAnalyzer:
    """
    AI agent that analyzes test results and provides intelligent insights.
    Supports multiple AI providers via configuration.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the AI test analyzer."""
        # Get configuration from centralized config
        self.config = TestingConfig.get_ai_config()
        self.model_name = model_name or TestingConfig.get_model_name()
        self.ai_provider = TestingConfig.MODEL_PROVIDER
        
        self.history_path = Path("testing_agent/data/test_history.json")
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if AI is properly configured
        self.ai_available = TestingConfig.validate_ai_config()
        
        # Print AI configuration status
        print("\n" + "="*80)
        print("🤖 AI TEST ANALYZER CONFIGURATION")
        print("="*80)
        print(f"Provider: {self.ai_provider}")
        print(f"Model: {self.model_name}")
        print(f"Status: {'✅ ENABLED' if self.ai_available else '❌ DISABLED'}")
        if self.ai_available:
            if self.ai_provider == 'ollama':
                print(f"URL: {self.config.get('base_url', 'N/A')}")
            elif self.ai_provider in ['api', 'openai', 'anthropic', 'custom']:
                print(f"URL: {self.config.get('base_url', 'N/A')}")
                api_key = self.config.get('api_key', '')
                if api_key:
                    masked_key = api_key[:4] + '...' + api_key[-4:] if len(api_key) > 12 else '***'
                    print(f"API Key: {masked_key}")
        else:
            print("ℹ️  AI analysis will be skipped - tests will still run!")
        print("="*80 + "\n")
    
    def _check_ai_availability(self) -> bool:
        """
        Check if AI provider is available and properly configured.
        Note: This is now handled by TestingConfig.validate_ai_config()
        """
        try:
            if self.ai_provider == 'ollama':
                import ollama
                ollama.list()  # Test connection
                return True
            # For API providers, config validation is sufficient
            return TestingConfig.validate_ai_config()
        except:
            return False
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM with appropriate provider using centralized config."""
        if self.ai_provider == 'ollama':
            import ollama
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': self.config['temperature']}
            )
            return response['message']['content']
        
        elif self.ai_provider == 'api':
            # Generic OpenAI-compatible API (Mistral, Groq, etc.)
            import requests
            import ssl
            
            # Prepare headers
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            # Prepare request body
            json_data = {
                'model': self.model_name,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': self.config['temperature'],
                'max_tokens': self.config['max_tokens']
            }
            
            # Handle SSL certificate if provided
            verify = True
            if self.config.get('cert_path'):
                verify = self.config['cert_path']
            
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                headers=headers,
                json=json_data,
                verify=verify,
                timeout=self.config.get('timeout', 30)
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        
        elif self.ai_provider == 'llamastack':
            # Use the LlamaStack provider from your main app
            from models.factory import ModelFactory
            model = ModelFactory.get_model()
            response = model.generate_response(prompt)
            return response
        
        else:
            raise ValueError(f"Unsupported AI provider: {self.ai_provider}")
    
    def analyze_test_results(
        self,
        current_results: Dict[str, Any],
        historical_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze test results using AI to identify patterns and issues.
        
        Args:
            current_results: Current test run results
            historical_results: Previous test results for trend analysis
            
        Returns:
            Comprehensive analysis with insights and recommendations
        """
        # Generate insights (returns AnalysisInsight objects)
        insights = self._generate_ai_insights(current_results, historical_results)
        
        # Convert insights to dictionaries for JSON serialization
        insights_dict = [asdict(insight) for insight in insights]
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(current_results),
            'regressions': self._detect_regressions(current_results, historical_results),
            'flaky_tests': self._identify_flaky_tests(current_results, historical_results),
            'performance_trends': self._analyze_performance_trends(current_results, historical_results),
            'insights': insights_dict,  # Use dict version for JSON
            'action_items': self._prioritize_actions(current_results, historical_results),
            'health_score': self._calculate_health_score(current_results)
        }
        
        return analysis
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of test results."""
        total = results.get('total', 0)
        passed = results.get('passed', 0)
        failed = results.get('failed', 0)
        skipped = results.get('skipped', 0)
        duration = results.get('duration', 0)
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'pass_rate': round(pass_rate, 2),
            'duration': round(duration, 2),
            'status': 'healthy' if pass_rate >= 95 else 'degraded' if pass_rate >= 85 else 'critical'
        }
    
    def _detect_regressions(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Detect tests that were passing but are now failing (regressions)."""
        if not historical or len(historical) == 0:
            return []
        
        regressions = []
        last_run = historical[-1] if historical else {}
        
        current_failed = set(current.get('failed_tests', []))
        last_passed = set(last_run.get('passed_tests', []))
        
        # Tests that were passing yesterday but failing today
        new_failures = current_failed.intersection(last_passed)
        
        for test_name in new_failures:
            failure_info = self._get_test_failure_info(current, test_name)
            regressions.append({
                'test_name': test_name,
                'failure_message': failure_info.get('message', 'Unknown'),
                'error_type': failure_info.get('type', 'Unknown'),
                'priority': 'high'
            })
        
        return regressions
    
    def _identify_flaky_tests(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Identify tests that intermittently fail (flaky tests)."""
        if not historical or len(historical) < 5:
            return []
        
        flaky_tests = []
        
        # Analyze last 10 runs
        recent_runs = historical[-10:] + [current]
        
        # Count failures for each test
        test_failures = {}
        for run in recent_runs:
            failed = run.get('failed_tests', [])
            passed = run.get('passed_tests', [])
            
            for test in failed:
                test_failures[test] = test_failures.get(test, 0) + 1
            for test in passed:
                if test not in test_failures:
                    test_failures[test] = 0
        
        # Tests that sometimes pass, sometimes fail are flaky
        for test, failure_count in test_failures.items():
            if 0 < failure_count < len(recent_runs):
                flaky_tests.append({
                    'test_name': test,
                    'failure_rate': round(failure_count / len(recent_runs) * 100, 2),
                    'total_runs': len(recent_runs),
                    'failures': failure_count,
                    'priority': 'medium' if failure_count / len(recent_runs) > 0.3 else 'low'
                })
        
        return sorted(flaky_tests, key=lambda x: x['failure_rate'], reverse=True)
    
    def _analyze_performance_trends(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze performance metrics and trends."""
        if not historical:
            return {
                'current_avg_duration': current.get('duration', 0),
                'trend': 'stable',
                'slowest_tests': self._get_slowest_tests(current)
            }
        
        # Get durations from last 30 days
        recent_runs = historical[-30:] + [current]
        durations = [run.get('duration', 0) for run in recent_runs]
        
        if len(durations) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate trend
        current_avg = sum(durations[-7:]) / min(7, len(durations[-7:]))
        previous_avg = sum(durations[-14:-7]) / min(7, len(durations[-14:-7])) if len(durations) > 7 else current_avg
        
        change_pct = ((current_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        
        trend = 'improving' if change_pct < -5 else 'degrading' if change_pct > 5 else 'stable'
        
        return {
            'current_avg_duration': round(current_avg, 2),
            'previous_avg_duration': round(previous_avg, 2),
            'change_percentage': round(change_pct, 2),
            'trend': trend,
            'slowest_tests': self._get_slowest_tests(current),
            'alert': change_pct > 20  # Alert if >20% slower
        }
    
    def _get_slowest_tests(self, results: Dict[str, Any], top_n: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest running tests."""
        test_durations = results.get('test_durations', {})
        
        slowest = sorted(
            [{'test': k, 'duration': v} for k, v in test_durations.items()],
            key=lambda x: x['duration'],
            reverse=True
        )
        
        return slowest[:top_n]
    
    def _generate_ai_insights(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> List[AnalysisInsight]:
        """Use AI to generate insights about test failures and patterns."""
        insights = []
        
        # Prepare context for LLM
        context = self._prepare_llm_context(current, historical)
        
        prompt = f"""You are an expert software testing engineer analyzing test results for a content editorial assistant application.

Current Test Run Summary:
- Total Tests: {context['total_tests']}
- Passed: {context['passed']}
- Failed: {context['failed']}
- Pass Rate: {context['pass_rate']}%
- Duration: {context['duration']}s

Failed Tests:
{self._format_failures_for_llm(current)}

Historical Context:
{self._format_historical_context(historical)}

Analyze the test results and provide:
1. Root cause analysis for failures
2. Patterns in failures (e.g., all database tests failing, UI tests timing out)
3. Correlation between failures
4. Prioritized recommendations

Format your response as JSON with this structure:
{{
    "insights": [
        {{
            "priority": 1-5,
            "title": "Brief title",
            "description": "Detailed explanation",
            "affected_tests": ["test1", "test2"],
            "suggested_actions": ["action1", "action2"],
            "category": "regression|performance|flaky|infrastructure|code_quality"
        }}
    ]
}}

Respond ONLY with valid JSON, no additional text."""

        try:
            # Check if AI is available
            if not self.ai_available:
                raise Exception("AI provider not available")
            
            print(f"🧠 Calling {self.ai_provider.upper()} AI for analysis...")
            # Call LLM with appropriate provider
            response_text = self._call_llm(prompt)
            print(f"✅ AI response received ({len(response_text)} chars)")
            
            # Parse JSON response
            insights_data = json.loads(response_text)
            
            for insight_dict in insights_data.get('insights', []):
                insight = AnalysisInsight(
                    priority=insight_dict['priority'],
                    title=insight_dict['title'],
                    description=insight_dict['description'],
                    affected_tests=insight_dict['affected_tests'],
                    suggested_actions=insight_dict['suggested_actions'],
                    category=insight_dict['category'],
                    confidence=0.8  # Default confidence
                )
                insights.append(insight)
        
        except Exception as e:
            # Fallback: Create basic insight
            print(f"⚠️  AI analysis failed: {str(e)}")
            print(f"ℹ️  Falling back to basic analysis (no AI insights)")
            insights.append(AnalysisInsight(
                priority=1,
                title="AI Analysis Unavailable",
                description=f"Could not generate AI insights: {str(e)}",
                affected_tests=[],
                suggested_actions=["Review failed tests manually"],
                category="infrastructure",
                confidence=1.0
            ))
        
        return insights
    
    def _prepare_llm_context(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Prepare context for LLM analysis."""
        summary = self._generate_summary(current)
        
        return {
            'total_tests': summary['total_tests'],
            'passed': summary['passed'],
            'failed': summary['failed'],
            'pass_rate': summary['pass_rate'],
            'duration': summary['duration'],
            'status': summary['status']
        }
    
    def _format_failures_for_llm(self, results: Dict[str, Any]) -> str:
        """Format failure information for LLM."""
        failures = results.get('failures', [])
        
        if not failures:
            return "No failures"
        
        formatted = []
        for i, failure in enumerate(failures[:10], 1):  # Limit to first 10
            formatted.append(f"{i}. {failure.get('test_name', 'Unknown')}")
            formatted.append(f"   Error: {failure.get('message', 'No message')}")
            formatted.append(f"   Type: {failure.get('type', 'Unknown')}")
            formatted.append("")
        
        return "\n".join(formatted)
    
    def _format_historical_context(self, historical: Optional[List[Dict[str, Any]]]) -> str:
        """Format historical context for LLM."""
        if not historical or len(historical) == 0:
            return "No historical data available"
        
        recent = historical[-7:]  # Last 7 runs
        
        context = []
        context.append(f"Last 7 test runs:")
        for i, run in enumerate(recent, 1):
            summary = self._generate_summary(run)
            context.append(
                f"Run {i}: {summary['passed']}/{summary['total_tests']} passed "
                f"({summary['pass_rate']}%) in {summary['duration']}s"
            )
        
        return "\n".join(context)
    
    def _prioritize_actions(
        self,
        current: Dict[str, Any],
        historical: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized list of actions to take."""
        actions = []
        
        # High priority: Regressions
        regressions = self._detect_regressions(current, historical)
        for regression in regressions:
            actions.append({
                'priority': 1,
                'type': 'regression',
                'title': f"Fix regression: {regression['test_name']}",
                'description': regression['failure_message'],
                'estimated_impact': 'high'
            })
        
        # Medium priority: Performance degradation
        perf = self._analyze_performance_trends(current, historical)
        if perf.get('alert'):
            actions.append({
                'priority': 2,
                'type': 'performance',
                'title': f"Investigate {perf['change_percentage']}% performance degradation",
                'description': f"Test suite is {perf['change_percentage']}% slower than last week",
                'estimated_impact': 'medium'
            })
        
        # Low priority: Flaky tests
        flaky = self._identify_flaky_tests(current, historical)
        for test in flaky[:3]:  # Top 3 flakiest
            actions.append({
                'priority': 3,
                'type': 'flaky',
                'title': f"Stabilize flaky test: {test['test_name']}",
                'description': f"Fails {test['failure_rate']}% of the time",
                'estimated_impact': 'low'
            })
        
        # Sort by priority
        actions.sort(key=lambda x: x['priority'])
        
        return actions
    
    def _calculate_health_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate an overall health score for the test suite."""
        summary = self._generate_summary(results)
        
        # Factors: pass rate (50%), duration (20%), flakiness (30%)
        pass_rate_score = summary['pass_rate'] / 100 * 50
        
        # Duration score (faster is better, baseline 5 minutes)
        duration = summary['duration']
        duration_score = max(0, min(20, 20 * (1 - (duration - 300) / 600))) if duration > 0 else 20
        
        # Flakiness score (assumed 30 for now, would need historical data)
        flakiness_score = 30
        
        total_score = pass_rate_score + duration_score + flakiness_score
        
        return {
            'overall_score': round(total_score, 1),
            'max_score': 100,
            'grade': self._score_to_grade(total_score),
            'components': {
                'pass_rate': round(pass_rate_score, 1),
                'performance': round(duration_score, 1),
                'reliability': round(flakiness_score, 1)
            }
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        else:
            return 'D'
    
    def _get_test_failure_info(self, results: Dict[str, Any], test_name: str) -> Dict[str, str]:
        """Get detailed failure information for a specific test."""
        failures = results.get('failures', [])
        
        for failure in failures:
            if failure.get('test_name') == test_name:
                return {
                    'message': failure.get('message', 'Unknown error'),
                    'type': failure.get('type', 'Unknown'),
                    'traceback': failure.get('traceback', '')
                }
        
        return {'message': 'Unknown error', 'type': 'Unknown', 'traceback': ''}
    
    def save_results(self, analysis: Dict[str, Any]):
        """Save analysis results to history."""
        # Load existing history
        history = []
        if self.history_path.exists():
            try:
                with open(self.history_path, 'r') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️  Corrupted history file detected: {e}")
                print(f"⚠️  Creating backup and starting fresh...")
                # Backup corrupted file
                backup_path = self.history_path.with_suffix('.json.backup')
                if self.history_path.exists():
                    import shutil
                    shutil.copy(self.history_path, backup_path)
                    print(f"⚠️  Backup saved to: {backup_path}")
                history = []
        
        # Add new analysis
        history.append(analysis)
        
        # Keep only last 90 days
        try:
            cutoff = datetime.now() - timedelta(days=90)
            history = [
                h for h in history
                if datetime.fromisoformat(h.get('timestamp', '')) > cutoff
            ]
        except (ValueError, KeyError) as e:
            print(f"⚠️  Error filtering history by date: {e}")
            # Keep all history if date parsing fails
        
        # Save with error handling
        try:
            with open(self.history_path, 'w') as f:
                json.dump(history, f, indent=2)
            print(f"✅ Analysis saved to: {self.history_path}")
        except Exception as e:
            print(f"❌ Error saving analysis: {e}")

