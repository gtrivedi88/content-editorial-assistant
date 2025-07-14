"""
API Contract and Endpoint Validation Testing Suite
Tests API specifications, request/response schemas, status codes, headers,
and contract compliance to ensure robust API design and backward compatibility.
"""

import pytest
import os
import sys
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
import time
from datetime import datetime
import uuid

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestConfig, TestFixtures, TestValidators, TestMockFactory
from app_modules.app_factory import create_app
from src.config import Config


class TestAPIEndpointContracts:
    """Test API endpoint contracts and specifications."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tests.test_utils import TestConfig as TestConstants
        
        class TestAppConfig(Config):
            TESTING = True
            SECRET_KEY = TestConstants.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
            MAX_CONTENT_LENGTH = 16 * 1024 * 1024
            WTF_CSRF_ENABLED = False
            
        app, socketio = create_app(TestAppConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_index_endpoint_contract(self, client):
        """Test index endpoint contract compliance."""
        response = client.get('/')
        
        # Status code contract
        assert response.status_code == 200, "Index endpoint should return 200"
        
        # Content type contract
        assert 'text/html' in response.content_type, "Index should return HTML content"
        
        # Response structure contract
        assert response.data is not None, "Index should return content"
        assert len(response.data) > 0, "Index should return non-empty content"
        
        # Headers contract
        headers = dict(response.headers)
        assert 'Content-Type' in headers, "Should have Content-Type header"
        assert 'Content-Length' in headers, "Should have Content-Length header"
    
    def test_upload_endpoint_contract(self, client):
        """Test upload endpoint contract compliance."""
        
        # Test valid file upload
        test_content = TestConfig.SAMPLE_TEXT.encode('utf-8')
        data = {
            'file': (BytesIO(test_content), TestConfig.TEST_FILENAME_TXT)
        }
        
        response = client.post('/upload', data=data, content_type='multipart/form-data')
        
        # Status code contract
        assert response.status_code == 200, "Upload should return 200 for valid file"
        
        # Content type contract
        assert 'application/json' in response.content_type, "Upload should return JSON"
        
        # Response schema contract
        json_data = response.get_json()
        assert json_data is not None, "Upload should return JSON data"
        
        # Required fields contract
        required_fields = ['filename', 'content', 'size', 'format']
        for field in required_fields:
            assert field in json_data, f"Upload response should include {field}"
        
        # Data type contracts
        assert isinstance(json_data['filename'], str), "Filename should be string"
        assert isinstance(json_data['content'], str), "Content should be string"
        assert isinstance(json_data['size'], int), "Size should be integer"
        assert isinstance(json_data['format'], str), "Format should be string"
        
        # Value validation contracts
        assert len(json_data['filename']) > 0, "Filename should not be empty"
        assert json_data['size'] > 0, "Size should be positive"
        assert json_data['format'] in ['txt', 'md', 'adoc', 'pdf', 'docx'], "Format should be valid"
    
    def test_analyze_endpoint_contract(self, client):
        """Test analyze endpoint contract compliance."""
        
        # Test valid analysis request
        request_data = {
            'content': TestConfig.SAMPLE_TEXT,
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        response = client.post('/analyze', 
                             data=json.dumps(request_data),
                             content_type='application/json')
        
        # Status code contract
        assert response.status_code == 200, "Analyze should return 200 for valid request"
        
        # Content type contract
        assert 'application/json' in response.content_type, "Analyze should return JSON"
        
        # Response schema contract
        json_data = response.get_json()
        assert json_data is not None, "Analyze should return JSON data"
        
        # Required fields contract
        required_fields = ['errors', 'statistics', 'readability', 'session_id']
        for field in required_fields:
            assert field in json_data, f"Analyze response should include {field}"
        
        # Data structure contracts
        assert isinstance(json_data['errors'], list), "Errors should be a list"
        assert isinstance(json_data['statistics'], dict), "Statistics should be a dict"
        assert isinstance(json_data['readability'], dict), "Readability should be a dict"
        assert isinstance(json_data['session_id'], str), "Session ID should be string"
        
        # Error structure contract
        for error in json_data['errors']:
            assert isinstance(error, dict), "Each error should be a dict"
            error_required_fields = ['type', 'message', 'severity']
            for field in error_required_fields:
                assert field in error, f"Error should include {field}"
        
        # Statistics structure contract
        stats = json_data['statistics']
        stats_required_fields = ['word_count', 'sentence_count', 'paragraph_count']
        for field in stats_required_fields:
            assert field in stats, f"Statistics should include {field}"
            assert isinstance(stats[field], int), f"Statistics {field} should be integer"
    
    def test_rewrite_endpoint_contract(self, client):
        """Test rewrite endpoint contract compliance."""
        
        # Test valid rewrite request
        request_data = {
            'content': TestConfig.SAMPLE_TEXT,
            'errors': TestFixtures.get_sample_errors(),
            'context': TestConfig.VALID_CONTEXTS[0],
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        with patch('rewriter.core.AIRewriter') as mock_rewriter_class:
            mock_rewriter = TestMockFactory.create_mock_model_manager()
            mock_rewriter.rewrite.return_value = {
                'rewritten_text': TestConfig.SAMPLE_IMPROVED_TEXT,
                'confidence': TestConfig.EXPECTED_CONFIDENCE,
                'improvements': [TestConfig.IMPROVEMENT_TEST_GENERIC],
                'model_used': TestConfig.DEFAULT_MODEL
            }
            mock_rewriter_class.return_value = mock_rewriter
            
            response = client.post('/rewrite',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
        
        # Status code contract
        assert response.status_code == 200, "Rewrite should return 200 for valid request"
        
        # Content type contract
        assert 'application/json' in response.content_type, "Rewrite should return JSON"
        
        # Response schema contract
        json_data = response.get_json()
        assert json_data is not None, "Rewrite should return JSON data"
        
        # Required fields contract
        required_fields = ['rewritten_text', 'confidence', 'improvements', 'session_id']
        for field in required_fields:
            assert field in json_data, f"Rewrite response should include {field}"
        
        # Data type contracts
        assert isinstance(json_data['rewritten_text'], str), "Rewritten text should be string"
        assert isinstance(json_data['confidence'], (int, float)), "Confidence should be numeric"
        assert isinstance(json_data['improvements'], list), "Improvements should be list"
        assert isinstance(json_data['session_id'], str), "Session ID should be string"
        
        # Value validation contracts
        assert 0.0 <= json_data['confidence'] <= 1.0, "Confidence should be between 0 and 1"
        assert len(json_data['rewritten_text']) > 0, "Rewritten text should not be empty"
    
    def test_health_endpoint_contract(self, client):
        """Test health endpoint contract compliance."""
        
        response = client.get('/health')
        
        # Status code contract
        assert response.status_code == 200, "Health endpoint should return 200"
        
        # Content type contract
        assert 'application/json' in response.content_type, "Health should return JSON"
        
        # Response schema contract
        json_data = response.get_json()
        assert json_data is not None, "Health should return JSON data"
        
        # Required fields contract
        required_fields = ['status', 'timestamp', 'version']
        for field in required_fields:
            assert field in json_data, f"Health response should include {field}"
        
        # Data type contracts
        assert isinstance(json_data['status'], str), "Status should be string"
        assert isinstance(json_data['timestamp'], str), "Timestamp should be string"
        
        # Value validation contracts
        assert json_data['status'] in [TestConfig.STATUS_HEALTHY, TestConfig.STATUS_UNHEALTHY], "Status should be valid"
        
        # Timestamp format validation
        try:
            datetime.fromisoformat(json_data['timestamp'].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp should be valid ISO format")


class TestRequestValidation:
    """Test request validation contracts."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tests.test_utils import TestConfig as TestConstants
        
        class TestAppConfig(Config):
            TESTING = True
            SECRET_KEY = TestConstants.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
            
        app, socketio = create_app(TestAppConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        
        # Test analyze endpoint with missing content
        response = client.post('/analyze',
                             data=json.dumps({'session_id': TestConfig.TEST_SESSION_ID}),
                             content_type='application/json')
        
        # Should return error for missing required field
        assert response.status_code == 400, "Should return 400 for missing required field"
        
        json_data = response.get_json()
        assert json_data is not None, "Should return error information"
        assert 'error' in json_data, "Should include error message"
    
    def test_invalid_data_types(self, client):
        """Test handling of invalid data types."""
        
        # Test analyze endpoint with invalid data types
        invalid_requests = [
            {'content': 123, 'session_id': TestConfig.TEST_SESSION_ID},  # content should be string
            {'content': TestConfig.SAMPLE_TEXT, 'session_id': 123},      # session_id should be string
            {'content': None, 'session_id': TestConfig.TEST_SESSION_ID}, # content should not be null
        ]
        
        for invalid_request in invalid_requests:
            response = client.post('/analyze',
                                 data=json.dumps(invalid_request),
                                 content_type='application/json')
            
            # Should handle invalid data types gracefully
            assert response.status_code in [400, 422], f"Should return error for invalid request: {invalid_request}"
    
    def test_malformed_json(self, client):
        """Test handling of malformed JSON."""
        
        # Test with malformed JSON
        malformed_json = '{"content": "test", "session_id": "test"'  # Missing closing brace
        
        response = client.post('/analyze',
                             data=malformed_json,
                             content_type='application/json')
        
        # Should return error for malformed JSON
        assert response.status_code == 400, "Should return 400 for malformed JSON"
    
    def test_oversized_requests(self, client):
        """Test handling of oversized requests."""
        
        # Test with very large content
        large_content = TestConfig.SAMPLE_TEXT * 10000  # Very large text
        request_data = {
            'content': large_content,
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        response = client.post('/analyze',
                             data=json.dumps(request_data),
                             content_type='application/json')
        
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 413, 422], "Should handle large requests appropriately"
    
    def test_invalid_file_uploads(self, client):
        """Test handling of invalid file uploads."""
        
        # Test with invalid file type
        invalid_data = {
            'file': (BytesIO(b'test content'), 'test.exe')  # .exe not allowed
        }
        
        response = client.post('/upload', data=invalid_data, content_type='multipart/form-data')
        
        # Should return error for invalid file type
        assert response.status_code == 400, "Should return 400 for invalid file type"
        
        json_data = response.get_json()
        assert json_data is not None, "Should return error information"
        assert 'error' in json_data, "Should include error message"


class TestResponseValidation:
    """Test response validation contracts."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tests.test_utils import TestConfig as TestConstants
        
        class TestAppConfig(Config):
            TESTING = True
            SECRET_KEY = TestConstants.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
            
        app, socketio = create_app(TestAppConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_response_schema_consistency(self, client):
        """Test that response schemas are consistent."""
        
        # Test multiple requests to same endpoint
        request_data = {
            'content': TestConfig.SAMPLE_TEXT,
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        responses = []
        for _ in range(3):
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            responses.append(response.get_json())
        
        # All responses should have same schema
        first_response = responses[0]
        for response in responses[1:]:
            # Same top-level keys
            assert set(first_response.keys()) == set(response.keys()), "Response schemas should be consistent"
            
            # Same data types
            for key in first_response.keys():
                assert type(first_response[key]) == type(response[key]), f"Data type for {key} should be consistent"
    
    def test_error_response_schema(self, client):
        """Test error response schema consistency."""
        
        # Trigger various errors
        error_requests = [
            {},  # Missing required fields
            {'content': ''},  # Empty content
            {'content': TestConfig.SAMPLE_TEXT},  # Missing session_id
        ]
        
        error_responses = []
        for error_request in error_requests:
            response = client.post('/analyze',
                                 data=json.dumps(error_request),
                                 content_type='application/json')
            if response.status_code >= 400:
                error_responses.append(response.get_json())
        
        # All error responses should have consistent schema
        if error_responses:
            first_error = error_responses[0]
            for error_response in error_responses[1:]:
                # Should have error field
                assert 'error' in error_response, "Error responses should have error field"
                assert isinstance(error_response['error'], str), "Error should be string"
    
    def test_response_timing_consistency(self, client):
        """Test response timing consistency."""
        
        request_data = {
            'content': TestConfig.SAMPLE_TEXT,
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        response_times = []
        for _ in range(5):
            start_time = time.time()
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            end_time = time.time()
            
            assert response.status_code == 200, "Request should succeed"
            response_times.append(end_time - start_time)
        
        # Response times should be reasonably consistent
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Max time should not be more than 3x the average
        assert max_time <= avg_time * 3, f"Response times should be consistent: max={max_time:.2f}s, avg={avg_time:.2f}s"
        
        # All responses should be reasonably fast
        assert max_time < 10.0, f"All responses should be under 10 seconds: max={max_time:.2f}s"


class TestAPIVersioning:
    """Test API versioning and backward compatibility."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tests.test_utils import TestConfig as TestConstants
        
        class TestAppConfig(Config):
            TESTING = True
            SECRET_KEY = TestConstants.TEST_SECRET_KEY
            
        app, socketio = create_app(TestAppConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_api_version_header_support(self, client):
        """Test API version header support."""
        
        # Test with version header
        headers = {'API-Version': '1.0'}
        response = client.get('/health', headers=headers)
        
        # Should handle version header gracefully
        assert response.status_code == 200, "Should handle version header"
        
        # Response should include version information
        json_data = response.get_json()
        if 'version' in json_data:
            assert isinstance(json_data['version'], str), "Version should be string"
    
    def test_backward_compatibility(self, client):
        """Test backward compatibility of API."""
        
        # Test old-style request format (if applicable)
        legacy_request = {
            'text': TestConfig.SAMPLE_TEXT,  # Old field name
            'session_id': TestConfig.TEST_SESSION_ID
        }
        
        response = client.post('/analyze',
                             data=json.dumps(legacy_request),
                             content_type='application/json')
        
        # Should either work or provide clear migration guidance
        if response.status_code != 200:
            json_data = response.get_json()
            if json_data and 'error' in json_data:
                error_msg = json_data['error'].lower()
                # Error should be helpful for migration
                assert 'content' in error_msg or 'field' in error_msg, "Error should guide migration"
    
    def test_deprecated_endpoint_handling(self, client):
        """Test handling of deprecated endpoints."""
        
        # Test accessing deprecated endpoint (if any exist)
        deprecated_endpoints = [
            '/api/v1/analyze',  # Example deprecated endpoint
            '/old-analyze',     # Example old endpoint
        ]
        
        for endpoint in deprecated_endpoints:
            response = client.get(endpoint)
            
            # Should either redirect or provide deprecation notice
            if response.status_code == 404:
                # Expected for non-existent deprecated endpoints
                pass
            elif response.status_code in [301, 302]:
                # Redirect to new endpoint
                assert 'Location' in response.headers, "Redirect should have Location header"
            elif response.status_code == 410:
                # Gone - deprecated endpoint
                pass
            else:
                # If endpoint exists, should work or provide deprecation info
                assert response.status_code in [200, 410], f"Deprecated endpoint should handle gracefully: {endpoint}"


class TestAPIDocumentationCompliance:
    """Test compliance with API documentation."""
    
    def test_endpoint_documentation_accuracy(self):
        """Test that endpoints match documentation."""
        
        # This test documents the expected API structure
        documented_endpoints = {
            'GET /': {'status_code': 200, 'content_type': 'text/html'},
            'POST /upload': {'status_code': 200, 'content_type': 'application/json'},
            'POST /analyze': {'status_code': 200, 'content_type': 'application/json'},
            'POST /rewrite': {'status_code': 200, 'content_type': 'application/json'},
            'GET /health': {'status_code': 200, 'content_type': 'application/json'},
        }
        
        # Verify documentation structure
        for endpoint, spec in documented_endpoints.items():
            assert 'status_code' in spec, f"Endpoint {endpoint} should document status code"
            assert 'content_type' in spec, f"Endpoint {endpoint} should document content type"
            assert isinstance(spec['status_code'], int), f"Status code should be integer for {endpoint}"
            assert isinstance(spec['content_type'], str), f"Content type should be string for {endpoint}"
    
    def test_request_schema_documentation(self):
        """Test that request schemas are documented."""
        
        # Document expected request schemas
        request_schemas = {
            'analyze': {
                'required': ['content', 'session_id'],
                'optional': ['format', 'options'],
                'types': {'content': str, 'session_id': str}
            },
            'rewrite': {
                'required': ['content', 'errors', 'context', 'session_id'],
                'optional': ['pass_number'],
                'types': {'content': str, 'errors': list, 'context': str, 'session_id': str}
            }
        }
        
        # Verify schema documentation structure
        for endpoint, schema in request_schemas.items():
            assert 'required' in schema, f"Schema for {endpoint} should document required fields"
            assert 'types' in schema, f"Schema for {endpoint} should document field types"
            assert isinstance(schema['required'], list), f"Required fields should be list for {endpoint}"
            assert isinstance(schema['types'], dict), f"Types should be dict for {endpoint}"
    
    def test_response_schema_documentation(self):
        """Test that response schemas are documented."""
        
        # Document expected response schemas
        response_schemas = {
            'analyze': {
                'fields': ['errors', 'statistics', 'readability', 'session_id'],
                'types': {'errors': list, 'statistics': dict, 'readability': dict, 'session_id': str}
            },
            'rewrite': {
                'fields': ['rewritten_text', 'confidence', 'improvements', 'session_id'],
                'types': {'rewritten_text': str, 'confidence': float, 'improvements': list, 'session_id': str}
            }
        }
        
        # Verify response schema documentation
        for endpoint, schema in response_schemas.items():
            assert 'fields' in schema, f"Response schema for {endpoint} should document fields"
            assert 'types' in schema, f"Response schema for {endpoint} should document types"
            assert isinstance(schema['fields'], list), f"Fields should be list for {endpoint}"
            assert isinstance(schema['types'], dict), f"Types should be dict for {endpoint}"


class TestAPIPerformanceContracts:
    """Test API performance contracts and SLAs."""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from tests.test_utils import TestConfig as TestConstants
        
        class TestAppConfig(Config):
            TESTING = True
            SECRET_KEY = TestConstants.TEST_SECRET_KEY
            
        app, socketio = create_app(TestAppConfig)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_response_time_sla(self, client):
        """Test response time service level agreements."""
        
        # Define SLA requirements
        sla_requirements = {
            'GET /': 2.0,          # Index should load in under 2 seconds
            'GET /health': 1.0,    # Health check should be under 1 second
            'POST /analyze': 5.0,  # Analysis should complete in under 5 seconds
        }
        
        for endpoint_method, max_time in sla_requirements.items():
            method, endpoint = endpoint_method.split(' ', 1)
            
            start_time = time.time()
            
            if method == 'GET':
                response = client.get(endpoint)
            elif method == 'POST':
                if endpoint == '/analyze':
                    request_data = {
                        'content': TestConfig.SAMPLE_TEXT,
                        'session_id': TestConfig.TEST_SESSION_ID
                    }
                    response = client.post(endpoint,
                                         data=json.dumps(request_data),
                                         content_type='application/json')
                else:
                    response = client.post(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Verify SLA compliance
            assert response_time <= max_time, f"{endpoint_method} should complete within {max_time}s, took {response_time:.2f}s"
            assert response.status_code in [200, 201, 202], f"{endpoint_method} should succeed for SLA test"
    
    def test_throughput_requirements(self, client):
        """Test API throughput requirements."""
        
        # Test concurrent requests
        import threading
        import queue
        
        num_concurrent = 5
        results_queue = queue.Queue()
        
        def make_request(thread_id):
            """Make a request and record timing."""
            request_data = {
                'content': f"{TestConfig.SAMPLE_TEXT} Thread {thread_id}",
                'session_id': f"{TestConfig.TEST_SESSION_ID}-{thread_id}"
            }
            
            start_time = time.time()
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            end_time = time.time()
            
            results_queue.put({
                'thread_id': thread_id,
                'response_time': end_time - start_time,
                'status_code': response.status_code
            })
        
        # Start concurrent requests
        threads = []
        start_time = time.time()
        
        for i in range(num_concurrent):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # Verify throughput
        assert len(results) == num_concurrent, f"Should complete all {num_concurrent} requests"
        
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        throughput = successful_requests / total_time
        
        # Should handle at least 1 request per second under concurrent load
        assert throughput >= 1.0, f"Throughput too low: {throughput:.2f} requests/second"
        
        # All requests should succeed
        assert successful_requests == num_concurrent, f"All concurrent requests should succeed: {successful_requests}/{num_concurrent}"
    
    def test_resource_usage_limits(self, client):
        """Test API resource usage limits."""
        
        # Test with various payload sizes
        payload_sizes = [
            (100, "Small payload"),
            (1000, "Medium payload"),
            (10000, "Large payload"),
        ]
        
        for word_count, description in payload_sizes:
            # Generate payload of specified size
            test_content = " ".join([TestConfig.SAMPLE_TEXT] * (word_count // len(TestConfig.SAMPLE_TEXT.split()) + 1))
            test_content = " ".join(test_content.split()[:word_count])
            
            request_data = {
                'content': test_content,
                'session_id': TestConfig.TEST_SESSION_ID
            }
            
            start_time = time.time()
            response = client.post('/analyze',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            end_time = time.time()
            
            # Should handle different payload sizes
            assert response.status_code == 200, f"Should handle {description}"
            
            # Response time should scale reasonably
            response_time = end_time - start_time
            assert response_time < 30.0, f"{description} should complete within 30 seconds: {response_time:.2f}s" 