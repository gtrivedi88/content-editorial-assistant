"""
Confidence Gateway - Intelligent Error Pre-filtering System
Pre-filters detected errors using confidence scoring to avoid unnecessary LLM calls.
"""

import logging
import time
import yaml
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


VALIDATION_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class GatewayMode(Enum):
    """Gateway operation modes for A/B testing."""
    DISABLED = "disabled"          # Pass all errors through (control group)
    ENABLED = "enabled"            # Filter errors with confidence threshold
    LOGGING_ONLY = "logging_only"  # Log decisions but don't filter (shadow mode)

@dataclass
class GatewayDecision:
    """Represents a gateway filtering decision."""
    error_id: str
    error_type: str
    flagged_text: str
    confidence_score: float
    decision: str  # "pass" or "suppress"
    threshold: float
    processing_time_ms: float
    reasoning: str

@dataclass
class GatewayStats:
    """Gateway performance statistics."""
    total_errors_processed: int = 0
    errors_passed: int = 0
    errors_suppressed: int = 0
    average_confidence: float = 0.0
    processing_time_ms: float = 0.0
    cost_savings_estimate: float = 0.0  # Estimated LLM call savings

class ConfidenceGateway:
    """
    Intelligent pre-filter for detected errors using confidence scoring.
    
    Phase 1 Features:
    - Conservative confidence threshold filtering
    - Comprehensive decision logging and analytics
    - A/B testing support with multiple operation modes
    - Detailed performance metrics and cost estimation
    - Integration with existing validation pipeline
    
    Phase 2A Features:
    - Error-type specific thresholds (spelling: 0.3, ambiguity: 0.6)
    - Context-aware threshold adjustment (technical vs marketing content)
    - Hot-reload configuration without restart
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.4,
                 mode: GatewayMode = GatewayMode.ENABLED,
                 enable_detailed_logging: bool = True,
                 config_file: Optional[str] = None):
        """
        Initialize Confidence Gateway.
        
        Args:
            confidence_threshold: Default minimum confidence to pass errors through (0.0-1.0)
            mode: Gateway operation mode for A/B testing
            enable_detailed_logging: Whether to log all decisions for analysis
            config_file: Optional path to YAML configuration file
        """
        self.default_confidence_threshold = confidence_threshold
        self.mode = mode
        self.enable_detailed_logging = enable_detailed_logging
        
        # Configuration system
        self.config_file = config_file or "config/confidence_gateway_schema.yaml"
        self.config = {}
        self.error_type_thresholds = {}
        self.context_adjustments = {}
        self.config_last_modified = 0
        
        # Load configuration
        self._load_configuration()
        
        # Phase 1: Use built-in confidence estimation (external validation in Phase 2)
        self.confidence_calculator = None
        
        # Performance tracking
        self.stats = GatewayStats()
        self.decisions_log = []  # Store all decisions for analysis
        
        # Cost estimation parameters
        self.estimated_llm_cost_per_call = self.config.get('cost_estimation', {}).get('llm_call_cost_estimate', 0.002)
        
        logger.info(f"🚪 Phase 2A Confidence Gateway initialized: default_threshold={confidence_threshold}, mode={mode.value}")
        logger.info(f"📋 Loaded {len(self.error_type_thresholds)} error-type specific thresholds")
    
    def filter_errors(self, errors: List[Dict[str, Any]], 
                     text: str = "", 
                     context: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Filter detected errors through confidence gateway.
        
        Args:
            errors: List of detected errors to filter
            text: Original text content for context
            context: Additional context for confidence calculation
            
        Returns:
            Tuple of (filtered_errors, gateway_report)
        """
        if not errors:
            return errors, self._create_empty_report()
        
        # Check for configuration updates before processing
        config_updated = self.check_for_config_updates()
        if config_updated:
            logger.info("🔄 Using updated configuration for this filtering session")
        
        start_time = time.time()
        passed_errors = []
        suppressed_errors = []
        decisions = []
        
        logger.info(f"🚪 Phase 2A Gateway filtering {len(errors)} detected errors (smart thresholding enabled)")
        
        for i, error in enumerate(errors):
            decision = self._evaluate_error_confidence(error, text, context, f"error_{i}")
            decisions.append(decision)
            
            if decision.decision == "pass" or self.mode == GatewayMode.DISABLED:
                passed_errors.append(error)
            elif decision.decision == "suppress" and self.mode == GatewayMode.ENABLED:
                suppressed_errors.append(error)
            else:  # LOGGING_ONLY mode
                passed_errors.append(error)  # Pass through but log decision
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        self._update_stats(decisions, processing_time)
        
        # Store decisions for analysis
        if self.enable_detailed_logging:
            self.decisions_log.extend(decisions)
            # Keep only recent decisions (last 1000) to prevent memory issues
            if len(self.decisions_log) > 1000:
                self.decisions_log = self.decisions_log[-1000:]
        
        # Create comprehensive report
        gateway_report = self._create_gateway_report(decisions, processing_time, len(suppressed_errors))
        
        # Log results
        if suppressed_errors and self.mode == GatewayMode.ENABLED:
            logger.info(f"🚪 Gateway filtered {len(suppressed_errors)}/{len(errors)} errors ({len(suppressed_errors)/len(errors)*100:.1f}% suppressed)")
            if self.enable_detailed_logging:
                for decision in decisions:
                    if decision.decision == "suppress":
                        logger.debug(f"   🛑 Suppressed {decision.error_type} '{decision.flagged_text}' (confidence: {decision.confidence_score:.2f})")
        
        return passed_errors, gateway_report
    
    def _evaluate_error_confidence(self, error: Dict[str, Any], text: str, 
                                 context: Optional[Dict[str, Any]], error_id: str) -> GatewayDecision:
        """Evaluate confidence for a single error and make gateway decision."""
        start_time = time.time()
        
        error_type = error.get('type', 'unknown')
        flagged_text = error.get('flagged_text', '')
        
        # Calculate confidence score
        confidence_score = self._calculate_error_confidence(error, text, context)
        
        # Use error-type specific threshold with context awareness
        applicable_threshold = self._get_error_type_threshold(error_type, context)
        
        # Make decision based on smart threshold
        if confidence_score >= applicable_threshold:
            decision = "pass"
            reasoning = f"Confidence {confidence_score:.3f} >= {error_type}_threshold {applicable_threshold:.3f}"
        else:
            decision = "suppress" 
            reasoning = f"Confidence {confidence_score:.3f} < {error_type}_threshold {applicable_threshold:.3f}"
        
        processing_time = (time.time() - start_time) * 1000
        
        return GatewayDecision(
            error_id=error_id,
            error_type=error_type,
            flagged_text=flagged_text,
            confidence_score=confidence_score,
            decision=decision,
            threshold=applicable_threshold,
            processing_time_ms=processing_time,
            reasoning=reasoning
        )
    
    def _calculate_error_confidence(self, error: Dict[str, Any], text: str, 
                                  context: Optional[Dict[str, Any]]) -> float:
        """
        Calculate confidence score for an error using built-in confidence estimation.
        
        Phase 1: Uses intelligent fallback estimation based on error attributes.
        Phase 2: Will integrate external validation system for enhanced accuracy.
        """
        return self._fallback_confidence_estimation(error, text, context)
    
    def _fallback_confidence_estimation(self, error: Dict[str, Any], text: str, 
                                      context: Optional[Dict[str, Any]]) -> float:
        """
        Built-in confidence estimation using error attributes and heuristics.
        
        This provides reliable confidence scoring without external dependencies.
        Calibrated based on observed error type performance in production.
        """
        
        base_confidence = 0.5  # Neutral starting point
        
        # Factor 1: Error type reliability (based on known performance)
        error_type = error.get('type', '').lower()
        
        high_confidence_types = {
            'spelling', 'contractions', 'prefixes', 'currency', 'abbreviations',
            'technical_files_directories', 'technical_commands'
        }
        
        medium_confidence_types = {
            'possessives', 'plurals', 'hyphens', 'commas', 'periods',
            'capitalization', 'spacing'
        }
        
        low_confidence_types = {
            'ambiguity', 'tone', 'passive_voice', 'sentence_length',
            'pronouns', 'articles'
        }
        
        if error_type in high_confidence_types:
            base_confidence = 0.8
        elif error_type in medium_confidence_types:
            base_confidence = 0.6
        elif error_type in low_confidence_types:
            base_confidence = 0.3
        
        # Factor 2: Error specificity (more specific = higher confidence)
        flagged_text = error.get('flagged_text', '')
        if len(flagged_text) > 0:
            # Shorter, more specific flags tend to be more reliable
            specificity_bonus = max(0, (10 - len(flagged_text)) / 20)
            base_confidence += specificity_bonus
        
        # Factor 3: Context indicators
        severity = error.get('severity', '').lower()
        if severity == 'high':
            base_confidence += 0.1
        elif severity == 'low':
            base_confidence -= 0.1
        
        # Factor 4: Span information quality
        span = error.get('span')
        if span and len(span) == 2 and span[1] > span[0]:
            base_confidence += 0.05  # Good span information
        
        return max(0.1, min(0.9, base_confidence))
    
    def _update_stats(self, decisions: List[GatewayDecision], processing_time: float):
        """Update gateway statistics with latest decisions."""
        
        passed = sum(1 for d in decisions if d.decision == "pass")
        suppressed = sum(1 for d in decisions if d.decision == "suppress")
        total_confidence = sum(d.confidence_score for d in decisions)
        
        # Update cumulative stats
        self.stats.total_errors_processed += len(decisions)
        self.stats.errors_passed += passed
        self.stats.errors_suppressed += suppressed
        self.stats.processing_time_ms += processing_time
        
        if self.stats.total_errors_processed > 0:
            self.stats.average_confidence = (
                self.stats.average_confidence * (self.stats.total_errors_processed - len(decisions)) +
                total_confidence
            ) / self.stats.total_errors_processed
        
        # Estimate cost savings (suppressed errors = avoided LLM calls)
        self.stats.cost_savings_estimate += suppressed * self.estimated_llm_cost_per_call
    
    def _create_gateway_report(self, decisions: List[GatewayDecision], 
                             processing_time: float, suppressed_count: int) -> Dict[str, Any]:
        """Create comprehensive gateway processing report."""
        
        passed_decisions = [d for d in decisions if d.decision == "pass"]
        suppressed_decisions = [d for d in decisions if d.decision == "suppress"]
        
        return {
            'gateway_mode': self.mode.value,
            'confidence_threshold': self.default_confidence_threshold,
            'total_errors': len(decisions),
            'errors_passed': len(passed_decisions),
            'errors_suppressed': len(suppressed_decisions),
            'suppression_rate': len(suppressed_decisions) / len(decisions) if decisions else 0,
            'average_confidence': sum(d.confidence_score for d in decisions) / len(decisions) if decisions else 0,
            'processing_time_ms': processing_time,
            'estimated_cost_savings': suppressed_count * self.estimated_llm_cost_per_call,
            'high_confidence_errors': len([d for d in decisions if d.confidence_score >= 0.7]),
            'low_confidence_errors': len([d for d in decisions if d.confidence_score < 0.3]),
            'gateway_enabled': self.mode == GatewayMode.ENABLED,
            'decisions': decisions if self.enable_detailed_logging else []
        }
    
    def _create_empty_report(self) -> Dict[str, Any]:
        """Create empty report for when no errors to process."""
        return {
            'gateway_mode': self.mode.value,
            'confidence_threshold': self.default_confidence_threshold,
            'total_errors': 0,
            'errors_passed': 0,
            'errors_suppressed': 0,
            'suppression_rate': 0.0,
            'average_confidence': 0.0,
            'processing_time_ms': 0.0,
            'estimated_cost_savings': 0.0,
            'high_confidence_errors': 0,
            'low_confidence_errors': 0,
            'gateway_enabled': self.mode == GatewayMode.ENABLED,
            'decisions': []
        }
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics for the gateway."""
        
        suppression_rate = (
            self.stats.errors_suppressed / self.stats.total_errors_processed 
            if self.stats.total_errors_processed > 0 else 0
        )
        
        return {
            'total_errors_processed': self.stats.total_errors_processed,
            'errors_passed': self.stats.errors_passed,
            'errors_suppressed': self.stats.errors_suppressed,
            'suppression_rate_percent': suppression_rate * 100,
            'average_confidence': round(self.stats.average_confidence, 3),
            'total_processing_time_ms': round(self.stats.processing_time_ms, 1),
            'average_processing_time_per_error_ms': (
                self.stats.processing_time_ms / self.stats.total_errors_processed
                if self.stats.total_errors_processed > 0 else 0
            ),
            'estimated_cost_savings_usd': round(self.stats.cost_savings_estimate, 4),
            'gateway_mode': self.mode.value,
            'confidence_threshold': self.default_confidence_threshold,
            'recent_decisions_count': len(self.decisions_log),
            'validation_system_available': VALIDATION_AVAILABLE
        }
    
    def get_recent_suppressions(self, limit: int = 20) -> List[GatewayDecision]:
        """Get recent suppressed errors for analysis."""
        recent_suppressions = [
            decision for decision in self.decisions_log[-100:]  # Last 100 decisions
            if decision.decision == "suppress"
        ]
        return recent_suppressions[-limit:]
    
    def update_threshold(self, new_threshold: float):
        """Update confidence threshold (for dynamic tuning)."""
        old_threshold = self.default_confidence_threshold
        self.default_confidence_threshold = max(0.0, min(1.0, new_threshold))
        
        logger.info(f"🚪 Gateway threshold updated: {old_threshold} → {self.default_confidence_threshold}")
    
    def set_mode(self, mode: GatewayMode):
        """Change gateway operation mode."""
        old_mode = self.mode
        self.mode = mode
        
        logger.info(f"🚪 Gateway mode changed: {old_mode.value} → {mode.value}")
    
    def _load_configuration(self):
        """
        Load configuration from YAML file with production-grade error handling.
        
        Features:
        - Graceful fallback to defaults on any error
        - Comprehensive validation of loaded configuration
        - Production monitoring and alerting
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = yaml.safe_load(f)
                
                # Validate configuration structure
                if not self._validate_configuration():
                    logger.error(f"❌ Invalid configuration structure in {self.config_file}, using defaults")
                    self.config = self._get_default_config()
                    return
                
                # Store last modified time for hot-reload
                self.config_last_modified = os.path.getmtime(self.config_file)
                
                # Parse error-type specific thresholds
                self._parse_error_type_thresholds()
                
                # Parse context-aware adjustments
                self._parse_context_adjustments()
                
                logger.info(f"✅ Phase 2A configuration loaded: {len(self.error_type_thresholds)} thresholds, {len(self.context_adjustments)} contexts")
            else:
                logger.warning(f"⚠️  Configuration file not found: {self.config_file}, creating with defaults")
                self.config = self._get_default_config()
                self._create_default_config_file()
                
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML parsing error in {self.config_file}: {e}")
            self.config = self._get_default_config()
        except IOError as e:
            logger.error(f"❌ File I/O error loading {self.config_file}: {e}")
            self.config = self._get_default_config()
        except Exception as e:
            logger.error(f"❌ Unexpected error loading configuration: {e}")
            self.config = self._get_default_config()
    
    def _parse_error_type_thresholds(self):
        """Parse error-type specific thresholds from configuration."""
        self.error_type_thresholds = {}
        
        error_type_config = self.config.get('error_type_thresholds', {})
        
        for confidence_level, level_config in error_type_config.items():
            threshold = level_config.get('threshold', self.default_confidence_threshold)
            error_types = level_config.get('types', [])
            
            for error_type in error_types:
                self.error_type_thresholds[error_type.lower()] = threshold
        
        logger.debug(f"📊 Parsed {len(self.error_type_thresholds)} error-type thresholds")
    
    def _parse_context_adjustments(self):
        """Parse context-aware threshold adjustments from configuration."""
        self.context_adjustments = self.config.get('context_adjustments', {
            'technical_documentation': {'adjustment': -0.05, 'reason': 'Technical content has clearer rules'},
            'marketing_content': {'adjustment': +0.10, 'reason': 'Marketing allows more creative freedom'},
            'legal_content': {'adjustment': -0.10, 'reason': 'Legal content requires strict accuracy'},
            'casual_content': {'adjustment': +0.15, 'reason': 'Casual content allows informal language'},
            'formal_documentation': {'adjustment': -0.05, 'reason': 'Formal docs require strict compliance'}
        })
        
        logger.debug(f"🎯 Loaded {len(self.context_adjustments)} context adjustment rules")
    
    def _get_default_config(self):
        """Get default configuration when file is unavailable."""
        return {
            'gateway': {
                'enabled': True,
                'confidence_threshold': self.default_confidence_threshold,
                'enable_detailed_logging': True
            },
            'error_type_thresholds': {
                'high_confidence': {
                    'threshold': 0.3,
                    'types': ['spelling', 'contractions', 'prefixes', 'currency']
                },
                'medium_confidence': {
                    'threshold': 0.4,
                    'types': ['hyphens', 'commas', 'periods', 'capitalization']
                },
                'low_confidence': {
                    'threshold': 0.6,
                    'types': ['ambiguity', 'tone', 'passive_voice', 'sentence_length']
                }
            },
            'cost_estimation': {
                'llm_call_cost_estimate': 0.002
            }
        }
    
    def _get_error_type_threshold(self, error_type: str, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Get threshold for specific error type with context-aware adjustment.
        
        Phase 2A Feature: Smart thresholding based on error type and content context.
        """
        # Base threshold from error-type specific configuration
        base_threshold = self.error_type_thresholds.get(
            error_type.lower(), 
            self.default_confidence_threshold
        )
        
        # Context-aware adjustment
        if context:
            content_type = context.get('content_type') or context.get('block_type', '').lower()
            
            # Map common block types to content contexts
            context_mapping = {
                'paragraph': 'technical_documentation',
                'heading': 'formal_documentation', 
                'list': 'technical_documentation',
                'code': 'technical_documentation',
                'marketing': 'marketing_content',
                'legal': 'legal_content',
                'casual': 'casual_content'
            }
            
            mapped_context = context_mapping.get(content_type, content_type)
            
            if mapped_context in self.context_adjustments:
                adjustment = self.context_adjustments[mapped_context].get('adjustment', 0.0)
                adjusted_threshold = base_threshold + adjustment
                
                # Keep within valid range
                adjusted_threshold = max(0.1, min(0.9, adjusted_threshold))
                
                logger.debug(f"🎯 {error_type} threshold adjusted: {base_threshold:.2f} → {adjusted_threshold:.2f} (context: {mapped_context})")
                
                return adjusted_threshold
        
        return base_threshold
    
    def check_for_config_updates(self):
        """
        Hot-reload configuration if file has been modified.
        
        Phase 2A Feature: Update thresholds without restart.
        """
        if not os.path.exists(self.config_file):
            return False
        
        try:
            current_modified_time = os.path.getmtime(self.config_file)
            
            if current_modified_time > self.config_last_modified:
                logger.info(f"🔄 Configuration file updated, reloading...")
                old_threshold_count = len(self.error_type_thresholds)
                
                self._load_configuration()
                
                new_threshold_count = len(self.error_type_thresholds)
                logger.info(f"🔄 Hot-reload complete: {old_threshold_count} → {new_threshold_count} error-type thresholds")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Hot-reload failed: {e}")
        
        return False
    
    def _validate_configuration(self) -> bool:
        """
        Validate configuration structure and values for production safety.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not isinstance(self.config, dict):
            logger.error("❌ Configuration must be a dictionary")
            return False
        
        # Validate error_type_thresholds structure
        if 'error_type_thresholds' in self.config:
            error_thresholds = self.config['error_type_thresholds']
            if not isinstance(error_thresholds, dict):
                logger.error("❌ error_type_thresholds must be a dictionary")
                return False
            
            for level_name, level_config in error_thresholds.items():
                if not isinstance(level_config, dict):
                    logger.error(f"❌ error_type_thresholds.{level_name} must be a dictionary")
                    return False
                
                threshold = level_config.get('threshold')
                if threshold is not None and (not isinstance(threshold, (int, float)) or threshold < 0.0 or threshold > 1.0):
                    logger.error(f"❌ error_type_thresholds.{level_name}.threshold must be between 0.0 and 1.0")
                    return False
                
                types = level_config.get('types', [])
                if not isinstance(types, list):
                    logger.error(f"❌ error_type_thresholds.{level_name}.types must be a list")
                    return False
        
        # Validate context_adjustments structure
        if 'context_adjustments' in self.config:
            context_adjustments = self.config['context_adjustments']
            if not isinstance(context_adjustments, dict):
                logger.error("❌ context_adjustments must be a dictionary")
                return False
            
            for context_name, context_config in context_adjustments.items():
                if not isinstance(context_config, dict):
                    logger.error(f"❌ context_adjustments.{context_name} must be a dictionary")
                    return False
                
                adjustment = context_config.get('adjustment')
                if adjustment is not None and (not isinstance(adjustment, (int, float)) or adjustment < -0.5 or adjustment > 0.5):
                    logger.error(f"❌ context_adjustments.{context_name}.adjustment must be between -0.5 and 0.5")
                    return False
        
        logger.debug("✅ Configuration validation passed")
        return True
    
    def _create_default_config_file(self):
        """Create default configuration file for production deployment."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"✅ Created default configuration file: {self.config_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create default configuration file: {e}")
    
    def get_production_health_check(self) -> Dict[str, Any]:
        """
        Get comprehensive health check for production monitoring.
        
        Returns:
            Dictionary with health status and key metrics
        """
        try:
            # Check configuration health
            config_healthy = os.path.exists(self.config_file) and len(self.error_type_thresholds) > 0
            
            # Check recent performance
            recent_decisions = self.decisions_log[-100:] if self.decisions_log else []
            avg_processing_time = (
                sum(d.processing_time_ms for d in recent_decisions) / len(recent_decisions)
                if recent_decisions else 0.0
            )
            
            # Calculate suppression rates by error type
            error_type_stats = {}
            for decision in recent_decisions:
                error_type = decision.error_type
                if error_type not in error_type_stats:
                    error_type_stats[error_type] = {'total': 0, 'suppressed': 0}
                
                error_type_stats[error_type]['total'] += 1
                if decision.decision == 'suppress':
                    error_type_stats[error_type]['suppressed'] += 1
            
            return {
                'status': 'healthy' if config_healthy else 'degraded',
                'config_file_exists': os.path.exists(self.config_file),
                'error_type_thresholds_loaded': len(self.error_type_thresholds),
                'context_adjustments_loaded': len(self.context_adjustments),
                'total_errors_processed': self.stats.total_errors_processed,
                'current_suppression_rate': (
                    self.stats.errors_suppressed / self.stats.total_errors_processed
                    if self.stats.total_errors_processed > 0 else 0.0
                ),
                'average_processing_time_ms': avg_processing_time,
                'estimated_cost_savings': self.stats.cost_savings_estimate,
                'recent_error_type_stats': error_type_stats,
                'gateway_mode': self.mode.value,
                'last_config_check': self.config_last_modified,
                'phase': 'Phase 2A - Smart Thresholding'
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'phase': 'Phase 2A - Smart Thresholding'
            }
