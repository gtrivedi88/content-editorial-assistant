"""
Concurrency and Thread Safety Tests for AI Rewriting System

This module contains comprehensive tests for concurrent operations,
thread safety, and multi-processing scenarios in the AI rewriting system.
"""

import pytest
import threading
import multiprocessing
import time
import queue
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
from threading import Lock, Event, Barrier
from collections import defaultdict
import weakref

from tests.test_utils import TestConfig
from rewriter.core import AIRewriter
from style_analyzer.base_analyzer import StyleAnalyzer
from rewriter.models import ModelManager
from app_modules.app_factory import create_app


class ThreadSafeCounter:
    """Thread-safe counter for testing concurrent operations."""
    
    def __init__(self):
        self._value = 0
        self._lock = Lock()
    
    def increment(self):
        with self._lock:
            self._value += 1
    
    def get_value(self):
        with self._lock:
            return self._value


class TestConcurrentAnalysis:
    """Test concurrent style analysis operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = StyleAnalyzer()
        self.counter = ThreadSafeCounter()
        self.results = {}
        self.errors = []
        
    def analyze_text_worker(self, text, thread_id):
        """Worker function for concurrent analysis."""
        try:
            result = self.analyzer.analyze(text)
            self.results[thread_id] = result
            self.counter.increment()
        except Exception as e:
            self.errors.append(f"Thread {thread_id}: {str(e)}")
    
    def test_concurrent_text_analysis(self):
        """Test concurrent text analysis with multiple threads."""
        test_texts = [
            TestConfig.TEST_PROMPT,
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            TestConfig.SAMPLE_RAW_RESPONSE
        ]
        
        threads = []
        for i, text in enumerate(test_texts):
            thread = threading.Thread(
                target=self.analyze_text_worker,
                args=(text, i)
            )
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        # Verify results
        assert len(self.errors) == 0, f"Errors in concurrent analysis: {self.errors}"
        assert self.counter.get_value() == len(test_texts)
        assert len(self.results) == len(test_texts)
    
    def test_concurrent_file_analysis(self):
        """Test concurrent file analysis operations."""
        # Create temporary test files
        test_files = []
        num_threads = 4
        for i in range(num_threads):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                f.write(f"# Test Document {i}\n\nThis is test content for document {i}.")
                test_files.append(f.name)
        
        try:
            def analyze_file_worker(file_path, thread_id):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    result = self.analyzer.analyze(content)
                    self.results[thread_id] = result
                    self.counter.increment()
                except Exception as e:
                    self.errors.append(f"Thread {thread_id}: {str(e)}")
            
            threads = []
            for i, file_path in enumerate(test_files):
                thread = threading.Thread(
                    target=analyze_file_worker,
                    args=(file_path, i)
                )
                threads.append(thread)
            
            # Start and wait for threads
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join(timeout=30)
            
            # Verify results
            assert len(self.errors) == 0, f"Errors in concurrent file analysis: {self.errors}"
            assert self.counter.get_value() == len(test_files)
            
        finally:
            # Clean up temporary files
            for file_path in test_files:
                if os.path.exists(file_path):
                    os.unlink(file_path)
    
    def test_thread_safety_shared_resources(self):
        """Test thread safety when accessing shared resources."""
        shared_data = {'counter': 0, 'results': []}
        lock = Lock()
        num_threads = 10
        
        def worker_with_shared_data(thread_id):
            try:
                # Simulate some processing
                time.sleep(0.01)
                
                with lock:
                    shared_data['counter'] += 1
                    shared_data['results'].append(f"Thread {thread_id} completed")
                
                self.counter.increment()
            except Exception as e:
                self.errors.append(f"Thread {thread_id}: {str(e)}")
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker_with_shared_data, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify thread safety
        assert len(self.errors) == 0, f"Errors in thread safety test: {self.errors}"
        assert shared_data['counter'] == num_threads
        assert len(shared_data['results']) == num_threads
        assert self.counter.get_value() == num_threads


class TestConcurrentRewriting:
    """Test concurrent AI rewriting operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.counter = ThreadSafeCounter()
        self.results = {}
        self.errors = []
        
    @patch('rewriter.models.ModelManager.get_model')
    def test_concurrent_rewriting_operations(self, mock_get_model):
        """Test concurrent rewriting operations."""
        # Mock the model
        mock_model = Mock()
        mock_model.generate_text.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        mock_get_model.return_value = mock_model
        
        rewriter = AIRewriter()
        
        def rewrite_worker(text, thread_id):
            try:
                # Use the correct method name 'rewrite' with required parameters
                result = rewriter.rewrite(text, [], "paragraph", 1)
                self.results[thread_id] = result
                self.counter.increment()
            except Exception as e:
                self.errors.append(f"Thread {thread_id}: {str(e)}")
        
        test_texts = [
            TestConfig.TEST_PROMPT,
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            TestConfig.SAMPLE_RAW_RESPONSE
        ]
        
        threads = []
        for i, text in enumerate(test_texts):
            thread = threading.Thread(target=rewrite_worker, args=(text, i))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        assert len(self.errors) == 0, f"Errors in concurrent rewriting: {self.errors}"
        assert self.counter.get_value() == len(test_texts)
        assert len(self.results) == len(test_texts)
    
    @patch('rewriter.models.ModelManager.get_model')
    def test_model_manager_thread_safety(self, mock_get_model):
        """Test ModelManager thread safety."""
        mock_model = Mock()
        mock_model.generate_text.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        mock_get_model.return_value = mock_model
        
        model_manager = ModelManager()
        num_threads = 8
        
        def model_access_worker(thread_id):
            try:
                model = model_manager.get_model(TestConfig.DEFAULT_MODEL)
                result = model.generate_text(TestConfig.TEST_PROMPT)
                self.results[thread_id] = result
                self.counter.increment()
            except Exception as e:
                self.errors.append(f"Thread {thread_id}: {str(e)}")
        
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=model_access_worker, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify thread safety
        assert len(self.errors) == 0, f"Errors in model manager thread safety: {self.errors}"
        assert self.counter.get_value() == num_threads


class TestRaceConditions:
    """Test for race conditions in concurrent operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.counter = ThreadSafeCounter()
        self.results = defaultdict(list)
        self.errors = []
        
    def test_file_access_race_conditions(self):
        """Test race conditions in file access operations."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(TestConfig.SAMPLE_TEXT)
            temp_file = f.name
        
        try:
            def file_reader_worker(thread_id):
                try:
                    with open(temp_file, 'r') as f:
                        content = f.read()
                    self.results[thread_id].append(content)
                    self.counter.increment()
                except Exception as e:
                    self.errors.append(f"Thread {thread_id}: {str(e)}")
            
            threads = []
            num_threads = 10
            for i in range(num_threads):
                thread = threading.Thread(target=file_reader_worker, args=(i,))
                threads.append(thread)
            
            for thread in threads:
                thread.start()
            
            for thread in threads:
                thread.join(timeout=30)
            
            # Verify no race conditions
            assert len(self.errors) == 0, f"Race condition errors: {self.errors}"
            assert self.counter.get_value() == num_threads
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_configuration_access_race_conditions(self):
        """Test race conditions in configuration access."""
        from src.config import Config
        
        def config_access_worker(thread_id):
            try:
                config = Config()
                # Access various configuration properties
                debug_mode = getattr(config, 'DEBUG', False)
                model_type = getattr(config, 'DEFAULT_MODEL', TestConfig.DEFAULT_MODEL)
                
                self.results[thread_id].extend([debug_mode, model_type])
                self.counter.increment()
            except Exception as e:
                self.errors.append(f"Thread {thread_id}: {str(e)}")
        
        threads = []
        num_threads = 10
        for i in range(num_threads):
            thread = threading.Thread(target=config_access_worker, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify no race conditions
        assert len(self.errors) == 0, f"Configuration race condition errors: {self.errors}"
        assert self.counter.get_value() == num_threads


class TestDeadlockPrevention:
    """Test deadlock prevention in concurrent operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.counter = ThreadSafeCounter()
        self.errors = []
        self.lock1 = Lock()
        self.lock2 = Lock()
        
    def test_ordered_lock_acquisition(self):
        """Test ordered lock acquisition to prevent deadlocks."""
        def worker_ordered_locks(thread_id, reverse_order=False):
            try:
                if reverse_order:
                    # Acquire locks in reverse order
                    with self.lock2:
                        time.sleep(0.01)  # Simulate work
                        with self.lock1:
                            time.sleep(0.01)  # Simulate work
                else:
                    # Acquire locks in normal order
                    with self.lock1:
                        time.sleep(0.01)  # Simulate work
                        with self.lock2:
                            time.sleep(0.01)  # Simulate work
                
                self.counter.increment()
            except Exception as e:
                self.errors.append(f"Thread {thread_id}: {str(e)}")
        
        threads = []
        num_threads = 10
        for i in range(num_threads):
            reverse = i % 2 == 1  # Alternate order
            thread = threading.Thread(
                target=worker_ordered_locks,
                args=(i, reverse)
            )
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        # Set a reasonable timeout to detect deadlocks
        for thread in threads:
            thread.join(timeout=30)
            if thread.is_alive():
                self.errors.append(f"Potential deadlock detected - thread still alive")
        
        # Verify no deadlocks
        assert len(self.errors) == 0, f"Deadlock errors: {self.errors}"
        assert self.counter.get_value() == num_threads


class TestMultiprocessing:
    """Test multiprocessing scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.results = []
        self.errors = []
    
    def process_worker(self, text, process_id, result_queue, error_queue):
        """Worker function for multiprocessing."""
        try:
            # Simulate analysis work
            analyzer = StyleAnalyzer()
            result = analyzer.analyze(text)
            result_queue.put((process_id, result))
        except Exception as e:
            error_queue.put((process_id, str(e)))
    
    def test_multiprocess_analysis(self):
        """Test multiprocess text analysis."""
        if multiprocessing.get_start_method() != 'spawn':
            pytest.skip("Multiprocessing test requires spawn method")
        
        test_texts = [
            TestConfig.TEST_PROMPT,
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            TestConfig.SAMPLE_RAW_RESPONSE
        ]
        
        result_queue = multiprocessing.Queue()
        error_queue = multiprocessing.Queue()
        processes = []
        
        for i, text in enumerate(test_texts):
            process = multiprocessing.Process(
                target=self.process_worker,
                args=(text, i, result_queue, error_queue)
            )
            processes.append(process)
        
        # Start all processes
        for process in processes:
            process.start()
        
        # Wait for all processes to complete
        for process in processes:
            process.join(timeout=30)
        
        # Collect results
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        errors = []
        while not error_queue.empty():
            errors.append(error_queue.get())
        
        # Verify results
        assert len(errors) == 0, f"Errors in multiprocessing: {errors}"
        assert len(results) == len(test_texts)


class TestMemoryLeaks:
    """Test for memory leaks in concurrent operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.weak_refs = []
        self.counter = ThreadSafeCounter()
        
    def test_object_cleanup_in_threads(self):
        """Test proper object cleanup in threaded operations."""
        def worker_with_objects(thread_id):
            analyzer = StyleAnalyzer()
            # Create weak reference to track object lifecycle
            weak_ref = weakref.ref(analyzer)
            self.weak_refs.append(weak_ref)
            
            # Simulate work
            result = analyzer.analyze(TestConfig.TEST_PROMPT)
            self.counter.increment()
            
            # Explicitly delete reference
            del analyzer
        
        threads = []
        num_threads = 10
        for i in range(num_threads):
            thread = threading.Thread(target=worker_with_objects, args=(i,))
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Check for memory leaks
        alive_objects = sum(1 for ref in self.weak_refs if ref() is not None)
        assert alive_objects == 0, f"Memory leak detected: {alive_objects} objects still alive"
        assert self.counter.get_value() == num_threads


class TestConcurrentWebRequests:
    """Test concurrent web request handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app, self.socketio = create_app()
        self.client = self.app.test_client()
        self.counter = ThreadSafeCounter()
        self.responses = {}
        self.errors = []
    
    def web_request_worker(self, endpoint, data, thread_id):
        """Worker function for concurrent web requests."""
        try:
            with self.app.test_request_context():
                if data:
                    response = self.client.post(endpoint, data=data)
                else:
                    response = self.client.get(endpoint)
                
                self.responses[thread_id] = {
                    'status_code': response.status_code,
                    'data': response.get_json() if response.is_json else response.data
                }
                self.counter.increment()
        except Exception as e:
            self.errors.append(f"Thread {thread_id}: {str(e)}")
    
    def test_concurrent_health_checks(self):
        """Test concurrent health check requests."""
        threads = []
        num_threads = 8
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.web_request_worker,
                args=('/health', None, i)
            )
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        assert len(self.errors) == 0, f"Errors in concurrent health checks: {self.errors}"
        assert self.counter.get_value() == num_threads
        
        # Verify all responses are successful
        for thread_id, response in self.responses.items():
            assert response['status_code'] == 200, f"Thread {thread_id} failed health check"
    
    def test_concurrent_analysis_requests(self):
        """Test concurrent analysis requests."""
        test_data = {
            'text': TestConfig.SAMPLE_TEXT,
            'format': TestConfig.FORMAT_MARKDOWN
        }
        
        threads = []
        num_threads = 6
        for i in range(num_threads):
            thread = threading.Thread(
                target=self.web_request_worker,
                args=('/analyze', test_data, i)
            )
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        assert len(self.errors) == 0, f"Errors in concurrent analysis: {self.errors}"
        assert self.counter.get_value() == num_threads 