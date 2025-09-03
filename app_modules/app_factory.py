"""
App Factory Module
Creates and configures the Flask application with all necessary components.
Implements the application factory pattern for better testing and modularity.
"""

import os
import logging
import atexit
import signal
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from config import Config
from .api_routes import setup_routes
from .error_handlers import setup_error_handlers
from .websocket_handlers import setup_websocket_handlers
from .fallback_services import SimpleDocumentProcessor, SimpleStyleAnalyzer, SimpleAIRewriter

# Initialize monitoring system
try:
    from validation.monitoring.metrics import get_metrics
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Create and configure Flask application using the application factory pattern."""
    
    # Get the correct path for templates and static files
    # Since we're in app_modules/, we need to go up one level
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'ui', 'templates')
    static_dir = os.path.join(base_dir, 'ui', 'static')
    
    # Create Flask app with correct template and static paths
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir if os.path.exists(static_dir) else None)
    app.config.from_object(config_class)
    
    # Set up logging
    setup_logging(app)
    
    # Initialize extensions
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    # Initialize services with fallbacks
    services = initialize_services()
    
    # Setup application components
    setup_routes(app, services['document_processor'], services['style_analyzer'], services['ai_rewriter'])
    setup_error_handlers(app)
    setup_websocket_handlers(socketio)
    
    # Store services and socketio in app context for access
    setattr(app, 'services', services)
    setattr(app, 'socketio', socketio)
    
    # Log initialization status
    log_initialization_status(services)
    
    # Initialize monitoring system if available
    if MONITORING_AVAILABLE:
        try:
            metrics = get_metrics()
            if metrics.prometheus_enabled:
                logger.info("✅ Prometheus metrics enabled and server started")
                logger.info("📊 Metrics available at: http://localhost:8000/metrics")
            else:
                logger.info("📊 Validation monitoring enabled (in-process counters only)")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize monitoring: {e}")
    
    # Register cleanup handlers
    register_cleanup_handlers()
    
    return app, socketio


def setup_logging(app):
    """Configure application logging."""
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s',
            handlers=[
                logging.FileHandler('logs/app.log'),
                logging.StreamHandler()
            ]
        )
        
        # Set specific logger levels
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('socketio').setLevel(logging.WARNING)
        logging.getLogger('engineio').setLevel(logging.WARNING)
        
        logger.info("Logging configured successfully")
        
    except Exception as e:
        print(f"Warning: Could not configure logging: {e}")


def initialize_services():
    """Initialize all services with fallback mechanisms."""
    services = {
        'document_processor': None,
        'style_analyzer': None,
        'ai_rewriter': None,
        'document_processor_available': False,
        'style_analyzer_available': False,
        'ai_rewriter_available': False
    }
    
    # Initialize Document Processor
    try:
        from structural_parsing.extractors import DocumentProcessor
        services['document_processor'] = DocumentProcessor()
        services['document_processor_available'] = True
        logger.info("✅ DocumentProcessor imported successfully")
    except ImportError as e:
        services['document_processor'] = SimpleDocumentProcessor()
        services['document_processor_available'] = False
        logger.warning(f"⚠️ Document processor not available - {e}")
    
    # Initialize Style Analyzer
    try:
        from style_analyzer import StyleAnalyzer
        services['style_analyzer'] = StyleAnalyzer()
        services['style_analyzer_available'] = True
        logger.info("✅ StyleAnalyzer imported successfully")
    except ImportError as e:
        services['style_analyzer'] = SimpleStyleAnalyzer()
        services['style_analyzer_available'] = False
        logger.warning(f"⚠️ Style analyzer not available - {e}")
    
    # Initialize AI Rewriter with progress callback support
    try:
        from rewriter import DocumentRewriter
        from models import ModelConfig
        from .websocket_handlers import emit_progress
        
        # Create progress callback function for real-time updates
        def progress_callback(session_id, step, status, detail, progress_percent):
            """Progress callback that emits WebSocket updates for specific or all sessions."""
            try:
                # Use the provided session_id, or broadcast to all if empty
                # Empty string or None means broadcast to all connected clients
                target_session = session_id if session_id and session_id != 'None' else ''
                emit_progress(target_session, step, status, detail, progress_percent)
                print(f"🔍 DEBUG PROGRESS CALLBACK: Emitted to {'all sessions' if not target_session else target_session}")
            except Exception as e:
                logger.debug(f"Progress callback error: {e}")
                print(f"❌ Progress callback error: {e}")
        
        # Get model configuration
        model_info = ModelConfig.get_model_info()
        
        # Initialize with progress callback for world-class real-time updates
        services['ai_rewriter'] = DocumentRewriter(progress_callback=progress_callback)
        services['ai_rewriter_available'] = True
        logger.info("✅ DocumentRewriter imported successfully with world-class progress tracking")
        logger.info(f"AI Model: {model_info.get('type', 'Unknown')} - {model_info.get('model', 'Unknown')}")
    except ImportError as e:
        services['ai_rewriter'] = SimpleAIRewriter()
        services['ai_rewriter_available'] = False
        logger.warning(f"⚠️ DocumentRewriter not available, using fallback - {e}")
    
    return services


def log_initialization_status(services):
    """Log the initialization status of all services."""
    try:
        logger.info("=== Service Initialization Status ===")
        
        status_map = {
            'document_processor': 'Document Processor',
            'style_analyzer': 'Style Analyzer',
            'ai_rewriter': 'AI Rewriter'
        }
        
        for service_key, display_name in status_map.items():
            available_key = f"{service_key}_available"
            status = "✅ Ready" if services.get(available_key, False) else "⚠️ Fallback"
            logger.info(f"{display_name}: {status}")
        
        # Log AI configuration with status
        try:
            from models import ModelConfig, is_model_available
            model_info = ModelConfig.get_model_info()
            active_config = ModelConfig.get_active_config()
            
            if active_config.get('provider_type') == 'ollama':
                # Check if Ollama is actually available
                ollama_status = "✅ Ready" if is_model_available() else "⚠️ Connection Issue"
                model_name = active_config.get('model', 'Unknown')
                logger.info(f"AI Configuration: {ollama_status} - Ollama ({model_name})")
            elif active_config.get('provider_type') == 'api':
                api_status = "✅ Ready" if is_model_available() else "⚠️ API Issue"
                provider_name = active_config.get('provider_name', 'Unknown')
                model_name = active_config.get('model', 'Unknown')
                logger.info(f"AI Configuration: {api_status} - {provider_name} API ({model_name})")
            else:
                logger.info("AI Configuration: ✅ Models system available")
        except Exception as e:
            logger.warning(f"Could not determine AI configuration: {e}")
        
        logger.info("=====================================")
        
    except Exception as e:
        logger.error(f"Error logging initialization status: {e}")


def configure_upload_folder(app):
    """Configure upload folder settings."""
    try:
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        max_content_length = app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Set Flask configuration
        app.config['UPLOAD_FOLDER'] = upload_folder
        app.config['MAX_CONTENT_LENGTH'] = max_content_length
        
        logger.info(f"Upload folder configured: {upload_folder} (max: {max_content_length // (1024*1024)}MB)")
        
    except Exception as e:
        logger.error(f"Error configuring upload folder: {e}")


def register_teardown_handlers(app):
    """Register application teardown handlers."""
    
    @app.teardown_appcontext
    def cleanup_session(error):
        """Cleanup session data on teardown."""
        try:
            # Add any session cleanup logic here
            pass
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
    
    @app.teardown_request
    def cleanup_request(error):
        """Cleanup request data on teardown."""
        try:
            # Add any request cleanup logic here
            if error:
                logger.error(f"Request error: {error}")
        except Exception as e:
            logger.error(f"Error in request cleanup: {e}")


def health_check_services(services):
    """Perform health check on all services."""
    health_status = {
        'overall': 'healthy',
        'services': {},
        'warnings': []
    }
    
    try:
        # Check document processor
        if services['document_processor_available']:
            health_status['services']['document_processor'] = 'ready'
        else:
            health_status['services']['document_processor'] = 'fallback'
            health_status['warnings'].append('Document processor using fallback implementation')
        
        # Check style analyzer
        if services['style_analyzer_available']:
            health_status['services']['style_analyzer'] = 'ready'
        else:
            health_status['services']['style_analyzer'] = 'fallback'
            health_status['warnings'].append('Style analyzer using fallback implementation')
        
        # Check AI rewriter
        if services['ai_rewriter_available']:
            health_status['services']['ai_rewriter'] = 'ready'
        else:
            health_status['services']['ai_rewriter'] = 'fallback'
            health_status['warnings'].append('AI rewriter using fallback implementation')
        
        # Overall health assessment
        if len(health_status['warnings']) > 2:
            health_status['overall'] = 'degraded'
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        health_status['overall'] = 'unhealthy'
        health_status['error'] = str(e)
    
    return health_status


def register_cleanup_handlers():
    """Register cleanup handlers for graceful shutdown."""
    
    def cleanup_ruby_client():
        """Cleanup the Ruby client on shutdown."""
        try:
            from structural_parsing.asciidoc.ruby_client import shutdown_client
            shutdown_client()
            logger.info("Ruby client shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down Ruby client: {e}")
    
    # Register cleanup on normal exit
    atexit.register(cleanup_ruby_client)
    
    # Register cleanup on signal termination
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        cleanup_ruby_client()
        exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler) 