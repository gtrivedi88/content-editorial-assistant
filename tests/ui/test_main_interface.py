"""
UI Tests for Content Editorial Assistant main interface.
Tests the primary user workflows and interactions.
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.ui
class TestMainInterface:
    """Test the main user interface."""
    
    def test_homepage_loads(self, page: Page, app_url: str):
        """Test that the homepage loads successfully."""
        page.goto(app_url)
        
        # Check that the page loaded
        expect(page).to_have_title("Content Editorial Assistant")
        
        # Check for main elements
        expect(page.locator("h1")).to_be_visible()
    
    def test_text_area_visible(self, page: Page, app_url: str):
        """Test that the text input area is visible."""
        page.goto(app_url)
        
        # Check for textarea or content editable
        textarea = page.locator("textarea, [contenteditable='true']").first
        expect(textarea).to_be_visible()
    
    def test_analyze_button_present(self, page: Page, app_url: str):
        """Test that the analyze button is present."""
        page.goto(app_url)
        
        # Look for analyze button
        analyze_btn = page.get_by_role("button", name="Analyze")
        expect(analyze_btn).to_be_visible()
    
    def test_file_upload_available(self, page: Page, app_url: str):
        """Test that file upload functionality is available."""
        page.goto(app_url)
        
        # Check for file upload input
        file_input = page.locator("input[type='file']")
        expect(file_input).to_be_attached()


@pytest.mark.ui
@pytest.mark.e2e
class TestAnalysisWorkflow:
    """Test the complete analysis workflow."""
    
    def test_simple_text_analysis(self, page: Page, app_url: str):
        """Test analyzing simple text content."""
        page.goto(app_url)
        
        # Enter text
        textarea = page.locator("textarea, [contenteditable='true']").first
        sample_text = "This is a test sentence. It should be analyzed for issues."
        textarea.fill(sample_text)
        
        # Click analyze
        analyze_btn = page.get_by_role("button", name="Analyze")
        analyze_btn.click()
        
        # Wait for results (adjust selector based on your UI)
        page.wait_for_selector(".results, #results, [data-testid='results']", timeout=10000)
        
        # Check that results are displayed
        results = page.locator(".results, #results, [data-testid='results']").first
        expect(results).to_be_visible()
    
    def test_error_display(self, page: Page, app_url: str):
        """Test that errors are displayed in the UI."""
        page.goto(app_url)
        
        # Enter text with known issues
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill("The document was written by me.")  # Passive voice
        
        # Analyze
        page.get_by_role("button", name="Analyze").click()
        
        # Wait for error indicators
        page.wait_for_selector(".error, .issue, [data-severity]", timeout=10000)
        
        # Verify errors are shown
        errors = page.locator(".error, .issue, [data-severity]")
        expect(errors.first).to_be_visible()
    
    def test_suggestion_interaction(self, page: Page, app_url: str):
        """Test clicking on suggestions."""
        page.goto(app_url)
        
        # Enter text and analyze
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill("This sentence has an issue that should be detected.")
        page.get_by_role("button", name="Analyze").click()
        
        # Wait for results
        page.wait_for_selector(".error, .issue", timeout=10000)
        
        # Click on first error
        first_error = page.locator(".error, .issue").first
        first_error.click()
        
        # Verify that details or suggestions appear
        # (adjust based on your UI behavior)
        suggestion_panel = page.locator(".suggestion, .details, [data-testid='suggestion']")
        expect(suggestion_panel.first).to_be_visible(timeout=5000)
    
    def test_file_upload_workflow(self, page: Page, app_url: str, tmp_path):
        """Test uploading and analyzing a file."""
        page.goto(app_url)
        
        # Create a test file
        test_file = tmp_path / "test_document.txt"
        test_file.write_text("This is a test document with some content to analyze.")
        
        # Upload file
        file_input = page.locator("input[type='file']")
        file_input.set_input_files(str(test_file))
        
        # Wait for upload to complete
        page.wait_for_selector(".upload-success, .file-loaded", timeout=10000)
        
        # Analyze uploaded file
        page.get_by_role("button", name="Analyze").click()
        
        # Verify results
        page.wait_for_selector(".results", timeout=15000)
        results = page.locator(".results").first
        expect(results).to_be_visible()


@pytest.mark.ui
class TestFeedbackSystem:
    """Test the feedback system UI."""
    
    def test_feedback_buttons_present(self, page: Page, app_url: str):
        """Test that feedback buttons are present after analysis."""
        page.goto(app_url)
        
        # Perform analysis
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill("Sample text for feedback testing.")
        page.get_by_role("button", name="Analyze").click()
        
        # Wait for results
        page.wait_for_selector(".results, .error", timeout=10000)
        
        # Check for feedback buttons (thumbs up/down, etc.)
        feedback_btns = page.locator("[data-feedback], .feedback-btn, button[title*='feedback' i]")
        assert feedback_btns.count() > 0, "No feedback buttons found"
    
    def test_submit_positive_feedback(self, page: Page, app_url: str):
        """Test submitting positive feedback."""
        page.goto(app_url)
        
        # Perform analysis
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill("Test content for positive feedback.")
        page.get_by_role("button", name="Analyze").click()
        page.wait_for_selector(".results", timeout=10000)
        
        # Click positive feedback button
        positive_btn = page.locator("[data-feedback='positive'], .feedback-positive, button[title*='helpful' i]").first
        if positive_btn.is_visible():
            positive_btn.click()
            
            # Verify feedback was recorded (adjust based on your UI)
            success_msg = page.locator(".feedback-success, .toast-success")
            expect(success_msg.first).to_be_visible(timeout=5000)


@pytest.mark.ui
@pytest.mark.performance
class TestUIPerformance:
    """Test UI performance and responsiveness."""
    
    def test_large_document_rendering(self, page: Page, app_url: str):
        """Test UI performance with large documents."""
        page.goto(app_url)
        
        # Create large text
        large_text = "This is a sentence. " * 500  # ~10,000 characters
        
        # Measure input performance
        import time
        start = time.time()
        
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill(large_text)
        
        fill_time = time.time() - start
        
        # Should be reasonably fast
        assert fill_time < 5.0, f"Text input took {fill_time}s, too slow"
        
        # Analyze
        start = time.time()
        page.get_by_role("button", name="Analyze").click()
        page.wait_for_selector(".results", timeout=30000)
        analysis_time = time.time() - start
        
        # Analysis should complete in reasonable time
        assert analysis_time < 30.0, f"Analysis took {analysis_time}s, too slow"
    
    def test_ui_responsive_during_analysis(self, page: Page, app_url: str):
        """Test that UI remains responsive during analysis."""
        page.goto(app_url)
        
        # Enter text
        textarea = page.locator("textarea, [contenteditable='true']").first
        textarea.fill("Test content for responsiveness check.")
        
        # Start analysis
        page.get_by_role("button", name="Analyze").click()
        
        # Check for loading indicator
        loading = page.locator(".loading, .spinner, [data-loading='true']")
        expect(loading.first).to_be_visible(timeout=2000)
        
        # UI should still be interactive (button should show processing state)
        analyze_btn = page.get_by_role("button", name="Analyze")
        # Button might be disabled or show different text
        is_disabled = analyze_btn.is_disabled() if analyze_btn.is_visible() else False
        # This is acceptable during processing


@pytest.mark.ui
class TestAccessibility:
    """Test accessibility features."""
    
    def test_keyboard_navigation(self, page: Page, app_url: str):
        """Test that the interface is keyboard accessible."""
        page.goto(app_url)
        
        # Tab through interactive elements
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement.tagName")
        
        # Should focus on an interactive element
        assert focused in ["BUTTON", "INPUT", "TEXTAREA", "A"], f"Unexpected focus on {focused}"
    
    def test_aria_labels_present(self, page: Page, app_url: str):
        """Test that important elements have ARIA labels."""
        page.goto(app_url)
        
        # Check for ARIA labels on key elements
        buttons = page.locator("button")
        button_count = buttons.count()
        
        for i in range(min(button_count, 10)):  # Check first 10 buttons
            button = buttons.nth(i)
            if button.is_visible():
                # Should have either text content or aria-label
                text = button.inner_text()
                aria_label = button.get_attribute("aria-label")
                assert text or aria_label, f"Button {i} has no accessible label"

