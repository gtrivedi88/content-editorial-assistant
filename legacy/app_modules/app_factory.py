"""
App Factory Module
Creates and configures the Flask application with all necessary components.
Implements the application factory pattern for better testing and modularity.
"""

import os
import logging
import atexit
import signal
from flask import Flask, request, g
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from .api_routes import setup_routes
from .error_handlers import setup_error_handlers
from .websocket_handlers import setup_websocket_handlers

# Import database components
from database import init_db, db
from database.services import database_service

logger = logging.getLogger(__name__)

# Status constants
STATUS_READY = "Ready"
STATUS_UNAVAILABLE = "Unavailable"


def create_app(config_class=Config):
    """Create and configure Flask application using the application factory pattern."""
    
    # Get the correct path for templates and static files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(base_dir, 'ui', 'templates')
    static_dir = os.path.join(base_dir, 'ui', 'static')
    
    # Create Flask app with correct template and static paths
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir if os.path.exists(static_dir) else None)
    app.config.from_object(config_class)
    
    # Set up logging
    setup_logging()
    
    # Initialize extensions
    CORS(app)
    async_mode = 'gevent' if os.getenv('ENVIRONMENT') == 'production' else 'threading'
    
    # Configure Socket.IO with extended timeouts for long-running operations
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*", 
        async_mode=async_mode,
        # Extended timeout settings for long-running analysis operations
        ping_timeout=60,        # 1 minute timeout for pong response
        ping_interval=25,       # Send ping every 25 seconds
        engineio_logger=False,  # Reduce log noise
        # Additional settings for stability
        max_http_buffer_size=10_000_000,  # 10MB for large documents
        allow_upgrades=True,
        http_compression=True
    )
    
    # Initialize rate limiter for production stability
    # Health checks are excluded to prevent pod restarts
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per hour", "20 per minute"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    
    app.limiter = limiter
    logger.info("Rate limiting enabled: 20 req/min per IP (health checks exempted)")

    # Initialize database
    database_initialized = initialize_database(app)

    # Initialize services
    services = initialize_services()
    
    # Add database service to services
    services['database_service'] = database_service
    services['database_available'] = database_initialized
    
    # Setup application components
    setup_routes(app, services['document_processor'], services['style_analyzer'], services['database_service'])
    setup_error_handlers(app)
    setup_websocket_handlers(socketio)

    # Store services and socketio in app context for access
    setattr(app, 'services', services)
    setattr(app, 'socketio', socketio)
    
    # Log initialization status
    log_initialization_status(services)

    # Register cleanup handlers
    register_cleanup_handlers()
    
    return app, socketio


def setup_logging():
    """Configure application logging."""
    try:
        handlers = [logging.StreamHandler()]
        
        # Only use file logging in local development (not in containers)
        if os.environ.get('PLATFORM') != 'lightrail':
            # Create logs directory if it doesn't exist
            if not os.path.exists('logs'):
                os.makedirs('logs')
            handlers.append(logging.FileHandler('logs/app.log'))
        
        # Configure logging (stdout always available in containers)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(name)s: %(message)s',
            handlers=handlers
        )
        
        # Set specific logger levels
        logging.getLogger('werkzeug').setLevel(logging.INFO)
        logging.getLogger('socketio').setLevel(logging.WARNING)
        logging.getLogger('engineio').setLevel(logging.WARNING)
        
        logger.info("Logging configured successfully")
        
    except Exception as e:
        print(f"Warning: Could not configure logging: {e}")


def initialize_database(app):
    """Initialize database with the Flask application."""
    try:
        init_db(app)

        with app.app_context():
            db.create_all()

            try:
                rules_created = database_service.initialize_default_rules()
                if rules_created > 0:
                    logger.info(f"Initialized {rules_created} default style rules")
                else:
                    logger.info("Database already contains default style rules")
            except Exception as e:
                logger.warning(f"Could not initialize default rules: {e}")

        logger.info("Database initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        logger.warning("Application will run without database persistence")
        return False

def initialize_services():
    """Initialize core services. Fails fast if required services are unavailable."""
    services = {}

    # Preload SpaCy model once at startup (singleton)
    try:
        from shared.spacy_singleton import get_spacy_model
        model = get_spacy_model()
        if model:
            logger.info("SpaCy model preloaded successfully (singleton)")
        else:
            logger.warning("SpaCy model not available")
    except Exception as e:
        logger.warning(f"Could not preload SpaCy model: {e}")

    # Initialize Document Processor
    from structural_parsing.extractors import DocumentProcessor
    services['document_processor'] = DocumentProcessor()
    logger.info("DocumentProcessor initialized")

    # Initialize Style Analyzer
    from style_analyzer import StyleAnalyzer
    services['style_analyzer'] = StyleAnalyzer()
    logger.info("StyleAnalyzer initialized")

    return services


def log_initialization_status(services):
    """Log the initialization status of all services."""
    try:
        logger.info("=== Service Initialization Status ===")
        logger.info(f"Document Processor: {STATUS_READY}")
        logger.info(f"Style Analyzer: {STATUS_READY}")
        db_status = STATUS_READY if services.get('database_available', False) else STATUS_UNAVAILABLE
        logger.info(f"Database Service: {db_status}")
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
        'services': {
            'document_processor': 'ready',
            'style_analyzer': 'ready',
        },
        'warnings': []
    }

    try:
        if not services.get('database_available', False):
            health_status['services']['database'] = 'unavailable'
            health_status['warnings'].append('Database service unavailable - no data persistence')
        else:
            health_status['services']['database'] = 'ready'
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