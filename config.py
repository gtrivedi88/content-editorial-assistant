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