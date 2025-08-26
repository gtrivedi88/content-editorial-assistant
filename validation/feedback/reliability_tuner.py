"""
Feedback-informed Reliability Calibration System (Upgrade 6)
Periodically adjusts rule reliability coefficients based on user feedback to create a closed-loop system.
"""

import json
import yaml
import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict, Counter
import statistics

from validation.confidence.rule_reliability import get_rule_reliability_coefficient


@dataclass
class FeedbackEntry:
    """Structured feedback entry from user interactions."""
    feedback_id: str
    session_id: str
    error_id: str
    error_type: str
    error_message: str
    feedback_type: str  # 'correct', 'incorrect', 'unclear', etc.
    confidence_score: float
    user_reason: Optional[str]
    timestamp: str
    user_agent: Optional[str] = None
    ip_hash: Optional[str] = None


@dataclass
class RulePerformanceMetrics:
    """Performance metrics for a specific rule type."""
    rule_type: str
    total_feedback: int
    correct_feedback: int
    incorrect_feedback: int
    unclear_feedback: int
    precision: float  # correct / (correct + incorrect)
    false_positive_rate: float  # incorrect / total
    avg_confidence: float
    confidence_correlation: float  # correlation between confidence and correctness
    current_reliability: float
    proposed_reliability: float
    adjustment: float


class ReliabilityTuner:
    """
    Feedback-informed reliability calibration system.
    
    Analyzes user feedback to adjust rule reliability coefficients within safe bounds,
    creating a closed-loop system that improves validation accuracy over time.
    """
    
    def __init__(self, 
                 min_feedback_threshold: int = 10,
                 max_adjustment_per_run: float = 0.02,
                 min_reliability: float = 0.70,
                 max_reliability: float = 0.98,
                 confidence_weight: float = 0.3):
        """
        Initialize the reliability tuner.
        
        Args:
            min_feedback_threshold: Minimum feedback entries needed to adjust a rule
            max_adjustment_per_run: Maximum adjustment per tuning run (±0.02)
            min_reliability: Minimum allowed reliability coefficient (0.70)
            max_reliability: Maximum allowed reliability coefficient (0.98)
            confidence_weight: Weight for confidence correlation in adjustment calculation
        """
        self.min_feedback_threshold = min_feedback_threshold
        self.max_adjustment_per_run = max_adjustment_per_run
        self.min_reliability = min_reliability
        self.max_reliability = max_reliability
        self.confidence_weight = confidence_weight
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def load_feedback_data(self, feedback_paths: List[str]) -> List[FeedbackEntry]:
        """
        Load feedback data from JSONL files.
        
        Args:
            feedback_paths: List of file paths containing feedback data
            
        Returns:
            List of structured feedback entries
        """
        feedback_entries = []
        
        for path in feedback_paths:
            try:
                with open(path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            entry = FeedbackEntry(
                                feedback_id=data.get('feedback_id', ''),
                                session_id=data.get('session_id', ''),
                                error_id=data.get('error_id', ''),
                                error_type=data.get('error_type', ''),
                                error_message=data.get('error_message', ''),
                                feedback_type=data.get('feedback_type', ''),
                                confidence_score=float(data.get('confidence_score', 0.0)),
                                user_reason=data.get('user_reason'),
                                timestamp=data.get('timestamp', ''),
                                user_agent=data.get('user_agent'),
                                ip_hash=data.get('ip_hash')
                            )
                            feedback_entries.append(entry)
                            
                        except (json.JSONDecodeError, ValueError, TypeError) as e:
                            self.logger.warning(f"Skipping malformed line {line_num} in {path}: {e}")
                            continue
                            
            except FileNotFoundError:
                self.logger.warning(f"Feedback file not found: {path}")
            except Exception as e:
                self.logger.error(f"Error loading feedback from {path}: {e}")
        
        self.logger.info(f"Loaded {len(feedback_entries)} feedback entries from {len(feedback_paths)} files")
        return feedback_entries
    
    def compute_rule_precision(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, RulePerformanceMetrics]:
        """
        Compute precision and performance metrics for each rule type.
        
        Args:
            feedback_entries: List of feedback entries to analyze
            
        Returns:
            Dictionary mapping rule types to their performance metrics
        """
        # Group feedback by rule type
        rule_feedback = defaultdict(list)
        for entry in feedback_entries:
            if entry.error_type:  # Only consider entries with rule type
                rule_feedback[entry.error_type].append(entry)
        
        rule_metrics = {}
        
        for rule_type, entries in rule_feedback.items():
            if len(entries) < self.min_feedback_threshold:
                self.logger.debug(f"Skipping {rule_type}: only {len(entries)} feedback entries (need {self.min_feedback_threshold})")
                continue
            
            # Count feedback types
            feedback_counts = Counter(entry.feedback_type for entry in entries)
            total_feedback = len(entries)
            correct_feedback = feedback_counts.get('correct', 0)
            incorrect_feedback = feedback_counts.get('incorrect', 0)
            unclear_feedback = feedback_counts.get('unclear', 0)
            
            # Calculate precision and false positive rate
            if correct_feedback + incorrect_feedback > 0:
                precision = correct_feedback / (correct_feedback + incorrect_feedback)
            else:
                precision = 0.5  # Default when no clear correct/incorrect feedback
            
            false_positive_rate = incorrect_feedback / total_feedback if total_feedback > 0 else 0.0
            
            # Calculate average confidence
            confidences = [entry.confidence_score for entry in entries if entry.confidence_score > 0]
            avg_confidence = statistics.mean(confidences) if confidences else 0.5
            
            # Calculate confidence correlation (how well confidence predicts correctness)
            correct_confidences = [entry.confidence_score for entry in entries 
                                 if entry.feedback_type == 'correct' and entry.confidence_score > 0]
            incorrect_confidences = [entry.confidence_score for entry in entries 
                                   if entry.feedback_type == 'incorrect' and entry.confidence_score > 0]
            
            if len(correct_confidences) > 1 and len(incorrect_confidences) > 1:
                # Simple correlation: difference in average confidence between correct and incorrect
                confidence_correlation = statistics.mean(correct_confidences) - statistics.mean(incorrect_confidences)
                confidence_correlation = max(-1.0, min(1.0, confidence_correlation))  # Clamp to [-1, 1]
            else:
                confidence_correlation = 0.0
            
            # Get current reliability
            current_reliability = get_rule_reliability_coefficient(rule_type)
            
            # Propose new reliability based on performance
            proposed_reliability, adjustment = self._calculate_reliability_adjustment(
                precision, false_positive_rate, confidence_correlation, current_reliability
            )
            
            rule_metrics[rule_type] = RulePerformanceMetrics(
                rule_type=rule_type,
                total_feedback=total_feedback,
                correct_feedback=correct_feedback,
                incorrect_feedback=incorrect_feedback,
                unclear_feedback=unclear_feedback,
                precision=precision,
                false_positive_rate=false_positive_rate,
                avg_confidence=avg_confidence,
                confidence_correlation=confidence_correlation,
                current_reliability=current_reliability,
                proposed_reliability=proposed_reliability,
                adjustment=adjustment
            )
        
        self.logger.info(f"Computed metrics for {len(rule_metrics)} rule types")
        return rule_metrics
    
    def _calculate_reliability_adjustment(self, 
                                        precision: float, 
                                        false_positive_rate: float,
                                        confidence_correlation: float,
                                        current_reliability: float) -> Tuple[float, float]:
        """
        Calculate reliability adjustment based on performance metrics.
        
        Args:
            precision: Rule precision (correct / (correct + incorrect))
            false_positive_rate: False positive rate (incorrect / total)
            confidence_correlation: Correlation between confidence and correctness
            current_reliability: Current reliability coefficient
            
        Returns:
            Tuple of (proposed_reliability, adjustment)
        """
        # Base adjustment on precision deviation from expected
        expected_precision = current_reliability  # Assume reliability correlates with precision
        precision_error = precision - expected_precision
        
        # Base adjustment proportional to precision error
        base_adjustment = precision_error * 0.1  # Scale factor
        
        # Adjust based on false positive rate (high FP rate should decrease reliability)
        fp_penalty = false_positive_rate * 0.05
        base_adjustment -= fp_penalty
        
        # Adjust based on confidence correlation (good correlation should increase reliability)
        confidence_bonus = confidence_correlation * self.confidence_weight * 0.05
        base_adjustment += confidence_bonus
        
        # Apply bounds for safety
        adjustment = max(-self.max_adjustment_per_run, min(self.max_adjustment_per_run, base_adjustment))
        
        # Calculate proposed reliability
        proposed_reliability = current_reliability + adjustment
        proposed_reliability = max(self.min_reliability, min(self.max_reliability, proposed_reliability))
        
        # Recalculate actual adjustment after clamping
        actual_adjustment = proposed_reliability - current_reliability
        
        return proposed_reliability, actual_adjustment
    
    def propose_adjustments(self, current_coeffs: Dict[str, float], 
                          performance_metrics: Dict[str, RulePerformanceMetrics]) -> Dict[str, float]:
        """
        Propose reliability coefficient adjustments based on performance metrics.
        
        Args:
            current_coeffs: Current reliability coefficients
            performance_metrics: Performance metrics for each rule type
            
        Returns:
            Dictionary of proposed reliability coefficients
        """
        proposed_coeffs = current_coeffs.copy()
        
        for rule_type, metrics in performance_metrics.items():
            if abs(metrics.adjustment) > 0.001:  # Only adjust if meaningful change
                proposed_coeffs[rule_type] = metrics.proposed_reliability
                self.logger.info(f"Proposing adjustment for {rule_type}: "
                               f"{metrics.current_reliability:.3f} → {metrics.proposed_reliability:.3f} "
                               f"(Δ{metrics.adjustment:+.3f}, precision: {metrics.precision:.3f})")
        
        return proposed_coeffs
    
    def apply_adjustments(self, adjustments: Dict[str, float], storage_path: str) -> bool:
        """
        Apply reliability coefficient adjustments by saving them to a file.
        
        Args:
            adjustments: Dictionary of rule type to new reliability coefficient
            storage_path: Path to save the reliability overrides
            
        Returns:
            True if successfully applied, False otherwise
        """
        try:
            # Prepare override data with metadata
            override_data = {
                'metadata': {
                    'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'version': '1.0',
                    'description': 'Feedback-informed reliability coefficient overrides',
                    'tuner_config': {
                        'min_feedback_threshold': self.min_feedback_threshold,
                        'max_adjustment_per_run': self.max_adjustment_per_run,
                        'min_reliability': self.min_reliability,
                        'max_reliability': self.max_reliability
                    }
                },
                'reliability_overrides': adjustments
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            
            # Save as YAML for readability
            with open(storage_path, 'w') as f:
                yaml.dump(override_data, f, default_flow_style=False, sort_keys=True)
            
            self.logger.info(f"Applied {len(adjustments)} reliability adjustments to {storage_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply adjustments to {storage_path}: {e}")
            return False
    
    def run_tuning_cycle(self, 
                        feedback_paths: List[str], 
                        storage_path: str) -> Dict[str, RulePerformanceMetrics]:
        """
        Run a complete tuning cycle: load feedback, compute metrics, propose and apply adjustments.
        
        Args:
            feedback_paths: List of feedback file paths
            storage_path: Path to save reliability overrides
            
        Returns:
            Dictionary of performance metrics for each rule type
        """
        self.logger.info("Starting reliability tuning cycle")
        
        # Load feedback data
        feedback_entries = self.load_feedback_data(feedback_paths)
        if not feedback_entries:
            self.logger.warning("No feedback data found, skipping tuning cycle")
            return {}
        
        # Compute performance metrics
        performance_metrics = self.compute_rule_precision(feedback_entries)
        if not performance_metrics:
            self.logger.warning("No performance metrics computed, skipping adjustments")
            return {}
        
        # Get current coefficients
        current_coeffs = {}
        for rule_type in performance_metrics.keys():
            current_coeffs[rule_type] = get_rule_reliability_coefficient(rule_type)
        
        # Propose adjustments
        proposed_coeffs = self.propose_adjustments(current_coeffs, performance_metrics)
        
        # Filter to only changed coefficients
        adjustments = {rule_type: coeff for rule_type, coeff in proposed_coeffs.items() 
                      if abs(coeff - current_coeffs.get(rule_type, 0)) > 0.001}
        
        if adjustments:
            # Apply adjustments
            success = self.apply_adjustments(adjustments, storage_path)
            if success:
                self.logger.info(f"Tuning cycle completed successfully. Adjusted {len(adjustments)} rule types.")
            else:
                self.logger.error("Failed to apply adjustments")
        else:
            self.logger.info("No adjustments needed, all rules performing within bounds")
        
        return performance_metrics


def tune_reliability_from_feedback(feedback_dir: str = None, 
                                 output_path: str = None,
                                 **tuner_kwargs) -> Dict[str, RulePerformanceMetrics]:
    """
    Convenience function to run reliability tuning from a feedback directory.
    
    Args:
        feedback_dir: Directory containing feedback JSONL files (default: feedback_data/daily)
        output_path: Path to save reliability overrides (default: validation/config/reliability_overrides.yaml)
        **tuner_kwargs: Additional arguments for ReliabilityTuner
        
    Returns:
        Dictionary of performance metrics for each rule type
    """
    # Set default paths
    if feedback_dir is None:
        feedback_dir = os.path.join(os.path.dirname(__file__), '../../feedback_data/daily')
    
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), '../config/reliability_overrides.yaml')
    
    # Find all JSONL files in feedback directory
    feedback_paths = []
    feedback_dir_path = Path(feedback_dir)
    if feedback_dir_path.exists():
        feedback_paths = list(feedback_dir_path.glob('*.jsonl'))
        feedback_paths = [str(path) for path in feedback_paths]
    
    if not feedback_paths:
        logging.warning(f"No feedback files found in {feedback_dir}")
        return {}
    
    # Run tuning
    tuner = ReliabilityTuner(**tuner_kwargs)
    return tuner.run_tuning_cycle(feedback_paths, output_path)


if __name__ == '__main__':
    # Set up logging for command-line usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tuning with default settings
    metrics = tune_reliability_from_feedback()
    
    if metrics:
        print(f"\n📊 Reliability Tuning Results:")
        print("=" * 50)
        for rule_type, metric in sorted(metrics.items()):
            print(f"{rule_type}:")
            print(f"  Feedback: {metric.total_feedback} total ({metric.correct_feedback} correct, {metric.incorrect_feedback} incorrect)")
            print(f"  Precision: {metric.precision:.3f}")
            print(f"  Reliability: {metric.current_reliability:.3f} → {metric.proposed_reliability:.3f} (Δ{metric.adjustment:+.3f})")
            print()
    else:
        print("No tuning performed - insufficient feedback data or no adjustments needed.")