"""Tests for account mapping functionality."""

import os
import pytest
import tempfile
from pathlib import Path
import pandas as pd
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import InvoiceUnitMapping, Unit, Tenant, User
from app.account_mapping import (
    get_unit_for_account,
    create_account_mapping,
    delete_account_mapping,
    import_account_mappings,
    export_account_mappings,
    create_mapping_template
)


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


def test_get_unit_for_account(db_session, test_tenant, test_mappings):
    """Test get_unit_for_account function."""
    # Test exact match
    unit_id = get_unit_for_account(
        account_number="ACC-001",
        tenant_id=test_tenant.id,
        session=db_session
    )
    assert unit_id == "UNIT-001"
    
    # Test with supplier name
    unit_id = get_unit_for_account(
        account_number="UNKNOWN",
        supplier_name="British Gas",
        tenant_id=test_tenant.id,
        session=db_session
    )
    assert unit_id == "UNIT-001"
    
    # Test with cleaned account number
    unit_id = get_unit_for_account(
        account_number="ACC 001",  # With space
        tenant_id=test_tenant.id,
        session=db_session
    )
    assert unit_id == "UNIT-001"
    
    # Test not found
    unit_id = get_unit_for_account(
        account_number="UNKNOWN",
        tenant_id=test_tenant.id,
        session=db_session
    )
    assert unit_id is None


def test_create_account_mapping(db_session, test_tenant, test_units, test_user):
    """Test create_account_mapping function."""
    # Create new mapping
    mapping = create_account_mapping(
        supplier_account_number="ACC-003",
        unit_id="UNIT-001",
        tenant_id=test_tenant.id,
        supplier_name="Water Company",
        notes="Test mapping",
        created_by_user_id=test_user.id,
        session=db_session
    )
    
    assert mapping is not None
    assert mapping.supplier_account_number == "ACC-003"
    assert mapping.unit_id == "UNIT-001"
    assert mapping.supplier_name == "Water Company"
    
    # Update existing mapping
    mapping = create_account_mapping(
        supplier_account_number="ACC-003",
        unit_id="UNIT-002",  # Changed unit
        tenant_id=test_tenant.id,
        supplier_name="Water Company",
        session=db_session
    )
    
    assert mapping.unit_id == "UNIT-002"
    
    # Clean up
    db_session.delete(mapping)
    db_session.commit()


def test_delete_account_mapping(db_session, test_tenant, test_mappings):
    """Test delete_account_mapping function."""
    mapping_id = test_mappings[0].id
    
    # Delete mapping
    result = delete_account_mapping(
        mapping_id=mapping_id,
        tenant_id=test_tenant.id,
        session=db_session
    )
    
    assert result is True
    
    # Check if mapping is inactive
    mapping = db_session.query(InvoiceUnitMapping).filter(
        InvoiceUnitMapping.id == mapping_id
    ).first()
    
    assert mapping is not None
    assert mapping.is_active is False


def test_import_export_mappings(db_session, test_tenant, test_units, test_user):
    """Test import_account_mappings and export_account_mappings functions."""
    # Create temporary file for import
    fd, import_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    
    # Create DataFrame with test data
    df = pd.DataFrame({
        "Supplier Name": ["Test Supplier 1", "Test Supplier 2"],
        "Account Number": ["TEST-001", "TEST-002"],
        "Unit ID": ["UNIT-001", "UNIT-002"],
        "Notes": ["Test note 1", "Test note 2"]
    })
    
    # Save to Excel
    df.to_excel(import_path, index=False)
    
    # Import mappings
    result = import_account_mappings(
        file_path=import_path,
        tenant_id=test_tenant.id,
        created_by_user_id=test_user.id,
        session=db_session
    )
    
    assert result["success"] is True
    assert result["created"] == 2
    
    # Create temporary file for export
    fd, export_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    
    # Export mappings
    result = export_account_mappings(
        tenant_id=test_tenant.id,
        output_path=export_path,
        session=db_session
    )
    
    assert result["success"] is True
    assert result["count"] >= 2
    
    # Read exported file
    exported_df = pd.read_excel(export_path)
    
    assert "Account Number" in exported_df.columns
    assert "Unit ID" in exported_df.columns
    
    # Clean up
    os.unlink(import_path)
    os.unlink(export_path)
    
    # Clean up mappings
    mappings = db_session.query(InvoiceUnitMapping).filter(
        InvoiceUnitMapping.supplier_account_number.in_(["TEST-001", "TEST-002"])
    ).all()
    
    for mapping in mappings:
        db_session.delete(mapping)
    
    db_session.commit()


def test_create_mapping_template():
    """Test create_mapping_template function."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    
    # Create template
    result = create_mapping_template(path)
    
    assert result["success"] is True
    
    # Read template
    df = pd.read_excel(path)
    
    assert "Supplier Name" in df.columns
    assert "Account Number" in df.columns
    assert "Unit ID" in df.columns
    assert "Notes" in df.columns
    
    # Clean up
    os.unlink(path)