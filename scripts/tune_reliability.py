#!/usr/bin/env python3
"""
CLI Script for Feedback-informed Reliability Calibration
Runs the reliability tuner to adjust rule coefficients based on user feedback.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from validation.feedback.reliability_tuner import (
    ReliabilityTuner, 
    tune_reliability_from_feedback
)
from validation.confidence.rule_reliability import reload_reliability_overrides


def setup_logging(verbose: bool = False, log_file: str = None):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )


def collect_feedback_files(feedback_dir: str, days_back: int = None) -> list:
    """
    Collect feedback files from the specified directory.
    
    Args:
        feedback_dir: Directory containing feedback JSONL files
        days_back: Number of days back to include (None for all files)
        
    Returns:
        List of feedback file paths
    """
    feedback_path = Path(feedback_dir)
    if not feedback_path.exists():
        logging.error(f"Feedback directory does not exist: {feedback_dir}")
        return []
    
    # Find all JSONL files
    feedback_files = list(feedback_path.glob('*.jsonl'))
    
    if days_back is not None:
        # Filter by date (assuming files are named with dates)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        filtered_files = []
        
        for file_path in feedback_files:
            try:
                # Try to extract date from filename (e.g., feedback_2025-01-15.jsonl)
                date_str = file_path.stem.split('_')[-1]
                file_date = datetime.strptime(date_str, '%Y-%m-%d')
                if file_date >= cutoff_date:
                    filtered_files.append(file_path)
            except (ValueError, IndexError):
                # If we can't parse the date, include the file
                filtered_files.append(file_path)
        
        feedback_files = filtered_files
    
    feedback_files = [str(f) for f in sorted(feedback_files)]
    logging.info(f"Found {len(feedback_files)} feedback files in {feedback_dir}")
    return feedback_files


def print_tuning_summary(metrics: dict, output_path: str):
    """Print a summary of the tuning results."""
    if not metrics:
        print("\n📊 No tuning performed - insufficient feedback data or no adjustments needed.")
        return
    
    print(f"\n📊 Reliability Tuning Summary")
    print("=" * 60)
    print(f"📁 Overrides saved to: {output_path}")
    print(f"🔧 Rules adjusted: {len(metrics)}")
    print()
    
    # Sort by adjustment magnitude for better display
    sorted_metrics = sorted(
        metrics.items(), 
        key=lambda x: abs(x[1].adjustment), 
        reverse=True
    )
    
    total_adjustments = 0
    for rule_type, metric in sorted_metrics:
        direction = "📈" if metric.adjustment > 0 else "📉"
        adjustment_magnitude = "significant" if abs(metric.adjustment) > 0.015 else "moderate"
        
        print(f"{direction} {rule_type}:")
        print(f"    Feedback: {metric.total_feedback} total "
              f"({metric.correct_feedback} ✅, {metric.incorrect_feedback} ❌)")
        print(f"    Precision: {metric.precision:.3f}")
        print(f"    Reliability: {metric.current_reliability:.3f} → {metric.proposed_reliability:.3f} "
              f"(Δ{metric.adjustment:+.3f}) [{adjustment_magnitude}]")
        print()
        
        if abs(metric.adjustment) > 0.001:
            total_adjustments += 1
    
    print(f"✅ Applied {total_adjustments} reliability adjustments")
    print(f"🎯 System will use updated coefficients on next startup or reload")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Tune rule reliability coefficients based on user feedback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Tune with default settings (last 30 days of feedback)
  python scripts/tune_reliability.py
  
  # Tune with all available feedback
  python scripts/tune_reliability.py --all-feedback
  
  # Tune with specific feedback directory and output
  python scripts/tune_reliability.py --feedback-dir /path/to/feedback --output /path/to/overrides.yaml
  
  # Dry run to see what would be changed
  python scripts/tune_reliability.py --dry-run
  
  # Tune with custom parameters
  python scripts/tune_reliability.py --min-feedback 20 --max-adjustment 0.01
        """
    )
    
    # Input/Output options
    parser.add_argument(
        '--feedback-dir', '-f',
        default=None,
        help='Directory containing feedback JSONL files (default: feedback_data/daily)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output path for reliability overrides (default: validation/config/reliability_overrides.yaml)'
    )
    
    # Feedback filtering options
    parser.add_argument(
        '--days-back', '-d',
        type=int,
        default=30,
        help='Number of days back to include feedback (default: 30, use --all-feedback for all)'
    )
    parser.add_argument(
        '--all-feedback',
        action='store_true',
        help='Use all available feedback (overrides --days-back)'
    )
    
    # Tuning parameters
    parser.add_argument(
        '--min-feedback',
        type=int,
        default=10,
        help='Minimum feedback entries required to adjust a rule (default: 10)'
    )
    parser.add_argument(
        '--max-adjustment',
        type=float,
        default=0.02,
        help='Maximum adjustment per run (default: 0.02)'
    )
    parser.add_argument(
        '--min-reliability',
        type=float,
        default=0.70,
        help='Minimum allowed reliability coefficient (default: 0.70)'
    )
    parser.add_argument(
        '--max-reliability',
        type=float,
        default=0.98,
        help='Maximum allowed reliability coefficient (default: 0.98)'
    )
    
    # Execution options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without applying adjustments'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Reload overrides in the current process after tuning'
    )
    
    # Logging options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--log-file',
        help='Log to file in addition to stdout'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose, args.log_file)
    
    # Validate parameters
    if args.min_feedback < 1:
        parser.error("--min-feedback must be at least 1")
    if not (0.001 <= args.max_adjustment <= 0.1):
        parser.error("--max-adjustment must be between 0.001 and 0.1")
    if not (0.5 <= args.min_reliability <= 1.0):
        parser.error("--min-reliability must be between 0.5 and 1.0")
    if not (0.5 <= args.max_reliability <= 1.0):
        parser.error("--max-reliability must be between 0.5 and 1.0")
    if args.min_reliability >= args.max_reliability:
        parser.error("--min-reliability must be less than --max-reliability")
    
    # Set default paths if not provided
    if args.feedback_dir is None:
        args.feedback_dir = str(project_root / 'feedback_data' / 'daily')
    
    if args.output is None:
        args.output = str(project_root / 'validation' / 'config' / 'reliability_overrides.yaml')
    
    # Collect feedback files
    days_back = None if args.all_feedback else args.days_back
    feedback_files = collect_feedback_files(args.feedback_dir, days_back)
    
    if not feedback_files:
        logging.error("No feedback files found. Cannot perform tuning.")
        sys.exit(1)
    
    # Log configuration
    logging.info(f"🚀 Starting reliability tuning")
    logging.info(f"📁 Feedback directory: {args.feedback_dir}")
    logging.info(f"📄 Feedback files: {len(feedback_files)}")
    logging.info(f"📅 Feedback period: {'all available' if args.all_feedback else f'last {args.days_back} days'}")
    logging.info(f"📊 Min feedback threshold: {args.min_feedback}")
    logging.info(f"⚖️  Max adjustment per run: ±{args.max_adjustment}")
    logging.info(f"🎯 Reliability bounds: [{args.min_reliability}, {args.max_reliability}]")
    
    if args.dry_run:
        logging.info("🔍 DRY RUN MODE - no changes will be applied")
    
    try:
        # Create tuner with specified parameters
        tuner = ReliabilityTuner(
            min_feedback_threshold=args.min_feedback,
            max_adjustment_per_run=args.max_adjustment,
            min_reliability=args.min_reliability,
            max_reliability=args.max_reliability
        )
        
        # Load and process feedback
        feedback_entries = tuner.load_feedback_data(feedback_files)
        if not feedback_entries:
            logging.error("No valid feedback entries found in files")
            sys.exit(1)
        
        logging.info(f"📊 Loaded {len(feedback_entries)} feedback entries")
        
        # Compute metrics
        metrics = tuner.compute_rule_precision(feedback_entries)
        if not metrics:
            logging.info("No rules meet the minimum feedback threshold")
            print_tuning_summary({}, args.output)
            sys.exit(0)
        
        logging.info(f"📈 Computed metrics for {len(metrics)} rule types")
        
        # Get current coefficients and propose adjustments
        current_coeffs = {}
        for rule_type in metrics.keys():
            from validation.confidence.rule_reliability import get_rule_reliability_coefficient
            current_coeffs[rule_type] = get_rule_reliability_coefficient(rule_type)
        
        proposed_coeffs = tuner.propose_adjustments(current_coeffs, metrics)
        
        # Filter to only meaningful changes
        adjustments = {
            rule_type: coeff for rule_type, coeff in proposed_coeffs.items() 
            if abs(coeff - current_coeffs.get(rule_type, 0)) > 0.001
        }
        
        if not adjustments:
            logging.info("No adjustments needed - all rules performing within bounds")
            print_tuning_summary({}, args.output)
            sys.exit(0)
        
        # Apply adjustments (unless dry run)
        if args.dry_run:
            logging.info(f"DRY RUN: Would apply {len(adjustments)} adjustments")
            print_tuning_summary(metrics, args.output + " (dry-run)")
        else:
            success = tuner.apply_adjustments(adjustments, args.output)
            if success:
                logging.info(f"✅ Applied {len(adjustments)} reliability adjustments to {args.output}")
                print_tuning_summary(metrics, args.output)
                
                # Reload overrides if requested
                if args.reload:
                    logging.info("🔄 Reloading overrides in current process")
                    reload_reliability_overrides(args.output)
                    logging.info("✅ Overrides reloaded successfully")
                
            else:
                logging.error("❌ Failed to apply adjustments")
                sys.exit(1)
    
    except KeyboardInterrupt:
        logging.info("🛑 Tuning interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Error during tuning: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()