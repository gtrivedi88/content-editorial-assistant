#!/bin/bash

# ============================================================
# Testing Infrastructure Setup Script
# Automated setup for Content Editorial Assistant testing
# ============================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Content Editorial Assistant"
echo "Testing Infrastructure Setup"
echo "=========================================="
echo ""

# Check Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python $PYTHON_VERSION (requires >= $REQUIRED_VERSION)"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -n "Creating virtual environment... "
    python3 -m venv venv
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}ℹ${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo -n "Activating virtual environment... "
source venv/bin/activate
echo -e "${GREEN}✓${NC}"

# Upgrade pip
echo -n "Upgrading pip... "
pip install --upgrade pip --quiet
echo -e "${GREEN}✓${NC}"

# Install main dependencies
echo "Installing main dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Main dependencies installed"

# Install test dependencies
echo "Installing test dependencies..."
pip install -r requirements-test.txt --quiet
echo -e "${GREEN}✓${NC} Test dependencies installed"

# Install Playwright browsers
echo "Installing Playwright browsers (this may take a few minutes)..."
playwright install chromium --quiet
echo -e "${GREEN}✓${NC} Playwright browsers installed"

# Install Playwright system dependencies
echo "Installing Playwright system dependencies..."
playwright install-deps chromium
echo -e "${GREEN}✓${NC} Playwright system dependencies installed"

# Create necessary directories
echo -n "Creating directory structure... "
mkdir -p testing_agent/{data,reports,results,coverage}
mkdir -p tests/ui/{screenshots,videos}
mkdir -p logs
echo -e "${GREEN}✓${NC}"

# Create pytest.ini if it doesn't exist
if [ ! -f "pytest.ini" ]; then
    echo -n "Creating pytest configuration... "
    cat > pytest.ini << 'EOF'
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    ui: UI tests with Playwright
    api: API tests
    performance: Performance benchmarks
    smoke: Quick smoke tests
    slow: Slow-running tests

addopts = 
    -v
    --strict-markers
    --tb=short
    --color=yes
    --junit-xml=testing_agent/results/junit.xml
    --cov=.
    --cov-report=html:testing_agent/coverage/html
    --cov-report=term-missing
EOF
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}ℹ${NC} pytest.ini already exists"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -n "Creating .env file... "
    cat > .env << 'EOF'
# Application Configuration
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=development-secret-key-change-in-production

# Testing Configuration
APP_URL=http://localhost:5000
HEADLESS=true
RECORD_VIDEO=false
PLAYWRIGHT_TIMEOUT=30000

# AI Analysis
OLLAMA_MODEL=llama3.2:latest
OLLAMA_URL=http://localhost:11434

# Notifications (Optional - configure as needed)
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# EMAIL_RECIPIENTS=team@example.com
EOF
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}ℹ${NC} .env file already exists"
fi

# Run feature-test mapper
echo "Running feature-test mapper..."
python -m testing_agent.feature_test_mapper 2>/dev/null || echo -e "${YELLOW}ℹ${NC} Feature mapper will run after first test execution"

# Check if Ollama is available
echo ""
echo "Checking optional dependencies..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama is installed"
    
    # Check if llama3.2 model is available
    if ollama list | grep -q "llama3.2"; then
        echo -e "${GREEN}✓${NC} Llama 3.2 model is available"
    else
        echo -e "${YELLOW}ℹ${NC} Llama 3.2 model not found. AI analysis will be limited."
        echo "  To install: ollama pull llama3.2:latest"
    fi
else
    echo -e "${YELLOW}ℹ${NC} Ollama not installed. AI analysis will be limited."
    echo "  To install Ollama:"
    echo "    Linux: curl -fsSL https://ollama.com/install.sh | sh"
    echo "    macOS: brew install ollama"
fi

# Run a quick smoke test
echo ""
echo "Running smoke tests..."
if pytest -m smoke --tb=short -q 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Smoke tests passed"
else
    echo -e "${YELLOW}ℹ${NC} Some smoke tests failed or no smoke tests found"
    echo "  This is normal for initial setup"
fi

# Print summary
echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run tests:"
echo "   python -m testing_agent.test_runner"
echo "   - or -"
echo "   pytest                    # Run all tests"
echo "   pytest -m unit            # Run only unit tests"
echo "   pytest -m ui              # Run only UI tests"
echo ""
echo "3. View reports:"
echo "   open testing_agent/reports/latest_report.html"
echo ""
echo "4. Set up GitLab CI schedule:"
echo "   - Go to CI/CD → Schedules"
echo "   - Create new schedule: 0 2 * * * (daily at 2 AM)"
echo "   - Add variable: SCHEDULED_JOB=daily_tests"
echo ""
echo "Documentation:"
echo "  - TESTING_SETUP.md - Detailed setup guide"
echo "  - IMPLEMENTATION_SUMMARY.md - Feature overview"
echo "  - testing_agent/README.md - Testing agent docs"
echo ""
echo "=========================================="

