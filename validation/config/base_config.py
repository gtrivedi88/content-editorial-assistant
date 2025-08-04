"""
Base Configuration Module for Validation System
Provides YAML configuration loading, validation, caching, and error handling.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import hashlib


logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""
    pass


class ConfigurationValidationError(ConfigurationError):
    """Exception raised when configuration validation fails."""
    pass


class ConfigurationLoadError(ConfigurationError):
    """Exception raised when configuration loading fails."""
    pass


class BaseConfig(ABC):
    """
    Abstract base class for configuration management.
    Provides YAML loading, validation, caching, and error handling.
    """
    
    def __init__(self, config_file: Union[str, Path], cache_ttl: int = 300):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to the YAML configuration file
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.config_file = Path(config_file)
        self.cache_ttl = cache_ttl
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._file_hash: Optional[str] = None
        
        # Validate that config file exists if it should
        if not self._is_optional() and not self.config_file.exists():
            raise ConfigurationLoadError(
                f"Required configuration file not found: {self.config_file}"
            )
    
    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration.
        Must be implemented by subclasses.
        
        Returns:
            Default configuration dictionary
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration structure and values.
        Must be implemented by subclasses.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, raises ConfigurationValidationError if invalid
        """
        pass
    
    def _is_optional(self) -> bool:
        """
        Whether this configuration file is optional.
        Can be overridden by subclasses.
        
        Returns:
            True if configuration file is optional
        """
        return False
    
    def _calculate_file_hash(self) -> Optional[str]:
        """
        Calculate MD5 hash of the configuration file.
        
        Returns:
            MD5 hash of file content, None if file doesn't exist
        """
        if not self.config_file.exists():
            return None
        
        try:
            with open(self.config_file, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except (IOError, OSError) as e:
            logger.warning(f"Failed to calculate file hash for {self.config_file}: {e}")
            return None
    
    def _is_cache_valid(self) -> bool:
        """
        Check if the current cache is valid.
        
        Returns:
            True if cache is valid and can be used
        """
        if self._config_cache is None or self._cache_timestamp is None:
            return False
        
        # Check cache TTL
        if datetime.now() - self._cache_timestamp > timedelta(seconds=self.cache_ttl):
            logger.debug(f"Cache expired for {self.config_file}")
            return False
        
        # Check if file has been modified
        current_hash = self._calculate_file_hash()
        if current_hash != self._file_hash:
            logger.debug(f"File modified, cache invalid for {self.config_file}")
            return False
        
        return True
    
    def _load_yaml_file(self) -> Dict[str, Any]:
        """
        Load and parse YAML configuration file.
        
        Returns:
            Parsed configuration dictionary
            
        Raises:
            ConfigurationLoadError: If file cannot be loaded or parsed
        """
        if not self.config_file.exists():
            if self._is_optional():
                logger.info(f"Optional configuration file not found: {self.config_file}")
                return {}
            else:
                raise ConfigurationLoadError(
                    f"Required configuration file not found: {self.config_file}"
                )
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Handle empty files
                if not content:
                    logger.warning(f"Configuration file is empty: {self.config_file}")
                    return {}
                
                config = yaml.safe_load(content)
                
                # Handle None result from yaml.safe_load
                if config is None:
                    logger.warning(f"Configuration file contains no data: {self.config_file}")
                    return {}
                
                # Ensure we have a dictionary
                if not isinstance(config, dict):
                    raise ConfigurationLoadError(
                        f"Configuration file must contain a YAML mapping/dictionary, "
                        f"got {type(config).__name__}: {self.config_file}"
                    )
                
                return config
                
        except yaml.YAMLError as e:
            raise ConfigurationLoadError(
                f"Failed to parse YAML configuration file {self.config_file}: {e}"
            )
        except (IOError, OSError) as e:
            raise ConfigurationLoadError(
                f"Failed to read configuration file {self.config_file}: {e}"
            )
        except UnicodeDecodeError as e:
            raise ConfigurationLoadError(
                f"Failed to decode configuration file {self.config_file}: {e}"
            )
    
    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded configuration with defaults.
        
        Args:
            config: Loaded configuration
            
        Returns:
            Merged configuration with defaults
        """
        defaults = self.get_default_config()
        
        # Deep merge - defaults first, then override with config
        merged = self._deep_merge(defaults, config)
        
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load configuration with caching support.
        
        Args:
            force_reload: Force reload even if cache is valid
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationLoadError: If configuration cannot be loaded
            ConfigurationValidationError: If configuration is invalid
        """
        # Use cache if valid and not forcing reload
        if not force_reload and self._is_cache_valid():
            logger.debug(f"Using cached configuration for {self.config_file}")
            return self._config_cache.copy()
        
        logger.debug(f"Loading configuration from {self.config_file}")
        
        try:
            # Load raw configuration
            raw_config = self._load_yaml_file()
            
            # Merge with defaults
            config = self._merge_with_defaults(raw_config)
            
            # Validate configuration
            self.validate_config(config)
            
            # Update cache
            self._config_cache = config.copy()
            self._cache_timestamp = datetime.now()
            self._file_hash = self._calculate_file_hash()
            
            logger.info(f"Successfully loaded configuration from {self.config_file}")
            
            return config.copy()
            
        except (ConfigurationLoadError, ConfigurationValidationError):
            # Re-raise configuration-specific errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise ConfigurationLoadError(
                f"Unexpected error loading configuration from {self.config_file}: {e}"
            )
    
    def reload_config(self) -> Dict[str, Any]:
        """
        Force reload configuration, clearing cache.
        
        Returns:
            Reloaded configuration dictionary
        """
        self.clear_cache()
        return self.load_config(force_reload=True)
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._config_cache = None
        self._cache_timestamp = None
        self._file_hash = None
        logger.debug(f"Cleared cache for {self.config_file}")
    
    def is_cached(self) -> bool:
        """
        Check if configuration is currently cached.
        
        Returns:
            True if configuration is cached
        """
        return self._config_cache is not None
    
    def get_cache_age(self) -> Optional[timedelta]:
        """
        Get the age of the current cache.
        
        Returns:
            Cache age or None if not cached
        """
        if self._cache_timestamp is None:
            return None
        
        return datetime.now() - self._cache_timestamp
    
    def get_config_file_path(self) -> Path:
        """
        Get the configuration file path.
        
        Returns:
            Path to configuration file
        """
        return self.config_file
    
    def config_file_exists(self) -> bool:
        """
        Check if configuration file exists.
        
        Returns:
            True if configuration file exists
        """
        return self.config_file.exists()
    
    def get_config_file_mtime(self) -> Optional[datetime]:
        """
        Get configuration file modification time.
        
        Returns:
            File modification time or None if file doesn't exist
        """
        if not self.config_file.exists():
            return None
        
        try:
            mtime = self.config_file.stat().st_mtime
            return datetime.fromtimestamp(mtime)
        except (OSError, IOError):
            return None


class SchemaValidator:
    """Helper class for configuration schema validation."""
    
    @staticmethod
    def validate_required_keys(config: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that required keys are present in configuration.
        
        Args:
            config: Configuration to validate
            required_keys: List of required key names
            
        Returns:
            True if all required keys are present
            
        Raises:
            ConfigurationValidationError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in config]
        
        if missing_keys:
            raise ConfigurationValidationError(
                f"Missing required configuration keys: {missing_keys}"
            )
        
        return True
    
    @staticmethod
    def validate_key_types(config: Dict[str, Any], key_types: Dict[str, type]) -> bool:
        """
        Validate that configuration keys have correct types.
        
        Args:
            config: Configuration to validate
            key_types: Dictionary mapping key names to expected types
            
        Returns:
            True if all key types are correct
            
        Raises:
            ConfigurationValidationError: If key types are incorrect
        """
        type_errors = []
        
        for key, expected_type in key_types.items():
            if key in config:
                value = config[key]
                if not isinstance(value, expected_type):
                    type_errors.append(
                        f"Key '{key}': expected {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )
        
        if type_errors:
            raise ConfigurationValidationError(
                f"Configuration type validation errors: {'; '.join(type_errors)}"
            )
        
        return True
    
    @staticmethod
    def validate_value_ranges(config: Dict[str, Any], 
                            value_ranges: Dict[str, Dict[str, Any]]) -> bool:
        """
        Validate that numeric values are within specified ranges.
        
        Args:
            config: Configuration to validate
            value_ranges: Dictionary mapping key names to range specifications
                         (e.g., {'min': 0, 'max': 100})
            
        Returns:
            True if all values are within ranges
            
        Raises:
            ConfigurationValidationError: If values are out of range
        """
        range_errors = []
        
        for key, range_spec in value_ranges.items():
            if key in config:
                value = config[key]
                
                if 'min' in range_spec and value < range_spec['min']:
                    range_errors.append(
                        f"Key '{key}': value {value} is less than minimum {range_spec['min']}"
                    )
                
                if 'max' in range_spec and value > range_spec['max']:
                    range_errors.append(
                        f"Key '{key}': value {value} is greater than maximum {range_spec['max']}"
                    )
        
        if range_errors:
            raise ConfigurationValidationError(
                f"Configuration range validation errors: {'; '.join(range_errors)}"
            )
        
        return True