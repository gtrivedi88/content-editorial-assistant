# AI-Powered Testing Agent Guide

Understand how the AI-powered testing agent works and how it helps maintain quality.

## Overview

The Content Editorial Assistant uses a **hybrid agent approach** combining:

  * **Simple Agent** (GitLab CI) - Reliable test execution

  * **AI Agent** (Your configured AI) - Intelligent analysis and insights

## Architecture
[code] 
    ┌──────────────────────────────────────────┐
    │  GitLab CI (Simple Agent)                │
    │  • Executes all tests daily              │
    │  • Collects results                      │
    │  • Stores data                           │
    └─────────────┬────────────────────────────┘
                  │
                  ▼
    ┌──────────────────────────────────────────┐
    │  Test Runner                             │
    │  testing_agent/test_runner.py            │
    │  • Runs 9 test categories                │
    │  • Collects metrics                      │
    └─────────────┬────────────────────────────┘
                  │
                  ▼
    ┌──────────────────────────────────────────┐
    │  AI Analyzer (Smart Agent)               │
    │  testing_agent/ai_test_analyzer.py       │
    │  • Detects patterns                      │
    │  • Identifies root causes                │
    │  • Prioritizes issues                    │
    │  • Generates insights                    │
    └─────────────┬────────────────────────────┘
                  │
                  ▼
    ┌──────────────────────────────────────────┐
    │  Report Generator                        │
    │  testing_agent/report_generator.py       │
    │  • Creates HTML/PDF reports              │
    │  • Generates charts                      │
    │  • Lists action items                    │
    └──────────────────────────────────────────┘
[/code]

## What the AI Agent Does

### Pattern Detection

The AI analyzes test failures to find common patterns:
[code] 
    {
      "test_database_connection": "ConnectionError: pool exhausted",
      "test_concurrent_access": "ConnectionError: pool exhausted",
      "test_transaction_rollback": "ConnectionError: pool exhausted"
    }
[/code]

**AI Analysis:**
[code] 
    🧠 Pattern Detected: 3 tests failing with identical ConnectionError
    Root Cause: Database connection pool exhaustion
    Likely Issue: Test fixtures not properly closing connections
    
    Recommended Actions:
    1. Add connection cleanup in test teardown (HIGH PRIORITY)
    2. Increase pool size in test config (MEDIUM)
    3. Add connection leak detection (LOW)
    
    Estimated Fix Time: 2 hours
[/code]

### Regression Detection

Automatically identifies tests that passed yesterday but fail today:
[code] 
    🔴 NEW FAILURES (regressions):
    
    1. test_holistic_rewrite
       Error: Confidence score too low (0.65 < 0.80)
       Priority: HIGH
       Estimate: 2 hours
       Action: Check line 245 confidence calculation
[/code]

### Performance Monitoring

Tracks test execution time over 30 days:
[code] 
    Test Duration: ↓ 5.2% faster ✅
    Average Latency: 1.2s (stable)
    Slowest Test: test_large_document (45s)
    
    ⚠️ Alert: test_api_response_time 20% slower
[/code]

### Smart Prioritization

AI prioritizes issues based on impact:

Priority | Issue Type | Action Needed  
---|---|---  
**P1 - HIGH** | Blocking release, new regressions | Fix today  
**P2 - MEDIUM** | Performance degradation | Fix this week  
**P3 - LOW** | Flaky tests, minor issues | Fix when convenient  
  
## Daily Report Contents

Every test run generates a comprehensive report:

### 1\. Executive Summary
[code] 
    Status: 🟢 HEALTHY
    Pass Rate: 96% (382/398 tests)
    Duration: 4m 32s
    Health Score: A+ (97.5/100)
[/code]

### 2\. Test Results Breakdown

Interactive pie chart showing:

  * Passed tests (green)

  * Failed tests (red)

  * Skipped tests (yellow)

### 3\. Regressions

List of tests that previously passed but now fail.

### 4\. Performance Trends

30-day chart showing:

  * Test execution time

  * Pass rate trend

  * Performance metrics

### 5\. AI-Generated Insights

Intelligent analysis of issues:
[code] 
    🧠 5 ISSUES IDENTIFIED:
    
    [1] Database connection pool exhaustion
        → Add cleanup in test teardown
    
    [2] Regex compilation in hot path
        → Cache compiled patterns
    
    [3] Flaky websocket test needs timeout
        → Increase timeout from 5s to 10s
[/code]

### 6\. Prioritized Action Items

Clear, actionable steps:
[code] 
    ✅ WHAT TO DO TODAY:
    
    1. Fix test_holistic_rewrite (HIGH - 2h)
       → Check line 245 confidence calculation
    
    2. Optimize SurgicalSnippetProcessor (MEDIUM - 4h)
       → Profile hot paths, cache regex
    
    3. Stabilize websocket test (LOW - 1h)
       → Increase timeout configuration
[/code]

## Test Coverage

### What's Tested

Module | Coverage  
---|---  
`ambiguity/` | Ambiguity detection rules  
`app_modules/` | API routes, websockets, PDF generation  
`database/` | DAO, models, services  
`error_consolidation/` | Error merging and prioritization  
`models/` | Model factory, manager  
`rewriter/` | Core rewriting engine  
`style_analyzer/` | Style analysis, readability  
`structural_parsing/` | Format detection, parsers  
`rules/` | All 111 editorial rules  
  
### Feature-Test Mapping

Automatically tracks which features have tests:
[code] 
    # Check coverage status
    python -m testing_agent.feature_test_mapper
    
    # Output:
    Total Features: 45
    Tested: 38 (84%)
    Missing Tests: 7
    
    ⚠️ Untested Features:
    - feature_x in module_y
    - feature_z in module_w
[/code]

## How Tests Stay In Sync

### 1\. CI Triggers on Code Changes
[code] 
    Developer commits → CI runs tests → Reports results
[/code]

### 2\. Feature-Test Mapping
[code] 
    New feature added → Mapper detects → Alerts "no tests found"
[/code]

### 3\. Daily Verification
[code] 
    Daily run → Checks all features → Reports coverage gaps
[/code]

## AI Configuration

The testing agent uses your existing AI configuration:
[code] 
    # From your .env file
    MODEL_PROVIDER=api                    # Your provider (api/ollama/llamastack)
    BASE_URL=https://your-api-url.com    # Your API endpoint
    MODEL_ID=mistralai/Mistral-7B         # Your model
    ACCESS_TOKEN=your-token               # Your credentials
    MODEL_TEMPERATURE=0.4                 # Your settings
[/code]

Tip |  The testing agent automatically detects and uses your configured AI provider. No separate setup needed!   
---|---  
  
## Alerts and Notifications

### Alert Triggers

Condition | Level | Action  
---|---|---  
Pass rate < 85% | 🔴 CRITICAL | Immediate fix needed  
New regressions | 🔴 HIGH | Review before release  
Performance -20% | 🟡 WARNING | Investigate today  
Flaky tests > 10% | 🟡 WARNING | Stabilize this week  
  
### Configure Notifications

Add to `.env`:
[code] 
    SLACK_WEBHOOK_URL=https://hooks.slack.com/...
    EMAIL_RECIPIENTS=team@example.com
[/code]

## Success Metrics

A healthy test suite has:

  * ✅ 95%+ pass rate

  * ✅ < 5 minutes execution time

  * ✅ < 5% flaky tests

  * ✅ 80%+ code coverage

  * ✅ Health score: A or A+

Check your current status:
[code] 
    python -m testing_agent.test_runner
[/code]

## Next Steps

  * [Learn to write new tests](<writing-tests.html>)

  * [Setup testing infrastructure](<testing-setup.html>)

  * [Return to documentation home](<ROOT:index.html>)

## Resources

  * [Testing Configuration Source](<../../testing_agent/config.py>)

  * [AI Analyzer Source](<../../testing_agent/ai_test_analyzer.py>)

  * [Pytest Configuration](<../../pytest.ini>)

Last updated 2025-12-20 04:32:26 +0530 
