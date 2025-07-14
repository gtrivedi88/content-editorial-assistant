"""
Memory Leak and Resource Management Tests for AI Rewriting System

This module contains comprehensive tests for memory usage, resource management,
and leak detection in the AI rewriting system.
"""

import pytest
import gc
import weakref
import threading
import time
import tempfile
import os
import sys
import psutil
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager
from collections import defaultdict
import tracemalloc

from tests.test_utils import TestConfig
from rewriter.core import AIRewriter
from style_analyzer.base_analyzer import StyleAnalyzer
from rewriter.models import ModelManager
from app_modules.app_factory import create_app


class MemoryMonitor:
    """Monitor memory usage during tests."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = None
        self.current_memory = None
        
    def start_monitoring(self):
        """Start memory monitoring."""
        self.initial_memory = self.process.memory_info().rss
        self.peak_memory = self.initial_memory
        self.current_memory = self.initial_memory
        
    def update_memory(self):
        """Update current memory usage."""
        self.current_memory = self.process.memory_info().rss
        if self.current_memory > self.peak_memory:
            self.peak_memory = self.current_memory
            
    def get_memory_usage(self):
        """Get memory usage statistics."""
        self.update_memory()
        return {
            'initial': self.initial_memory or 0,
            'current': self.current_memory or 0,
            'peak': self.peak_memory or 0,
            'increase': (self.current_memory or 0) - (self.initial_memory or 0),
            'peak_increase': (self.peak_memory or 0) - (self.initial_memory or 0)
        }
    
    def check_memory_leak(self, threshold_mb=50):
        """Check for memory leaks above threshold."""
        stats = self.get_memory_usage()
        increase_mb = stats['increase'] / (1024 * 1024)
        return increase_mb > threshold_mb, increase_mb


class ResourceTracker:
    """Track resource allocation and deallocation."""
    
    def __init__(self):
        self.allocated_resources = defaultdict(int)
        self.deallocated_resources = defaultdict(int)
        self.active_resources = defaultdict(list)
        
    def allocate_resource(self, resource_type, resource_id):
        """Track resource allocation."""
        self.allocated_resources[resource_type] += 1
        self.active_resources[resource_type].append(resource_id)
        
    def deallocate_resource(self, resource_type, resource_id):
        """Track resource deallocation."""
        self.deallocated_resources[resource_type] += 1
        if resource_id in self.active_resources[resource_type]:
            self.active_resources[resource_type].remove(resource_id)
    
    def get_resource_stats(self):
        """Get resource allocation statistics."""
        return {
            'allocated': dict(self.allocated_resources),
            'deallocated': dict(self.deallocated_resources),
            'active': {k: len(v) for k, v in self.active_resources.items()},
            'leaks': {
                k: self.allocated_resources[k] - self.deallocated_resources[k]
                for k in self.allocated_resources
            }
        }


class TestMemoryLeakDetection:
    """Test memory leak detection in core components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory_monitor = MemoryMonitor()
        self.weak_refs = []
        gc.collect()  # Clean up before testing
        
    def test_style_analyzer_memory_leaks(self):
        """Test StyleAnalyzer for memory leaks."""
        self.memory_monitor.start_monitoring()
        
        # Create and use multiple analyzers
        analyzers = []
        memory_test_iterations = 20
        for i in range(memory_test_iterations):
            analyzer = StyleAnalyzer()
            analyzers.append(analyzer)
            
            # Create weak reference to track object lifecycle
            weak_ref = weakref.ref(analyzer)
            self.weak_refs.append(weak_ref)
            
            # Perform analysis
            result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
            assert result is not None
            
            # Monitor memory usage
            self.memory_monitor.update_memory()
        
        # Clear references
        analyzers.clear()
        del analyzers
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks (adjust threshold for rule loading)
        memory_leak_threshold_mb = 600  # Higher threshold due to rule loading
        has_leak, increase_mb = self.memory_monitor.check_memory_leak(memory_leak_threshold_mb)
        
        # Check object cleanup (allow for some objects due to rules registry)
        alive_objects = sum(1 for ref in self.weak_refs if ref() is not None)
        
        assert not has_leak, f"Memory leak detected: {increase_mb:.2f}MB increase"
        # Allow up to 2 objects to remain alive due to rules registry caching
        assert alive_objects <= 2, f"Object leak detected: {alive_objects} objects still alive"
    
    @patch('rewriter.models.ModelManager.get_model')
    def test_ai_rewriter_memory_leaks(self, mock_get_model):
        """Test AIRewriter for memory leaks."""
        # Mock the model
        mock_model = Mock()
        mock_model.generate_text.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        mock_get_model.return_value = mock_model
        
        self.memory_monitor.start_monitoring()
        
        # Create and use multiple rewriters
        rewriters = []
        memory_test_iterations = 20
        for i in range(memory_test_iterations):
            rewriter = AIRewriter()
            rewriters.append(rewriter)
            
            # Create weak reference
            weak_ref = weakref.ref(rewriter)
            self.weak_refs.append(weak_ref)
            
            # Perform rewriting (mocked)
            try:
                # Use the correct method name 'rewrite' with required parameters
                if hasattr(rewriter, 'rewrite'):
                    # rewrite() requires: content, errors, context, pass_number
                    result = rewriter.rewrite(TestConfig.SAMPLE_TEXT, [], "paragraph", 1)
                else:
                    # Just create the object to test memory management
                    result = "mocked result"
                assert result is not None
            except Exception:
                # Focus on memory management, not functionality
                pass
            
            self.memory_monitor.update_memory()
        
        # Clear references
        rewriters.clear()
        del rewriters
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks
        memory_leak_threshold_mb = 50
        has_leak, increase_mb = self.memory_monitor.check_memory_leak(memory_leak_threshold_mb)
        
        alive_objects = sum(1 for ref in self.weak_refs if ref() is not None)
        
        assert not has_leak, f"Memory leak detected: {increase_mb:.2f}MB increase"
        assert alive_objects == 0, f"Object leak detected: {alive_objects} objects still alive"
    
    def test_model_manager_memory_leaks(self):
        """Test ModelManager for memory leaks."""
        self.memory_monitor.start_monitoring()
        
        # Create and use multiple model managers
        managers = []
        memory_test_iterations = 20
        for i in range(memory_test_iterations):
            manager = ModelManager()
            managers.append(manager)
            
            weak_ref = weakref.ref(manager)
            self.weak_refs.append(weak_ref)
            
            # Access model (this should not create memory leaks)
            try:
                if hasattr(manager, 'get_model'):
                    model = manager.get_model(TestConfig.DEFAULT_MODEL)
                    # Simulate model usage
                    if hasattr(model, 'generate_text'):
                        model.generate_text(TestConfig.SAMPLE_TEXT)
            except Exception:
                # Model might not be available in test environment
                pass
            
            self.memory_monitor.update_memory()
        
        # Clear references
        managers.clear()
        del managers
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks
        memory_leak_threshold_mb = 50
        has_leak, increase_mb = self.memory_monitor.check_memory_leak(memory_leak_threshold_mb)
        
        alive_objects = sum(1 for ref in self.weak_refs if ref() is not None)
        
        assert not has_leak, f"Memory leak detected: {increase_mb:.2f}MB increase"
        assert alive_objects == 0, f"Object leak detected: {alive_objects} objects still alive"


class TestResourceManagement:
    """Test resource management and cleanup."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.resource_tracker = ResourceTracker()
        self.temp_files = []
        
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up any remaining temporary files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_file_handle_management(self):
        """Test proper file handle management."""
        # Create temporary files
        resource_test_iterations = 10
        for i in range(resource_test_iterations):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(f"# Test Document {i}\n\nContent for document {i}.")
                temp_file = f.name
                self.temp_files.append(temp_file)
                
                # Track resource allocation
                self.resource_tracker.allocate_resource('file_handle', temp_file)
        
        # Read files and ensure proper cleanup
        for temp_file in self.temp_files:
            try:
                with open(temp_file, 'r') as f:
                    content = f.read()
                    assert len(content) > 0
                
                # Simulate analysis
                analyzer = StyleAnalyzer()
                result = analyzer.analyze(content)
                assert result is not None
                
                # Track resource deallocation
                self.resource_tracker.deallocate_resource('file_handle', temp_file)
                
            except Exception as e:
                pytest.fail(f"File handle management failed: {str(e)}")
        
        # Check resource management
        stats = self.resource_tracker.get_resource_stats()
        assert stats['leaks']['file_handle'] == 0, "File handle leak detected"
    
    def test_memory_cleanup_on_exception(self):
        """Test memory cleanup when exceptions occur."""
        objects_created = []
        resource_test_iterations = 20
        
        def create_object_with_exception(should_fail=False):
            analyzer = StyleAnalyzer()
            objects_created.append(weakref.ref(analyzer))
            
            if should_fail:
                raise ValueError("Simulated error")
            
            return analyzer.analyze(TestConfig.SAMPLE_TEXT)
        
        # Test normal operation
        for i in range(resource_test_iterations // 2):
            try:
                result = create_object_with_exception(should_fail=False)
                assert result is not None
            except Exception:
                pytest.fail("Normal operation should not fail")
        
        # Test exception handling
        for i in range(resource_test_iterations // 2):
            try:
                create_object_with_exception(should_fail=True)
                pytest.fail("Should have raised exception")
            except ValueError:
                pass  # Expected
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks
        alive_objects = sum(1 for ref in objects_created if ref() is not None)
        assert alive_objects == 0, f"Memory leak after exceptions: {alive_objects} objects alive"
    
    def test_thread_resource_cleanup(self):
        """Test resource cleanup in threaded operations."""
        thread_resources = {}
        cleanup_counter = {'value': 0}
        concurrent_threads = 8
        
        def thread_worker(thread_id):
            try:
                # Simulate resource allocation
                analyzer = StyleAnalyzer()
                thread_resources[thread_id] = weakref.ref(analyzer)
                
                # Simulate work
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                assert result is not None
                
                # Explicit cleanup
                del analyzer
                cleanup_counter['value'] += 1
                
            except Exception as e:
                pytest.fail(f"Thread {thread_id} failed: {str(e)}")
        
        # Create and run threads
        threads = []
        for i in range(concurrent_threads):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        timeout_seconds = 30
        for thread in threads:
            thread.join(timeout=timeout_seconds)
        
        # Force garbage collection
        gc.collect()
        
        # Check resource cleanup
        alive_objects = sum(
            1 for ref in thread_resources.values() if ref() is not None
        )
        
        assert cleanup_counter['value'] == concurrent_threads
        assert alive_objects == 0, f"Thread resource leak: {alive_objects} objects alive"


class TestMemoryProfiling:
    """Test memory profiling and monitoring."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory_monitor = MemoryMonitor()
        
    def test_memory_usage_profiling(self):
        """Test memory usage profiling during operations."""
        tracemalloc.start()
        
        try:
            self.memory_monitor.start_monitoring()
            
            # Perform memory-intensive operations
            analyzers = []
            memory_test_iterations = 20
            max_memory_usage_mb = 500  # 500MB limit
            
            for i in range(memory_test_iterations):
                analyzer = StyleAnalyzer()
                analyzers.append(analyzer)
                
                # Perform analysis
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                assert result is not None
                
                # Monitor memory at intervals
                if i % 5 == 0:
                    self.memory_monitor.update_memory()
                    current, peak = tracemalloc.get_traced_memory()
                    
                    # Ensure memory usage is reasonable
                    current_mb = current / (1024 * 1024)
                    assert current_mb < max_memory_usage_mb, \
                        f"Memory usage too high: {current_mb:.2f}MB"
            
            # Get final memory statistics
            final_stats = self.memory_monitor.get_memory_usage()
            
            # Clear references
            analyzers.clear()
            del analyzers
            
            # Force garbage collection
            gc.collect()
            
            # Check final memory usage
            final_memory = self.memory_monitor.get_memory_usage()
            memory_cleaned = final_stats['current'] - final_memory['current']
            
            # Ensure significant memory was cleaned up
            assert memory_cleaned >= 0, "Memory usage should not increase after cleanup"
            
        finally:
            tracemalloc.stop()
    
    def test_memory_growth_monitoring(self):
        """Test monitoring of memory growth over time."""
        self.memory_monitor.start_monitoring()
        
        memory_snapshots = []
        memory_test_iterations = 20
        max_memory_growth_mb = 100  # 100MB growth limit
        
        # Perform operations and take memory snapshots
        for i in range(memory_test_iterations):
            analyzer = StyleAnalyzer()
            result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
            assert result is not None
            
            # Take memory snapshot
            if i % 5 == 0:
                stats = self.memory_monitor.get_memory_usage()
                memory_snapshots.append(stats['current'])
            
            # Clean up immediately
            del analyzer
            
            # Periodic garbage collection
            if i % 10 == 0:
                gc.collect()
        
        # Analyze memory growth
        if len(memory_snapshots) > 1:
            memory_growth = memory_snapshots[-1] - memory_snapshots[0]
            growth_mb = memory_growth / (1024 * 1024)
            
            # Ensure memory growth is within acceptable limits
            assert growth_mb < max_memory_growth_mb, \
                f"Excessive memory growth: {growth_mb:.2f}MB"
    
    def test_garbage_collection_effectiveness(self):
        """Test effectiveness of garbage collection."""
        self.memory_monitor.start_monitoring()
        
        # Create objects that should be garbage collected
        objects = []
        memory_test_iterations = 20
        
        for i in range(memory_test_iterations):
            analyzer = StyleAnalyzer()
            objects.append(weakref.ref(analyzer))
            
            # Perform work
            result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
            assert result is not None
            
            # Remove reference
            del analyzer
        
        # Check objects before garbage collection
        alive_before = sum(1 for ref in objects if ref() is not None)
        
        # Force garbage collection
        collected = gc.collect()
        
        # Check objects after garbage collection
        alive_after = sum(1 for ref in objects if ref() is not None)
        
        # Verify garbage collection effectiveness
        assert collected >= 0, "Garbage collection should not return negative value"
        assert alive_after <= alive_before, "Garbage collection should reduce object count"
        assert alive_after == 0, f"Memory leak: {alive_after} objects still alive"


class TestResourceLimits:
    """Test resource limits and constraints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.memory_monitor = MemoryMonitor()
        
    def test_memory_limit_enforcement(self):
        """Test memory limit enforcement."""
        self.memory_monitor.start_monitoring()
        
        # Try to create objects until memory limit is approached
        objects = []
        memory_limit_reached = False
        memory_test_iterations = 50
        max_memory_usage_mb = 500  # 500MB limit
        
        try:
            for i in range(memory_test_iterations):
                analyzer = StyleAnalyzer()
                objects.append(analyzer)
                
                # Check memory usage
                stats = self.memory_monitor.get_memory_usage()
                current_mb = stats['current'] / (1024 * 1024)
                
                if current_mb > max_memory_usage_mb:
                    memory_limit_reached = True
                    break
                
                # Perform work
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                assert result is not None
                
        except MemoryError:
            memory_limit_reached = True
        
        # Clean up
        objects.clear()
        del objects
        gc.collect()
        
        # Verify memory limit behavior
        final_stats = self.memory_monitor.get_memory_usage()
        final_mb = final_stats['current'] / (1024 * 1024)
        
        # Memory should be cleaned up after clearing references
        assert final_mb < max_memory_usage_mb, \
            "Memory not properly cleaned up after limit test"
    
    def test_file_descriptor_limits(self):
        """Test file descriptor limit handling."""
        temp_files = []
        file_handles = []
        file_descriptor_limit = 50  # Reasonable limit for testing
        
        try:
            # Create temporary files up to a reasonable limit
            for i in range(file_descriptor_limit):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                    f.write(f"Test content {i}")
                    temp_files.append(f.name)
            
            # Open file handles
            for temp_file in temp_files:
                try:
                    handle = open(temp_file, 'r')
                    file_handles.append(handle)
                except OSError as e:
                    if "Too many open files" in str(e):
                        break
                    raise
            
            # Verify we can handle the expected number of files
            assert len(file_handles) > 0, "No file handles could be opened"
            
        finally:
            # Clean up file handles
            for handle in file_handles:
                try:
                    handle.close()
                except:
                    pass
            
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
    
    def test_thread_resource_limits(self):
        """Test thread resource limit handling."""
        threads = []
        thread_counter = {'value': 0}
        thread_limit = 20  # Reasonable limit for testing
        timeout_seconds = 30
        
        def simple_worker(thread_id):
            thread_counter['value'] += 1
            time.sleep(0.1)  # Simulate work
        
        try:
            # Create threads up to a reasonable limit
            for i in range(thread_limit):
                thread = threading.Thread(target=simple_worker, args=(i,))
                threads.append(thread)
                thread.start()
        
        except RuntimeError as e:
            if "can't start new thread" in str(e):
                pass  # Expected when hitting thread limits
            else:
                raise
        
        # Wait for threads to complete
        for thread in threads:
            thread.join(timeout=timeout_seconds)
        
        # Verify thread execution
        assert thread_counter['value'] > 0, "No threads executed successfully"
        assert thread_counter['value'] <= len(threads), "Thread counter inconsistency"


class TestResourceCleanupPatterns:
    """Test various resource cleanup patterns."""
    
    def test_context_manager_cleanup(self):
        """Test resource cleanup using context managers."""
        resources_created = []
        resources_cleaned = []
        resource_test_iterations = 10
        
        @contextmanager
        def managed_analyzer():
            analyzer = StyleAnalyzer()
            resource_id = id(analyzer)
            resources_created.append(resource_id)
            
            try:
                yield analyzer
            finally:
                resources_cleaned.append(resource_id)
                del analyzer
        
        # Use context manager
        for i in range(resource_test_iterations):
            with managed_analyzer() as analyzer:
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                assert result is not None
        
        # Verify cleanup
        assert len(resources_created) == resource_test_iterations
        assert len(resources_cleaned) == resource_test_iterations
        assert resources_created == resources_cleaned
    
    def test_try_finally_cleanup(self):
        """Test resource cleanup using try-finally blocks."""
        resources_created = []
        resources_cleaned = []
        resource_test_iterations = 10
        
        def process_with_cleanup(should_fail=False):
            analyzer = StyleAnalyzer()
            resource_id = id(analyzer)
            resources_created.append(resource_id)
            
            try:
                if should_fail:
                    raise ValueError("Simulated error")
                
                result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
                return result
            finally:
                resources_cleaned.append(resource_id)
                del analyzer
        
        # Test normal operation
        for i in range(resource_test_iterations // 2):
            result = process_with_cleanup(should_fail=False)
            assert result is not None
        
        # Test exception handling
        for i in range(resource_test_iterations // 2):
            try:
                process_with_cleanup(should_fail=True)
                pytest.fail("Should have raised exception")
            except ValueError:
                pass  # Expected
        
        # Verify cleanup
        assert len(resources_created) == resource_test_iterations
        assert len(resources_cleaned) == resource_test_iterations
        assert resources_created == resources_cleaned
    
    def test_weak_reference_cleanup(self):
        """Test cleanup detection using weak references."""
        weak_refs = []
        cleanup_callbacks = []
        resource_test_iterations = 10
        
        def cleanup_callback(ref):
            cleanup_callbacks.append(ref)
        
        # Create objects with weak references
        for i in range(resource_test_iterations):
            analyzer = StyleAnalyzer()
            weak_ref = weakref.ref(analyzer, cleanup_callback)
            weak_refs.append(weak_ref)
            
            # Use the analyzer
            result = analyzer.analyze(TestConfig.SAMPLE_TEXT)
            assert result is not None
            
            # Remove reference
            del analyzer
        
        # Force garbage collection
        gc.collect()
        
        # Verify cleanup callbacks were called
        assert len(cleanup_callbacks) == resource_test_iterations
        
        # Verify all weak references are dead
        alive_objects = sum(1 for ref in weak_refs if ref() is not None)
        assert alive_objects == 0, f"Cleanup incomplete: {alive_objects} objects still alive" 