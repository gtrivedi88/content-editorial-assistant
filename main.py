"""
Content Editorial Assistant - Production Entry Point

"""

import os
import sys
import logging
import signal
import ssl
from pathlib import Path
from llama_stack_client import LlamaStackClient, DefaultHttpxClient
from app_modules.app_factory import create_app, configure_upload_folder
from config import Config

# Environment configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Logging configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Global variables
app = None
socketio = None
llama_stack_client = None

def setup_llama_stack_client():
    """Initialize Llama Stack client (pre-hook already validated connectivity)."""
    global llama_stack_client
    
    base_url = os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL')
    ca_cert_path = os.environ.get('LIGHTRAIL_LLAMA_STACK_TLS_SERVICE_CA_CERT_PATH')
    
    if not base_url:
        if ENVIRONMENT == 'development':
            logger.info("Development mode: Llama Stack not configured")
            return True
        else:
            logger.error("LIGHTRAIL_LLAMA_STACK_BASE_URL not set")
            return False
    
    try:
        # Setup TLS context
        ctx = ssl.create_default_context()
        if ca_cert_path and os.path.exists(ca_cert_path):
            ctx.load_verify_locations(ca_cert_path)
        
        # Initialize client (pre-hook validated connectivity)
        llama_stack_client = LlamaStackClient(
            base_url=base_url,
            http_client=DefaultHttpxClient(verify=ctx)
        )
        
        logger.info("Llama Stack client ready")
        return True
        
    except Exception as e:
        logger.error(f"Llama Stack client initialization failed: {e}")
        return False

def create_directories():
    """Create necessary application directories.""" 
    directories = ["uploads", "logs", "instance", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    return True

def signal_handler(signum, frame):
    """Handle graceful shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if socketio:
        socketio.stop()
    sys.exit(0)

def initialize_application():
    """Initialize the Style Guide AI application."""
    global app, socketio
    
    logger.info("Initializing Style Guide AI...")
    
    # Simple initialization (pre-hook handles deployment validation)
    create_directories()
    setup_llama_stack_client()
    
    # Create Flask application
    app, socketio = create_app(Config)
    configure_upload_folder(app)
    
    # Add Llama Stack client to app context
    if llama_stack_client:
        app.llama_stack_client = llama_stack_client
    
    logger.info("Application ready")
    return True

def main():
    """Main application entry point."""
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 50)
    logger.info("Style Guide AI - Production Application")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("=" * 50)
    
    # Initialize application
    if not initialize_application():
        logger.error("Application initialization failed")
        sys.exit(1)
    
    # Configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' and ENVIRONMENT != 'production'
    port = int(os.getenv('PORT', 8080))  # Default port 8080 for Lightrail
    host = os.getenv('HOST', '0.0.0.0')  # Bind to all interfaces for container deployment
    
    # Disable debug mode in production
    if ENVIRONMENT == 'production' and debug_mode:
        logger.warning("Debug mode disabled in production environment")
        debug_mode = False
    
    logger.info(f"Starting application on {host}:{port}")
    logger.info(f"Debug mode: {debug_mode}")
    
    if ENVIRONMENT == 'production':
        logger.info("Production mode: Enhanced security and performance settings enabled")
    
    try:
        # Run with SocketIO support
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            allow_unsafe_werkzeug=debug_mode  # Only allow in debug mode
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

# Application entry point
if __name__ == '__main__':
    main()
else:
    # For WSGI deployment (production servers like Gunicorn)
    if not initialize_application():
        logger.error("Application initialization failed")
        raise RuntimeError("Failed to initialize application")
    
    # Export app for WSGI server
    application = app 