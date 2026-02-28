"""
Configuration for Content Editorial Assistant.
"""

import os
import logging
import secrets
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables (optional - only if .env file exists)
load_dotenv()

class Config:
    """Application configuration."""

    # Flask Configuration - Auto-generate secure key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Auto-generate a secure secret key for this session
        # In production, set SECRET_KEY environment variable
        SECRET_KEY = secrets.token_hex(32)
        if os.environ.get('FLASK_ENV') == 'production':
            logging.warning("Using auto-generated SECRET_KEY. Set SECRET_KEY environment variable in production!")

    # Production/Development Mode
    DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development'
    TESTING = False

    # Database Configuration
    # Priority: DATABASE_URL > component-based URL > SQLite fallback
    @staticmethod
    def _build_database_url():
        """Build database URL from environment variables."""
        # Option 1: Use full DATABASE_URL if provided
        if os.environ.get('DATABASE_URL'):
            return os.environ.get('DATABASE_URL')
        
        # Option 2: Build from components (for Lightrail with split secrets)
        db_host = os.environ.get('DATABASE_HOST')
        db_password = os.environ.get('DATABASE_PASSWORD')
        
        if db_host and db_password:
            db_user = os.environ.get('DATABASE_USER', 'cea_user')
            db_port = os.environ.get('DATABASE_PORT', '5432')
            db_name = os.environ.get('DATABASE_NAME', 'ccs_ai_data')
            db_schema = os.environ.get('DATABASE_SCHEMA', 'cea')
            db_sslmode = os.environ.get('DATABASE_SSLMODE', 'require')
            
            # Build PostgreSQL URL with schema search path
            from urllib.parse import quote_plus
            encoded_password = quote_plus(db_password)
            return f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}&options=-csearch_path%3D{db_schema}"
        
        # Option 3: Lightrail SQLite fallback
        if os.environ.get('PLATFORM') == 'lightrail':
            if os.environ.get('ENVIRONMENT') == 'local':
                return "sqlite:///:memory:"
            else:
                persist_dir = os.environ.get('LIGHTRAIL_APPLICATION_PERSISTENCE_DIRECTORY', '/tmp')
                return f"sqlite:///{persist_dir}/instance/content_editorial_assistant.db"
        
        # Option 4: Default SQLite
        return 'sqlite:///content_editorial_assistant.db'
    
    SQLALCHEMY_DATABASE_URI = _build_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Database Connection Pool Settings
    @staticmethod
    def _get_engine_options():
        """Optimized database engine options."""
        is_postgresql = (
            os.environ.get('DATABASE_URL', '').startswith('postgresql') or
            (os.environ.get('DATABASE_HOST') and os.environ.get('DATABASE_PASSWORD'))
        )
        if is_postgresql:
            return {
                'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
                'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
                'pool_pre_ping': os.environ.get('DB_POOL_PRE_PING', 'true').lower() == 'true',
                'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
                'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20'))
            }
        return {}  # No special settings for SQLite

    SQLALCHEMY_ENGINE_OPTIONS = _get_engine_options()

    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    if os.environ.get('PLATFORM') == 'lightrail':
        UPLOAD_FOLDER = os.path.join(os.environ.get("LIGHTRAIL_APPLICATION_PERSISTENCE_DIRECTORY"), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'adoc', 'md', 'dita', 'xml', 'docx', 'pdf', 'txt'}

    # Style Guide Rules Configuration
    ENABLE_GRAMMAR_CHECK = True
    ENABLE_READABILITY_CHECK = True
    ENABLE_PASSIVE_VOICE_CHECK = True
    ENABLE_SENTENCE_LENGTH_CHECK = True
    ENABLE_CONCISENESS_CHECK = True

    # Rule Thresholds
    MAX_SENTENCE_LENGTH = int(os.environ.get('MAX_SENTENCE_LENGTH', 25))
    MIN_READABILITY_SCORE = float(os.environ.get('MIN_READABILITY_SCORE', 60.0))

    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # SpaCy model settings
    SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en_core_web_sm')

    # Block Processing Configuration
    BLOCK_PROCESSING_TIMEOUT = int(os.environ.get('BLOCK_PROCESSING_TIMEOUT', 60))
    BLOCK_PROCESSING_MAX_RETRIES = int(os.environ.get('BLOCK_PROCESSING_MAX_RETRIES', 3))
    BLOCK_PROCESSING_BATCH_SIZE = int(os.environ.get('BLOCK_PROCESSING_BATCH_SIZE', 10))

    # Performance Monitoring Configuration
    ENABLE_PERFORMANCE_MONITORING = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    PERFORMANCE_METRICS_RETENTION_DAYS = int(os.environ.get('PERFORMANCE_METRICS_RETENTION_DAYS', 30))
    WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', 25))
    WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', 60))

    # Error Rate Monitoring
    ERROR_RATE_THRESHOLD = float(os.environ.get('ERROR_RATE_THRESHOLD', 0.01))  # 1% threshold
    ERROR_RATE_WINDOW_MINUTES = int(os.environ.get('ERROR_RATE_WINDOW_MINUTES', 15))

    @staticmethod
    def init_app(app):
        """Initialize application"""
        # Configure logging
        if not app.config['DEBUG']:
            if not app.logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(logging.INFO)
                formatter = logging.Formatter(
                    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
                )
                handler.setFormatter(formatter)
                app.logger.addHandler(handler)
                app.logger.setLevel(logging.INFO)

    @classmethod
    def get_upload_config(cls) -> Dict[str, Any]:
        """Get file upload configuration."""
        return {
            'max_content_length': cls.MAX_CONTENT_LENGTH,
            'allowed_extensions': cls.ALLOWED_EXTENSIONS
        }

    @classmethod
    def get_analysis_config(cls) -> Dict[str, Any]:
        """Get style analysis configuration."""
        return {
            'spacy_model': cls.SPACY_MODEL,
            'max_sentence_length': cls.MAX_SENTENCE_LENGTH,
            'min_readability_score': cls.MIN_READABILITY_SCORE
        }

    @classmethod
    def get_block_processing_config(cls) -> Dict[str, Any]:
        """Get block processing configuration."""
        return {
            'timeout': cls.BLOCK_PROCESSING_TIMEOUT,
            'max_retries': cls.BLOCK_PROCESSING_MAX_RETRIES,
            'batch_size': cls.BLOCK_PROCESSING_BATCH_SIZE
        }

    @classmethod
    def get_performance_monitoring_config(cls) -> Dict[str, Any]:
        """Get performance monitoring configuration."""
        return {
            'enabled': cls.ENABLE_PERFORMANCE_MONITORING,
            'retention_days': cls.PERFORMANCE_METRICS_RETENTION_DAYS,
            'websocket_ping_interval': cls.WEBSOCKET_PING_INTERVAL,
            'websocket_ping_timeout': cls.WEBSOCKET_PING_TIMEOUT,
            'error_rate_threshold': cls.ERROR_RATE_THRESHOLD,
            'error_rate_window_minutes': cls.ERROR_RATE_WINDOW_MINUTES
        }


# For testing only
class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'testing-secret-key-not-for-production'
    SQLALCHEMY_ENGINE_OPTIONS = {}  # No pooling for test
