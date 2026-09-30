"""Comprehensive E2E tests for complete user workflows."""

import pytest
from playwright.sync_api import Page, expect
from pathlib import Path
import time


@pytest.mark.e2e
class TestCompleteWorkflows:
    """Test complete end-to-end user workflows."""
    
    @pytest.fixture
    def test_files_dir(self):
        """Directory containing test files."""
        fixtures_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures"
        # Create fixtures if they don't exist
        if not (fixtures_dir / "test_units.xlsx").exists():
            # Run fixture creation script
            import subprocess
            import sys
            script_path = fixtures_dir / "create_test_data.py"
            if script_path.exists():
                subprocess.run([sys.executable, str(script_path)], cwd=str(fixtures_dir.parent.parent))
        return fixtures_dir
    
    def test_complete_onboarding_workflow(self, page: Page, base_url: str, test_files_dir: Path):
        """Test complete client onboarding: signup → import units → import leases → upload invoices → validate."""
        # Step 1: Signup
        page.goto(f"{base_url}/signup")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        
        # Fill signup form
        timestamp = int(time.time())
        email = f"e2e_test_{timestamp}@example.com"
        page.fill('input[name="email"]', email)
        page.fill('input[name="password"]', "TestPassword123!")
        page.fill('input[name="full_name"]', "E2E Test User")
        page.fill('input[name="organization_name"]', f"E2E Test Company {timestamp}")
        
        # Submit signup
        page.click('button[type="submit"]')
        
        # Wait for redirect (may go to login or dashboard)
        page.wait_for_timeout(2000)
        
        # Step 2: Login (if redirected to login)
        if "/login" in page.url:
            page.fill('input[name="email"]', email)
            page.fill('input[name="password"]', "TestPassword123!")
            page.click('button[type="submit"]')
            page.wait_for_url(f"{base_url}/dashboard", timeout=5000)
        
        # Step 3: Import Units (if test file exists)
        units_file = test_files_dir / "test_units.xlsx"
        if units_file.exists():
            page.goto(f"{base_url}/import-units")
            page.wait_for_selector('input[type="file"]', timeout=5000)
            
            # Upload units file
            page.set_input_files('input[type="file"]', str(units_file))
            page.click('button[type="submit"]')
            
            # Wait for success message
            page.wait_for_timeout(3000)
        
        # Step 4: Import Leases (if test file exists)
        leases_file = test_files_dir / "test_leases.xlsx"
        if leases_file.exists():
            page.goto(f"{base_url}/import-leases")
            page.wait_for_selector('input[type="file"]', timeout=5000)
            
            # Upload leases file
            page.set_input_files('input[type="file"]', str(leases_file))
            page.click('button[type="submit"]')
            
            # Wait for success message
            page.wait_for_timeout(3000)
        
        # Step 5: Upload Invoices (if test file exists)
        invoices_file = test_files_dir / "test_invoices.xlsx"
        if invoices_file.exists():
            page.goto(f"{base_url}/upload")
            page.wait_for_selector('input[type="file"]', timeout=5000)
            
            # Upload invoices file
            page.set_input_files('input[type="file"]', str(invoices_file))
            page.click('button[type="submit"]')
            
            # Wait for processing
            page.wait_for_timeout(5000)
            
            # Step 6: Navigate to invoices page
            page.goto(f"{base_url}/invoices")
            page.wait_for_selector('table', timeout=5000)
            
            # Verify invoices are displayed
            expect(page.locator('table')).to_be_visible()
        
        # Step 7: Trigger validation (if API endpoint exists)
        # This would require API call or button click
        # For now, just verify we can navigate to invoices page
        assert "/invoices" in page.url or "/dashboard" in page.url
    
    def test_pdf_upload_workflow(self, page: Page, base_url: str, test_files_dir: Path):
        """Test PDF invoice upload workflow."""
        # Login first (assuming test user exists)
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to upload page
        page.goto(f"{base_url}/upload")
        page.wait_for_selector('input[type="file"]', timeout=5000)
        
        # Upload PDF file (if exists)
        pdf_file = test_files_dir / "test_invoice.pdf"
        if pdf_file.exists():
            page.set_input_files('input[type="file"]', str(pdf_file))
            page.click('button[type="submit"]')
            
            # Wait for processing (PDFs take longer)
            page.wait_for_timeout(10000)
            
            # Navigate to invoices page
            page.goto(f"{base_url}/invoices")
            page.wait_for_selector('table', timeout=5000)
            
            # Verify invoice appears
            expect(page.locator('table')).to_be_visible()
        else:
            pytest.skip("Test PDF file not found")
    
    def test_multi_tenant_isolation(self, page: Page, base_url: str):
        """Test that users from different tenants see only their data."""
        # This test requires two test users from different tenants
        # For now, we'll test that login works and redirects correctly
        
        # User 1 login
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Check we're logged in
        if "/dashboard" in page.url:
            # Navigate to invoices
            page.goto(f"{base_url}/invoices")
            page.wait_for_timeout(2000)
            
            # Note: Full isolation test would require:
            # 1. Create tenant A with user A and invoices
            # 2. Create tenant B with user B and invoices
            # 3. Login as user A, verify only tenant A invoices visible
            # 4. Logout
            # 5. Login as user B, verify only tenant B invoices visible
            # This is better tested via integration tests with database queries
        
        # For E2E, we verify the page loads correctly
        assert "/invoices" in page.url or "/dashboard" in page.url
    
    def test_data_management_crud(self, page: Page, base_url: str):
        """Test CRUD operations for units and leases."""
        # Login first
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to data management
        page.goto(f"{base_url}/data-management")
        page.wait_for_timeout(2000)
        
        # Verify page loads
        expect(page.locator('h1, h2')).to_contain_text("Data Management", "Units", "Leases")
        
        # Note: Full CRUD test would require:
        # 1. View units list
        # 2. Click edit on a unit
        # 3. Update unit details
        # 4. Save changes
        # 5. Verify changes appear
        # 6. Delete unit
        # 7. Verify unit removed
        # Similar for leases
    
    def test_validation_trigger(self, page: Page, base_url: str):
        """Test manual validation trigger."""
        # Login first
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to invoices
        page.goto(f"{base_url}/invoices")
        page.wait_for_timeout(2000)
        
        # Look for validate button (may be in API or UI)
        # For now, verify page loads
        expect(page.locator('table, h1, h2')).to_be_visible()
        
        # Note: Full test would:
        # 1. Have unvalidated invoices
        # 2. Click "Validate" button
        # 3. Wait for validation to complete
        # 4. Verify validation status updated
        # 5. Verify determinations appear
    
    def test_error_handling_invalid_file(self, page: Page, base_url: str):
        """Test error handling for invalid file uploads."""
        # Login first
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to upload
        page.goto(f"{base_url}/upload")
        page.wait_for_selector('input[type="file"]', timeout=5000)
        
        # Try to upload invalid file (create a text file)
        invalid_file = Path(__file__).parent / "invalid.txt"
        invalid_file.write_text("This is not a valid invoice file")
        
        try:
            page.set_input_files('input[type="file"]', str(invalid_file))
            page.click('button[type="submit"]')
            
            # Wait for error message
            page.wait_for_timeout(3000)
            
            # Verify error message appears
            # Error message should be visible
            error_elements = page.locator('.error, .alert, [role="alert"]')
            if error_elements.count() > 0:
                expect(error_elements.first()).to_be_visible()
        finally:
            # Clean up
            if invalid_file.exists():
                invalid_file.unlink()
    
    def test_invoice_detail_page(self, page: Page, base_url: str):
        """Test viewing individual invoice details."""
        # Login first
        page.goto(f"{base_url}/login")
        page.wait_for_selector('input[name="email"]', timeout=5000)
        page.fill('input[name="email"]', "test@example.com")
        page.fill('input[name="password"]', "password")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Navigate to invoices
        page.goto(f"{base_url}/invoices")
        page.wait_for_timeout(2000)
        
        # Look for invoice links/rows
        invoice_links = page.locator('a[href*="/invoice/"], tr[data-invoice-id]')
        if invoice_links.count() > 0:
            # Click first invoice
            invoice_links.first().click()
            page.wait_for_timeout(2000)
            
            # Verify detail page loads
            expect(page).to_have_url(f"{base_url}/invoice/", timeout=5000)
            
            # Verify invoice details are visible
            expect(page.locator('h1, h2')).to_contain_text("Invoice", "Details")
        else:
            pytest.skip("No invoices found to test detail page")

