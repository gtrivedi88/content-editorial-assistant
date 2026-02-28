#!/usr/bin/env python3
"""
Memory Profiling Script for Block Processing (Phase 4)
Monitors memory usage during block processing operations.
"""

import psutil
import time
import json
import sys
import argparse
import logging
import requests
import threading
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class MemorySnapshot:
    """Memory usage snapshot at a point in time."""
    timestamp: float
    rss_mb: float  # Resident Set Size (physical memory)
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float  # Available system memory
    cpu_percent: float  # CPU usage
    active_connections: int  # Active connections if available


class MemoryProfiler:
    """Memory profiler for block processing operations."""
    
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.snapshots: List[MemorySnapshot] = []
        self.profiling = False
        self.process = psutil.Process()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start_profiling(self):
        """Start memory profiling."""
        self.profiling = True
        self.snapshots = []
        
        def profile_worker():
            while self.profiling:
                try:
                    # Get memory info
                    memory_info = self.process.memory_info()
                    memory_percent = self.process.memory_percent()
                    cpu_percent = self.process.cpu_percent()
                    
                    # Get system memory info
                    system_memory = psutil.virtual_memory()
                    
                    # Try to get active connections (if WebSocket endpoint available)
                    active_connections = self._get_active_connections()
                    
                    snapshot = MemorySnapshot(
                        timestamp=time.time(),
                        rss_mb=memory_info.rss / (1024 * 1024),
                        vms_mb=memory_info.vms / (1024 * 1024),
                        percent=memory_percent,
                        available_mb=system_memory.available / (1024 * 1024),
                        cpu_percent=cpu_percent,
                        active_connections=active_connections
                    )
                    
                    self.snapshots.append(snapshot)
                    
                except Exception as e:
                    self.logger.error(f"Error taking memory snapshot: {e}")
                
                time.sleep(self.sampling_interval)
        
        self.profile_thread = threading.Thread(target=profile_worker, daemon=True)
        self.profile_thread.start()
        self.logger.info("Memory profiling started")
    
    def stop_profiling(self):
        """Stop memory profiling."""
        self.profiling = False
        if hasattr(self, 'profile_thread'):
            self.profile_thread.join(timeout=5)
        self.logger.info("Memory profiling stopped")
    
    def _get_active_connections(self) -> int:
        """Get number of active WebSocket connections if possible."""
        try:
            # Try to get WebSocket metrics from the application
            response = requests.get('http://localhost:5000/api/websocket-metrics', timeout=2)
            if response.status_code == 200:
                metrics = response.json()
                return metrics.get('active_sessions_count', 0)
        except:
            pass
        return 0
    
    def analyze_memory_usage(self) -> Dict[str, Any]:
        """Analyze memory usage patterns."""
        if not self.snapshots:
            return {'error': 'No memory snapshots available'}
        
        # Basic statistics
        rss_values = [s.rss_mb for s in self.snapshots]
        vms_values = [s.vms_mb for s in self.snapshots]
        percent_values = [s.percent for s in self.snapshots]
        cpu_values = [s.cpu_percent for s in self.snapshots]
        
        # Calculate statistics
        initial_rss = rss_values[0]
        final_rss = rss_values[-1]
        max_rss = max(rss_values)
        min_rss = min(rss_values)
        avg_rss = sum(rss_values) / len(rss_values)
        
        memory_growth = final_rss - initial_rss
        peak_memory_usage = max_rss
        
        # Calculate growth rate
        if len(self.snapshots) > 1:
            time_span = self.snapshots[-1].timestamp - self.snapshots[0].timestamp
            growth_rate = memory_growth / time_span if time_span > 0 else 0  # MB per second
        else:
            growth_rate = 0
        
        # Detect memory leaks (significant upward trend)
        if len(rss_values) >= 10:
            # Simple linear trend detection
            x_values = list(range(len(rss_values)))
            n = len(rss_values)
            sum_x = sum(x_values)
            sum_y = sum(rss_values)
            sum_xy = sum(x * y for x, y in zip(x_values, rss_values))
            sum_x2 = sum(x * x for x in x_values)
            
            # Calculate slope of trend line
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            trend_direction = 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
            potential_leak = slope > 0.5  # More than 0.5 MB growth per sample
        else:
            slope = 0
            trend_direction = 'unknown'
            potential_leak = False
        
        # CPU correlation
        avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        max_cpu = max(cpu_values) if cpu_values else 0
        
        return {
            'summary': {
                'total_snapshots': len(self.snapshots),
                'duration_seconds': self.snapshots[-1].timestamp - self.snapshots[0].timestamp if len(self.snapshots) > 1 else 0,
                'sampling_interval': self.sampling_interval
            },
            'memory_statistics': {
                'initial_rss_mb': initial_rss,
                'final_rss_mb': final_rss,
                'peak_rss_mb': peak_memory_usage,
                'min_rss_mb': min_rss,
                'average_rss_mb': avg_rss,
                'memory_growth_mb': memory_growth,
                'growth_rate_mb_per_sec': growth_rate
            },
            'memory_analysis': {
                'trend_direction': trend_direction,
                'trend_slope': slope,
                'potential_memory_leak': potential_leak,
                'memory_efficiency': 'good' if memory_growth < 50 else 'concerning' if memory_growth < 100 else 'poor'
            },
            'cpu_statistics': {
                'average_cpu_percent': avg_cpu,
                'peak_cpu_percent': max_cpu
            },
            'performance_assessment': {
                'memory_stable': abs(memory_growth) < 100,  # Less than 100MB growth
                'cpu_reasonable': avg_cpu < 80,  # Less than 80% average CPU
                'no_memory_leaks': not potential_leak,
                'overall_healthy': abs(memory_growth) < 100 and avg_cpu < 80 and not potential_leak
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def print_analysis_summary(self, analysis: Dict[str, Any]):
        """Print formatted analysis summary."""
        
        print("\n" + "="*80)
        print("🔍 MEMORY PROFILING ANALYSIS")
        print("="*80)
        
        # Summary
        summary = analysis['summary']
        print(f"\n📊 Profiling Summary:")
        print(f"   Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"   Snapshots: {summary['total_snapshots']}")
        print(f"   Sampling Interval: {summary['sampling_interval']:.1f} seconds")
        
        # Memory Statistics
        mem_stats = analysis['memory_statistics']
        print(f"\n💾 Memory Statistics:")
        print(f"   Initial Memory: {mem_stats['initial_rss_mb']:.1f} MB")
        print(f"   Final Memory: {mem_stats['final_rss_mb']:.1f} MB")
        print(f"   Peak Memory: {mem_stats['peak_rss_mb']:.1f} MB")
        print(f"   Average Memory: {mem_stats['average_rss_mb']:.1f} MB")
        print(f"   Memory Growth: {mem_stats['memory_growth_mb']:+.1f} MB")
        print(f"   Growth Rate: {mem_stats['growth_rate_mb_per_sec']:+.3f} MB/second")
        
        # Memory Analysis
        mem_analysis = analysis['memory_analysis']
        trend_icon = "📈" if mem_analysis['trend_direction'] == 'increasing' else "📉" if mem_analysis['trend_direction'] == 'decreasing' else "➡️"
        leak_icon = "⚠️" if mem_analysis['potential_memory_leak'] else "✅"
        
        print(f"\n🔬 Memory Analysis:")
        print(f"   Trend: {trend_icon} {mem_analysis['trend_direction']}")
        print(f"   Trend Slope: {mem_analysis['trend_slope']:.3f}")
        print(f"   Memory Leak Risk: {leak_icon} {'HIGH' if mem_analysis['potential_memory_leak'] else 'LOW'}")
        print(f"   Memory Efficiency: {mem_analysis['memory_efficiency'].upper()}")
        
        # CPU Statistics
        cpu_stats = analysis['cpu_statistics']
        print(f"\n🖥️  CPU Statistics:")
        print(f"   Average CPU: {cpu_stats['average_cpu_percent']:.1f}%")
        print(f"   Peak CPU: {cpu_stats['peak_cpu_percent']:.1f}%")
        
        # Performance Assessment
        perf = analysis['performance_assessment']
        print(f"\n🎯 Performance Assessment:")
        print(f"   Memory Stable: {'✅ YES' if perf['memory_stable'] else '❌ NO'}")
        print(f"   CPU Reasonable: {'✅ YES' if perf['cpu_reasonable'] else '❌ NO'}")
        print(f"   No Memory Leaks: {'✅ YES' if perf['no_memory_leaks'] else '❌ NO'}")
        print(f"   Overall Health: {'✅ HEALTHY' if perf['overall_healthy'] else '⚠️ CONCERNING'}")
        
        # Recommendations
        if not perf['overall_healthy']:
            print(f"\n💡 Recommendations:")
            if not perf['memory_stable']:
                print("   - Monitor memory usage patterns and optimize data structures")
                print("   - Consider implementing memory cleanup routines")
            if not perf['cpu_reasonable']:
                print("   - Optimize CPU-intensive operations")
                print("   - Consider async processing for heavy workloads")
            if not perf['no_memory_leaks']:
                print("   - Investigate potential memory leaks")
                print("   - Review object lifecycle management")
                print("   - Consider using memory debugging tools")
        
        print("\n" + "="*80)


def simulate_block_processing_load(base_url: str, num_blocks: int = 10, concurrent: bool = False):
    """Simulate block processing load for memory profiling."""
    
    def process_single_block(block_id: int):
        """Process a single block."""
        block_data = {
            'block_content': f'This content was processed by block {block_id} and needs improvement.',
            'block_errors': [
                {
                    'type': 'passive_voice',
                    'flagged_text': 'was processed',
                    'position': 13,
                    'message': 'Consider using active voice'
                }
            ],
            'block_type': 'paragraph',
            'block_id': f'memory-test-block-{block_id}',
            'session_id': f'memory-test-session-{block_id}'
        }
        
        try:
            response = requests.post(
                f"{base_url}/rewrite-block",
                json=block_data,
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Error processing block {block_id}: {e}")
            return False
    
    logging.info(f"Starting to process {num_blocks} blocks ({'concurrent' if concurrent else 'sequential'})")
    
    if concurrent:
        # Process blocks concurrently
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_block, i) for i in range(num_blocks)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
    else:
        # Process blocks sequentially
        results = [process_single_block(i) for i in range(num_blocks)]
    
    successful = sum(1 for r in results if r)
    logging.info(f"Completed processing: {successful}/{num_blocks} blocks successful")
    
    return successful, num_blocks


def main():
    """Main function for command-line usage."""
    
    parser = argparse.ArgumentParser(description="Memory Profiling for Block Processing")
    parser.add_argument('--base-url', default='http://localhost:5000', help='Base URL for the API')
    parser.add_argument('--duration', type=int, default=60, help='Profiling duration in seconds')
    parser.add_argument('--interval', type=float, default=1.0, help='Sampling interval in seconds')
    parser.add_argument('--blocks', type=int, default=10, help='Number of blocks to process during profiling')
    parser.add_argument('--concurrent', action='store_true', help='Process blocks concurrently')
    parser.add_argument('--output', help='Output file for detailed results (JSON)')
    parser.add_argument('--no-load', action='store_true', help='Profile without generating load')
    
    args = parser.parse_args()
    
    # Create profiler
    profiler = MemoryProfiler(sampling_interval=args.interval)
    
    try:
        # Start profiling
        profiler.start_profiling()
        
        if not args.no_load:
            # Wait a bit for baseline
            time.sleep(2)
            
            # Generate load
            simulate_block_processing_load(args.base_url, args.blocks, args.concurrent)
            
            # Wait for remaining duration
            remaining_time = args.duration - 2
            if remaining_time > 0:
                time.sleep(remaining_time)
        else:
            # Just profile for the specified duration
            time.sleep(args.duration)
        
        # Stop profiling
        profiler.stop_profiling()
        
        # Analyze results
        analysis = profiler.analyze_memory_usage()
        
        # Print results
        profiler.print_analysis_summary(analysis)
        
        # Save detailed results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    'analysis': analysis,
                    'snapshots': [s.__dict__ for s in profiler.snapshots]
                }, f, indent=2, default=str)
            print(f"\n📄 Detailed results saved to: {args.output}")
        
        # Exit with appropriate code
        if analysis['performance_assessment']['overall_healthy']:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Performance issues detected
            
    except KeyboardInterrupt:
        print("\n🛑 Memory profiling interrupted by user")
        profiler.stop_profiling()
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Memory profiling failed: {e}")
        profiler.stop_profiling()
        sys.exit(1)


if __name__ == "__main__":
    main()
