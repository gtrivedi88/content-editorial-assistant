"""
Metadata Assistant Configuration Module

Manages configuration settings, taxonomy definitions, and system parameters
for the metadata generation system.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MetadataConfig:
    """Configuration management for metadata generation system."""
    
    DEFAULT_CONFIG = {
        # Processing limits
        'max_content_length': 100000,  # 100KB limit
        'processing_timeout': 30,      # 30 second timeout
        'max_concurrent_requests': 10,  # Concurrency limit
        
        # Quality settings
        'min_confidence_threshold': 0.3,
        'max_keywords': 10,
        'min_keywords': 3,
        'max_description_words': 60,
        'min_description_words': 10,
        'max_title_length': 200,
        
        # Feature flags
        'enable_semantic_classification': True,
        'enable_ai_fallback': True,
        'enable_caching': True,
        
        # Cache settings
        'cache_ttl_minutes': 60,
        'cache_max_size': 1000,
        
        # Model settings
        'sentence_transformer_model': 'all-MiniLM-L6-v2',
        'enable_model_download': True,
        'model_cache_dir': None,  # Will be set to default
        
        # Output settings
        'default_output_format': 'yaml',
        'supported_formats': ['yaml', 'json', 'dict'],
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Optional path to custom configuration file
        """
        self.config_path = config_path or self._get_default_config_path()
        self.taxonomy_config = {}
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path(__file__).parent / 'config'
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / 'metadata_config.yaml')
    
    def _load_config(self):
        """Load configuration from file and set up defaults."""
        # Start with default configuration
        config = self.DEFAULT_CONFIG.copy()
        
        # Load user configuration if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f) or {}
                    config.update(user_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
        else:
            logger.info("Using default configuration")
        
        # Set model cache directory if not specified
        if not config['model_cache_dir']:
            config['model_cache_dir'] = str(Path.home() / '.cache' / 'metadata_assistant')
        
        # Create model cache directory if it doesn't exist
        os.makedirs(config['model_cache_dir'], exist_ok=True)
        
        # Set attributes from config
        for key, value in config.items():
            setattr(self, key, value)
        
        # Load taxonomy configuration
        self._load_taxonomy_config()
    
    def _load_taxonomy_config(self):
        """Load taxonomy classification configuration."""
        taxonomy_path = Path(__file__).parent / 'config' / 'taxonomy_types.yaml'
        
        if taxonomy_path.exists():
            try:
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    self.taxonomy_config = yaml.safe_load(f) or {}
                logger.info(f"Loaded taxonomy configuration with {len(self.taxonomy_config)} categories")
            except Exception as e:
                logger.warning(f"Failed to load taxonomy config: {e}")
                self.taxonomy_config = self._get_default_taxonomy()
        else:
            logger.info("Using default taxonomy configuration")
            self.taxonomy_config = self._get_default_taxonomy()
    
    def _get_default_taxonomy(self) -> Dict[str, Dict[str, Any]]:
        """Get default taxonomy configuration for technical documentation."""
        return {
            'Troubleshooting': {
                'description': 'Content focused on diagnosing and resolving problems, errors, and issues',
                'indicators': [
                    'error', 'fix', 'resolve', 'issue', 'problem', 'debug', 'troubleshoot', 
                    'diagnose', 'solve', 'repair', 'failure', 'bug', 'fault'
                ],
                'structure_hints': ['numbered_list', 'procedure_steps', 'error_messages'],
                'examples': ['Error resolution guides', 'Debugging procedures', 'FAQ sections'],
                'confidence_boost': 1.2,
                'required_keywords': []
            },
            'Installation': {
                'description': 'Step-by-step guides for installing, setting up, or configuring software and systems',
                'indicators': [
                    'install', 'setup', 'configure', 'deploy', 'requirements', 'prerequisite',
                    'download', 'build', 'compile', 'environment'
                ],
                'structure_hints': ['prerequisite_section', 'step_by_step', 'command_blocks'],
                'examples': ['Installation guides', 'Setup procedures', 'Configuration tutorials'],
                'confidence_boost': 1.3,
                'required_keywords': ['install']
            },
            'API_Documentation': {
                'description': 'Technical documentation for APIs, endpoints, and programmatic interfaces',
                'indicators': [
                    'api', 'endpoint', 'request', 'response', 'parameter', 'method', 
                    'rest', 'graphql', 'webhook', 'authentication', 'token'
                ],
                'structure_hints': ['code_blocks', 'parameter_tables', 'example_requests'],
                'examples': ['REST API docs', 'SDK documentation', 'Integration guides'],
                'confidence_boost': 1.4,
                'required_keywords': ['api']
            },
            'Security': {
                'description': 'Content related to security practices, authentication, and access control',
                'indicators': [
                    'security', 'authentication', 'authorization', 'encrypt', 'permission',
                    'credential', 'token', 'certificate', 'firewall', 'vulnerability'
                ],
                'structure_hints': ['warning_blocks', 'security_notes', 'best_practices'],
                'examples': ['Security policies', 'Authentication setup', 'Access control guides'],
                'confidence_boost': 1.1,
                'required_keywords': []
            },
            'Best_Practices': {
                'description': 'Guidelines, recommendations, and best practices for optimal implementation',
                'indicators': [
                    'best', 'practice', 'recommend', 'guideline', 'standard', 'convention',
                    'pattern', 'strategy', 'approach', 'methodology'
                ],
                'structure_hints': ['recommendation_blocks', 'tip_boxes', 'guidelines'],
                'examples': ['Coding standards', 'Design patterns', 'Implementation guidelines'],
                'confidence_boost': 1.0,
                'required_keywords': []
            },
            'Reference': {
                'description': 'Reference materials, specifications, and lookup information',
                'indicators': [
                    'reference', 'specification', 'manual', 'documentation', 'glossary',
                    'definition', 'command', 'option', 'syntax', 'format'
                ],
                'structure_hints': ['tables', 'lists', 'definitions'],
                'examples': ['Command references', 'Configuration options', 'Glossaries'],
                'confidence_boost': 1.0,
                'required_keywords': []
            },
            'Tutorial': {
                'description': 'Educational content that teaches concepts and skills through examples',
                'indicators': [
                    'tutorial', 'learn', 'example', 'walkthrough', 'guide', 'introduction',
                    'getting started', 'how to', 'step by step', 'beginner'
                ],
                'structure_hints': ['examples', 'step_by_step', 'learning_objectives'],
                'examples': ['Getting started guides', 'Learning tutorials', 'How-to articles'],
                'confidence_boost': 1.1,
                'required_keywords': []
            }
        }
    
    def get_taxonomy_category(self, category_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific taxonomy category."""
        return self.taxonomy_config.get(category_name)
    
    def get_all_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get all taxonomy categories."""
        return self.taxonomy_config.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            config = {}
            for key in self.DEFAULT_CONFIG.keys():
                if hasattr(self, key):
                    config[key] = getattr(self, key)
            
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=True)
            
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status."""
        issues = []
        warnings = []
        
        # Check required settings
        if self.max_keywords < self.min_keywords:
            issues.append("max_keywords must be greater than min_keywords")
        
        if self.max_description_words < self.min_description_words:
            issues.append("max_description_words must be greater than min_description_words")
        
        if self.min_confidence_threshold < 0 or self.min_confidence_threshold > 1:
            issues.append("min_confidence_threshold must be between 0 and 1")
        
        # Check optional settings
        if not os.path.exists(self.model_cache_dir):
            warnings.append(f"Model cache directory does not exist: {self.model_cache_dir}")
        
        if len(self.taxonomy_config) == 0:
            warnings.append("No taxonomy categories configured")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }
