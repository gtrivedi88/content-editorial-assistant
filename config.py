"""
Configuration module for the Style Guide Application.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Application configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'style-guide-secret-key-2024'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///style_guide.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
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
    
    # Redis Configuration (for Celery)
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # SpaCy model settings (for linguistic analysis, not AI generation)
    SPACY_MODEL = os.environ.get('SPACY_MODEL', 'en_core_web_sm')
    
    # Block Processing Configuration
    BLOCK_PROCESSING_TIMEOUT = int(os.environ.get('BLOCK_PROCESSING_TIMEOUT', 30))  # seconds
    BLOCK_PROCESSING_MAX_RETRIES = int(os.environ.get('BLOCK_PROCESSING_MAX_RETRIES', 2))
    BLOCK_PROCESSING_BATCH_SIZE = int(os.environ.get('BLOCK_PROCESSING_BATCH_SIZE', 5))
    
    # Performance Monitoring Configuration
    ENABLE_PERFORMANCE_MONITORING = os.environ.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
    PERFORMANCE_METRICS_RETENTION_DAYS = int(os.environ.get('PERFORMANCE_METRICS_RETENTION_DAYS', 7))
    WEBSOCKET_PING_INTERVAL = int(os.environ.get('WEBSOCKET_PING_INTERVAL', 25))  # seconds
    WEBSOCKET_PING_TIMEOUT = int(os.environ.get('WEBSOCKET_PING_TIMEOUT', 60))  # seconds
    
    # Error Rate Monitoring
    ERROR_RATE_THRESHOLD = float(os.environ.get('ERROR_RATE_THRESHOLD', 0.05))  # 5% error rate threshold
    ERROR_RATE_WINDOW_MINUTES = int(os.environ.get('ERROR_RATE_WINDOW_MINUTES', 15))  # 15 minute window
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass
    
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

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 