"""E2E test configuration and fixtures."""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext
from playwright.sync_api import sync_playwright
import os


@pytest.fixture(scope="session")
def playwright():
    """Playwright instance."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright):
    """Launch browser for E2E tests."""
    browser = playwright.chromium.launch(
        headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    )
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def firefox_browser(playwright):
    """Launch Firefox for E2E tests."""
    browser = playwright.firefox.launch(
        headless=os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    )
    yield browser
    browser.close()


@pytest.fixture
def page(browser: Browser) -> Page:
    """Create a new page for each test."""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def firefox_page(firefox_browser: Browser) -> Page:
    """Create a new Firefox page for each test."""
    context = firefox_browser.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture
def base_url():
    """Base URL for the application."""
    return os.getenv("BASE_URL", "http://localhost:8000")

