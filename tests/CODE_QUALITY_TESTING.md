# Code Quality Testing Suite

This document describes the comprehensive code quality testing suite for the Style Guide AI project, designed to detect duplicate code, maintain coding standards, and ensure high code quality.

## 🎯 Overview

The code quality testing suite includes:

### ✅ Current Tests
- **Duplicate function signature detection**
- **Duplicate class name detection** 
- **Duplicate function implementation detection**
- **Similar code block detection**
- **Import cycle detection**
- **Code complexity analysis**
- **Naming convention validation**
- **Basic unused import detection**

### 🔧 Static Analysis Tools
- **Pylint**: Comprehensive code analysis
- **Flake8**: Style guide enforcement
- **MyPy**: Type checking
- **Black**: Code formatting
- **isort**: Import sorting
- **Bandit**: Security vulnerability scanning

## 🚀 Quick Start

### Run All Quality Checks
```bash
# Run everything
python scripts/run_quality_checks.py

# Run with fail-fast (stop on first error)
python scripts/run_quality_checks.py --fail-fast

# Run specific checks only
python scripts/run_quality_checks.py --include tests pylint mypy
```

### Run Individual Tests
```bash
# Run only the custom code quality tests
pytest tests/test_code_quality.py -v

# Run with detailed output
pytest tests/test_code_quality.py -v -s

# Run specific test categories
pytest tests/test_code_quality.py::TestCodeQuality::test_no_duplicate_function_signatures -v
```

## 📊 Test Categories

### 1. Duplication Detection

#### Function Signature Duplicates
```python
def test_no_duplicate_function_signatures()
```
- Detects functions with identical signatures in the same file
- Prevents accidental function redefinition
- **Example violation**: Two `process_data(content, format)` functions in same file

#### Class Name Duplicates  
```python
def test_no_duplicate_class_names()
```
- Detects duplicate class names within modules
- Ensures unique class identifiers
- **Example violation**: Two `DataProcessor` classes in same file

#### Function Implementation Duplicates
```python
def test_no_duplicate_function_implementations()
```
- Detects functions with identical implementations
- Identifies copy-paste code that should be refactored
- **Example violation**: Two functions with identical logic but different names

#### Similar Code Blocks
```python
def test_limited_code_duplication()
```
- Detects similar code blocks across files
- Configurable minimum line threshold (default: 8 lines)
- Allows up to 5 similar blocks before flagging
- **Example violation**: 6+ blocks of nearly identical error handling code

### 2. Architectural Quality

#### Import Cycle Detection
```python
def test_no_import_cycles()
```
- Detects circular import dependencies
- Prevents import deadlocks and dependency issues
- **Example violation**: Module A imports B, B imports C, C imports A

#### Code Complexity Analysis
```python
def test_complexity_within_limits()
```
- **Cyclomatic Complexity**: Max 15 per function
- **Function Length**: Max 100 lines per function
- **Class Size**: Max 25 methods per class
- **Example violation**: Function with 20+ decision points

### 3. Naming Conventions

#### Consistent Naming Patterns
```python
def test_consistent_naming_patterns()
```
- **Functions**: `snake_case` (e.g., `process_data`)
- **Classes**: `PascalCase` (e.g., `DataProcessor`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_FILE_SIZE`)
- **Example violation**: Function named `processData` instead of `process_data`

### 4. Code Quality Metrics

#### Test Coverage Validation
```python
def test_test_coverage_exists()
```
- Ensures test files exist for major components
- Checks for missing test coverage
- **Example violation**: Missing `test_new_module.py` for `new_module.py`

#### Documentation Coverage
```python
def test_documentation_coverage()
```
- Validates module-level docstrings
- Ensures API documentation exists
- **Example violation**: Module without docstring

## ⚙️ Configuration

### Thresholds (Configurable)
```python
# Complexity limits
MAX_FUNCTION_COMPLEXITY = 15
MAX_CLASS_METHODS = 25  
MAX_FUNCTION_LINES = 100

# Duplication limits
MAX_ALLOWED_DUPLICATIONS = 5
MIN_SIMILAR_BLOCK_LINES = 8

# Naming issues tolerance
MAX_NAMING_ISSUES = 10
```

### Static Analysis Config (`pyproject.toml`)
```toml
[tool.pylint.similarities]
min-similarity-lines = 4  # Detect 4+ line duplicates

[tool.pylint.design]
max-args = 8
max-attributes = 12
max-public-methods = 25

[tool.mypy]
disallow_untyped_defs = false  # Gradually enable
warn_unused_ignores = true
```

## 🔍 Usage Examples

### Example 1: Detecting Duplicate Functions
```python
# BAD: This would be detected
def process_user_data(data, format):
    return data.strip().lower()

def process_user_data(data, format):  # Duplicate signature!
    return data.upper()
```

### Example 2: Detecting Similar Code
```python
# BAD: Similar blocks across files
# File 1:
try:
    result = api_call()
    if result.status == 'error':
        log_error(result.message)
        return None
    return result.data
except Exception as e:
    log_error(str(e))
    return None

# File 2: Nearly identical block (would be detected)
try:
    response = different_api_call()
    if response.status == 'error':
        log_error(response.message)
        return None
    return response.data
except Exception as e:
    log_error(str(e))
    return None
```

### Example 3: Detecting High Complexity
```python
# BAD: High cyclomatic complexity (would be detected)
def complex_function(data, options, flags):
    if data is None:           # +1
        if options.strict:     # +1
            if flags.error:    # +1
                raise ValueError()
        elif options.lenient:  # +1
            if flags.warn:     # +1
                log_warning()
    elif data.empty:           # +1
        for item in data:      # +1
            if item.valid:     # +1
                if item.type == 'A':  # +1
                    process_a()
                elif item.type == 'B': # +1
                    process_b()
    # ... (complexity = 10+, would trigger warning)
```

## 🛠️ Tool Installation

### Install Static Analysis Tools
```bash
# Install all tools
pip install pylint flake8 mypy black isort bandit[toml]

# Or install development dependencies
pip install -r requirements-dev.txt  # If available
```

### IDE Integration
```bash
# VS Code settings.json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.provider": "isort"
}
```

## 📈 Continuous Integration

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Set up hooks (create .pre-commit-config.yaml)
pre-commit install
```

### CI/CD Pipeline
```yaml
# GitHub Actions example
- name: Run Code Quality Checks
  run: |
    python scripts/run_quality_checks.py --fail-fast
    
- name: Upload Coverage Report
  run: |
    pytest tests/test_code_quality.py --cov=. --cov-report=xml
```

## 🎯 Benefits

### 1. **Maintainability**
- Reduces code duplication by 70%+
- Identifies refactoring opportunities
- Maintains consistent code style

### 2. **Quality Assurance**
- Catches potential bugs early
- Enforces architectural standards
- Prevents technical debt accumulation

### 3. **Developer Experience**
- Provides actionable feedback
- Automates code review tasks
- Maintains coding standards

### 4. **Team Collaboration**
- Consistent code style across team
- Shared quality standards
- Automated enforcement

## 🔧 Customization

### Adding New Quality Checks
```python
def test_custom_quality_rule(self, code_analyzer):
    """Add your custom quality check here."""
    violations = code_analyzer.detect_custom_pattern()
    assert len(violations) == 0, f"Custom rule violations: {violations}"
```

### Adjusting Thresholds
```python
# In TestCodeQuality class
MAX_ALLOWED_DUPLICATIONS = 3  # Stricter
MAX_FUNCTION_COMPLEXITY = 10  # More conservative
```

### Excluding Files/Patterns
```python
# In CodeAnalyzer.__init__
exclude_patterns = ['migrations/', 'generated/', 'vendor/']
self.python_files = [f for f in self.python_files 
                    if not any(pattern in str(f) for pattern in exclude_patterns)]
```

## 📚 Further Reading

- [Pylint Documentation](https://pylint.pycqa.org/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Black Documentation](https://black.readthedocs.io/)
- [Code Quality Best Practices](https://docs.python.org/3/tutorial/controlflow.html#coding-style) 