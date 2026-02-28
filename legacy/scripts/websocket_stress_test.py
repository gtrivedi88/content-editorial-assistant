#!/usr/bin/env python3
"""
WebSocket Stress Testing Script (Phase 4)
Tests WebSocket reliability and performance under load conditions.
"""

import asyncio
import websockets
import json
import time
import logging
import statistics
import sys
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
import random


@dataclass
class WebSocketTestConfig:
    """Configuration for WebSocket stress testing."""
    base_url: str = 'ws://localhost:5000'
    num_concurrent_connections: int = 20
    test_duration_seconds: int = 60
    messages_per_connection: int = 50
    message_interval_seconds: float = 1.0
    connection_timeout: int = 10
    ping_interval: int = 25
    ping_timeout: int = 60


@dataclass
class ConnectionResult:
    """Result data for a single WebSocket connection."""
    connection_id: str
    connected: bool
    connection_time: float
    total_messages_sent: int
    total_messages_received: int
    total_ping_responses: int
    average_response_time: float
    errors: List[str]
    disconnection_reason: Optional[str] = None


class WebSocketStressTester:
    """WebSocket stress tester for real-time communication reliability."""
    
    def __init__(self, config: WebSocketTestConfig):
        self.config = config
        self.results: List[ConnectionResult] = []
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    async def _test_single_connection(self, connection_id: str) -> ConnectionResult:
        """Test a single WebSocket connection."""
        
        result = ConnectionResult(
            connection_id=connection_id,
            connected=False,
            connection_time=0.0,
            total_messages_sent=0,
            total_messages_received=0,
            total_ping_responses=0,
            average_response_time=0.0,
            errors=[]
        )
        
        connection_start = time.time()
        
        try:
            # Connect to WebSocket
            uri = f"{self.config.base_url.replace('http', 'ws')}/socket.io/?transport=websocket"
            
            async with websockets.connect(
                uri,
                timeout=self.config.connection_timeout,
                ping_interval=self.config.ping_interval,
                ping_timeout=self.config.ping_timeout
            ) as websocket:
                
                result.connected = True
                result.connection_time = time.time() - connection_start
                
                self.logger.debug(f"Connection {connection_id} established in {result.connection_time:.2f}s")
                
                # Generate session ID
                session_id = f"stress-test-{connection_id}-{int(time.time())}"
                
                # Join session
                join_message = {
                    'type': 'join_session',
                    'data': {'session_id': session_id}
                }
                
                await websocket.send(json.dumps(join_message))
                result.total_messages_sent += 1
                
                # Track response times
                response_times = []
                
                # Send test messages
                for message_num in range(self.config.messages_per_connection):
                    
                    # Create test message (simulating various event types)
                    message_types = [
                        {
                            'type': 'request_confidence_update',
                            'data': {'session_id': session_id}
                        },
                        {
                            'type': 'ping',
                            'data': {}
                        },
                        {
                            'type': 'submit_feedback_realtime',
                            'data': {
                                'session_id': session_id,
                                'feedback_data': {
                                    'feedback_type': 'correct',
                                    'error_type': 'test_error',
                                    'block_id': f'test-block-{message_num}'
                                }
                            }
                        }
                    ]
                    
                    message = random.choice(message_types)
                    message_start = time.time()
                    
                    # Send message
                    await websocket.send(json.dumps(message))
                    result.total_messages_sent += 1
                    
                    try:
                        # Wait for response with timeout
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=5.0
                        )
                        
                        response_time = time.time() - message_start
                        response_times.append(response_time)
                        result.total_messages_received += 1
                        
                        # Check if it's a pong response
                        try:
                            response_data = json.loads(response)
                            if response_data.get('type') == 'pong':
                                result.total_ping_responses += 1
                        except (json.JSONDecodeError, KeyError):
                            pass
                        
                    except asyncio.TimeoutError:
                        result.errors.append(f"Message {message_num}: Response timeout")
                    except Exception as e:
                        result.errors.append(f"Message {message_num}: {str(e)}")
                    
                    # Wait before next message
                    await asyncio.sleep(self.config.message_interval_seconds)
                
                # Calculate average response time
                if response_times:
                    result.average_response_time = statistics.mean(response_times)
                
                self.logger.debug(f"Connection {connection_id} completed successfully")
                
        except websockets.exceptions.ConnectionClosed as e:
            result.disconnection_reason = f"Connection closed: {e}"
            result.errors.append(result.disconnection_reason)
            
        except asyncio.TimeoutError:
            result.disconnection_reason = "Connection timeout"
            result.errors.append(result.disconnection_reason)
            
        except Exception as e:
            result.disconnection_reason = f"Connection error: {str(e)}"
            result.errors.append(result.disconnection_reason)
        
        return result
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Run the complete WebSocket stress test."""
        
        self.logger.info(f"Starting WebSocket stress test with {self.config.num_concurrent_connections} connections")
        self.logger.info(f"Each connection will send {self.config.messages_per_connection} messages")
        
        start_time = time.time()
        
        # Create tasks for all connections
        tasks = []
        for i in range(self.config.num_concurrent_connections):
            connection_id = f"conn-{i:03d}"
            task = self._test_single_connection(connection_id)
            tasks.append(task)
        
        # Run all connections concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Process results
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Connection failed: {result}")
                continue
            valid_results.append(result)
        
        self.results = valid_results
        
        self.logger.info(f"WebSocket stress test completed in {total_time:.2f} seconds")
        return self._analyze_results(total_time)
    
    def _analyze_results(self, total_test_time: float) -> Dict[str, Any]:
        """Analyze WebSocket stress test results."""
        
        if not self.results:
            return {'error': 'No results to analyze'}
        
        # Connection statistics
        total_connections = len(self.results)
        successful_connections = sum(1 for r in self.results if r.connected)
        failed_connections = total_connections - successful_connections
        connection_success_rate = successful_connections / total_connections if total_connections > 0 else 0
        
        # Connection time statistics
        connection_times = [r.connection_time for r in self.results if r.connected]
        avg_connection_time = statistics.mean(connection_times) if connection_times else 0
        max_connection_time = max(connection_times) if connection_times else 0
        
        # Message statistics
        total_messages_sent = sum(r.total_messages_sent for r in self.results)
        total_messages_received = sum(r.total_messages_received for r in self.results)
        message_success_rate = total_messages_received / total_messages_sent if total_messages_sent > 0 else 0
        
        # Response time statistics
        response_times = [r.average_response_time for r in self.results if r.average_response_time > 0]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Ping statistics
        total_ping_responses = sum(r.total_ping_responses for r in self.results)
        avg_ping_responses_per_connection = total_ping_responses / successful_connections if successful_connections > 0 else 0
        
        # Error analysis
        total_errors = sum(len(r.errors) for r in self.results)
        error_types = {}
        for result in self.results:
            for error in result.errors:
                # Categorize errors
                if 'timeout' in error.lower():
                    error_types['Timeout'] = error_types.get('Timeout', 0) + 1
                elif 'connection' in error.lower():
                    error_types['Connection'] = error_types.get('Connection', 0) + 1
                elif 'response' in error.lower():
                    error_types['Response'] = error_types.get('Response', 0) + 1
                else:
                    error_types['Other'] = error_types.get('Other', 0) + 1
        
        # Reliability metrics
        uptime_percentage = (total_messages_received / (total_connections * self.config.messages_per_connection)) * 100 if total_connections > 0 else 0
        
        return {
            'test_summary': {
                'total_connections': total_connections,
                'successful_connections': successful_connections,
                'failed_connections': failed_connections,
                'connection_success_rate': connection_success_rate,
                'total_test_time': total_test_time,
                'concurrent_connections': self.config.num_concurrent_connections
            },
            'connection_performance': {
                'avg_connection_time': avg_connection_time,
                'max_connection_time': max_connection_time,
                'connection_timeout_threshold': self.config.connection_timeout,
                'connection_time_acceptable': max_connection_time <= self.config.connection_timeout
            },
            'message_statistics': {
                'total_messages_sent': total_messages_sent,
                'total_messages_received': total_messages_received,
                'message_success_rate': message_success_rate,
                'avg_response_time': avg_response_time,
                'max_response_time': max_response_time,
                'response_time_acceptable': avg_response_time <= 1.0  # 1 second threshold
            },
            'reliability_metrics': {
                'uptime_percentage': uptime_percentage,
                'total_ping_responses': total_ping_responses,
                'avg_ping_responses_per_connection': avg_ping_responses_per_connection,
                'total_errors': total_errors,
                'error_rate': total_errors / total_messages_sent if total_messages_sent > 0 else 0
            },
            'error_analysis': error_types,
            'performance_requirements': {
                'min_connection_success_rate': 0.95,
                'min_message_success_rate': 0.98,
                'min_uptime_percentage': 99.0,
                'max_avg_response_time': 1.0,
                'connection_success_met': connection_success_rate >= 0.95,
                'message_success_met': message_success_rate >= 0.98,
                'uptime_met': uptime_percentage >= 99.0,
                'response_time_met': avg_response_time <= 1.0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def print_results_summary(self, analysis: Dict[str, Any]):
        """Print a formatted summary of WebSocket stress test results."""
        
        print("\n" + "="*80)
        print("📡 WEBSOCKET STRESS TEST RESULTS")
        print("="*80)
        
        # Test Summary
        summary = analysis['test_summary']
        print(f"\n📊 Test Summary:")
        print(f"   Concurrent Connections: {summary['concurrent_connections']}")
        print(f"   Total Connections: {summary['total_connections']}")
        print(f"   Successful: {summary['successful_connections']} ({summary['connection_success_rate']:.1%})")
        print(f"   Failed: {summary['failed_connections']}")
        print(f"   Test Duration: {summary['total_test_time']:.2f} seconds")
        
        # Connection Performance
        conn_perf = analysis['connection_performance']
        print(f"\n🔗 Connection Performance:")
        print(f"   Average Connection Time: {conn_perf['avg_connection_time']:.2f}s")
        print(f"   Maximum Connection Time: {conn_perf['max_connection_time']:.2f}s")
        print(f"   Connection Timeout: {conn_perf['connection_timeout_threshold']}s")
        print(f"   Connection Time Acceptable: {'✅ YES' if conn_perf['connection_time_acceptable'] else '❌ NO'}")
        
        # Message Statistics
        msg_stats = analysis['message_statistics']
        print(f"\n💬 Message Statistics:")
        print(f"   Total Messages Sent: {msg_stats['total_messages_sent']}")
        print(f"   Total Messages Received: {msg_stats['total_messages_received']}")
        print(f"   Message Success Rate: {msg_stats['message_success_rate']:.1%}")
        print(f"   Average Response Time: {msg_stats['avg_response_time']:.3f}s")
        print(f"   Maximum Response Time: {msg_stats['max_response_time']:.3f}s")
        
        # Reliability Metrics
        reliability = analysis['reliability_metrics']
        print(f"\n📈 Reliability Metrics:")
        print(f"   System Uptime: {reliability['uptime_percentage']:.1f}%")
        print(f"   Total Ping Responses: {reliability['total_ping_responses']}")
        print(f"   Avg Ping Responses/Connection: {reliability['avg_ping_responses_per_connection']:.1f}")
        print(f"   Total Errors: {reliability['total_errors']}")
        print(f"   Error Rate: {reliability['error_rate']:.2%}")
        
        # Error Analysis
        if analysis['error_analysis']:
            print(f"\n❌ Error Breakdown:")
            for error_type, count in analysis['error_analysis'].items():
                print(f"   {error_type}: {count} occurrences")
        else:
            print(f"\n✅ No Errors Detected")
        
        # Performance Requirements
        perf_req = analysis['performance_requirements']
        print(f"\n🎯 Performance Requirements:")
        print(f"   Connection Success (≥95%): {'✅ PASS' if perf_req['connection_success_met'] else '❌ FAIL'} ({summary['connection_success_rate']:.1%})")
        print(f"   Message Success (≥98%): {'✅ PASS' if perf_req['message_success_met'] else '❌ FAIL'} ({msg_stats['message_success_rate']:.1%})")
        print(f"   System Uptime (≥99%): {'✅ PASS' if perf_req['uptime_met'] else '❌ FAIL'} ({reliability['uptime_percentage']:.1f}%)")
        print(f"   Response Time (≤1s): {'✅ PASS' if perf_req['response_time_met'] else '❌ FAIL'} ({msg_stats['avg_response_time']:.3f}s)")
        
        # Overall Assessment
        print(f"\n🏆 Overall Assessment:")
        all_requirements_met = all([
            perf_req['connection_success_met'],
            perf_req['message_success_met'],
            perf_req['uptime_met'],
            perf_req['response_time_met']
        ])
        
        if all_requirements_met:
            print("   ✅ WEBSOCKET STRESS TEST PASSED - System meets reliability requirements")
        else:
            print("   ❌ WEBSOCKET STRESS TEST FAILED - System does not meet reliability requirements")
            
            # Recommendations
            print("\n💡 Recommendations:")
            if not perf_req['connection_success_met']:
                print("   - Investigate connection failures and improve connection handling")
            if not perf_req['message_success_met']:
                print("   - Review message handling and improve reliability")
            if not perf_req['uptime_met']:
                print("   - Implement better error handling and connection recovery")
            if not perf_req['response_time_met']:
                print("   - Optimize WebSocket message processing for faster responses")
        
        print("\n" + "="*80)


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(description="WebSocket Stress Testing")
    parser.add_argument('--base-url', default='ws://localhost:5000', help='Base WebSocket URL')
    parser.add_argument('--connections', type=int, default=20, help='Number of concurrent connections')
    parser.add_argument('--messages', type=int, default=50, help='Number of messages per connection')
    parser.add_argument('--duration', type=int, default=60, help='Test duration in seconds')
    parser.add_argument('--interval', type=float, default=1.0, help='Message interval in seconds')
    parser.add_argument('--timeout', type=int, default=10, help='Connection timeout in seconds')
    parser.add_argument('--output', help='Output file for detailed results (JSON)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = WebSocketTestConfig(
        base_url=args.base_url,
        num_concurrent_connections=args.connections,
        messages_per_connection=args.messages,
        test_duration_seconds=args.duration,
        message_interval_seconds=args.interval,
        connection_timeout=args.timeout
    )
    
    # Run stress test
    tester = WebSocketStressTester(config)
    
    try:
        analysis = asyncio.run(tester.run_stress_test())
        
        # Print results
        tester.print_results_summary(analysis)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    'config': config.__dict__,
                    'analysis': analysis,
                    'detailed_results': [r.__dict__ for r in tester.results]
                }, f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {args.output}")
        
        # Exit with appropriate code
        perf_req = analysis['performance_requirements']
        all_met = all([
            perf_req['connection_success_met'],
            perf_req['message_success_met'],
            perf_req['uptime_met'],
            perf_req['response_time_met']
        ])
        
        if all_met:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Requirements not met
            
    except KeyboardInterrupt:
        print("\n🛑 WebSocket stress test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ WebSocket stress test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
