"""
Test Validation Monitoring Metrics

Focused tests for the monitoring system as per Upgrade 9.
"""

import pytest
import os
from unittest.mock import patch

from validation.monitoring.metrics import (
    ValidationMetrics, get_metrics, reset_global_metrics,
    record_shortcut_applied, record_confidence_floor_triggered,
    record_consolidation_adjustment, record_pipeline_execution
)


class TestMetricsBasics:
    """Test basic metrics functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_global_metrics()
        self.metrics = ValidationMetrics(enable_prometheus=False)
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_global_metrics()
    
    def test_counter_operations(self):
        """Test counter increment and retrieval."""
        self.metrics.increment_counter('test_counter')
        assert self.metrics.get_counter_value('test_counter') == 1
        
        self.metrics.increment_counter('test_counter', 5)
        assert self.metrics.get_counter_value('test_counter') == 6
    
    def test_validation_specific_metrics(self):
        """Test validation-specific metric recording."""
        # Test shortcut applied
        self.metrics.record_shortcut_applied('grammar', 0.90)
        shortcut_count = self.metrics.get_counter_value(
            'shortcut_applied',
            labels={'rule_type': 'grammar', 'evidence_score_range': 'very_high'}
        )
        assert shortcut_count == 1
        
        # Test confidence floor triggered
        self.metrics.record_confidence_floor_triggered('punctuation', 'soft')
        floor_count = self.metrics.get_counter_value(
            'confidence_floor_triggered',
            labels={'rule_type': 'punctuation', 'floor_type': 'soft'}
        )
        assert floor_count == 1
        
        # Test consolidation adjustment
        self.metrics.record_consolidation_adjustment('averaging', 'spelling')
        adjust_count = self.metrics.get_counter_value(
            'consolidation_confidence_adjustments',
            labels={'adjustment_type': 'averaging', 'rule_type': 'spelling'}
        )
        assert adjust_count == 1
    
    def test_prometheus_integration(self):
        """Test Prometheus integration behavior."""
        # Test with Prometheus disabled
        with patch.dict(os.environ, {'ENABLE_PROMETHEUS_METRICS': 'false'}):
            metrics = ValidationMetrics()
            assert not metrics.prometheus_enabled
        
        # Test graceful fallback when Prometheus not available
        with patch('validation.monitoring.metrics.PROMETHEUS_AVAILABLE', False):
            metrics = ValidationMetrics(enable_prometheus=True)
            assert not metrics.prometheus_enabled


class TestIntegrationMonitoring:
    """Test monitoring integration with validation components."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_global_metrics()
    
    def teardown_method(self):
        """Cleanup after each test."""
        reset_global_metrics()
    
    def test_error_consolidator_monitoring(self):
        """Test that consolidator triggers monitoring correctly."""
        from error_consolidation.consolidator import ErrorConsolidator
        
        # Create test errors
        test_errors = [
            {
                'type': 'grammar',
                'message': 'Test error 1',
                'span': (0, 10),
                'confidence_score': 0.8,
                'suggestions': ['Fix 1']
            },
            {
                'type': 'grammar', 
                'message': 'Test error 2',
                'span': (5, 15),
                'confidence_score': 0.7,
                'suggestions': ['Fix 2']
            },
            {
                'type': 'spelling',
                'message': 'Low confidence error',
                'span': (20, 25),
                'confidence_score': 0.1,  # Below threshold
                'suggestions': ['Fix 3']
            }
        ]
        
        # Process with consolidator
        consolidator = ErrorConsolidator(
            enable_enhanced_validation=True,
            confidence_threshold=0.35
        )
        
        consolidated = consolidator.consolidate(test_errors)
        
        # Check monitoring was triggered
        metrics = get_metrics()
        
        # Should record confidence floor for low confidence error
        floor_count = metrics.get_counter_value(
            'confidence_floor_triggered',
            labels={'rule_type': 'spelling', 'floor_type': 'universal_threshold'}
        )
        assert floor_count == 1
        
        # Verify that at least one error was filtered (low confidence)
        assert len(consolidated) < len(test_errors), "Should have filtered some errors"
        
        # The low confidence spelling error should have been filtered out
        consolidated_types = [error.get('type') for error in consolidated]
        assert 'spelling' not in consolidated_types, "Low confidence error should be filtered"
        assert 'grammar' in consolidated_types, "High confidence errors should remain"


if __name__ == '__main__':
    pytest.main([__file__])
