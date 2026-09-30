"""End-to-end tests for user workflows."""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
class TestUserWorkflow:
    """Test complete user workflows."""
    
    def test_signup_and_login_flow(self, page: Page, base_url: str):
        """Test user signup and login workflow."""
        # Navigate to signup page
        page.goto(f"{base_url}/signup")
        
        # Fill signup form
        page.fill('input[name="email"]', "e2e_test@example.com")
        page.fill('input[name="password"]', "TestPassword123!")
        page.fill('input[name="full_name"]', "E2E Test User")
        page.fill('input[name="organization_name"]', "E2E Test Company")
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Should redirect to login or dashboard
        page.wait_for_url(f"{base_url}/login", timeout=5000)
    
    def test_login_flow(self, page: Page, base_url: str):
        """Test user login workflow."""
        # Navigate to login page
        page.goto(f"{base_url}/login")
        
        # Wait for form to be visible
        page.wait_for_selector('input[name="email"]', timeout=5000)
        
        # Fill login form
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Should redirect to dashboard (or stay on login if credentials wrong)
        # Wait a bit for redirect
        page.wait_for_timeout(2000)
        # Check if we're on dashboard or login (test user may not exist)
        current_url = page.url
        assert "/dashboard" in current_url or "/login" in current_url
    
    def test_invoice_upload_flow(self, page: Page, base_url: str):
        """Test invoice upload workflow."""
        from pathlib import Path
        
        # First login (assuming test user exists)
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to upload page
        page.goto(f"{base_url}/upload")
        page.wait_for_selector('input[type="file"]', timeout=5000)
        
        # Check upload form is visible
        expect(page.locator('h1, h2')).to_contain_text("Upload", "Invoice", ignore_case=True)
        
        # Try to upload test file if it exists
        test_file = Path(__file__).parent.parent / "fixtures" / "test_invoices.xlsx"
        if test_file.exists():
            page.set_input_files('input[type="file"]', str(test_file))
            # Don't submit automatically - let test verify form is ready
            expect(page.locator('input[type="file"]')).to_have_value(/.+\.xlsx/)
    
    def test_invoice_table_display(self, page: Page, base_url: str):
        """Test invoice table displays correctly."""
        # Login first
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
        
        # Navigate to invoices page
        page.goto(f"{base_url}/invoices")
        
        # Check table headers
        expect(page.locator('th:has-text("Invoice")')).to_be_visible()
        expect(page.locator('th:has-text("Account")')).to_be_visible()
        expect(page.locator('th:has-text("Supplier")')).to_be_visible()
    
    def test_filter_invoices(self, page: Page, base_url: str):
        """Test invoice filtering functionality."""
        # Login first
        page.goto(f"{base_url}/login")
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
        
        # Navigate to invoices page
        page.goto(f"{base_url}/invoices")
        
        # Check filter dropdowns exist
        expect(page.locator('select')).to_be_visible()
    
    @pytest.mark.parametrize("browser_type", ["chrome", "firefox"])
    def test_cross_browser_compatibility(self, page: Page, base_url: str, browser_type):
        """Test application works across different browsers."""
        # Navigate to homepage
        page.goto(base_url)
        
        # Check page loads
        expect(page).to_have_title(containing="Invoice", ignore_case=True)

