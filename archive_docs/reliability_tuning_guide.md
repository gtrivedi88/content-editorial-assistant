# Feedback-informed Reliability Calibration Guide

## Overview

The Feedback-informed Reliability Calibration system (Upgrade 6) continuously improves validation accuracy by adjusting rule reliability coefficients based on real user feedback. This creates a closed-loop learning system that makes your style guide validation smarter over time.

## What This Feature Does

- **Analyzes user feedback** to measure rule performance (precision, false positive rate)
- **Automatically adjusts** rule reliability coefficients based on real-world performance
- **Improves validation accuracy** by increasing reliability of well-performing rules and decreasing reliability of problematic rules
- **Provides audit trails** for all adjustments with metadata and reasoning

---

## Prerequisites

1. **Feedback Data**: Your application should be collecting user feedback in JSONL format
2. **Python Environment**: Virtual environment activated with all dependencies
3. **File Permissions**: Write access to `validation/config/` directory

## 📊 Understanding Feedback Data Format

Your application should save user feedback in JSONL format like this:

```json
{
  "feedback_id": "unique_id_123",
  "session_id": "user_session_456", 
  "error_id": "error_789",
  "error_type": "inclusive_language",
  "error_message": "Consider using 'primary' instead of 'master'",
  "feedback_type": "correct",
  "confidence_score": 0.85,
  "user_reason": null,
  "timestamp": "2025-01-15T10:30:00"
}
```

**Feedback Types:**
- `"correct"` - User agrees the error is valid
- `"incorrect"` - User disagrees (false positive)
- `"unclear"` - User is unsure

---

## 🚀 Quick Start Guide

### Step 1: Check Your Feedback Data

First, verify you have feedback data available:

```bash
# Check for feedback files
ls -la feedback_data/daily/

# Count feedback entries
wc -l feedback_data/daily/*.jsonl
```

### Step 2: Run a Dry Run

Always start with a dry run to see what changes would be made:

```bash
# Activate your virtual environment
source venv/bin/activate

# Run dry run to preview changes
python scripts/tune_reliability.py --dry-run --verbose
```

**Expected Output:**
```
🚀 Starting reliability tuning
📁 Feedback directory: feedback_data/daily
📄 Feedback files: 5
📊 Loaded 142 feedback entries
📈 Computed metrics for 8 rule types

📊 Reliability Tuning Summary
============================
🔧 Rules adjusted: 3

📈 inclusive_language:
    Feedback: 23 total (21 ✅, 2 ❌)
    Precision: 0.913
    Reliability: 0.880 → 0.895 (Δ+0.015) [moderate]

📉 tone:
    Feedback: 15 total (8 ✅, 7 ❌)  
    Precision: 0.533
    Reliability: 0.720 → 0.705 (Δ-0.015) [moderate]
```

### Step 3: Apply Changes

If you're satisfied with the proposed changes:

```bash
# Apply the reliability adjustments
python scripts/tune_reliability.py --verbose
```

### Step 4: Verify Changes Applied

Check that the override file was created:

```bash
# Check the generated override file
cat validation/config/reliability_overrides.yaml
```

**Example Override File:**
```yaml
metadata:
  description: Feedback-informed reliability coefficient overrides
  generated_at: '2025-01-15 14:30:22'
  tuner_config:
    max_adjustment_per_run: 0.02
    min_feedback_threshold: 10
    min_reliability: 0.7
    max_reliability: 0.98
  version: '1.0'
reliability_overrides:
  inclusive_language: 0.895
  tone: 0.705
  spelling: 0.925
```

### Step 5: Hot-Reload (Optional)

If your application is running, hot-reload the new coefficients:

```bash
# Reload coefficients without restarting your app
python scripts/tune_reliability.py --reload
```

---

## 🔧 Advanced Usage

### Custom Parameters

Adjust tuning behavior with command-line options:

```bash
# More conservative tuning (smaller adjustments)
python scripts/tune_reliability.py --max-adjustment 0.01 --min-feedback 20

# Aggressive tuning (larger adjustments, less data required)
python scripts/tune_reliability.py --max-adjustment 0.03 --min-feedback 5

# Use only recent feedback (last 7 days)
python scripts/tune_reliability.py --days-back 7

# Use all available feedback
python scripts/tune_reliability.py --all-feedback
```

### Custom Feedback Directory

```bash
# Use different feedback directory
python scripts/tune_reliability.py --feedback-dir /path/to/custom/feedback

# Save overrides to custom location
python scripts/tune_reliability.py --output /path/to/custom/overrides.yaml
```

### Logging and Monitoring

```bash
# Enable detailed logging
python scripts/tune_reliability.py --verbose --log-file logs/tuning.log

# Check tuning logs
tail -f logs/tuning.log
```

---

## 📅 Production Workflow

### Recommended Schedule

**Daily Monitoring:**
```bash
# Morning check - dry run to see potential changes
python scripts/tune_reliability.py --dry-run --days-back 1
```

**Weekly Tuning:**
```bash
# Weekend tuning with more data
python scripts/tune_reliability.py --days-back 7 --verbose
```

**Monthly Review:**
```bash
# Comprehensive monthly review
python scripts/tune_reliability.py --all-feedback --dry-run > monthly_review.txt
```

### Automation with Cron

Add to your crontab for automatic execution:

```bash
# Edit crontab
crontab -e

# Add daily tuning at 2 AM (adjust paths as needed)
0 2 * * * cd /home/user/style-guide-ai && source venv/bin/activate && python scripts/tune_reliability.py >> logs/daily_tuning.log 2>&1

# Add weekly comprehensive tuning on Sundays at 3 AM
0 3 * * 0 cd /home/user/style-guide-ai && source venv/bin/activate && python scripts/tune_reliability.py --all-feedback >> logs/weekly_tuning.log 2>&1
```

---

## 📊 Understanding the Results

### Performance Metrics

**Precision**: `correct_feedback / (correct_feedback + incorrect_feedback)`
- **High (>0.8)**: Rule performs well, reliability should increase
- **Medium (0.6-0.8)**: Rule is decent, minor adjustments
- **Low (<0.6)**: Rule has issues, reliability should decrease

**False Positive Rate**: `incorrect_feedback / total_feedback`
- **Low (<0.2)**: Good rule, few false positives
- **Medium (0.2-0.4)**: Some issues, monitor closely  
- **High (>0.4)**: Problematic rule, needs reliability reduction

**Confidence Correlation**: How well rule confidence predicts correctness
- **Positive**: Higher confidence → more likely correct
- **Negative**: Higher confidence → more likely incorrect (concerning)

### Adjustment Direction

- **📈 Positive Adjustment**: Rule performs better than expected → increase reliability
- **📉 Negative Adjustment**: Rule performs worse than expected → decrease reliability
- **➡️ No Adjustment**: Rule performs as expected → no change needed

---

## 🛠️ Troubleshooting

### No Adjustments Made

**Possible Causes:**
```bash
# Check if you have enough feedback data
python scripts/tune_reliability.py --min-feedback 5 --dry-run

# Check feedback file format
head -5 feedback_data/daily/*.jsonl | python -m json.tool
```

**Solutions:**
- Lower `--min-feedback` threshold
- Accumulate more feedback data over time
- Check feedback file format for errors

### Permission Errors

```bash
# Check write permissions
ls -la validation/config/

# Create directory if needed
mkdir -p validation/config/

# Fix permissions
chmod 755 validation/config/
```

### Invalid Feedback Data

```bash
# Validate feedback format
python -c "
import json
with open('feedback_data/daily/feedback_2025-01-15.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line.strip())
        except:
            print(f'Invalid JSON on line {i}: {line}')
"
```

---

## 🎯 Best Practices

### 1. Start Conservative

```bash
# Begin with smaller adjustments
python scripts/tune_reliability.py --max-adjustment 0.01 --min-feedback 15
```

### 2. Monitor Changes

```bash
# Always review before applying
python scripts/tune_reliability.py --dry-run --verbose

# Keep logs for audit trail
python scripts/tune_reliability.py --log-file logs/tuning_$(date +%Y%m%d).log
```

### 3. Test Impact

After tuning, test a sample of your content to verify the adjustments improve accuracy.

### 4. Backup Override Files

```bash
# Backup before major changes
cp validation/config/reliability_overrides.yaml validation/config/reliability_overrides_backup_$(date +%Y%m%d).yaml
```

### 5. Gradual Rollouts

For production systems:
1. Run dry-run during business hours to review
2. Apply changes during maintenance windows
3. Monitor application performance after changes
4. Revert if issues arise

---

## 🔄 Integration with Your Application

### Hot-Reloading in Running App

If you want to apply changes without restarting your Flask application:

```python
# Add this endpoint to your Flask app
@app.route('/admin/reload-reliability', methods=['POST'])
def reload_reliability():
    from validation.confidence.rule_reliability import reload_reliability_overrides
    try:
        reload_reliability_overrides()
        return {"status": "success", "message": "Reliability coefficients reloaded"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500
```

Then call after tuning:
```bash
# After running tuner
curl -X POST http://localhost:5000/admin/reload-reliability
```

### Programmatic Usage

```python
from validation.feedback.reliability_tuner import tune_reliability_from_feedback
from validation.confidence.rule_reliability import reload_reliability_overrides

def update_reliability_coefficients():
    """Update reliability coefficients based on recent feedback."""
    
    # Run tuning
    metrics = tune_reliability_from_feedback(
        feedback_dir="feedback_data/daily",
        min_feedback_threshold=10
    )
    
    if metrics:
        print(f"Updated reliability for {len(metrics)} rules")
        
        # Hot-reload coefficients
        reload_reliability_overrides()
        
        return metrics
    else:
        print("No adjustments needed")
        return {}
```

---

## 📈 Monitoring and Reporting

### Generate Reports

```bash
# Generate detailed tuning report
python scripts/tune_reliability.py --dry-run --verbose > reports/tuning_report_$(date +%Y%m%d).txt

# Extract key metrics
grep -E "(Precision|Reliability|Adjustment)" reports/tuning_report_*.txt
```

### Track Performance Over Time

```bash
# Monitor reliability changes over time
git log --oneline validation/config/reliability_overrides.yaml

# Compare override files
diff validation/config/reliability_overrides_backup.yaml validation/config/reliability_overrides.yaml
```

---

## ⚠️ Important Notes

1. **Minimum Data**: Requires at least 10 feedback entries per rule by default
2. **Safety Bounds**: Adjustments limited to ±0.02 per run, coefficients clamped to [0.70, 0.98]
3. **Gradual Changes**: System designed for gradual improvement, not sudden shifts
4. **Audit Trail**: All changes logged with timestamps and reasoning
5. **Reversible**: You can always restore from backup override files

---

## 🆘 Support and Debugging

### Enable Debug Mode

```bash
# Maximum verbosity for debugging
python scripts/tune_reliability.py --verbose --dry-run --log-file debug.log

# Check debug log
cat debug.log
```

### Validate System Health

```bash
# Test with minimal data
python scripts/tune_reliability.py --min-feedback 1 --dry-run

# Verify override loading works
python -c "
from validation.confidence.rule_reliability import get_rule_reliability_coefficient
print('Test rule reliability:', get_rule_reliability_coefficient('grammar'))
"
```

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| No feedback files found | Check `feedback_data/daily/` directory exists and contains `.jsonl` files |
| Permission denied | Ensure write access to `validation/config/` directory |
| JSON parsing errors | Validate feedback file format with `python -m json.tool` |
| No rules meet threshold | Lower `--min-feedback` or collect more feedback data |
| Import errors | Ensure virtual environment is activated and dependencies installed |

---

## 🎉 Success Criteria

You'll know the system is working when:

1. **✅ Dry runs show meaningful adjustments** based on feedback patterns
2. **✅ Override files are generated** with proper metadata structure  
3. **✅ Application continues working** with new reliability coefficients
4. **✅ Validation accuracy improves** over time with more feedback
5. **✅ False positive rates decrease** for problematic rules

---

This system will continuously learn from your users' feedback and make your style guide validation more accurate and trustworthy over time! 🚀