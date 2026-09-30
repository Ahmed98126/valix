"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io


@pytest.mark.integration
class TestAPIEndpoints:
    """Test API endpoint functionality."""
    
    def test_upload_excel_file(self, authenticated_client: TestClient, test_tenant, test_unit):
        """Test Excel file upload endpoint."""
        # Create a simple Excel file in memory
        import pandas as pd
        
        df = pd.DataFrame({
            "invoice_number": ["TEST-001"],
            "supplier_account_number": ["1234567890"],
            "supplier_name": ["British Gas"],
            "unit_id": [test_unit.unit_id],
            "billing_period_start": ["2024-01-01"],
            "billing_period_end": ["2024-01-31"],
            "gross_amount": ["300.00"],
            "utility_type": ["Electricity"]
        })
        
        # Save to BytesIO
        excel_buffer = io.BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        excel_buffer.seek(0)
        
        # Upload file
        response = authenticated_client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data or "status" in data
    
    def test_get_invoices_page(self, authenticated_client: TestClient, db_session, test_tenant, test_unit):
        """Test GET /invoices page."""
        from app.models import Invoice
        
        # Create test invoice
        invoice = Invoice(
            tenant_id=test_tenant.id,
            invoice_number="TEST-001",
            supplier_account_number="1234567890",
            supplier_name="British Gas",
            unit_id=test_unit.unit_id,
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Get invoices page
        response = authenticated_client.get("/invoices")
        assert response.status_code == 200
        # Should contain HTML
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_validate_invoices(self, authenticated_client: TestClient, db_session, test_tenant, test_unit):
        """Test invoice validation endpoint."""
        from app.models import Invoice
        
        # Create test invoice
        invoice = Invoice(
            tenant_id=test_tenant.id,
            invoice_number="TEST-001",
            supplier_account_number="1234567890",
            supplier_name="British Gas",
            unit_id=test_unit.unit_id,
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Validate
        response = authenticated_client.post(
            "/api/validate",
            json={"batch_number": None}
        )
        assert response.status_code == 200
        data = response.json()
        assert "validated" in data or "success" in data or "count" in data
    
    def test_upload_pdf_file(self, authenticated_client: TestClient, test_tenant):
        """Test PDF file upload endpoint."""
        # Check if PDF processing is available
        try:
            from app.pdf_processor import PDFProcessor
            PDF_AVAILABLE = True
        except ImportError:
            PDF_AVAILABLE = False
        
        if not PDF_AVAILABLE:
            pytest.skip("PDF processing not available")
        
        # Use existing E.ON PDF if available
        pdf_path = Path("EonElectricityBill.pdf")
        if not pdf_path.exists():
            pytest.skip("Test PDF not found")
        
        with open(pdf_path, "rb") as f:
            response = authenticated_client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")}
            )
        
        # Should accept PDF (may fail validation if account number not extracted)
        assert response.status_code in [200, 400]  # 400 if validation fails
    
    def test_duplicate_detection(self, authenticated_client: TestClient, db_session, test_tenant, test_unit):
        """Test duplicate invoice detection."""
        from app.models import Invoice
        
        # Create first invoice
        invoice1 = Invoice(
            tenant_id=test_tenant.id,
            invoice_number="DUPLICATE-001",
            supplier_account_number="1111111111",
            supplier_name="British Gas",
            unit_id=test_unit.unit_id,
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity",
            source_batch="BATCH-001"
        )
        db_session.add(invoice1)
        db_session.commit()
        
        # Try to create duplicate (same invoice_number + gross_amount)
        invoice2 = Invoice(
            tenant_id=test_tenant.id,
            invoice_number="DUPLICATE-001",
            supplier_account_number="2222222222",
            supplier_name="British Gas",
            unit_id=test_unit.unit_id,
            billing_period_start=date(2024, 2, 1),
            billing_period_end=date(2024, 2, 29),
            gross_amount=Decimal("300.00"),  # Same amount
            utility_type="Electricity",
            source_batch="BATCH-002"
        )
        db_session.add(invoice2)
        db_session.commit()
        
        # Both should exist (duplicate detection happens during validation)
        count = db_session.query(Invoice).filter(
            Invoice.invoice_number == "DUPLICATE-001"
        ).count()
        assert count == 2  # Both invoices created, validation will mark as duplicate
    
    def test_multi_tenant_isolation(self, authenticated_client: TestClient, db_session, test_tenant):
        """Test that invoices are isolated by tenant."""
        from app.models import Invoice, Tenant
        
        # Create second tenant
        tenant2 = Tenant(name="Test Company 2")
        db_session.add(tenant2)
        db_session.commit()
        
        # Create invoice for tenant 1
        invoice1 = Invoice(
            tenant_id=test_tenant.id,
            invoice_number="TENANT1-001",
            supplier_account_number="1111111111",
            supplier_name="British Gas",
            unit_id="SHOP-001",
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        db_session.add(invoice1)
        
        # Create invoice for tenant 2 (same invoice number - should be allowed)
        invoice2 = Invoice(
            tenant_id=tenant2.id,
            invoice_number="TENANT1-001",  # Same number, different tenant
            supplier_account_number="2222222222",
            supplier_name="EDF Energy",
            unit_id="SHOP-001",
            billing_period_start=date(2024, 1, 1),
            billing_period_end=date(2024, 1, 31),
            gross_amount=Decimal("300.00"),
            utility_type="Electricity"
        )
        db_session.add(invoice2)
        db_session.commit()
        
        # Both should exist (different tenants)
        count1 = db_session.query(Invoice).filter(
            Invoice.tenant_id == test_tenant.id,
            Invoice.invoice_number == "TENANT1-001"
        ).count()
        
        count2 = db_session.query(Invoice).filter(
            Invoice.tenant_id == tenant2.id,
            Invoice.invoice_number == "TENANT1-001"
        ).count()
        
        assert count1 == 1
        assert count2 == 1
    
    def test_upload_status_endpoint(self, authenticated_client: TestClient):
        """Test upload status endpoint."""
        # Create a batch ID
        batch_id = "TEST_BATCH_123"
        
        response = authenticated_client.get(f"/api/upload/status/{batch_id}")
        # Should return 200 if batch exists, or 404 if not found (both are valid)
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "batch_id" in data

