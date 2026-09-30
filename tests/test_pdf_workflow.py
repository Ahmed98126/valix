"""Tests for PDF workflow with account mappings."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.db import get_session
from app.models import InvoiceUnitMapping, Unit, Tenant, User, Invoice, InvoiceValidation
from app.pdf_workflow import process_pdf_invoice, process_pdf_batch, UnmappedInvoiceQueue


@pytest.fixture
def db_session():
    """Create a test database session."""
    session = next(get_session())
    yield session
    session.close()


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        is_active=True
    )
    db_session.add(tenant)
    db_session.commit()
    
    yield tenant
    
    # Clean up
    db_session.delete(tenant)
    db_session.commit()


@pytest.fixture
def test_user(db_session, test_tenant):
    """Create a test user."""
    user = User(
        email="test@example.com",
        tenant_id=test_tenant.id,
        is_active=True,
        is_super_admin=False
    )
    user.set_password("password123")
    db_session.add(user)
    db_session.commit()
    
    yield user
    
    # Clean up
    db_session.delete(user)
    db_session.commit()


@pytest.fixture
def test_units(db_session, test_tenant):
    """Create test units."""
    units = [
        Unit(
            tenant_id=test_tenant.id,
            unit_id="UNIT-001",
            building_name="Building A",
            address_line_1="123 Main St",
            city="London",
            postcode="SW1A 1AA"
        ),
        Unit(
            tenant_id=test_tenant.id,
            unit_id="UNIT-002",
            building_name="Building B",
            address_line_1="456 High St",
            city="London",
            postcode="SW1A 2BB"
        )
    ]
    
    for unit in units:
        db_session.add(unit)
    
    db_session.commit()
    
    yield units
    
    # Clean up
    for unit in units:
        db_session.delete(unit)
    
    db_session.commit()


@pytest.fixture
def test_mappings(db_session, test_tenant, test_units, test_user):
    """Create test mappings."""
    mappings = [
        InvoiceUnitMapping(
            tenant_id=test_tenant.id,
            supplier_account_number="ACC-001",
            unit_id="UNIT-001",
            supplier_name="British Gas",
            is_active=True,
            created_by_user_id=test_user.id
        ),
        InvoiceUnitMapping(
            tenant_id=test_tenant.id,
            supplier_account_number="ACC-002",
            unit_id="UNIT-002",
            supplier_name="E.ON",
            is_active=True,
            created_by_user_id=test_user.id
        )
    ]
    
    for mapping in mappings:
        db_session.add(mapping)
    
    db_session.commit()
    
    yield mappings
    
    # Clean up
    for mapping in mappings:
        db_session.delete(mapping)
    
    db_session.commit()


@pytest.fixture
def mock_pdf_processor():
    """Mock PDFProcessor for testing."""
    with patch("app.pdf_workflow.PDFProcessor") as mock:
        # Mock extract_invoice method
        processor_instance = mock.return_value
        processor_instance.extract_invoice.return_value = {
            "fields": {
                "InvoiceId": {"value": "INV-001"},
                "VendorName": {"value": "British Gas"},
                "CustomerNumber": {"value": "ACC-001"},
                "InvoiceDate": {"value": "2023-01-01"},
                "DueDate": {"value": "2023-02-01"},
                "SubTotal": {"value": 100.00},
                "TotalTax": {"value": 20.00},
                "InvoiceTotal": {"value": 120.00},
                "BillingAddress": {"value": "123 Main St, London, SW1A 1AA"}
            }
        }
        yield processor_instance


@pytest.fixture
def mock_pdf_normalizer():
    """Mock normalize_pdf_invoice for testing."""
    with patch("app.pdf_workflow.normalize_pdf_invoice") as mock:
        mock.return_value = [{
            "invoice_number": "INV-001",
            "supplier_name": "British Gas",
            "supplier_account_number": "ACC-001",
            "invoice_date": "2023-01-01",
            "billing_period_start": "2023-01-01",
            "billing_period_end": "2023-01-31",
            "gross_amount": 120.00,
            "net_amount": 100.00,
            "vat_amount": 20.00,
            "utility_type": "Electricity",
            "currency": "GBP",
            "address": "123 Main St, London, SW1A 1AA"
        }]
        yield mock


@pytest.fixture
def mock_validate_invoice():
    """Mock validate_invoice for testing."""
    with patch("app.pdf_workflow.validate_invoice") as mock:
        mock.return_value = MagicMock(
            validation_status="Valid",
            determination="OK TO PAY",
            invoice_days=31,
            total_vacancy_overlap_days=0,
            is_duplicate="No"
        )
        yield mock


def test_process_pdf_invoice_success(
    db_session, test_tenant, test_user, test_mappings,
    mock_pdf_processor, mock_pdf_normalizer, mock_validate_invoice
):
    """Test process_pdf_invoice with successful mapping."""
    # Create a temporary PDF file
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    try:
        # Process PDF
        result = process_pdf_invoice(
            pdf_path=pdf_path,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            session=db_session
        )
        
        # Check result
        assert result["status"] == "success"
        assert "invoice_id" in result
        assert result["unit_id"] == "UNIT-001"
        assert result["validation_status"] == "Valid"
        assert result["determination"] == "OK TO PAY"
        
        # Check if invoice was created
        invoice = db_session.query(Invoice).filter(
            Invoice.invoice_number == "INV-001",
            Invoice.tenant_id == test_tenant.id
        ).first()
        
        assert invoice is not None
        assert invoice.supplier_name == "British Gas"
        assert invoice.supplier_account_number == "ACC-001"
        assert invoice.unit_id == "UNIT-001"
        
        # Check if validation was created
        validation = db_session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        assert validation is not None
        assert validation.validation_status == "Valid"
        assert validation.determination == "OK TO PAY"
        
        # Clean up
        db_session.delete(validation)
        db_session.delete(invoice)
        db_session.commit()
    
    finally:
        # Clean up temporary file
        os.unlink(pdf_path)


def test_process_pdf_invoice_unmapped(
    db_session, test_tenant, test_user,
    mock_pdf_processor, mock_pdf_normalizer
):
    """Test process_pdf_invoice with unmapped account."""
    # Override mock_pdf_normalizer to return unmapped account
    mock_pdf_normalizer.return_value = [{
        "invoice_number": "INV-002",
        "supplier_name": "Water Company",
        "supplier_account_number": "UNMAPPED",
        "invoice_date": "2023-01-01",
        "billing_period_start": "2023-01-01",
        "billing_period_end": "2023-01-31",
        "gross_amount": 50.00,
        "net_amount": 40.00,
        "vat_amount": 10.00,
        "utility_type": "Water",
        "currency": "GBP",
        "address": "456 High St, London, SW1A 2BB"
    }]
    
    # Create a temporary PDF file
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    try:
        # Process PDF
        result = process_pdf_invoice(
            pdf_path=pdf_path,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            session=db_session
        )
        
        # Check result
        assert result["status"] == "unmapped"
        assert result["account_number"] == "UNMAPPED"
        assert result["supplier_name"] == "Water Company"
        assert "extracted_data" in result
    
    finally:
        # Clean up temporary file
        os.unlink(pdf_path)


def test_process_pdf_invoice_error(
    db_session, test_tenant, test_user,
    mock_pdf_processor
):
    """Test process_pdf_invoice with extraction error."""
    # Override mock_pdf_processor to return empty data
    mock_pdf_processor.extract_invoice.return_value = {}
    
    # Create a temporary PDF file
    fd, pdf_path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    
    try:
        # Process PDF
        result = process_pdf_invoice(
            pdf_path=pdf_path,
            tenant_id=test_tenant.id,
            user_id=test_user.id,
            session=db_session
        )
        
        # Check result
        assert result["status"] == "error"
        assert "message" in result
    
    finally:
        # Clean up temporary file
        os.unlink(pdf_path)


def test_unmapped_invoice_queue():
    """Test UnmappedInvoiceQueue."""
    # Add to queue
    UnmappedInvoiceQueue.add_to_queue(
        pdf_path="test.pdf",
        account_number="TEST-001",
        supplier_name="Test Supplier",
        extracted_data={
            "invoice_number": "INV-001",
            "invoice_date": "2023-01-01",
            "address": "Test Address",
            "gross_amount": 100.00
        },
        tenant_id=1
    )
    
    # Check if item was added to queue
    from app.routes.unmapped_invoices import UNMAPPED_QUEUE
    
    assert len(UNMAPPED_QUEUE) > 0
    assert UNMAPPED_QUEUE[-1]["pdf_path"] == "test.pdf"
    assert UNMAPPED_QUEUE[-1]["account_number"] == "TEST-001"
    assert UNMAPPED_QUEUE[-1]["supplier_name"] == "Test Supplier"
    assert UNMAPPED_QUEUE[-1]["tenant_id"] == 1