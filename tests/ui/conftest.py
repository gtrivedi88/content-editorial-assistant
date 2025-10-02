"""
Playwright configuration and fixtures for UI testing.
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from pathlib import Path
import os


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Configure browser launch arguments."""
    return {
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
        "slow_mo": int(os.getenv("SLOW_MO", "0")),
        "args": ["--start-maximized"] if os.getenv("HEADLESS", "true").lower() == "false" else []
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context arguments."""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "record_video_dir": "tests/ui/videos" if os.getenv("RECORD_VIDEO", "false").lower() == "true" else None,
        "record_video_size": {"width": 1280, "height": 720}
    }


@pytest.fixture(scope="session")
def playwright():
    """Start Playwright."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright, browser_type_launch_args):
    """Launch browser for the session."""
    browser = playwright.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser, browser_context_args):
    """Create a new browser context for each test."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Create a new page for each test."""
    page = context.new_page()
    
    # Set default timeout
    page.set_default_timeout(30000)
    
    # Set default navigation timeout
    page.set_default_navigation_timeout(30000)
    
    yield page
    
    # Take screenshot on failure
    if hasattr(page, 'video'):
        video = page.video
        if video:
            video.path()
    
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page, app_url):
    """Create an authenticated page (if your app has authentication)."""
    # Navigate to login page
    page.goto(f"{app_url}/login")
    
    # Perform login (adjust selectors as needed)
    # page.fill("#username", "test_user")
    # page.fill("#password", "test_password")
    # page.click("#login-button")
    # page.wait_for_url(f"{app_url}/dashboard")
    
    yield page


@pytest.fixture(scope="session")
def app_url():
    """Get the application URL for testing."""
    return os.getenv("APP_URL", "http://localhost:5000")


@pytest.fixture(scope="function")
def screenshot_dir():
    """Create directory for test screenshots."""
    screenshot_path = Path("tests/ui/screenshots")
    screenshot_path.mkdir(parents=True, exist_ok=True)
    return screenshot_path


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on test failure."""
    outcome = yield
    rep = outcome.get_result()
    
    if rep.when == "call" and rep.failed:
        # Get the page fixture if it exists
        if "page" in item.funcargs:
            page = item.funcargs["page"]
            screenshot_dir = Path("tests/ui/screenshots")
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            screenshot_path = screenshot_dir / f"{item.name}_{call.when}.png"
            page.screenshot(path=str(screenshot_path))
            
            # Attach screenshot to report
            if hasattr(rep, 'extra'):
                rep.extra = getattr(rep, 'extra', [])
                rep.extra.append(pytest_html.extras.image(str(screenshot_path)))

