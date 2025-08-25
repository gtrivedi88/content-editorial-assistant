"""
Production Metrics for Validation System
Provides lightweight in-process counters and optional Prometheus integration for monitoring
validation pipeline behavior.
"""

import logging
import os
import threading
from collections import defaultdict
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Optional Prometheus imports
PROMETHEUS_AVAILABLE = False
try:
    import prometheus_client  # type: ignore[import-untyped]
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, CollectorRegistry  # type: ignore[import-untyped]
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Prometheus is optional - create dummy classes to avoid AttributeError
    class Counter:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def inc(self, value=1): pass
    
    class Histogram:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def observe(self, value): pass
    
    class Gauge:  # type: ignore
        def __init__(self, *args, **kwargs): pass
        def labels(self, **kwargs): return self
        def set(self, value): pass
    
    class CollectorRegistry:  # type: ignore
        def __init__(self, *args, **kwargs): pass
    
    def start_http_server(*args, **kwargs):  # type: ignore
        pass
    
    logger.debug("Prometheus client not available. Using in-process counters only.")

@dataclass
class MetricEvent:
    """Represents a validation metric event."""
    name: str
    value: float = 1.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ValidationMetrics:
    """
    Lightweight metrics collection for validation system.
    Provides in-process counters and optional Prometheus integration.
    """
    
    def __init__(self, enable_prometheus: Optional[bool] = None, prometheus_port: int = 8000):
        """
        Initialize metrics collection.
        
        Args:
            enable_prometheus: Whether to enable Prometheus export (defaults to env var check)
            prometheus_port: Port for Prometheus HTTP server
        """
        self._lock = threading.Lock()
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._histograms = defaultdict(list)
        
        # Prometheus setup
        if enable_prometheus is None:
            enable_prometheus = os.getenv('ENABLE_PROMETHEUS_METRICS', 'false').lower() == 'true'
        
        self.prometheus_enabled = enable_prometheus and PROMETHEUS_AVAILABLE
        self.prometheus_registry = None
        self.prometheus_counters = {}
        self.prometheus_gauges = {}
        self.prometheus_histograms = {}
        
        if self.prometheus_enabled:
            self._setup_prometheus(prometheus_port)
        
        logger.info(f"ValidationMetrics initialized. Prometheus enabled: {self.prometheus_enabled}")
    
    def _setup_prometheus(self, port: int):
        """Set up Prometheus metrics and HTTP server."""
        try:
            self.prometheus_registry = CollectorRegistry()
            
            # Define validation-specific metrics
            self.prometheus_counters = {
                'shortcut_applied': Counter(
                    'validation_shortcut_applied_total',
                    'Number of times evidence shortcut was applied',
                    ['rule_type', 'evidence_score_range'],
                    registry=self.prometheus_registry
                ),
                'confidence_floor_triggered': Counter(
                    'validation_confidence_floor_triggered_total',
                    'Number of times confidence floor was triggered',
                    ['rule_type', 'floor_type'],
                    registry=self.prometheus_registry
                ),
                'consolidation_confidence_adjustments': Counter(
                    'validation_consolidation_adjustments_total',
                    'Number of confidence adjustments during consolidation',
                    ['adjustment_type', 'rule_type'],
                    registry=self.prometheus_registry
                ),
                'negative_evidence_detected': Counter(
                    'validation_negative_evidence_detected_total',
                    'Number of negative evidence detections',
                    ['evidence_type', 'confidence_range'],
                    registry=self.prometheus_registry
                ),
                'validation_pipeline_executions': Counter(
                    'validation_pipeline_executions_total',
                    'Total validation pipeline executions',
                    ['stage', 'result'],
                    registry=self.prometheus_registry
                )
            }
            
            self.prometheus_histograms = {
                'validation_duration': Histogram(
                    'validation_duration_seconds',
                    'Time spent in validation pipeline',
                    ['stage', 'rule_type'],
                    registry=self.prometheus_registry
                )
            }
            
            self.prometheus_gauges = {
                'active_validation_sessions': Gauge(
                    'validation_active_sessions',
                    'Number of active validation sessions',
                    registry=self.prometheus_registry
                )
            }
            
            # Start HTTP server for metrics endpoint
            start_http_server(port, registry=self.prometheus_registry)
            logger.info(f"Prometheus metrics server started on port {port}")
            
        except Exception as e:
            logger.warning(f"Failed to setup Prometheus metrics: {e}")
            self.prometheus_enabled = False
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        Args:
            name: Counter name
            value: Increment value (default 1.0)
            labels: Optional labels for the metric
        """
        labels = labels or {}
        
        with self._lock:
            # Update in-process counter
            counter_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            self._counters[counter_key] += value
            
            # Update Prometheus counter if enabled
            if self.prometheus_enabled and name in self.prometheus_counters:
                try:
                    self.prometheus_counters[name].labels(**labels).inc(value)
                except Exception as e:
                    logger.warning(f"Failed to update Prometheus counter {name}: {e}")
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.
        
        Args:
            name: Gauge name
            value: Gauge value
            labels: Optional labels for the metric
        """
        labels = labels or {}
        
        with self._lock:
            # Update in-process gauge
            gauge_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            self._gauges[gauge_key] = value
            
            # Update Prometheus gauge if enabled
            if self.prometheus_enabled and name in self.prometheus_gauges:
                try:
                    self.prometheus_gauges[name].labels(**labels).set(value)
                except Exception as e:
                    logger.warning(f"Failed to update Prometheus gauge {name}: {e}")
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a value in a histogram metric.
        
        Args:
            name: Histogram name
            value: Observed value
            labels: Optional labels for the metric
        """
        labels = labels or {}
        
        with self._lock:
            # Update in-process histogram
            hist_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
            self._histograms[hist_key].append(value)
            
            # Update Prometheus histogram if enabled
            if self.prometheus_enabled and name in self.prometheus_histograms:
                try:
                    self.prometheus_histograms[name].labels(**labels).observe(value)
                except Exception as e:
                    logger.warning(f"Failed to update Prometheus histogram {name}: {e}")
    
    def get_counter_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Get current counter value."""
        labels = labels or {}
        counter_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        with self._lock:
            return self._counters.get(counter_key, 0)
    
    def get_gauge_value(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get current gauge value."""
        labels = labels or {}
        gauge_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        with self._lock:
            return self._gauges.get(gauge_key, 0.0)
    
    def get_histogram_stats(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get histogram statistics."""
        labels = labels or {}
        hist_key = f"{name}:{':'.join(f'{k}={v}' for k, v in sorted(labels.items()))}"
        with self._lock:
            values = self._histograms.get(hist_key, [])
            if not values:
                return {'count': 0, 'sum': 0.0, 'avg': 0.0, 'min': 0.0, 'max': 0.0}
            
            return {
                'count': len(values),
                'sum': sum(values),
                'avg': sum(values) / len(values),
                'min': min(values),
                'max': max(values)
            }
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        with self._lock:
            return {
                'counters': dict(self._counters),
                'gauges': dict(self._gauges),
                'histograms': {k: self.get_histogram_stats('', {}) for k in self._histograms.keys()}
            }
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
    
    # Convenience methods for validation-specific metrics
    def record_shortcut_applied(self, rule_type: str, evidence_score: float):
        """Record that evidence shortcut was applied."""
        evidence_range = self._get_score_range(evidence_score)
        self.increment_counter('shortcut_applied', labels={
            'rule_type': rule_type,
            'evidence_score_range': evidence_range
        })
    
    def record_confidence_floor_triggered(self, rule_type: str, floor_type: str = 'soft'):
        """Record that confidence floor was triggered."""
        self.increment_counter('confidence_floor_triggered', labels={
            'rule_type': rule_type,
            'floor_type': floor_type
        })
    
    def record_consolidation_adjustment(self, adjustment_type: str, rule_type: str):
        """Record confidence adjustment during consolidation."""
        self.increment_counter('consolidation_confidence_adjustments', labels={
            'adjustment_type': adjustment_type,
            'rule_type': rule_type
        })
    
    def record_negative_evidence(self, evidence_type: str, confidence: float):
        """Record negative evidence detection."""
        confidence_range = self._get_score_range(confidence)
        self.increment_counter('negative_evidence_detected', labels={
            'evidence_type': evidence_type,
            'confidence_range': confidence_range
        })
    
    def record_pipeline_execution(self, stage: str, result: str):
        """Record pipeline execution."""
        self.increment_counter('validation_pipeline_executions', labels={
            'stage': stage,
            'result': result
        })
    
    def record_validation_duration(self, stage: str, rule_type: str, duration: float):
        """Record validation duration."""
        self.observe_histogram('validation_duration', duration, labels={
            'stage': stage,
            'rule_type': rule_type
        })
    
    def _get_score_range(self, score: float) -> str:
        """Convert score to range label."""
        if score >= 0.9:
            return 'very_high'
        elif score >= 0.8:
            return 'high'
        elif score >= 0.6:
            return 'medium'
        elif score >= 0.4:
            return 'low'
        else:
            return 'very_low'

# Global metrics instance
_global_metrics: Optional[ValidationMetrics] = None

def get_metrics() -> ValidationMetrics:
    """Get or create global metrics instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = ValidationMetrics()
    return _global_metrics

def reset_global_metrics():
    """Reset global metrics instance (useful for testing)."""
    global _global_metrics
    if _global_metrics:
        _global_metrics.reset_metrics()
    _global_metrics = None

# Convenience functions for direct access
def increment_counter(name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
    """Increment a counter metric using global instance."""
    get_metrics().increment_counter(name, value, labels)

def set_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Set a gauge metric using global instance."""
    get_metrics().set_gauge(name, value, labels)

def observe_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """Observe a histogram metric using global instance."""
    get_metrics().observe_histogram(name, value, labels)

def record_shortcut_applied(rule_type: str, evidence_score: float):
    """Record shortcut applied using global instance."""
    get_metrics().record_shortcut_applied(rule_type, evidence_score)

def record_confidence_floor_triggered(rule_type: str, floor_type: str = 'soft'):
    """Record confidence floor triggered using global instance."""
    get_metrics().record_confidence_floor_triggered(rule_type, floor_type)

def record_consolidation_adjustment(adjustment_type: str, rule_type: str):
    """Record consolidation adjustment using global instance."""
    get_metrics().record_consolidation_adjustment(adjustment_type, rule_type)

def record_negative_evidence(evidence_type: str, confidence: float):
    """Record negative evidence using global instance."""
    get_metrics().record_negative_evidence(evidence_type, confidence)

def record_pipeline_execution(stage: str, result: str):
    """Record pipeline execution using global instance."""
    get_metrics().record_pipeline_execution(stage, result)

def record_validation_duration(stage: str, rule_type: str, duration: float):
    """Record validation duration using global instance."""
    get_metrics().record_validation_duration(stage, rule_type, duration)
