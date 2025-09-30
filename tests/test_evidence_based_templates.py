"""
Comprehensive Tests for Evidence-Based Instruction Templates
Tests the complete learning system that optimizes AI instruction effectiveness.
"""

import pytest
import sys
import os
import tempfile
import json
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from validation.feedback.instruction_template_tracker import InstructionTemplateTracker, TemplateUsageRecord
from rewriter.prompts import PromptGenerator


class TestInstructionTemplateTracker:
    """Test the core template tracking and performance measurement system."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary directory with test configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test assembly_line_config.yaml
            config_data = {
                'evidence_based_templates': {
                    'verbs': [
                        {
                            'style': 'direct',
                            'template': 'Change to present tense. "will provide" → "provides".',
                            'success_rate': 0.92,
                            'usage_count': 0,
                            'last_updated': None
                        },
                        {
                            'style': 'detailed',
                            'template': 'Convert passive voice to active voice with clear actor specification...',
                            'success_rate': 0.87,
                            'usage_count': 0,
                            'last_updated': None
                        }
                    ],
                    'contractions': [
                        {
                            'style': 'simple',
                            'template': 'Expand contractions. "you\'ll" → "you will".',
                            'success_rate': 0.95,
                            'usage_count': 0,
                            'last_updated': None
                        },
                        {
                            'style': 'comprehensive',
                            'template': 'Expand all contractions to their full forms for formal writing...',
                            'success_rate': 0.91,
                            'usage_count': 0,
                            'last_updated': None
                        }
                    ]
                }
            }
            
            config_path = os.path.join(temp_dir, 'assembly_line_config.yaml')
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            storage_path = os.path.join(temp_dir, 'template_performance.json')
            
            yield config_path, storage_path
    
    def test_template_tracker_initialization(self, temp_config_dir):
        """Test that template tracker initializes correctly."""
        config_path, storage_path = temp_config_dir
        
        tracker = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        assert len(tracker.templates_config) == 2  # verbs and contractions
        assert 'verbs' in tracker.templates_config
        assert 'contractions' in tracker.templates_config
        assert len(tracker.templates_config['verbs']) == 2  # direct and detailed styles
        
        # Test system stats
        stats = tracker.get_system_stats()
        assert stats['total_rule_types'] == 2
        assert stats['total_templates'] == 4  # 2 rules × 2 templates each
    
    def test_template_selection_by_performance(self, temp_config_dir):
        """Test that template selection prioritizes higher performing templates."""
        config_path, storage_path = temp_config_dir
        
        tracker = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        # Test selection for verbs (direct style has higher success rate: 0.92 vs 0.87)
        style, template = tracker.select_best_template('verbs')
        
        assert style == 'direct'  # Should select higher performing template
        assert 'present tense' in template
    
    def test_template_performance_recording(self, temp_config_dir):
        """Test recording and updating template performance metrics."""
        config_path, storage_path = temp_config_dir
        
        tracker = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        # Record several usage instances
        tracker.record_template_usage(
            rule_type='verbs',
            template_style='direct',
            success=True,
            confidence_score=0.95,
            processing_time_ms=150.0
        )
        
        tracker.record_template_usage(
            rule_type='verbs',
            template_style='direct',
            success=True,
            confidence_score=0.88,
            processing_time_ms=120.0
        )
        
        tracker.record_template_usage(
            rule_type='verbs',
            template_style='direct',
            success=False,
            confidence_score=0.60,
            processing_time_ms=200.0
        )
        
        # Get performance metrics
        performance = tracker.get_template_performance('verbs', 'direct')
        
        assert performance['total_usage'] == 3
        assert performance['success_rate'] == 2/3  # 2 successes out of 3 attempts
        assert performance['average_confidence'] == (0.95 + 0.88 + 0.60) / 3
    
    def test_template_selection_with_actual_performance(self, temp_config_dir):
        """Test that template selection adapts based on actual usage data."""
        config_path, storage_path = temp_config_dir
        
        tracker = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path,
            min_usage_threshold=3
        )
        
        # Initially, 'direct' should win (0.92 vs 0.87 base success rate)
        style, template = tracker.select_best_template('verbs')
        assert style == 'direct'
        
        # Record poor performance for 'direct' style
        for _ in range(5):
            tracker.record_template_usage(
                rule_type='verbs',
                template_style='direct',
                success=False,
                confidence_score=0.40
            )
        
        # Record good performance for 'detailed' style
        for _ in range(5):
            tracker.record_template_usage(
                rule_type='verbs',
                template_style='detailed',
                success=True,
                confidence_score=0.95
            )
        
        # Now 'detailed' should win due to better actual performance
        style, template = tracker.select_best_template('verbs')
        assert style == 'detailed'
    
    def test_data_persistence(self, temp_config_dir):
        """Test that performance data persists across tracker instances."""
        config_path, storage_path = temp_config_dir
        
        # Create first tracker instance and record data
        tracker1 = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        tracker1.record_template_usage(
            rule_type='contractions',
            template_style='simple',
            success=True,
            confidence_score=0.98
        )
        
        tracker1.save_performance_data()
        
        # Create second tracker instance and verify data is loaded
        tracker2 = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        performance = tracker2.get_template_performance('contractions', 'simple')
        assert performance['total_usage'] == 1
        assert performance['success_rate'] == 1.0


class TestPromptGeneratorIntegration:
    """Test integration of evidence-based templates with PromptGenerator."""
    
    @pytest.fixture
    def mock_template_tracker(self):
        """Create mock template tracker for testing."""
        mock_tracker = Mock()
        mock_tracker.select_best_template.return_value = (
            'direct',
            'Change to present tense. "will provide" → "provides".'
        )
        return mock_tracker
    
    def test_prompt_generator_template_selection(self, mock_template_tracker):
        """Test that PromptGenerator uses evidence-based template selection."""
        # Create prompt generator with mocked template tracking
        prompt_gen = PromptGenerator()
        prompt_gen.template_tracking_enabled = True
        prompt_gen.template_tracker = mock_template_tracker
        
        # Test instruction creation
        instruction = prompt_gen._create_enhanced_instruction(
            error_type='verbs',
            spacy_message='Tense issue detected',
            spacy_suggestions=['provides'],
            flagged_text='will provide',
            context='text'
        )
        
        # Verify template tracker was called
        mock_template_tracker.select_best_template.assert_called_once_with('verbs')
        
        # Verify instruction contains evidence-based template
        assert 'Change to present tense' in instruction
        assert '**Template**: direct' in instruction
    
    def test_template_feedback_recording(self, mock_template_tracker):
        """Test recording template feedback through PromptGenerator."""
        prompt_gen = PromptGenerator()
        prompt_gen.template_tracking_enabled = True
        prompt_gen.template_tracker = mock_template_tracker
        
        # Record feedback
        prompt_gen.record_template_feedback(
            error_type='verbs',
            template_style='direct',
            success=True,
            confidence_score=0.92
        )
        
        # Verify feedback was recorded
        mock_template_tracker.record_template_usage.assert_called_once()
        call_args = mock_template_tracker.record_template_usage.call_args
        assert call_args[1]['rule_type'] == 'verbs'
        assert call_args[1]['template_style'] == 'direct'
        assert call_args[1]['success'] is True
        assert call_args[1]['confidence_score'] == 0.92
    
    def test_fallback_to_legacy_templates(self):
        """Test fallback to legacy templates when evidence-based tracking is unavailable."""
        prompt_gen = PromptGenerator()
        prompt_gen.template_tracking_enabled = False
        
        # Should fall back to legacy template system
        instruction = prompt_gen._create_enhanced_instruction(
            error_type='verbs',
            spacy_message='Tense issue detected',
            spacy_suggestions=['provides'],
            flagged_text='will provide',
            context='text'
        )
        
        # Should not contain template metadata (evidence-based feature)
        assert '**Template**:' not in instruction
        # Should contain legacy template structure
        assert '**Rule**:' in instruction


class TestEndToEndEvidenceBasedSystem:
    """Test the complete evidence-based instruction template system."""
    
    def test_complete_learning_cycle(self):
        """Test the complete cycle: selection → usage → feedback → improved selection."""
        print("\n" + "="*80)
        print("🧪 EVIDENCE-BASED INSTRUCTION TEMPLATES - COMPLETE LEARNING CYCLE TEST")
        print("="*80)
        
        # This test simulates the complete learning cycle
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup configuration
            config_data = {
                'evidence_based_templates': {
                    'test_rule': [
                        {
                            'style': 'baseline',
                            'template': 'Basic instruction for test rule.',
                            'success_rate': 0.70,
                            'usage_count': 0,
                            'last_updated': None
                        },
                        {
                            'style': 'enhanced',
                            'template': 'Enhanced instruction with detailed guidance for test rule.',
                            'success_rate': 0.68,  # Initially lower
                            'usage_count': 0,
                            'last_updated': None
                        }
                    ]
                }
            }
            
            config_path = os.path.join(temp_dir, 'test_config.yaml')
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            storage_path = os.path.join(temp_dir, 'test_performance.json')
            
            tracker = InstructionTemplateTracker(
                config_path=config_path,
                storage_path=storage_path,
                min_usage_threshold=3
            )
            
            print(f"📊 Initial setup: {tracker.get_system_stats()}")
            
            # Phase 1: Initial selection should favor 'baseline' (higher initial success rate)
            style1, template1 = tracker.select_best_template('test_rule')
            print(f"🎯 Phase 1 - Initial selection: {style1} (expected: baseline)")
            assert style1 == 'baseline'
            
            # Phase 2: Simulate 'baseline' performing poorly
            print(f"📉 Phase 2 - Recording poor performance for baseline...")
            for i in range(5):
                tracker.record_template_usage(
                    rule_type='test_rule',
                    template_style='baseline',
                    success=False,
                    confidence_score=0.30 + i * 0.02
                )
            
            # Phase 3: Simulate 'enhanced' performing well
            print(f"📈 Phase 3 - Recording good performance for enhanced...")
            for i in range(5):
                tracker.record_template_usage(
                    rule_type='test_rule',
                    template_style='enhanced',
                    success=True,
                    confidence_score=0.90 + i * 0.01
                )
            
            # Phase 4: Selection should now favor 'enhanced' due to better actual performance
            style2, template2 = tracker.select_best_template('test_rule')
            print(f"🎯 Phase 4 - Adapted selection: {style2} (expected: enhanced)")
            
            # Get performance metrics
            baseline_perf = tracker.get_template_performance('test_rule', 'baseline')
            enhanced_perf = tracker.get_template_performance('test_rule', 'enhanced')
            
            print(f"📊 Baseline performance: {baseline_perf['success_rate']:.3f} success rate")
            print(f"📊 Enhanced performance: {enhanced_perf['success_rate']:.3f} success rate")
            
            assert style2 == 'enhanced'  # Should switch to better performing template
            assert enhanced_perf['success_rate'] > baseline_perf['success_rate']
            
            # Phase 5: Test persistence
            tracker.save_performance_data()
            
            # Create new tracker instance and verify learning persists
            tracker2 = InstructionTemplateTracker(
                config_path=config_path,
                storage_path=storage_path,
                min_usage_threshold=3
            )
            
            style3, template3 = tracker2.select_best_template('test_rule')
            print(f"🎯 Phase 5 - Persistent learning: {style3} (expected: enhanced)")
            assert style3 == 'enhanced'  # Learning should persist
            
            print(f"✅ Complete learning cycle successful!")
            print(f"   Initial choice: {style1} → Final choice: {style3}")
            print(f"   System learned to prefer higher-performing templates")
            print(f"   Learning persisted across tracker instances")
            
            return True
    
    def test_integration_with_consolidation(self):
        """Test that evidence-based templates work with instruction consolidation."""
        print(f"\n📋 Testing integration with Instruction Consolidation...")
        
        # This would test that the consolidated instructions use the best-performing
        # templates for each error type, combining both systems effectively
        
        # For now, we verify the systems can coexist
        prompt_gen = PromptGenerator()
        
        # Check that template tracking is available
        template_available = hasattr(prompt_gen, 'template_tracking_enabled')
        print(f"Template tracking integration: {'✅ Available' if template_available else '❌ Missing'}")
        
        return template_available


def run_evidence_based_template_demo():
    """
    Run comprehensive demonstration of evidence-based instruction templates.
    """
    print("🚀 Starting Evidence-Based Instruction Templates Demo...")
    
    # Test core template tracking
    print("\n1. Testing Template Tracker...")
    test_instance = TestInstructionTemplateTracker()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_data = {
            'evidence_based_templates': {
                'demo_rule': [
                    {
                        'style': 'concise',
                        'template': 'Brief instruction.',
                        'success_rate': 0.85,
                        'usage_count': 0
                    },
                    {
                        'style': 'verbose',
                        'template': 'Detailed instruction with comprehensive guidance and examples.',
                        'success_rate': 0.78,
                        'usage_count': 0
                    }
                ]
            }
        }
        
        config_path = os.path.join(temp_dir, 'demo_config.yaml')
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        storage_path = os.path.join(temp_dir, 'demo_performance.json')
        
        tracker = InstructionTemplateTracker(
            config_path=config_path,
            storage_path=storage_path
        )
        
        print(f"   ✅ Tracker initialized with {tracker.get_system_stats()['total_templates']} templates")
        
        # Test selection
        style, template = tracker.select_best_template('demo_rule')
        print(f"   🎯 Selected template: {style} ({template[:30]}...)")
        
        # Test feedback
        tracker.record_template_usage('demo_rule', style, True, 0.92)
        print(f"   📊 Recorded feedback successfully")
    
    # Test end-to-end learning
    print(f"\n2. Testing Complete Learning Cycle...")
    end_to_end_test = TestEndToEndEvidenceBasedSystem()
    learning_success = end_to_end_test.test_complete_learning_cycle()
    
    # Test integration
    print(f"\n3. Testing Integration...")
    integration_success = end_to_end_test.test_integration_with_consolidation()
    
    print(f"\n" + "="*80)
    print(f"🎉 EVIDENCE-BASED TEMPLATES DEMO COMPLETE!")
    print(f"="*80)
    
    if learning_success and integration_success:
        print(f"✅ All systems operational and learning successfully!")
        print(f"🚀 Ready to optimize AI instruction effectiveness in production!")
    else:
        print(f"⚠️  Some components need attention - check logs above")
        
    return learning_success and integration_success


if __name__ == '__main__':
    # Run comprehensive demo
    success = run_evidence_based_template_demo()
    
    if success:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Deploy to production environment")
        print(f"   2. Monitor template performance in real-world usage")
        print(f"   3. Collect user feedback to further refine templates")
        print(f"   4. Expand to more rule types based on performance data")
    else:
        print(f"\n❌ Fix issues before deployment")
