#!/usr/bin/env python3
"""
Block Processing Load Testing Script (Phase 4)
Performs comprehensive load testing and performance benchmarking for block-level rewriting.
"""

import asyncio
import aiohttp
import time
import json
import logging
import statistics
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import random


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    base_url: str = 'http://localhost:5000'
    num_concurrent_users: int = 10
    num_blocks_per_user: int = 5
    test_duration_seconds: int = 60
    ramp_up_seconds: int = 10
    think_time_min: float = 1.0
    think_time_max: float = 3.0
    timeout_seconds: int = 30


@dataclass
class BlockTestCase:
    """Test case for block processing."""
    name: str
    block_content: str
    block_errors: List[Dict[str, Any]]
    block_type: str
    expected_processing_time: float = 25.0  # seconds


class BlockProcessingLoadTester:
    """Load tester for block processing functionality."""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results = []
        self.errors = []
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Generate test cases
        self.test_cases = self._generate_test_cases()
    
    def _generate_test_cases(self) -> List[BlockTestCase]:
        """Generate diverse test cases for load testing."""
        return [
            BlockTestCase(
                name="passive_voice_simple",
                block_content="The document was written by the team.",
                block_errors=[{
                    'type': 'passive_voice',
                    'flagged_text': 'was written',
                    'position': 13,
                    'message': 'Consider using active voice'
                }],
                block_type="paragraph",
                expected_processing_time=15.0
            ),
            
            BlockTestCase(
                name="multiple_errors",
                block_content="You should not use these contractions and the data was processed incorrectly.",
                block_errors=[
                    {
                        'type': 'second_person',
                        'flagged_text': 'You should',
                        'position': 0,
                        'message': 'Avoid second person'
                    },
                    {
                        'type': 'contractions',
                        'flagged_text': "should not",
                        'position': 4,
                        'message': 'Consider spelling out contractions'
                    },
                    {
                        'type': 'passive_voice',
                        'flagged_text': 'was processed',
                        'position': 50,
                        'message': 'Consider using active voice'
                    }
                ],
                block_type="paragraph",
                expected_processing_time=20.0
            ),
            
            BlockTestCase(
                name="long_content",
                block_content="This is a very long paragraph that contains multiple sentences with various issues that need to be addressed. " * 5,
                block_errors=[{
                    'type': 'sentence_length',
                    'flagged_text': 'This is a very long paragraph',
                    'position': 0,
                    'message': 'Sentence is too long'
                }],
                block_type="paragraph",
                expected_processing_time=25.0
            ),
            
            BlockTestCase(
                name="clean_content",
                block_content="The team implemented the solution. Experts conducted thorough testing.",
                block_errors=[],
                block_type="paragraph",
                expected_processing_time=5.0
            ),
            
            BlockTestCase(
                name="heading_content",
                block_content="Getting Started With Documentation",
                block_errors=[{
                    'type': 'headings',
                    'flagged_text': 'Getting Started With',
                    'position': 0,
                    'message': 'Consider headline case'
                }],
                block_type="heading",
                expected_processing_time=10.0
            )
        ]
    
    async def _process_single_block(self, session: aiohttp.ClientSession, test_case: BlockTestCase, user_id: int, block_num: int) -> Dict[str, Any]:
        """Process a single block and measure performance."""
        
        block_data = {
            'block_content': test_case.block_content,
            'block_errors': test_case.block_errors,
            'block_type': test_case.block_type,
            'block_id': f'load-test-{user_id}-{block_num}-{int(time.time())}',
            'session_id': f'load-test-session-{user_id}'
        }
        
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.config.base_url}/rewrite-block",
                json=block_data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            ) as response:
                
                response_time = time.time() - start_time
                response_data = await response.json()
                
                result = {
                    'user_id': user_id,
                    'block_num': block_num,
                    'test_case': test_case.name,
                    'start_time': start_time,
                    'response_time': response_time,
                    'status_code': response.status,
                    'success': response.status == 200,
                    'block_id': block_data['block_id'],
                    'expected_time': test_case.expected_processing_time,
                    'performance_met': response_time <= test_case.expected_processing_time,
                    'response_size': len(json.dumps(response_data)),
                    'errors_fixed': response_data.get('errors_fixed', 0) if response.status == 200 else 0,
                    'confidence': response_data.get('confidence', 0.0) if response.status == 200 else 0.0
                }
                
                return result
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self.logger.warning(f"Timeout for user {user_id}, block {block_num}")
            return {
                'user_id': user_id,
                'block_num': block_num,
                'test_case': test_case.name,
                'start_time': start_time,
                'response_time': response_time,
                'status_code': 408,
                'success': False,
                'block_id': block_data['block_id'],
                'expected_time': test_case.expected_processing_time,
                'performance_met': False,
                'response_size': 0,
                'errors_fixed': 0,
                'confidence': 0.0,
                'error': 'Timeout'
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Error for user {user_id}, block {block_num}: {e}")
            return {
                'user_id': user_id,
                'block_num': block_num,
                'test_case': test_case.name,
                'start_time': start_time,
                'response_time': response_time,
                'status_code': 500,
                'success': False,
                'block_id': block_data['block_id'],
                'expected_time': test_case.expected_processing_time,
                'performance_met': False,
                'response_size': 0,
                'errors_fixed': 0,
                'confidence': 0.0,
                'error': str(e)
            }
    
    async def _simulate_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Simulate a single user processing multiple blocks."""
        
        self.logger.info(f"Starting user simulation {user_id}")
        user_results = []
        
        async with aiohttp.ClientSession() as session:
            for block_num in range(self.config.num_blocks_per_user):
                # Select a random test case
                test_case = random.choice(self.test_cases)
                
                # Process the block
                result = await self._process_single_block(session, test_case, user_id, block_num)
                user_results.append(result)
                
                # Think time between requests
                think_time = random.uniform(self.config.think_time_min, self.config.think_time_max)
                await asyncio.sleep(think_time)
        
        self.logger.info(f"Completed user simulation {user_id}")
        return user_results
    
    async def run_load_test(self) -> Dict[str, Any]:
        """Run the complete load test."""
        
        self.logger.info(f"Starting load test with {self.config.num_concurrent_users} concurrent users")
        self.logger.info(f"Each user will process {self.config.num_blocks_per_user} blocks")
        
        start_time = time.time()
        
        # Create tasks for all users
        tasks = []
        for user_id in range(self.config.num_concurrent_users):
            # Stagger user starts for ramp-up
            ramp_delay = (user_id * self.config.ramp_up_seconds) / self.config.num_concurrent_users
            
            async def delayed_user(uid, delay):
                await asyncio.sleep(delay)
                return await self._simulate_user(uid)
            
            task = delayed_user(user_id, ramp_delay)
            tasks.append(task)
        
        # Run all user simulations concurrently
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Flatten results
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, Exception):
                self.logger.error(f"User simulation failed: {user_result}")
                continue
            all_results.extend(user_result)
        
        self.results = all_results
        
        self.logger.info(f"Load test completed in {total_time:.2f} seconds")
        return self._analyze_results(total_time)
    
    def _analyze_results(self, total_test_time: float) -> Dict[str, Any]:
        """Analyze load test results and generate report."""
        
        if not self.results:
            return {'error': 'No results to analyze'}
        
        # Basic statistics
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r['success'])
        failed_requests = total_requests - successful_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        # Response time statistics
        response_times = [r['response_time'] for r in self.results]
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))] if response_times else 0
        p99_response_time = sorted(response_times)[int(0.99 * len(response_times))] if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Performance requirements
        performance_met_count = sum(1 for r in self.results if r['performance_met'])
        performance_met_rate = performance_met_count / total_requests if total_requests > 0 else 0
        
        # Throughput
        requests_per_second = total_requests / total_test_time if total_test_time > 0 else 0
        
        # Error analysis
        error_types = {}
        for result in self.results:
            if not result['success']:
                error_key = f"{result['status_code']}: {result.get('error', 'Unknown')}"
                error_types[error_key] = error_types.get(error_key, 0) + 1
        
        # Test case performance
        test_case_stats = {}
        for test_case in self.test_cases:
            case_results = [r for r in self.results if r['test_case'] == test_case.name]
            if case_results:
                case_response_times = [r['response_time'] for r in case_results]
                case_success_rate = sum(1 for r in case_results if r['success']) / len(case_results)
                
                test_case_stats[test_case.name] = {
                    'requests': len(case_results),
                    'success_rate': case_success_rate,
                    'avg_response_time': statistics.mean(case_response_times),
                    'expected_time': test_case.expected_processing_time,
                    'performance_met_rate': sum(1 for r in case_results if r['performance_met']) / len(case_results)
                }
        
        return {
            'test_summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': success_rate,
                'total_test_time': total_test_time,
                'requests_per_second': requests_per_second,
                'concurrent_users': self.config.num_concurrent_users
            },
            'response_times': {
                'average': avg_response_time,
                'median': median_response_time,
                'min': min_response_time,
                'max': max_response_time,
                'p95': p95_response_time,
                'p99': p99_response_time
            },
            'performance_requirements': {
                'performance_met_count': performance_met_count,
                'performance_met_rate': performance_met_rate,
                'target_avg_time': 25.0,
                'target_max_time': 30.0,
                'avg_time_met': avg_response_time <= 25.0,
                'max_time_met': max_response_time <= 30.0
            },
            'error_analysis': error_types,
            'test_case_performance': test_case_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    def print_results_summary(self, analysis: Dict[str, Any]):
        """Print a formatted summary of load test results."""
        
        print("\n" + "="*80)
        print("🚀 BLOCK PROCESSING LOAD TEST RESULTS")
        print("="*80)
        
        # Test Summary
        summary = analysis['test_summary']
        print(f"\n📊 Test Summary:")
        print(f"   Total Requests: {summary['total_requests']}")
        print(f"   Successful: {summary['successful_requests']} ({summary['success_rate']:.1%})")
        print(f"   Failed: {summary['failed_requests']}")
        print(f"   Concurrent Users: {summary['concurrent_users']}")
        print(f"   Test Duration: {summary['total_test_time']:.2f} seconds")
        print(f"   Throughput: {summary['requests_per_second']:.2f} requests/second")
        
        # Response Times
        times = analysis['response_times']
        print(f"\n⏱️  Response Times:")
        print(f"   Average: {times['average']:.2f}s")
        print(f"   Median: {times['median']:.2f}s")
        print(f"   Min: {times['min']:.2f}s")
        print(f"   Max: {times['max']:.2f}s")
        print(f"   95th percentile: {times['p95']:.2f}s")
        print(f"   99th percentile: {times['p99']:.2f}s")
        
        # Performance Requirements
        perf = analysis['performance_requirements']
        print(f"\n🎯 Performance Requirements:")
        print(f"   Target Avg Time (<25s): {'✅ PASS' if perf['avg_time_met'] else '❌ FAIL'} ({times['average']:.2f}s)")
        print(f"   Target Max Time (<30s): {'✅ PASS' if perf['max_time_met'] else '❌ FAIL'} ({times['max']:.2f}s)")
        print(f"   Individual Performance Met: {perf['performance_met_rate']:.1%}")
        
        # Error Analysis
        if analysis['error_analysis']:
            print(f"\n❌ Errors:")
            for error, count in analysis['error_analysis'].items():
                print(f"   {error}: {count} occurrences")
        else:
            print(f"\n✅ No Errors Detected")
        
        # Test Case Performance
        print(f"\n📝 Test Case Performance:")
        for case_name, stats in analysis['test_case_performance'].items():
            performance_icon = "✅" if stats['performance_met_rate'] > 0.9 else "⚠️" if stats['performance_met_rate'] > 0.7 else "❌"
            print(f"   {performance_icon} {case_name}:")
            print(f"      Requests: {stats['requests']}")
            print(f"      Success Rate: {stats['success_rate']:.1%}")
            print(f"      Avg Response: {stats['avg_response_time']:.2f}s (target: {stats['expected_time']:.2f}s)")
            print(f"      Performance Met: {stats['performance_met_rate']:.1%}")
        
        # Overall Assessment
        print(f"\n🏆 Overall Assessment:")
        overall_pass = (
            summary['success_rate'] >= 0.95 and
            perf['avg_time_met'] and
            perf['max_time_met'] and
            perf['performance_met_rate'] >= 0.90
        )
        
        if overall_pass:
            print("   ✅ LOAD TEST PASSED - System meets performance requirements")
        else:
            print("   ❌ LOAD TEST FAILED - System does not meet performance requirements")
            
            # Recommendations
            print("\n💡 Recommendations:")
            if summary['success_rate'] < 0.95:
                print("   - Investigate and fix errors causing request failures")
            if not perf['avg_time_met']:
                print("   - Optimize block processing to reduce average response time")
            if not perf['max_time_met']:
                print("   - Implement timeout handling and performance optimization")
            if perf['performance_met_rate'] < 0.90:
                print("   - Review individual test case performance and optimize accordingly")
        
        print("\n" + "="*80)


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(description="Block Processing Load Testing")
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL for the API')
    parser.add_argument('--users', type=int, default=10, help='Number of concurrent users')
    parser.add_argument('--blocks', type=int, default=5, help='Number of blocks per user')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--ramp-up', type=int, default=10, help='Ramp-up time in seconds')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--output', help='Output file for detailed results (JSON)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = LoadTestConfig(
        base_url=args.base_url,
        num_concurrent_users=args.users,
        num_blocks_per_user=args.blocks,
        test_duration_seconds=args.duration,
        ramp_up_seconds=args.ramp_up,
        timeout_seconds=args.timeout
    )
    
    # Run load test
    tester = BlockProcessingLoadTester(config)
    
    try:
        analysis = asyncio.run(tester.run_load_test())
        
        # Print results
        tester.print_results_summary(analysis)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    'config': config.__dict__,
                    'analysis': analysis,
                    'detailed_results': tester.results
                }, f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {args.output}")
        
        # Exit with appropriate code
        perf_met = analysis['performance_requirements']['avg_time_met'] and analysis['performance_requirements']['max_time_met']
        success_rate_ok = analysis['test_summary']['success_rate'] >= 0.95
        
        if perf_met and success_rate_ok:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Performance requirements not met
            
    except KeyboardInterrupt:
        print("\n🛑 Load test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Load test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
