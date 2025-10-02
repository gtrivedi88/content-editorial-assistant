"""
Pytest configuration and shared fixtures for Content Editorial Assistant tests.
This file is automatically loaded by pytest and provides fixtures for all test modules.
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Generator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import with error handling for optional dependencies
try:
    from main import create_app
except ImportError as e:
    print(f"⚠️  Warning: Could not import main app ({e})")
    print(f"⚠️  Creating mock app for testing. Some fixtures may have limited functionality.")
    from flask import Flask
    def create_app():
        return Flask(__name__)

try:
    from database.models import db as _db
    from database.services import DatabaseService
except ImportError as e:
    print(f"⚠️  Warning: Could not import database modules ({e})")
    _db = None
    DatabaseService = None


# ================================
# Application Fixtures
# ================================

@pytest.fixture(scope='session')
def app():
    """Create and configure a test Flask application instance."""
    # Use in-memory database for tests
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
    }
    
    app = create_app(test_config)
    
    # Create application context
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create a CLI runner for testing CLI commands."""
    return app.test_cli_runner()


# ================================
# Database Fixtures
# ================================

@pytest.fixture(scope='function')
def db(app):
    """Provide a clean database for each test."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def db_service(app, db):
    """Provide a DatabaseService instance for testing."""
    return DatabaseService()


# ================================
# File System Fixtures
# ================================

@pytest.fixture(scope='function')
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope='function')
def sample_text_file(temp_dir) -> Path:
    """Create a sample text file for testing."""
    file_path = temp_dir / "sample.txt"
    file_path.write_text("This is a sample text for testing purposes.")
    return file_path


@pytest.fixture(scope='function')
def sample_markdown_file(temp_dir) -> Path:
    """Create a sample markdown file for testing."""
    content = """# Sample Markdown
    
This is a sample markdown document.

## Features
- Item 1
- Item 2
- Item 3

## Conclusion
This concludes the sample.
"""
    file_path = temp_dir / "sample.md"
    file_path.write_text(content)
    return file_path


# ================================
# Test Data Fixtures
# ================================

@pytest.fixture
def sample_content():
    """Provide sample content for analysis testing."""
    return """
    This is a sample document for testing. The document contains multiple sentences.
    Some sentences are longer than others. This helps test various rules and checks.
    
    The system should detect issues like passive voice, wordiness, and other problems.
    """


@pytest.fixture
def sample_analysis_result():
    """Provide a sample analysis result for testing."""
    return {
        'errors': [
            {
                'rule_id': 'passive_voice',
                'message': 'Passive voice detected',
                'start': 10,
                'end': 30,
                'severity': 'warning',
                'suggestions': ['Use active voice']
            }
        ],
        'statistics': {
            'word_count': 100,
            'sentence_count': 5,
            'readability_score': 65.5
        }
    }


# ================================
# Mock Fixtures
# ================================

@pytest.fixture
def mock_ollama_response(monkeypatch):
    """Mock Ollama API responses for testing."""
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code
        
        def json(self):
            return self.json_data
    
    def mock_post(*args, **kwargs):
        return MockResponse({
            'response': 'This is a mocked response from Ollama',
            'model': 'llama2',
            'done': True
        })
    
    import requests
    monkeypatch.setattr(requests, 'post', mock_post)


# ================================
# Performance Testing Fixtures
# ================================

@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests."""
    metrics = {
        'start_time': datetime.now(),
        'operations': []
    }
    
    def record_operation(name: str, duration: float):
        metrics['operations'].append({
            'name': name,
            'duration': duration,
            'timestamp': datetime.now()
        })
    
    metrics['record'] = record_operation
    return metrics


# ================================
# Pytest Hooks
# ================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "ui: marks tests as UI tests requiring Playwright"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "smoke: marks tests as smoke tests for quick validation"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark UI tests
        if "ui" in str(item.fspath) or "playwright" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        
        # Auto-mark API tests
        if "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        
        # Auto-mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Auto-mark E2E tests
        if "e2e" in str(item.fspath) or "end_to_end" in str(item.name):
            item.add_marker(pytest.mark.e2e)
        
        # Auto-mark performance tests
        if "performance" in str(item.fspath) or "benchmark" in str(item.name):
            item.add_marker(pytest.mark.performance)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test results for reporting."""
    outcome = yield
    rep = outcome.get_result()
    
    # Store the result on the item for later access
    setattr(item, f"rep_{rep.when}", rep)

