"""
Detailed Application Factory Tests
Comprehensive testing of the Flask application factory with all configurations,
service initialization, fallback mechanisms, and error handling scenarios.
"""

import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, MagicMock, patch
from flask import Flask
from flask_socketio import SocketIO

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_modules.app_factory import create_app, configure_upload_folder, initialize_services
from src.config import Config
from tests.test_utils import TestConfig, TestFixtures, TestValidators


class TestAppFactoryDetailed:
    """Detailed tests for Flask application factory."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        class TempConfig(Config):
            TESTING = True
            SECRET_KEY = TestConfig.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
            WTF_CSRF_ENABLED = False
            
        yield TempConfig
        
        # Cleanup
        if hasattr(TempConfig, 'UPLOAD_FOLDER') and os.path.exists(TempConfig.UPLOAD_FOLDER):
            shutil.rmtree(TempConfig.UPLOAD_FOLDER)
    
    def test_create_app_with_all_configs(self, temp_config):
        """Test app creation with complete configuration."""
        app, socketio = create_app(temp_config)
        
        # Validate Flask app
        assert isinstance(app, Flask), "Should create Flask app instance"
        assert app.config['TESTING'] is True, "Should apply testing configuration"
        assert app.config['SECRET_KEY'] == TestConfig.TEST_SECRET_KEY, "Should set secret key"
        
        # Validate SocketIO
        assert isinstance(socketio, SocketIO), "Should create SocketIO instance"
        assert hasattr(app, 'socketio'), "Should attach SocketIO to app"
        
        # Validate services
        assert hasattr(app, 'services'), "Should attach services to app"
        services = getattr(app, 'services', {})
        assert 'document_processor' in services, "Should have document processor"
        assert 'style_analyzer' in services, "Should have style analyzer"
        assert 'ai_rewriter' in services, "Should have AI rewriter"
    
    def test_service_initialization_order(self, temp_config):
        """Test that services are initialized in correct order."""
        with patch('app_modules.app_factory.initialize_services') as mock_init:
            mock_services = {
                'document_processor': Mock(),
                'style_analyzer': Mock(), 
                'ai_rewriter': Mock()
            }
            mock_init.return_value = mock_services
            
            app, socketio = create_app(temp_config)
            
            # Services should be initialized
            mock_init.assert_called_once()
            
            # Services should be attached to app
            assert getattr(app, 'services', {}) == mock_services
    
    def test_fallback_service_activation(self, temp_config):
        """Test fallback services when dependencies are unavailable."""
        # Mock missing dependencies
        with patch('app_modules.app_factory.initialize_services') as mock_init:
            # Simulate services with fallback
            fallback_services = {
                'document_processor': Mock(),
                'style_analyzer': Mock(spec=['analyze']),  # Fallback analyzer
                'ai_rewriter': Mock(spec=['rewrite'])     # Fallback rewriter
            }
            mock_init.return_value = fallback_services
            
            app, socketio = create_app(temp_config)
            
            # Should still create app successfully
            assert isinstance(app, Flask)
            assert getattr(app, 'services', None) is not None
            
            # Services should be functional (even if fallback)
            services = getattr(app, 'services', {})
            assert hasattr(services['style_analyzer'], 'analyze')
            assert hasattr(services['ai_rewriter'], 'rewrite')
    
    def test_logging_configuration(self, temp_config):
        """Test logging setup and configuration."""
        with patch('app_modules.app_factory.setup_logging') as mock_logging:
            app, socketio = create_app(temp_config)
            
            # Logging should be configured
            mock_logging.assert_called_once_with(app)
            
            # App should have logger
            assert app.logger is not None
    
    def test_error_handler_registration(self, temp_config):
        """Test error handler registration."""
        with patch('app_modules.app_factory.setup_error_handlers') as mock_error_handlers:
            app, socketio = create_app(temp_config)
            
            # Error handlers should be registered
            mock_error_handlers.assert_called_once_with(app)
    
    def test_websocket_setup(self, temp_config):
        """Test WebSocket configuration and setup."""
        with patch('app_modules.app_factory.setup_websocket_handlers') as mock_ws_setup:
            app, socketio = create_app(temp_config)
            
            # WebSocket handlers should be set up
            mock_ws_setup.assert_called_once_with(socketio)
            
            # SocketIO should be configured properly
            assert isinstance(socketio, SocketIO)
            assert getattr(socketio, 'async_mode', None) == 'threading'
    
    def test_cleanup_handlers(self, temp_config):
        """Test cleanup handler registration."""
        with patch('app_modules.app_factory.register_cleanup_handlers') as mock_cleanup:
            app, socketio = create_app(temp_config)
            
            # Cleanup handlers should be registered
            mock_cleanup.assert_called_once()
    
    def test_teardown_scenarios(self, temp_config):
        """Test application teardown scenarios."""
        app, socketio = create_app(temp_config)
        
        # Test app context teardown
        with app.app_context():
            # Should not raise errors
            pass
        
        # Test request context teardown
        with app.test_request_context():
            # Should not raise errors
            pass
    
    def test_configure_upload_folder_success(self, temp_config):
        """Test successful upload folder configuration."""
        app, socketio = create_app(temp_config)
        
        # Configure upload folder
        configure_upload_folder(app)
        
        # Should create upload folder
        assert os.path.exists(app.config['UPLOAD_FOLDER'])
        
        # Should be writable
        test_file = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        assert os.path.exists(test_file)
    
    def test_configure_upload_folder_permissions(self, temp_config):
        """Test upload folder permission handling."""
        app, socketio = create_app(temp_config)
        
        # Test with read-only directory
        readonly_dir = tempfile.mkdtemp()
        try:
            os.chmod(readonly_dir, 0o444)  # Read-only
            app.config['UPLOAD_FOLDER'] = readonly_dir
            
            # Should handle permission errors gracefully
            configure_upload_folder(app)
            
        finally:
            os.chmod(readonly_dir, 0o755)  # Restore permissions
            shutil.rmtree(readonly_dir)
    
    def test_services_health_check(self, temp_config):
        """Test service health checking."""
        app, socketio = create_app(temp_config)
        
        # All services should be available
        services = getattr(app, 'services', {})
        
        # Document processor health
        doc_processor = services['document_processor']
        assert hasattr(doc_processor, 'allowed_file'), "Document processor should have allowed_file method"
        assert hasattr(doc_processor, 'extract_text'), "Document processor should have extract_text method"
        
        # Style analyzer health
        style_analyzer = services['style_analyzer']
        assert hasattr(style_analyzer, 'analyze'), "Style analyzer should have analyze method"
        
        # AI rewriter health
        ai_rewriter = services['ai_rewriter']
        assert hasattr(ai_rewriter, 'rewrite'), "AI rewriter should have rewrite method"
    
    def test_app_config_validation(self, temp_config):
        """Test application configuration validation."""
        app, socketio = create_app(temp_config)
        
        # Required config values should be set
        required_configs = [
            'SECRET_KEY', 'UPLOAD_FOLDER', 'MAX_CONTENT_LENGTH', 
            'ALLOWED_EXTENSIONS'
        ]
        
        for config_key in required_configs:
            assert config_key in app.config, f"Missing required config: {config_key}"
            assert app.config[config_key] is not None, f"Config {config_key} should not be None"
    
    def test_cors_configuration(self, temp_config):
        """Test CORS configuration."""
        app, socketio = create_app(temp_config)
        
        # CORS should be configured
        assert 'CORS' in app.extensions or hasattr(app, 'cors'), "CORS should be configured"
    
    def test_template_and_static_paths(self, temp_config):
        """Test template and static file path configuration."""
        app, socketio = create_app(temp_config)
        
        # Template folder should be configured
        assert app.template_folder is not None, "Template folder should be configured"
        
        # Static folder should be configured if exists
        if app.static_folder:
            assert os.path.exists(app.static_folder) or app.static_folder is None
    
    def test_development_vs_production_config(self):
        """Test different configurations for development and production."""
        
        # Development config
        class DevConfig(Config):
            TESTING = True
            DEBUG = True
            SECRET_KEY = TestConfig.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
        
        # Production config  
        class ProdConfig(Config):
            TESTING = False
            DEBUG = False
            SECRET_KEY = TestConfig.PRODUCTION_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
        
        try:
            # Test development app
            dev_app, dev_socketio = create_app(DevConfig)
            assert dev_app.config['DEBUG'] is True
            assert dev_app.config['TESTING'] is True
            
            # Test production app
            prod_app, prod_socketio = create_app(ProdConfig)
            assert prod_app.config['DEBUG'] is False
            assert prod_app.config['TESTING'] is False
            
        finally:
            # Cleanup
            if os.path.exists(DevConfig.UPLOAD_FOLDER):
                shutil.rmtree(DevConfig.UPLOAD_FOLDER)
            if os.path.exists(ProdConfig.UPLOAD_FOLDER):
                shutil.rmtree(ProdConfig.UPLOAD_FOLDER)
    
    def test_service_initialization_errors(self, temp_config):
        """Test service initialization error handling."""
        
        # Mock service initialization failure
        with patch('app_modules.app_factory.initialize_services') as mock_init:
            mock_init.side_effect = Exception("Service initialization failed")
            
            # App creation should still succeed with fallback
            app, socketio = create_app(temp_config)
            
            assert isinstance(app, Flask), "Should create app even with service errors"
            
            # Should have fallback services
            assert hasattr(app, 'services'), "Should have services attribute"
    
    def test_concurrent_app_creation(self, temp_config):
        """Test concurrent application creation."""
        import threading
        import time
        
        apps = []
        errors = []
        
        def create_app_thread():
            try:
                app, socketio = create_app(temp_config)
                apps.append(app)
            except Exception as e:
                errors.append(e)
        
        # Create multiple apps concurrently
        threads = [threading.Thread(target=create_app_thread) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed
        assert len(errors) == 0, f"Concurrent app creation failed: {errors}"
        assert len(apps) == 3, "Should create all apps successfully"
        
        # All apps should be valid
        for app in apps:
            assert isinstance(app, Flask)
            assert hasattr(app, 'services')


class TestServiceInitializationDetailed:
    """Detailed tests for service initialization."""
    
    def test_initialize_services_with_all_dependencies(self):
        """Test service initialization with all dependencies available."""
        
        # Mock all dependencies as available
        with patch('app_modules.app_factory.DocumentProcessor') as mock_doc_proc:
            with patch('app_modules.app_factory.StyleAnalyzer') as mock_analyzer:
                with patch('app_modules.app_factory.AIRewriter') as mock_rewriter:
                    
                    # Configure mocks
                    mock_doc_proc.return_value = Mock()
                    mock_analyzer.return_value = Mock()
                    mock_rewriter.return_value = Mock()
                    
                    services = initialize_services()
                    
                    # All services should be initialized
                    assert 'document_processor' in services
                    assert 'style_analyzer' in services
                    assert 'ai_rewriter' in services
                    
                    # Should use real implementations
                    mock_doc_proc.assert_called_once()
                    mock_analyzer.assert_called_once()
                    mock_rewriter.assert_called_once()
    
    def test_initialize_services_with_missing_dependencies(self):
        """Test service initialization with missing dependencies."""
        
        # Mock missing dependencies
        with patch('app_modules.app_factory.DocumentProcessor', side_effect=ImportError):
            with patch('app_modules.app_factory.StyleAnalyzer', side_effect=ImportError):
                with patch('app_modules.app_factory.AIRewriter', side_effect=ImportError):
                    
                    services = initialize_services()
                    
                    # Should still return services (fallback)
                    assert 'document_processor' in services
                    assert 'style_analyzer' in services  
                    assert 'ai_rewriter' in services
                    
                    # Services should be functional fallbacks
                    assert services['document_processor'] is not None
                    assert services['style_analyzer'] is not None
                    assert services['ai_rewriter'] is not None
    
    def test_service_health_validation(self):
        """Test service health validation after initialization."""
        
        services = initialize_services()
        
        # Each service should be functional
        for service_name, service in services.items():
            assert service is not None, f"Service {service_name} should not be None"
            
            # Check service has expected methods
            if service_name == 'document_processor':
                assert hasattr(service, 'extract_text'), "Document processor should have extract_text"
                assert hasattr(service, 'allowed_file'), "Document processor should have allowed_file"
            
            elif service_name == 'style_analyzer':
                assert hasattr(service, 'analyze'), "Style analyzer should have analyze method"
            
            elif service_name == 'ai_rewriter':
                assert hasattr(service, 'rewrite'), "AI rewriter should have rewrite method"


class TestAppFactoryIntegration:
    """Integration tests for app factory with real components."""
    
    def test_full_app_integration(self):
        """Test full application integration with real components."""
        
        class IntegrationConfig(Config):
            TESTING = True
            SECRET_KEY = TestConfig.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
            WTF_CSRF_ENABLED = False
        
        try:
            app, socketio = create_app(IntegrationConfig)
            
            # Test with real request
            with app.test_client() as client:
                response = client.get('/')
                assert response.status_code == 200, "Index page should load"
            
            # Test service integration
            services = getattr(app, 'services', {})
            
            # Document processor integration
            doc_processor = services['document_processor']
            assert doc_processor.allowed_file('test.txt'), "Should allow txt files"
            assert not doc_processor.allowed_file('test.exe'), "Should reject exe files"
            
            # Style analyzer integration
            style_analyzer = services['style_analyzer']
            result = style_analyzer.analyze("This is a test sentence.", [])
            assert 'errors' in result or hasattr(result, 'errors'), "Should return analysis result"
            
        finally:
            if os.path.exists(IntegrationConfig.UPLOAD_FOLDER):
                shutil.rmtree(IntegrationConfig.UPLOAD_FOLDER)
    
    def test_websocket_integration(self):
        """Test WebSocket integration with real components."""
        
        class WSConfig(Config):
            TESTING = True
            SECRET_KEY = TestConfig.TEST_SECRET_KEY
            UPLOAD_FOLDER = tempfile.mkdtemp()
        
        try:
            app, socketio = create_app(WSConfig)
            
            # Test WebSocket client
            client = socketio.test_client(app)
            
            # Should connect successfully
            assert client.is_connected(), "WebSocket client should connect"
            
            # Test disconnect
            client.disconnect()
            
        finally:
            if os.path.exists(WSConfig.UPLOAD_FOLDER):
                shutil.rmtree(WSConfig.UPLOAD_FOLDER) 