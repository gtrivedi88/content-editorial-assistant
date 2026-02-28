"""Content Editorial Assistant - Entry Point"""

# Gevent monkey-patching
from gevent import monkey
monkey.patch_all()

import os
import sys
import logging
import signal
from pathlib import Path

import nltk
PRODUCTION_NLTK_PATH = '/app/.cache/nltk_data'
nltk_data_path = PRODUCTION_NLTK_PATH if os.path.exists(PRODUCTION_NLTK_PATH) else os.getenv('NLTK_DATA', os.path.expanduser('~/nltk_data'))
nltk.data.path.clear()
nltk.data.path.append(nltk_data_path)
os.environ['NLTK_DATA'] = nltk_data_path

from app_modules.app_factory import create_app, configure_upload_folder
from config import Config

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Logging configuration
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.info(f"NLTK data path configured: {nltk_data_path} (paths: {nltk.data.path})")

app = None
socketio = None

def create_directories():
    """Create necessary application directories."""
    if os.environ.get('PLATFORM') == 'lightrail':
        # Use platform-provided writable directories (per SME guidance)
        persist_dir = os.environ.get("LIGHTRAIL_APPLICATION_PERSISTENCE_DIRECTORY")
        
        # Persistent data: uploads, instance (database), logs (if needed)
        for directory in ["uploads", "instance", "logs"]:
            Path(os.path.join(persist_dir, directory)).mkdir(exist_ok=True, parents=True)
        
        # Temporary data: use /tmp (cleared on restart)
        Path("/tmp/app-temp").mkdir(exist_ok=True, parents=True)
    else:
        # Local development: use current directory
        for directory in ["uploads", "logs", "instance", "temp"]:
            Path(os.path.join(os.getcwd(), directory)).mkdir(exist_ok=True, parents=True)

    return True

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    if socketio:
        socketio.stop()
    sys.exit(0)

def initialize_application():
    global app, socketio
    logger.info("Initializing application...")
    create_directories()
    app, socketio = create_app(Config)
    configure_upload_folder(app)
    logger.info("Application ready")
    return True

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    logger.info("=" * 50)
    logger.info(f"Content Editorial Assistant - {ENVIRONMENT.upper()}")
    logger.info("=" * 50)

    if not initialize_application():
        logger.error("Initialization failed")
        sys.exit(1)

    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true' and ENVIRONMENT != 'production'
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')

    if ENVIRONMENT == 'production' and debug_mode:
        logger.warning("Debug mode disabled in production")
        debug_mode = False

    logger.info(f"Starting on {host}:{port} (debug={debug_mode})")

    try:
        socketio.run(app, host=host, port=port, debug=debug_mode, log_output=True, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        logger.info("Stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
else:
    logger.info(f"Initializing for WSGI (Gunicorn) - {ENVIRONMENT}")
    try:
        if not initialize_application():
            raise RuntimeError("Initialization failed")
        logger.info(f"Ready on {os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8080')}")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    application = app
