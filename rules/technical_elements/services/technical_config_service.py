"""
Technical Configuration Service for Technical Elements Rules

Manages YAML-based configurations with caching, pattern compilation,
and context-aware evidence calculation for zero false positives.
"""

import os
import yaml
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple, Pattern
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class TechnicalPattern:
    """Represents a technical pattern with evidence scoring and context."""
    pattern: str
    compiled_pattern: Optional[Pattern] = None
    evidence: float = 0.7
    category: str = ""
    description: str = ""
    format_suggestion: str = ""
    correct_usage: str = ""
    legitimate_patterns: List[str] = field(default_factory=list)
    context_adjustments: Dict[str, float] = field(default_factory=dict)

@dataclass
class TechnicalContext:
    """Context information for technical-specific appropriateness."""
    content_type: str = ""
    audience: str = ""
    domain: str = ""
    block_type: str = ""

class TechnicalConfigService:
    """
    Technical configuration management service.
    
    Features:
    - YAML-based configuration management
    - Automatic pattern compilation and caching
    - Context-aware evidence calculation
    - Runtime configuration updates
    - Caching for performance
    """
    
    _instances: Dict[str, 'TechnicalConfigService'] = {}
    
    def __new__(cls, config_name: str):
        """Singleton pattern for each configuration type."""
        if config_name not in cls._instances:
            cls._instances[config_name] = super(TechnicalConfigService, cls).__new__(cls)
        return cls._instances[config_name]
    
    def __init__(self, config_name: str):
        """Initialize technical config service for a specific config."""
        if hasattr(self, '_initialized'):
            return
            
        self.config_name = config_name
        self.config_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', f'{config_name}.yaml'
        )
        self._patterns: Dict[str, TechnicalPattern] = {}
        self._context_adjustments: Dict[str, Dict[str, float]] = {}
        self._thresholds: Dict[str, float] = {}
        self._messages: Dict[str, Dict[str, Any]] = {}
        self._suggestions: Dict[str, List[str]] = {}
        self._guard_patterns: Dict[str, Any] = {}
        
        self._load_configuration()
        self._initialized = True
    
    def _load_configuration(self):
        """Load configuration from YAML file."""
        logger.info(f"Loading technical configuration from {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load based on config type
            if self.config_name == 'commands_patterns':
                self._load_commands_config(config)
            elif self.config_name == 'keyboard_patterns':
                self._load_keyboard_config(config)
            elif self.config_name == 'files_directories_patterns':
                self._load_files_config(config)
            elif self.config_name == 'mouse_patterns':
                self._load_mouse_config(config)
            elif self.config_name == 'programming_patterns':
                self._load_programming_config(config)
            elif self.config_name == 'ui_elements_patterns':
                self._load_ui_config(config)
            elif self.config_name == 'web_addresses_patterns':
                self._load_web_config(config)
            
            # Load common sections
            self._context_adjustments = config.get('context_adjustments', {})
            self._thresholds = config.get('thresholds', {})
            self._messages = config.get('messages', {})
            self._suggestions = config.get('suggestions', {})
            self._guard_patterns = config.get('guard_patterns', {})
            
            logger.info(f"Loaded {len(self._patterns)} technical patterns")
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            self._patterns = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration YAML: {e}")
            self._patterns = {}
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            self._patterns = {}
    
    def _load_commands_config(self, config: Dict[str, Any]):
        """Load commands-specific configuration."""
        # Load Unix commands
        unix_commands = config.get('unix_commands', {})
        for category, commands in unix_commands.items():
            for cmd_config in commands:
                pattern_id = f"unix_{cmd_config['command']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=cmd_config['command'],
                    evidence=cmd_config.get('evidence', 0.7),
                    category=cmd_config.get('category', 'unix_command'),
                    description=cmd_config.get('description', ''),
                    legitimate_patterns=cmd_config.get('legitimate_patterns', [])
                )
        
        # Load Git commands
        git_commands = config.get('git_commands', {})
        for category, commands in git_commands.items():
            for cmd_config in commands:
                pattern_id = f"git_{cmd_config['command']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=cmd_config['command'],
                    evidence=cmd_config.get('evidence', 0.7),
                    category=cmd_config.get('category', 'git_command'),
                    description=cmd_config.get('description', ''),
                    legitimate_patterns=cmd_config.get('legitimate_patterns', [])
                )
        
        # Load Database commands
        db_commands = config.get('database_commands', {})
        for category, commands in db_commands.items():
            for cmd_config in commands:
                pattern_id = f"db_{cmd_config['command']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=cmd_config['command'],
                    evidence=cmd_config.get('evidence', 0.7),
                    category=cmd_config.get('category', 'database_command'),
                    description=cmd_config.get('description', ''),
                    legitimate_patterns=cmd_config.get('legitimate_patterns', [])
                )
    
    def _load_keyboard_config(self, config: Dict[str, Any]):
        """Load keyboard-specific configuration."""
        # Load key combinations
        key_combinations = config.get('key_combinations', {})
        for category, patterns in key_combinations.items():
            for pattern_config in patterns:
                pattern_id = f"keycomb_{category}_{hash(pattern_config['pattern'])}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=pattern_config['pattern'],
                    compiled_pattern=re.compile(pattern_config['pattern']),
                    evidence=pattern_config.get('evidence', 0.7),
                    category=pattern_config.get('category', 'key_combination'),
                    description=pattern_config.get('description', ''),
                    correct_usage=pattern_config.get('correct_format', '')
                )
        
        # Load individual keys
        individual_keys = config.get('individual_keys', {})
        for category, keys in individual_keys.items():
            for key_config in keys:
                pattern_id = f"key_{key_config['key']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=key_config['key'],
                    evidence=key_config.get('evidence', 0.7),
                    category=key_config.get('category', 'individual_key'),
                    correct_usage=key_config.get('correct_format', ''),
                    legitimate_patterns=key_config.get('legitimate_patterns', [])
                )
    
    def _load_files_config(self, config: Dict[str, Any]):
        """Load files and directories configuration."""
        # Load file paths
        file_paths = config.get('file_paths', {})
        for category, paths in file_paths.items():
            for path_config in paths:
                pattern_id = f"path_{category}_{hash(path_config['pattern'])}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=path_config['pattern'],
                    compiled_pattern=re.compile(path_config['pattern']),
                    evidence=path_config.get('evidence', 0.7),
                    category=path_config.get('category', 'file_path'),
                    description=path_config.get('description', ''),
                    format_suggestion=path_config.get('format_suggestion', '')
                )
        
        # Load file extensions
        file_extensions = config.get('file_extensions', {})
        for category, extensions in file_extensions.items():
            for ext_config in extensions:
                pattern_id = f"ext_{ext_config['extension']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=f"\\.{ext_config['extension']}\\b",
                    compiled_pattern=re.compile(f"\\.{ext_config['extension']}\\b"),
                    evidence=ext_config.get('evidence', 0.7),
                    category=ext_config.get('category', 'file_extension'),
                    description=ext_config.get('description', ''),
                    correct_usage=ext_config.get('correct_usage', '')
                )
    
    def _load_mouse_config(self, config: Dict[str, Any]):
        """Load mouse actions configuration."""
        mouse_actions = config.get('mouse_actions', {})
        for category, actions in mouse_actions.items():
            for action_config in actions:
                pattern_id = f"mouse_{action_config['action'].replace(' ', '_')}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=action_config['action'],
                    evidence=action_config.get('evidence', 0.7),
                    category=action_config.get('category', 'mouse_action'),
                    description=action_config.get('description', ''),
                    correct_usage=action_config.get('correct_usage', '')
                )
    
    def _load_programming_config(self, config: Dict[str, Any]):
        """Load programming keywords configuration and enhanced linguistic intelligence data."""
        # Original programming keywords loading
        programming_keywords = config.get('programming_keywords', {})
        for category, keywords in programming_keywords.items():
            for keyword_config in keywords:
                pattern_id = f"prog_{keyword_config['keyword']}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=keyword_config['keyword'],
                    evidence=keyword_config.get('evidence', 0.7),
                    category=keyword_config.get('category', 'programming_keyword'),
                    description=keyword_config.get('description', ''),
                    legitimate_patterns=keyword_config.get('legitimate_patterns', [])
                )
        
        # === ENHANCED: Load linguistic intelligence configurations ===
        
        # Load linguistic guards data
        self._linguistic_guards = config.get('linguistic_guards', {})
        
        # Load programming pattern templates  
        pattern_templates = config.get('programming_patterns', {})
        self._programming_pattern_templates = pattern_templates.get('templates', [])
        
        # Load evidence adjustments
        self._evidence_adjustments = config.get('evidence_adjustments', {})
    
    def _load_ui_config(self, config: Dict[str, Any]):
        """Load UI elements configuration."""
        ui_elements = config.get('ui_elements', {})
        for category, elements in ui_elements.items():
            for element_config in elements:
                pattern_id = f"ui_{element_config['element'].replace(' ', '_')}"
                # Store both approved and incorrect verbs for reference
                pattern_data = TechnicalPattern(
                    pattern=element_config['element'],
                    evidence=element_config.get('evidence', 0.7),
                    category=element_config.get('category', 'ui_element'),
                    description=element_config.get('description', '')
                )
                # Add UI-specific data
                pattern_data.approved_verbs = element_config.get('approved_verbs', [])
                pattern_data.incorrect_verbs = element_config.get('incorrect_verbs', [])
                self._patterns[pattern_id] = pattern_data
    
    def _load_web_config(self, config: Dict[str, Any]):
        """Load web addresses configuration."""
        # Load URL patterns
        url_patterns = config.get('url_patterns', {})
        for category, patterns in url_patterns.items():
            for pattern_config in patterns:
                pattern_id = f"url_{category}_{hash(pattern_config['pattern'])}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=pattern_config['pattern'],
                    compiled_pattern=re.compile(pattern_config['pattern']),
                    evidence=pattern_config.get('evidence', 0.7),
                    category=pattern_config.get('category', 'url_pattern'),
                    description=pattern_config.get('description', ''),
                    format_suggestion=pattern_config.get('format_suggestion', '')
                )
        
        # Load email patterns  
        email_patterns = config.get('email_patterns', {})
        for category, patterns in email_patterns.items():
            for pattern_config in patterns:
                pattern_id = f"email_{category}_{hash(pattern_config['pattern'])}"
                self._patterns[pattern_id] = TechnicalPattern(
                    pattern=pattern_config['pattern'],
                    compiled_pattern=re.compile(pattern_config['pattern']),
                    evidence=pattern_config.get('evidence', 0.5),
                    category=pattern_config.get('category', 'email_pattern'),
                    description=pattern_config.get('description', ''),
                    format_suggestion=pattern_config.get('format_suggestion', '')
                )
    
    def get_patterns(self, category: Optional[str] = None) -> Dict[str, TechnicalPattern]:
        """Get patterns, optionally filtered by category."""
        if category:
            return {k: v for k, v in self._patterns.items() if v.category == category}
        return self._patterns.copy()
    
    def get_pattern(self, pattern_id: str) -> Optional[TechnicalPattern]:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def calculate_context_evidence(self, base_evidence: float, context) -> float:
        """Calculate context-adjusted evidence score."""
        evidence = base_evidence
        
        # Handle both dict and TechnicalContext objects
        if isinstance(context, dict):
            content_type = context.get('content_type', '')
            audience = context.get('audience', '')
            domain = context.get('domain', '')
        else:
            content_type = getattr(context, 'content_type', '')
            audience = getattr(context, 'audience', '')
            domain = getattr(context, 'domain', '')
        
        # Apply content type adjustments
        content_adjustments = self._context_adjustments.get('content_type', {})
        if content_type in content_adjustments:
            evidence += content_adjustments[content_type]
        
        # Apply audience adjustments
        audience_adjustments = self._context_adjustments.get('audience', {})
        if audience in audience_adjustments:
            evidence += audience_adjustments[audience]
        
        # Apply domain adjustments
        domain_adjustments = self._context_adjustments.get('domain', {})
        if domain in domain_adjustments:
            evidence += domain_adjustments[domain]
        
        return max(0.0, min(1.0, evidence))  # Clamp to [0, 1]
    
    def get_threshold(self, threshold_name: str, default: float = 0.1) -> float:
        """Get threshold value."""
        return self._thresholds.get(threshold_name, default)
    
    def get_message_template(self, confidence_level: str, default: str = "") -> str:
        """Get message template for confidence level."""
        messages = self._messages.get(confidence_level, {})
        return messages.get('template', default)
    
    def get_suggestions(self, confidence_level: str) -> List[str]:
        """Get suggestions for confidence level."""
        return self._suggestions.get(confidence_level, [])
    
    # === ENHANCED: Linguistic Intelligence Accessor Methods ===
    
    def get_programming_context_indicators(self) -> List[str]:
        """Get programming context indicators for guard analysis."""
        return self._linguistic_guards.get('programming_context_indicators', [])
    
    def get_programming_objects(self, category: Optional[str] = None) -> List[str]:
        """Get programming objects that should trigger flagging."""
        programming_objects = self._linguistic_guards.get('programming_objects', {})
        if category and category in programming_objects:
            return programming_objects[category]
        
        # Return all programming objects from all categories
        all_objects = []
        for objects_list in programming_objects.values():
            if isinstance(objects_list, list):
                all_objects.extend(objects_list)
        return all_objects
    
    def get_non_programming_objects(self, category: Optional[str] = None) -> List[str]:
        """Get non-programming objects that indicate business/general usage."""
        non_programming_objects = self._linguistic_guards.get('non_programming_objects', {})
        if category and category in non_programming_objects:
            return non_programming_objects[category]
        
        # Return all non-programming objects from all categories
        all_objects = []
        for objects_list in non_programming_objects.values():
            if isinstance(objects_list, list):
                all_objects.extend(objects_list)
        return all_objects
    
    def get_infinitive_verbs(self) -> List[str]:
        """Get verbs that indicate infinitive usage."""
        return self._linguistic_guards.get('infinitive_verbs', [])
    
    def get_general_context_indicators(self) -> List[str]:
        """Get general context indicators for imperative analysis."""
        return self._linguistic_guards.get('general_context_indicators', [])
    
    def get_programming_pattern_templates(self) -> List[str]:
        """Get programming pattern templates with {keyword} placeholders."""
        return getattr(self, '_programming_pattern_templates', [])
    
    def generate_programming_patterns(self, keyword: str) -> List[str]:
        """Generate programming patterns for a specific keyword."""
        templates = self.get_programming_pattern_templates()
        return [template.format(keyword=keyword) for template in templates]
    
    def get_evidence_adjustment(self, adjustment_type: str, default: float = 0.0) -> float:
        """Get evidence adjustment value for specific types."""
        return getattr(self, '_evidence_adjustments', {}).get(adjustment_type, default)
    
    def get_guard_patterns(self) -> Dict[str, Any]:
        """Get guard patterns configuration."""
        return self._guard_patterns.copy()
    
    def get_config(self, section_name: str, default=None):
        """Get configuration section by name."""
        config_sections = {
            'context_adjustments': self._context_adjustments,
            'thresholds': self._thresholds,
            'messages': self._messages,
            'suggestions': self._suggestions,
            'guard_patterns': self._guard_patterns
        }
        return config_sections.get(section_name, default or {})
    
    def is_legitimate_pattern(self, pattern_id: str, text: str) -> bool:
        """Check if text matches legitimate patterns for given pattern ID."""
        pattern = self._patterns.get(pattern_id)
        if not pattern or not pattern.legitimate_patterns:
            return False
        
        text_lower = text.lower()
        return any(legit_pattern in text_lower for legit_pattern in pattern.legitimate_patterns)

# Service Factory - Singleton access pattern
class TechnicalConfigServices:
    """Factory for accessing technical configuration services."""
    
    @staticmethod
    def commands() -> TechnicalConfigService:
        return TechnicalConfigService('commands_patterns')
    
    @staticmethod
    def keyboard() -> TechnicalConfigService:
        return TechnicalConfigService('keyboard_patterns')
    
    @staticmethod
    def files_directories() -> TechnicalConfigService:
        return TechnicalConfigService('files_directories_patterns')
    
    @staticmethod
    def mouse() -> TechnicalConfigService:
        return TechnicalConfigService('mouse_patterns')
    
    @staticmethod
    def programming() -> TechnicalConfigService:
        return TechnicalConfigService('programming_patterns')
    
    @staticmethod
    def ui_elements() -> TechnicalConfigService:
        return TechnicalConfigService('ui_elements_patterns')
    
    @staticmethod
    def web_addresses() -> TechnicalConfigService:
        return TechnicalConfigService('web_addresses_patterns')
