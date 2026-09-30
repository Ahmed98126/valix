"""Playwright configuration for E2E tests."""

from playwright.sync_api import Playwright, sync_playwright
import pytest


@pytest.fixture(scope="session")
def playwright():
    """Playwright instance."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Browser launch arguments."""
    return {
        "headless": True,
        "slow_mo": 0,
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments."""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }

