"""
Configuration for Content Editorial Assistant.
"""

import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is required")
    
    # Production/Development Mode
    DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development'
    TESTING = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///content_editorial_assistant.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Connection Pool Settings
    @staticmethod
    def _get_engine_options():
        """Optimized database engine options."""
        if os.environ.get('DATABASE_URL', '').startswith('postgresql'):
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
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'adoc', 'md', 'dita', 'docx', 'pdf', 'txt'}
    
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
        if not app.debug:
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