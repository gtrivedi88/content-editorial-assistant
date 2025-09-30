"""
Instruction Template Performance Tracker
Tracks success rates of different instruction templates and enables evidence-based template selection.

Integrates with existing ReliabilityTuner and ValidationMetrics for comprehensive performance monitoring.
"""

import os
import yaml
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


@dataclass
class TemplateUsageRecord:
    """Record of instruction template usage and outcome."""
    rule_type: str
    template_style: str
    template_id: str
    success: bool
    confidence_score: float
    processing_time_ms: float
    error_context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    feedback_source: str = "automatic"  # "automatic", "user_feedback", "validation_pipeline"


@dataclass  
class TemplatePerformanceMetrics:
    """Performance metrics for a specific instruction template."""
    rule_type: str
    template_style: str
    total_usage: int
    successful_usage: int
    failed_usage: int
    success_rate: float
    average_confidence: float
    average_processing_time: float
    confidence_correlation: float  # How well template confidence predicts success
    last_updated: datetime
    trending_direction: str  # "improving", "declining", "stable"
    
    def update_metrics(self, records: List[TemplateUsageRecord]):
        """Update metrics based on new usage records."""
        if not records:
            return
        
        self.total_usage = len(records)
        self.successful_usage = sum(1 for r in records if r.success)
        self.failed_usage = self.total_usage - self.successful_usage
        
        self.success_rate = self.successful_usage / self.total_usage if self.total_usage > 0 else 0.0
        self.average_confidence = sum(r.confidence_score for r in records) / self.total_usage if self.total_usage > 0 else 0.0
        self.average_processing_time = sum(r.processing_time_ms for r in records) / self.total_usage if self.total_usage > 0 else 0.0
        
        # Calculate confidence correlation (how well confidence predicts success)
        if self.total_usage > 5:  # Need sufficient data
            successful_confidences = [r.confidence_score for r in records if r.success]
            failed_confidences = [r.confidence_score for r in records if not r.success]
            
            if successful_confidences and failed_confidences:
                avg_success_conf = sum(successful_confidences) / len(successful_confidences)
                avg_fail_conf = sum(failed_confidences) / len(failed_confidences)
                self.confidence_correlation = avg_success_conf - avg_fail_conf
            else:
                self.confidence_correlation = 0.0
        else:
            self.confidence_correlation = 0.0
        
        self.last_updated = datetime.utcnow()


class InstructionTemplateTracker:
    """
    Tracks performance of instruction templates and enables evidence-based selection.
    
    Integrates with existing validation infrastructure for comprehensive monitoring.
    """
    
    def __init__(self, 
                 config_path: Optional[str] = None,
                 storage_path: Optional[str] = None,
                 min_usage_threshold: int = 5,
                 confidence_weight: float = 0.3,
                 recency_weight: float = 0.2):
        """
        Initialize template tracker.
        
        Args:
            config_path: Path to assembly_line_config.yaml
            storage_path: Path to store template performance data
            min_usage_threshold: Minimum usage before reliable metrics
            confidence_weight: Weight for confidence in selection algorithm
            recency_weight: Weight for recent performance in selection
        """
        self.min_usage_threshold = min_usage_threshold
        self.confidence_weight = confidence_weight
        self.recency_weight = recency_weight
        
        # Set up paths
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '../../rewriter/assembly_line_config.yaml')
        if storage_path is None:
            storage_path = os.path.join(os.path.dirname(__file__), 'template_performance.json')
            
        self.config_path = config_path
        self.storage_path = storage_path
        
        # Load configuration and performance data
        self.templates_config = self._load_templates_config()
        self.performance_data = self._load_performance_data()
        self.usage_records = []  # In-memory cache of recent records
        
        logger.info(f"InstructionTemplateTracker initialized with {len(self.templates_config)} rule types")
    
    def _load_templates_config(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load evidence-based templates configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            evidence_templates = config.get('evidence_based_templates', {})
            logger.info(f"Loaded {len(evidence_templates)} rule types with evidence-based templates")
            return evidence_templates
        
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load templates config from {self.config_path}: {e}")
            return {}
    
    def _load_performance_data(self) -> Dict[str, Dict[str, TemplatePerformanceMetrics]]:
        """Load existing performance data."""
        if not os.path.exists(self.storage_path):
            return defaultdict(dict)
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            performance_data = defaultdict(dict)
            
            # Convert JSON back to TemplatePerformanceMetrics objects
            for rule_type, templates in data.items():
                for template_style, metrics_data in templates.items():
                    metrics = TemplatePerformanceMetrics(
                        rule_type=metrics_data['rule_type'],
                        template_style=metrics_data['template_style'],
                        total_usage=metrics_data['total_usage'],
                        successful_usage=metrics_data['successful_usage'],
                        failed_usage=metrics_data['failed_usage'],
                        success_rate=metrics_data['success_rate'],
                        average_confidence=metrics_data['average_confidence'],
                        average_processing_time=metrics_data['average_processing_time'],
                        confidence_correlation=metrics_data['confidence_correlation'],
                        last_updated=datetime.fromisoformat(metrics_data['last_updated']),
                        trending_direction=metrics_data.get('trending_direction', 'stable')
                    )
                    performance_data[rule_type][template_style] = metrics
            
            logger.info(f"Loaded performance data for {len(performance_data)} rule types")
            return performance_data
        
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Could not load performance data from {self.storage_path}: {e}")
            return defaultdict(dict)
    
    def select_best_template(self, rule_type: str, context: Dict[str, Any] = None) -> Tuple[str, str]:
        """
        Select the best performing template for a rule type.
        
        Args:
            rule_type: The rule type to get template for
            context: Optional context for template selection (future enhancement)
            
        Returns:
            Tuple of (template_style, template_text)
        """
        available_templates = self.templates_config.get(rule_type, [])
        
        if not available_templates:
            logger.warning(f"No evidence-based templates found for {rule_type}")
            return "default", ""
        
        if len(available_templates) == 1:
            template = available_templates[0]
            return template['style'], template['template']
        
        # Score each template based on performance metrics
        template_scores = []
        
        for template in available_templates:
            style = template['style']
            base_success_rate = template.get('success_rate', 0.5)
            
            # Get actual performance metrics if available
            metrics = self.performance_data.get(rule_type, {}).get(style)
            
            if metrics and metrics.total_usage >= self.min_usage_threshold:
                # Use actual performance data
                performance_score = metrics.success_rate
                confidence_boost = metrics.average_confidence * self.confidence_weight
                
                # Recency boost for recently updated templates
                days_since_update = (datetime.utcnow() - metrics.last_updated).days
                recency_boost = max(0, (30 - days_since_update) / 30) * self.recency_weight
                
                final_score = performance_score + confidence_boost + recency_boost
                
                logger.debug(f"Template {rule_type}/{style}: performance={performance_score:.3f}, confidence_boost={confidence_boost:.3f}, recency_boost={recency_boost:.3f}, final={final_score:.3f}")
            else:
                # Use initial success rate from config
                final_score = base_success_rate
                logger.debug(f"Template {rule_type}/{style}: using base rate {final_score:.3f} (insufficient usage data)")
            
            template_scores.append((final_score, style, template['template']))
        
        # Select highest scoring template
        template_scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_style, best_template = template_scores[0]
        
        logger.debug(f"Selected template {rule_type}/{best_style} with score {best_score:.3f}")
        
        return best_style, best_template
    
    def record_template_usage(self, 
                            rule_type: str, 
                            template_style: str,
                            success: bool,
                            confidence_score: float = 0.0,
                            processing_time_ms: float = 0.0,
                            error_context: Dict[str, Any] = None,
                            session_id: str = None,
                            feedback_source: str = "automatic"):
        """
        Record usage and outcome of an instruction template.
        
        Args:
            rule_type: Rule type that used the template
            template_style: Style of template that was used
            success: Whether the template usage was successful
            confidence_score: Confidence score of the result
            processing_time_ms: Processing time in milliseconds
            error_context: Additional context about the error
            session_id: Session ID for tracking
            feedback_source: Source of feedback (automatic, user_feedback, etc.)
        """
        record = TemplateUsageRecord(
            rule_type=rule_type,
            template_style=template_style,
            template_id=f"{rule_type}_{template_style}",
            success=success,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            error_context=error_context or {},
            session_id=session_id,
            feedback_source=feedback_source
        )
        
        self.usage_records.append(record)
        
        # Update performance metrics
        self._update_performance_metrics(rule_type, template_style, [record])
        
        logger.debug(f"Recorded template usage: {rule_type}/{template_style} -> {'success' if success else 'failure'} (conf={confidence_score:.3f})")
    
    def _update_performance_metrics(self, rule_type: str, template_style: str, new_records: List[TemplateUsageRecord]):
        """Update performance metrics for a template based on new usage records."""
        # Get or create metrics object
        if rule_type not in self.performance_data:
            self.performance_data[rule_type] = {}
        
        if template_style not in self.performance_data[rule_type]:
            self.performance_data[rule_type][template_style] = TemplatePerformanceMetrics(
                rule_type=rule_type,
                template_style=template_style,
                total_usage=0,
                successful_usage=0,
                failed_usage=0,
                success_rate=0.0,
                average_confidence=0.0,
                average_processing_time=0.0,
                confidence_correlation=0.0,
                last_updated=datetime.utcnow(),
                trending_direction="stable"
            )
        
        metrics = self.performance_data[rule_type][template_style]
        
        # Get recent records for this template (including new ones)
        all_records = [r for r in self.usage_records if r.rule_type == rule_type and r.template_style == template_style]
        all_records.extend(new_records)
        
        # Keep only recent records (last 100 uses) to prevent stale data
        recent_records = sorted(all_records, key=lambda r: r.timestamp)[-100:]
        
        # Update metrics
        metrics.update_metrics(recent_records)
    
    def get_template_performance(self, rule_type: str, template_style: str = None) -> Dict[str, Any]:
        """Get performance metrics for templates."""
        if template_style:
            # Get specific template performance
            metrics = self.performance_data.get(rule_type, {}).get(template_style)
            if not metrics:
                return {}
            
            return {
                'rule_type': metrics.rule_type,
                'template_style': metrics.template_style,
                'success_rate': metrics.success_rate,
                'total_usage': metrics.total_usage,
                'average_confidence': metrics.average_confidence,
                'confidence_correlation': metrics.confidence_correlation,
                'last_updated': metrics.last_updated.isoformat(),
                'trending_direction': metrics.trending_direction
            }
        else:
            # Get all templates for rule type
            rule_templates = self.performance_data.get(rule_type, {})
            return {
                style: {
                    'success_rate': metrics.success_rate,
                    'total_usage': metrics.total_usage,
                    'average_confidence': metrics.average_confidence,
                    'last_updated': metrics.last_updated.isoformat()
                }
                for style, metrics in rule_templates.items()
            }
    
    def save_performance_data(self):
        """Save performance data to storage."""
        try:
            # Convert to JSON-serializable format
            data = {}
            for rule_type, templates in self.performance_data.items():
                data[rule_type] = {}
                for template_style, metrics in templates.items():
                    data[rule_type][template_style] = {
                        'rule_type': metrics.rule_type,
                        'template_style': metrics.template_style,
                        'total_usage': metrics.total_usage,
                        'successful_usage': metrics.successful_usage,
                        'failed_usage': metrics.failed_usage,
                        'success_rate': metrics.success_rate,
                        'average_confidence': metrics.average_confidence,
                        'average_processing_time': metrics.average_processing_time,
                        'confidence_correlation': metrics.confidence_correlation,
                        'last_updated': metrics.last_updated.isoformat(),
                        'trending_direction': metrics.trending_direction
                    }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Save with backup
            backup_path = f"{self.storage_path}.backup"
            if os.path.exists(self.storage_path):
                os.rename(self.storage_path, backup_path)
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Remove backup on successful save
            if os.path.exists(backup_path):
                os.remove(backup_path)
            
            logger.info(f"Saved template performance data to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to save template performance data: {e}")
            # Restore backup if save failed
            backup_path = f"{self.storage_path}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, self.storage_path)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        total_templates = sum(len(templates) for templates in self.templates_config.values())
        tracked_templates = sum(len(templates) for templates in self.performance_data.values())
        total_usage = sum(
            metrics.total_usage 
            for rule_templates in self.performance_data.values()
            for metrics in rule_templates.values()
        )
        
        return {
            'total_rule_types': len(self.templates_config),
            'total_templates': total_templates,
            'tracked_templates': tracked_templates,
            'total_usage_records': total_usage,
            'recent_records': len(self.usage_records),
            'min_usage_threshold': self.min_usage_threshold,
            'tracking_coverage': tracked_templates / total_templates if total_templates > 0 else 0.0
        }


# Global instance for easy access
_global_tracker: Optional[InstructionTemplateTracker] = None


def get_template_tracker() -> InstructionTemplateTracker:
    """Get or create global template tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = InstructionTemplateTracker()
    return _global_tracker


def select_instruction_template(rule_type: str, context: Dict[str, Any] = None) -> Tuple[str, str]:
    """Convenience function to select best template using global tracker."""
    return get_template_tracker().select_best_template(rule_type, context)


def record_instruction_success(rule_type: str, 
                             template_style: str,
                             success: bool,
                             confidence_score: float = 0.0,
                             processing_time_ms: float = 0.0,
                             **kwargs):
    """Convenience function to record template usage using global tracker."""
    get_template_tracker().record_template_usage(
        rule_type=rule_type,
        template_style=template_style,
        success=success,
        confidence_score=confidence_score,
        processing_time_ms=processing_time_ms,
        **kwargs
    )


if __name__ == '__main__':
    # Demo/test the system
    print("🧪 Testing Instruction Template Tracker...")
    
    tracker = InstructionTemplateTracker()
    
    print(f"📊 System stats: {tracker.get_system_stats()}")
    
    # Test template selection
    style, template = tracker.select_best_template('verbs')
    print(f"🎯 Best template for 'verbs': {style}")
    print(f"📝 Template: {template[:100]}...")
    
    # Test recording usage
    tracker.record_template_usage('verbs', style, success=True, confidence_score=0.92)
    print(f"✅ Recorded successful usage")
    
    # Get performance data
    performance = tracker.get_template_performance('verbs', style)
    print(f"📈 Performance: {performance}")
    
    print("🎉 Template tracker test complete!")
