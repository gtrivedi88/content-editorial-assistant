# Testing Setup and Quick Start

Learn how to set up and run the comprehensive testing infrastructure for the Content Editorial Assistant.

## Prerequisites

  * Python 3.12+ with virtual environment

  * Git and GitLab access

  * Your existing `.env` configuration

## Quick Setup (5 Minutes)

### 1\. Install Test Dependencies
[code] 
    # Activate your virtual environment
    source venv/bin/activate
    
    # Install test packages
    pip install -r requirements-test.txt
    
    # Install Playwright browsers for UI testing
    playwright install chromium
[/code]

### 2\. Run Your First Test
[code] 
    # Run all tests with AI analysis and report
    python -m testing_agent.test_runner
    
    # Or run specific categories
    pytest tests/unit/ -v          # Unit tests only
    pytest tests/integration/ -v   # Integration tests
    pytest tests/ui/ -v            # UI tests with browser
[/code]

### 3\. View the Report
[code] 
    # Open the generated HTML report
    open testing_agent/reports/latest_report.html
    # Or: firefox testing_agent/reports/latest_report.html
[/code]

## Test Categories

The testing system runs 9 categories of tests:

Category | Description | Typical Duration  
---|---|---  
**Unit** | Fast, isolated component tests | 2 min  
**Integration** | Multi-component workflow tests | 5 min  
**API** | REST endpoint tests | 1 min  
**Database** | Database operations | 2 min  
**Frontend** | Frontend component tests | 2 min  
**UI** | Browser-based tests (Playwright) | 3 min  
**WebSocket** | Real-time communication tests | 1 min  
**Validation** | Validation module tests | 3 min  
**Performance** | Load and stress testing | 2 min  
  
## AI-Powered Analysis

The testing agent uses your existing AI configuration from `.env`:
[code] 
    # Your .env file
    MODEL_PROVIDER=api                    # Uses your configured provider
    BASE_URL=https://your-api-url.com
    MODEL_ID=mistralai/Mistral-7B-Instruct-v0.3
    ACCESS_TOKEN=your-token
[/code]

The AI analyzes test results and provides:

  * Pattern detection (same error across multiple tests)

  * Root cause suggestions

  * Prioritized action items

  * Regression detection

  * Performance trend analysis

## Daily Automation (GitLab CI)

Set up automated daily test runs:

  1. Go to **GitLab → CI/CD → Schedules**

  2. Click **New schedule**

  3. Set schedule: `0 2 * * *` (runs at 2 AM)

  4. Add variable: `SCHEDULED_JOB=daily_tests`

  5. Save

Tests will run automatically every day and generate reports.

## Configuration

Create or update `.env` for testing-specific settings:
[code] 
    # Application
    APP_URL=http://localhost:5000
    HEADLESS=true
    
    # Test Execution
    PARALLEL_TESTS=true
    TEST_TIMEOUT=300
[/code]

Note |  The testing agent reuses your existing `MODEL_PROVIDER`, `BASE_URL`, and other model settings from `.env`.   
---|---  
  
## Common Commands
[code] 
    # Run all tests with coverage
    pytest --cov=. --cov-report=html
    
    # Run specific test file
    pytest tests/unit/rules/test_base_rule.py -v
    
    # Collect tests without running
    pytest --collect-only tests/
    
    # Run tests matching a pattern
    pytest -k "database" -v
    
    # Run with different verbosity
    pytest -v           # Verbose
    pytest -vv          # Very verbose
    pytest -q           # Quiet
[/code]

## Troubleshooting

### Import Errors
[code] 
    # Ensure virtual environment is activated
    source venv/bin/activate
    
    # Set PYTHONPATH
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
[/code]

### Missing Dependencies
[code] 
    # Reinstall test dependencies
    pip install -r requirements-test.txt --force-reinstall
[/code]

### Playwright Errors
[code] 
    # Install system dependencies
    playwright install-deps chromium
    
    # Reinstall browsers
    playwright install chromium --force
[/code]

## Next Steps

  * [Learn about agent-driven testing](<testing-guide.html>)

  * [Write new tests](<writing-tests.html>)

  * [Return to documentation home](<ROOT:index.html>)

## Resources

  * [Main README](<../../README.md>)

  * [Testing Agent Technical Reference](<../../testing_agent/README.md>)

  * [Pytest Documentation](<https://docs.pytest.org/>)

  * [Playwright Documentation](<https://playwright.dev/python/>)

Last updated 2025-11-24 22:49:07 +0530 
