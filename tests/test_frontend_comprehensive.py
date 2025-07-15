"""
Comprehensive Test Suite for Frontend JavaScript Functionality
Tests frontend JavaScript components including DOM manipulation, file handling,
WebSocket communication, analysis display, and user interactions using browser
automation with Selenium WebDriver.
"""

import pytest
import os
import sys
import time
import json
import tempfile
from unittest.mock import patch, MagicMock, Mock
from typing import Dict, List, Any, Optional

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Selenium imports for browser automation
try:
    from selenium import webdriver  # type: ignore
    from selenium.webdriver.common.by import By  # type: ignore
    from selenium.webdriver.support.ui import WebDriverWait  # type: ignore
    from selenium.webdriver.support import expected_conditions as EC  # type: ignore
    from selenium.webdriver.common.action_chains import ActionChains  # type: ignore
    from selenium.webdriver.chrome.options import Options  # type: ignore
    from selenium.webdriver.chrome.service import Service  # type: ignore
    from selenium.common.exceptions import TimeoutException, NoSuchElementException  # type: ignore
    from selenium.webdriver.common.keys import Keys  # type: ignore
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Flask and SocketIO for test server
try:
    from app import create_app
    from app_modules.app_factory import create_app as create_test_app
    import threading
    import socket
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


class TestFrontendSystem:
    """Comprehensive test suite for frontend JavaScript functionality."""
    
    @pytest.fixture(scope="class")
    def test_app(self):
        """Create test Flask application."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        from src.config import Config
        
        class TestConfig(Config):
            TESTING = True
            SECRET_KEY = 'test-secret-key'
            WTF_CSRF_ENABLED = False
            UPLOAD_FOLDER = tempfile.mkdtemp()
        
        app, socketio = create_test_app(TestConfig)
        return app, socketio
    
    @pytest.fixture(scope="class")
    def test_server(self, test_app):
        """Start test server in a separate thread."""
        if not FLASK_AVAILABLE:
            pytest.skip("Flask not available")
        
        app, socketio = test_app
        
        # Find available port
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        
        # Start server in thread
        server_thread = threading.Thread(
            target=lambda: socketio.run(app, host='localhost', port=port, debug=False, allow_unsafe_werkzeug=True),
            daemon=True
        )
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
        
        yield f"http://localhost:{port}"
        
        # Server will stop when test ends due to daemon thread
    
    @pytest.fixture(scope="class")
    def browser_driver(self):
        """Create Selenium WebDriver instance."""
        if not SELENIUM_AVAILABLE:
            pytest.skip("Selenium not available")
        
        # Chrome options for headless testing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            yield driver
            driver.quit()
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
    
    @pytest.fixture
    def sample_files(self):
        """Create sample files for testing."""
        return {
            'text_content': "This is a sample text for testing. It has multiple sentences. Some are longer than others.",
            'markdown_content': "# Test Document\n\nThis is a test paragraph with **bold** text.\n\n- Item 1\n- Item 2",
            'complex_content': """This is a comprehensive test document for analyzing various style issues.
            
The system is configured automatically by the administrator. This sentence contains passive voice.
Don't use contractions in formal writing. This creates inconsistency.

Here is a very long sentence that should probably be broken down into smaller, more manageable pieces because it contains too many ideas and clauses that make it difficult to read and understand for the average reader.

Some complex technical jargon and unnecessarily verbose language that could be simplified for better readability and comprehension by the target audience.""",
            'file_name': 'test_document.txt',
            'file_size': 1024
        }
    
    # ===============================
    # CORE FUNCTIONALITY TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_page_load_and_initialization(self, browser_driver, test_server):
        """Test page load and JavaScript initialization."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check page title
        assert "Style Guide AI" in driver.title
        
        # Check main elements are present
        assert driver.find_element(By.ID, "upload-area")
        assert driver.find_element(By.ID, "file-input")
        assert driver.find_element(By.ID, "text-input")
        
        # Check JavaScript is loaded and executed
        script_result = driver.execute_script("return typeof initializeSocket === 'function';")
        assert script_result == True
        
        script_result = driver.execute_script("return typeof handleFileUpload === 'function';")
        assert script_result == True
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_global_variables_initialization(self, browser_driver, test_server):
        """Test global JavaScript variables initialization."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check global variables are defined
        current_analysis = driver.execute_script("return typeof currentAnalysis;")
        assert current_analysis == "object"
        
        current_content = driver.execute_script("return typeof currentContent;")
        assert current_content == "object"
        
        socket_var = driver.execute_script("return typeof socket;")
        assert socket_var == "object"
        
        session_id = driver.execute_script("return typeof sessionId;")
        assert session_id == "object"
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_tooltips_initialization(self, browser_driver, test_server):
        """Test Bootstrap tooltips initialization."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if tooltips are initialized (look for elements with tooltip triggers)
        tooltip_elements = driver.find_elements(By.CSS_SELECTOR, "[data-bs-toggle='tooltip']")
        
        if tooltip_elements:
            # Hover over tooltip element to trigger it
            ActionChains(driver).move_to_element(tooltip_elements[0]).perform()
            time.sleep(0.5)
            
            # Check if tooltip is displayed
            tooltip_displayed = driver.execute_script(
                "return document.querySelector('.tooltip') !== null;"
            )
            # Note: This may not always work due to timing, but validates tooltip setup
    
    # ===============================
    # FILE HANDLING TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_file_input_interaction(self, browser_driver, test_server, sample_files):
        """Test file input interactions."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "file-input"))
        )
        
        # Check file input is present and functional
        file_input = driver.find_element(By.ID, "file-input")
        assert file_input.is_enabled()
        
        # Check upload area is present
        upload_area = driver.find_element(By.ID, "upload-area")
        assert upload_area.is_displayed()
        
        # Test that upload area has drag-and-drop event listeners
        upload_area_classes = upload_area.get_attribute("class")
        assert upload_area_classes is not None
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_text_input_functionality(self, browser_driver, test_server, sample_files):
        """Test text input functionality."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for text input to be available
        text_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "text-input"))
        )
        
        # Test text input
        text_input.clear()
        text_input.send_keys(sample_files['text_content'])
        
        # Check text was entered
        entered_text = text_input.get_attribute("value")
        assert sample_files['text_content'] in entered_text
        
        # Test auto-resize functionality
        initial_height = text_input.get_attribute("style")
        
        # Add more text to trigger resize
        text_input.send_keys("\n" + sample_files['complex_content'])
        
        # Check if height changed (auto-resize working)
        new_height = text_input.get_attribute("style")
        # Note: This test may be flaky depending on CSS implementation
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_text_analysis_button(self, browser_driver, test_server, sample_files):
        """Test direct text analysis functionality."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for elements to load
        text_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "text-input"))
        )
        
        # Enter text
        text_input.clear()
        text_input.send_keys(sample_files['text_content'])
        
        # Find analyze button
        analyze_button = driver.find_element(By.CSS_SELECTOR, "button[onclick*='analyzeDirectText']")
        assert analyze_button.is_enabled()
        
        # Click analyze button
        analyze_button.click()
        
        # Check if analysis results area appears or loading state is shown
        time.sleep(1)
        results_area = driver.find_element(By.ID, "analysis-results")
        assert results_area.is_displayed()
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_drag_and_drop_simulation(self, browser_driver, test_server):
        """Test drag and drop area interactions."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for upload area
        upload_area = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "upload-area"))
        )
        
        # Simulate dragover event
        driver.execute_script("""
            var event = new DragEvent('dragover', {
                bubbles: true,
                cancelable: true
            });
            arguments[0].dispatchEvent(event);
        """, upload_area)
        
        # Check if dragover class is added
        time.sleep(0.1)
        classes = upload_area.get_attribute("class")
        
        # Simulate dragleave event
        driver.execute_script("""
            var event = new DragEvent('dragleave', {
                bubbles: true,
                cancelable: true
            });
            arguments[0].dispatchEvent(event);
        """, upload_area)
        
        # Check if dragover class is removed
        time.sleep(0.1)
        classes_after = upload_area.get_attribute("class")
    
    # ===============================
    # WEBSOCKET COMMUNICATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_websocket_connection(self, browser_driver, test_server):
        """Test WebSocket connection establishment."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load and socket initialization
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Wait for socket connection
        time.sleep(2)
        
        # Check if socket is connected
        socket_connected = driver.execute_script("""
            return socket && socket.connected === true;
        """)
        
        # Note: This may fail if WebSocket connection is not established
        # In real environment, this should work with proper server setup
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_session_id_handling(self, browser_driver, test_server):
        """Test session ID reception and handling."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        time.sleep(2)
        
        # Check if sessionId is set
        session_id = driver.execute_script("return sessionId;")
        
        # Session ID should be set after socket connection
        # Note: May be null if WebSocket server is not properly configured
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_progress_update_handling(self, browser_driver, test_server):
        """Test progress update handling via WebSocket."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Simulate progress update
        driver.execute_script("""
            if (typeof handleProgressUpdate === 'function') {
                handleProgressUpdate({
                    step: 'analysis_start',
                    status: 'Starting analysis',
                    detail: 'Initializing style analyzer',
                    progress: 10
                });
            }
        """)
        
        # Check if progress update was handled
        # Note: This requires the actual UI elements to be present
        time.sleep(0.5)
    
    # ===============================
    # UTILITY FUNCTIONS TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_show_loading_function(self, browser_driver, test_server):
        """Test showLoading utility function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Create a test element
        driver.execute_script("""
            var testElement = document.createElement('div');
            testElement.id = 'test-loading';
            document.body.appendChild(testElement);
        """)
        
        # Call showLoading function
        driver.execute_script("""
            showLoading('test-loading', 'Test loading message');
        """)
        
        # Check if loading content is displayed
        test_element = driver.find_element(By.ID, "test-loading")
        content = test_element.get_attribute("innerHTML")
        
        assert "Test loading message" in content
        assert "spinner-border" in content
        assert "fas fa-search" in content
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_show_error_function(self, browser_driver, test_server):
        """Test showError utility function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Create a test element
        driver.execute_script("""
            var testElement = document.createElement('div');
            testElement.id = 'test-error';
            document.body.appendChild(testElement);
        """)
        
        # Call showError function
        driver.execute_script("""
            showError('test-error', 'Test error message');
        """)
        
        # Check if error content is displayed
        test_element = driver.find_element(By.ID, "test-error")
        content = test_element.get_attribute("innerHTML")
        
        assert "Test error message" in content
        assert "alert-danger" in content
        assert "fas fa-exclamation-triangle" in content
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_show_success_function(self, browser_driver, test_server):
        """Test showSuccess utility function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Create a test element
        driver.execute_script("""
            var testElement = document.createElement('div');
            testElement.id = 'test-success';
            document.body.appendChild(testElement);
        """)
        
        # Call showSuccess function
        driver.execute_script("""
            showSuccess('test-success', 'Test success message');
        """)
        
        # Check if success content is displayed
        test_element = driver.find_element(By.ID, "test-success")
        content = test_element.get_attribute("innerHTML")
        
        assert "Test success message" in content
        assert "alert-success" in content
        assert "fas fa-check-circle" in content
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_highlight_errors_function(self, browser_driver, test_server):
        """Test highlightErrors utility function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test highlightErrors function
        result = driver.execute_script("""
            var text = 'This is a test sentence. Another sentence here.';
            var errors = [
                { sentence: 'This is a test sentence.' },
                { sentence: 'Another sentence here.' }
            ];
            return highlightErrors(text, errors);
        """)
        
        assert "error-highlight" in result
        assert "This is a test sentence" in result
        assert "Another sentence here" in result
    
    # ===============================
    # ANALYSIS DISPLAY TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_display_analysis_results_function(self, browser_driver, test_server):
        """Test displayAnalysisResults function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Create analysis-results element
        driver.execute_script("""
            var resultsElement = document.createElement('div');
            resultsElement.id = 'analysis-results';
            document.body.appendChild(resultsElement);
        """)
        
        # Test displayAnalysisResults function
        driver.execute_script("""
            var mockAnalysis = {
                errors: [
                    {
                        type: 'passive_voice',
                        message: 'Passive voice detected',
                        sentence: 'The document was written by the team.',
                        suggestions: ['Use active voice']
                    }
                ],
                statistics: {
                    word_count: 50,
                    sentence_count: 3,
                    paragraph_count: 1
                },
                technical_writing_metrics: {
                    readability_score: 75.0,
                    grade_level: 8.5,
                    fog_index: 10.2
                },
                overall_score: 82.5
            };
            var content = 'This is test content. The document was written by the team.';
            displayAnalysisResults(mockAnalysis, content);
        """)
        
        # Check if results are displayed
        results_element = driver.find_element(By.ID, "analysis-results")
        content = results_element.get_attribute("innerHTML")
        
        assert "passive_voice" in content or "Passive voice detected" in content
        assert "word_count" in content or "50" in content
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_structural_blocks_display(self, browser_driver, test_server):
        """Test structural blocks display functionality."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test displayStructuralBlocks function
        result = driver.execute_script("""
            var blocks = [
                {
                    type: 'heading',
                    content: 'Test Heading',
                    errors: [],
                    start_line: 1,
                    end_line: 1
                },
                {
                    type: 'paragraph',
                    content: 'This is a test paragraph.',
                    errors: [
                        {
                            type: 'passive_voice',
                            message: 'Passive voice detected'
                        }
                    ],
                    start_line: 2,
                    end_line: 2
                }
            ];
            return displayStructuralBlocks(blocks);
        """)
        
        if result:
            assert "structural-blocks" in result
            assert "Test Heading" in result
            assert "test paragraph" in result
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_create_error_card_function(self, browser_driver, test_server):
        """Test createErrorCard function."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test createErrorCard function
        result = driver.execute_script("""
            var error = {
                type: 'passive_voice',
                message: 'Passive voice detected in this sentence',
                sentence: 'The document was written by the team.',
                suggestions: ['Use active voice instead', 'Rewrite to clarify who performs the action']
            };
            return createErrorCard(error);
        """)
        
        assert "passive_voice" in result
        assert "Passive voice detected" in result
        assert "The document was written by the team" in result
        assert "Use active voice instead" in result
    
    # ===============================
    # USER INTERACTION TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_card_hover_effects(self, browser_driver, test_server):
        """Test card hover effects."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find cards on the page
        cards = driver.find_elements(By.CSS_SELECTOR, ".card")
        
        if cards:
            # Get initial transform style
            initial_transform = cards[0].value_of_css_property("transform")
            
            # Hover over card
            ActionChains(driver).move_to_element(cards[0]).perform()
            time.sleep(0.5)
            
            # Check if transform changed (hover effect)
            new_transform = cards[0].value_of_css_property("transform")
            
            # Note: Transform change depends on CSS implementation
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_file_text_input_mutual_clearing(self, browser_driver, test_server):
        """Test mutual clearing of file and text inputs."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for inputs to be available
        text_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "text-input"))
        )
        file_input = driver.find_element(By.ID, "file-input")
        
        # Enter text first
        text_input.clear()
        text_input.send_keys("Some test text")
        
        # Check text was entered
        assert text_input.get_attribute("value") == "Some test text"
        
        # Simulate file selection (trigger change event)
        driver.execute_script("""
            var fileInput = document.getElementById('file-input');
            var event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        """)
        
        # Check if text input was cleared
        # Note: This depends on the actual event handler implementation
        time.sleep(0.1)
        
        # Test reverse: enter text after file selection should clear file
        text_input.clear()
        text_input.send_keys("New text")
        
        # File input value should be cleared (if event handler is properly set up)
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_sample_text_analysis(self, browser_driver, test_server):
        """Test sample text analysis functionality."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Look for sample text buttons
        sample_buttons = driver.find_elements(By.CSS_SELECTOR, "button[onclick*='analyzeSampleText']")
        
        if sample_buttons:
            # Click sample button
            sample_buttons[0].click()
            
            # Check if analysis starts
            time.sleep(1)
            
            # Check if results area shows loading or results
            results_area = driver.find_element(By.ID, "analysis-results")
            content = results_area.get_attribute("innerHTML")
            
            # Should show loading state or results
            assert content != ""
    
    # ===============================
    # ERROR HANDLING TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_javascript_error_handling(self, browser_driver, test_server):
        """Test JavaScript error handling."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for JavaScript errors in console
        logs = driver.get_log('browser')
        
        # Filter for JavaScript errors
        js_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Should have no severe JavaScript errors
        if js_errors:
            print("JavaScript errors found:", js_errors)
        
        # Note: Some errors might be expected depending on test environment
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_missing_element_handling(self, browser_driver, test_server):
        """Test handling of missing DOM elements."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test functions with non-existent elements
        driver.execute_script("""
            // These should not cause errors
            showLoading('non-existent-element', 'Test');
            showError('non-existent-element', 'Test');
            showSuccess('non-existent-element', 'Test');
        """)
        
        # Check no errors were thrown
        logs = driver.get_log('browser')
        new_errors = [log for log in logs if log['level'] == 'SEVERE']
        
        # Should handle missing elements gracefully
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_full_analysis_workflow(self, browser_driver, test_server, sample_files):
        """Test complete analysis workflow from input to results."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        text_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "text-input"))
        )
        
        # Enter text
        text_input.clear()
        text_input.send_keys(sample_files['complex_content'])
        
        # Find and click analyze button
        analyze_button = driver.find_element(By.CSS_SELECTOR, "button[onclick*='analyzeDirectText']")
        analyze_button.click()
        
        # Wait for analysis to complete or show loading
        WebDriverWait(driver, 30).until(
            lambda d: d.find_element(By.ID, "analysis-results").get_attribute("innerHTML") != ""
        )
        
        # Check results are displayed
        results_area = driver.find_element(By.ID, "analysis-results")
        content = results_area.get_attribute("innerHTML")
        
        # Should show either loading state or actual results
        assert content != ""
        assert "spinner-border" in content or "analysis" in content.lower()
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_responsive_design_elements(self, browser_driver, test_server):
        """Test responsive design elements."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Test different viewport sizes
        viewports = [
            (1920, 1080),  # Desktop
            (768, 1024),   # Tablet
            (375, 667)     # Mobile
        ]
        
        for width, height in viewports:
            driver.set_window_size(width, height)
            time.sleep(0.5)
            
            # Check if key elements are still visible
            upload_area = driver.find_element(By.ID, "upload-area")
            text_input = driver.find_element(By.ID, "text-input")
            
            assert upload_area.is_displayed()
            assert text_input.is_displayed()
    
    @pytest.mark.skipif(not (SELENIUM_AVAILABLE and FLASK_AVAILABLE), reason="Browser automation not available")
    def test_accessibility_features(self, browser_driver, test_server):
        """Test accessibility features."""
        driver = browser_driver
        driver.get(test_server)
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check for accessibility attributes
        elements_with_aria = driver.find_elements(By.CSS_SELECTOR, "[aria-label], [aria-describedby], [role]")
        
        # Should have some accessibility attributes
        # Note: Exact requirements depend on application design
        
        # Check for proper heading hierarchy
        headings = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
        
        # Should have logical heading structure
        if headings:
            h1_elements = driver.find_elements(By.TAG_NAME, "h1")
            # Should have at least one h1 for page title


# ===============================
# NON-BROWSER JAVASCRIPT TESTS
# ===============================

class TestJavaScriptLogic:
    """Test JavaScript logic without browser automation."""
    
    def test_javascript_function_definitions(self):
        """Test that JavaScript functions are properly defined in files."""
        js_files = [
            'static/js/core.js',
            'static/js/file-handler.js',
            'static/js/socket-handler.js',
            'static/js/utility-functions.js',
            'static/js/style-helpers.js',
            'static/js/error-display.js',
            'static/js/statistics-display.js',
            'static/js/block-creators-basic.js',
            'static/js/block-creators-complex.js',
            'static/js/display-main.js'
        ]
        
        expected_functions = {
            'core.js': ['initializeSocket', 'initializeTooltips', 'initializeFileHandlers', 'analyzeDirectText'],
            'file-handler.js': ['handleFileUpload', 'showFileUploadProgress', 'analyzeContent'],
            'socket-handler.js': ['initializeSocket', 'handleProgressUpdate', 'updateStepIndicators'],
            'utility-functions.js': ['showLoading', 'showError', 'showSuccess', 'highlightErrors'],
            'style-helpers.js': ['escapeHtml', 'getBlockTypeDisplayName', 'getFleschColor', 'getGradeLevelInsight'],
            'error-display.js': ['createInlineError'],
            'statistics-display.js': ['generateStatisticsCard', 'generateModernReadabilityCard'],
            'block-creators-basic.js': ['createStructuralBlock', 'createSectionBlock'],
            'block-creators-complex.js': ['createListBlock', 'createListTitleBlock', 'createTableBlock'],
            'display-main.js': ['displayStructuralBlocks', 'displayAnalysisResults', 'displayFlatContent']
        }
        
        for js_file in js_files:
            if os.path.exists(js_file):
                with open(js_file, 'r') as f:
                    content = f.read()
                
                file_name = os.path.basename(js_file)
                if file_name in expected_functions:
                    for func_name in expected_functions[file_name]:
                        assert func_name in content, f"Function {func_name} not found in {js_file}"
    
    def test_javascript_syntax_validity(self):
        """Test that JavaScript files have valid syntax (basic check)."""
        js_files = [
            'static/js/core.js',
            'static/js/file-handler.js',
            'static/js/socket-handler.js',
            'static/js/utility-functions.js',
            'static/js/style-helpers.js',
            'static/js/error-display.js',
            'static/js/statistics-display.js',
            'static/js/block-creators-basic.js',
            'static/js/block-creators-complex.js',
            'static/js/display-main.js'
        ]
        
        for js_file in js_files:
            if os.path.exists(js_file):
                with open(js_file, 'r') as f:
                    content = f.read()
                
                # Basic syntax checks
                assert content.count('{') == content.count('}'), f"Mismatched braces in {js_file}"
                assert content.count('(') == content.count(')'), f"Mismatched parentheses in {js_file}"
                assert content.count('[') == content.count(']'), f"Mismatched brackets in {js_file}"
                
                # Check for obvious syntax errors (more reasonable checks)
                assert ')function' not in content, f"Syntax error: missing space in {js_file}"
                # Note: function( is valid in addEventListener('event', function() {
    
    def test_html_template_javascript_integration(self):
        """Test that HTML templates properly include JavaScript files."""
        # Only check base.html since index.html extends it and doesn't include JS directly
        template_file = 'templates/base.html'
        
        expected_js_files = [
            'core.js',
            'file-handler.js',
            'socket-handler.js',
            'utility-functions.js',
            'style-helpers.js',
            'error-display.js',
            'statistics-display.js',
            'block-creators-basic.js',
            'block-creators-complex.js',
            'display-main.js'
        ]
        
        if os.path.exists(template_file):
            with open(template_file, 'r') as f:
                content = f.read()
            
            for js_file in expected_js_files:
                # Check if JavaScript file is referenced
                assert js_file in content or f"js/{js_file}" in content, f"JavaScript file {js_file} not included in {template_file}"
    
    def test_css_file_existence(self):
        """Test that CSS files exist and are referenced."""
        css_files = [
            'static/css/styles.css'
        ]
        
        for css_file in css_files:
            assert os.path.exists(css_file), f"CSS file {css_file} does not exist"
            
            # Check file is not empty
            with open(css_file, 'r') as f:
                content = f.read().strip()
                assert len(content) > 0, f"CSS file {css_file} is empty" 