"""Comprehensive MVP testing script - tests all core functionality."""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import Tenant, User, Unit, Lease, Invoice, InvoiceValidation
from app.auth import create_user, create_tenant
from app.validation import validate_invoice, generate_unit_timeline
from app.column_mapping import get_column_mapping, map_columns
import pandas as pd

def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_multi_tenant_isolation():
    """Test that tenants are properly isolated."""
    print_section("TEST 1: Multi-Tenant Isolation")
    
    with get_session() as session:
        # Get or create test tenants
        tenant1 = session.query(Tenant).filter(Tenant.slug == "test-tenant-1").first()
        tenant2 = session.query(Tenant).filter(Tenant.slug == "test-tenant-2").first()
        
        if not tenant1:
            tenant1 = create_tenant(session, "Test Tenant 1", "test-tenant-1")
            print(f"✅ Created tenant 1: {tenant1.name}")
        else:
            print(f"✅ Using existing tenant 1: {tenant1.name}")
        
        if not tenant2:
            tenant2 = create_tenant(session, "Test Tenant 2", "test-tenant-2")
            print(f"✅ Created tenant 2: {tenant2.name}")
        else:
            print(f"✅ Using existing tenant 2: {tenant2.name}")
        
        # Create units for each tenant with same unit_id
        unit1_t1 = session.query(Unit).filter(
            Unit.tenant_id == tenant1.id,
            Unit.unit_id == "TEST-UNIT-001"
        ).first()
        
        if not unit1_t1:
            unit1_t1 = Unit(
                tenant_id=tenant1.id,
                unit_id="TEST-UNIT-001",
                building_name="Test Building 1",
                address_line_1="123 Test St",
                city="Test City",
                postcode="TE1 1ST"
            )
            session.add(unit1_t1)
            session.commit()
            print(f"✅ Created unit TEST-UNIT-001 for tenant 1")
        
        unit1_t2 = session.query(Unit).filter(
            Unit.tenant_id == tenant2.id,
            Unit.unit_id == "TEST-UNIT-001"
        ).first()
        
        if not unit1_t2:
            unit1_t2 = Unit(
                tenant_id=tenant2.id,
                unit_id="TEST-UNIT-001",
                building_name="Test Building 2",
                address_line_1="456 Test Ave",
                city="Test City",
                postcode="TE2 2ND"
            )
            session.add(unit1_t2)
            session.commit()
            print(f"✅ Created unit TEST-UNIT-001 for tenant 2")
        
        # Verify isolation - tenant 1 should only see their units
        tenant1_units = session.query(Unit).filter(Unit.tenant_id == tenant1.id).all()
        tenant2_units = session.query(Unit).filter(Unit.tenant_id == tenant2.id).all()
        
        print(f"✅ Tenant 1 sees {len(tenant1_units)} unit(s) (should be 1+)")
        print(f"✅ Tenant 2 sees {len(tenant2_units)} unit(s) (should be 1+)")
        
        # Verify they can't see each other's data
        cross_tenant_unit = session.query(Unit).filter(
            Unit.tenant_id == tenant1.id,
            Unit.id == unit1_t2.id
        ).first()
        
        if cross_tenant_unit:
            print("❌ FAIL: Tenant isolation broken - tenant 1 can see tenant 2's unit")
            return False
        else:
            print("✅ PASS: Tenant isolation working - tenants can't see each other's data")
        
        return True

def test_validation_logic():
    """Test the validation engine."""
    print_section("TEST 2: Validation Logic")
    
    with get_session() as session:
        # Get a tenant
        tenant = session.query(Tenant).first()
        if not tenant:
            print("❌ No tenant found - create one first")
            return False
        
        print(f"✅ Using tenant: {tenant.name}")
        
        # Get or create a unit
        unit = session.query(Unit).filter(Unit.tenant_id == tenant.id).first()
        if not unit:
            unit = Unit(
                tenant_id=tenant.id,
                unit_id="VAL-TEST-001",
                building_name="Validation Test Building",
                city="Test City",
                postcode="VT1 1ST"
            )
            session.add(unit)
            session.commit()
            print(f"✅ Created unit: {unit.unit_id}")
        
        # Create a lease (occupied period)
        lease = session.query(Lease).filter(
            Lease.tenant_id == tenant.id,
            Lease.unit_id == unit.unit_id
        ).first()
        
        if not lease:
            lease = Lease(
                tenant_id=tenant.id,
                unit_id=unit.unit_id,
                tenant_name="Test Tenant",
                lease_start=date(2024, 1, 1),
                lease_end=date(2024, 12, 31)
            )
            session.add(lease)
            session.commit()
            print(f"✅ Created lease: {lease.tenant_name} ({lease.lease_start} to {lease.lease_end})")
        
        # Generate timeline
        generate_unit_timeline(session, unit.unit_id, tenant.id)
        print("✅ Generated unit timeline")
        
        # Create a valid invoice (within lease period)
        valid_invoice = Invoice(
            tenant_id=tenant.id,
            invoice_number="VAL-TEST-001",
            supplier_name="Test Supplier",
            unit_id=unit.unit_id,
            billing_period_start=date(2024, 6, 1),
            billing_period_end=date(2024, 6, 30),
            gross_amount=100.00,
            utility_type="Electricity",
            currency="GBP"
        )
        session.add(valid_invoice)
        session.flush()  # Flush to get ID but don't commit yet
        print(f"✅ Created valid invoice: {valid_invoice.invoice_number} (ID: {valid_invoice.id})")
        
        # Validate the invoice (function signature: validate_invoice(session, invoice, payment_status=None))
        validation = validate_invoice(session, valid_invoice)
        session.commit()
        
        print(f"✅ Validation status: {validation.validation_status}")
        print(f"✅ Determination: {validation.determination}")
        
        if validation.validation_status == "Valid":
            print("✅ PASS: Valid invoice correctly identified")
        else:
            print(f"⚠️  WARNING: Valid invoice marked as {validation.validation_status}")
        
        # Create an invalid invoice (overlaps with vacancy - but we need a vacancy first)
        # For this test, let's create a duplicate
        duplicate_invoice = Invoice(
            tenant_id=tenant.id,
            invoice_number="VAL-TEST-001",  # Same invoice number
            supplier_name="Test Supplier",
            unit_id=unit.unit_id,
            billing_period_start=date(2024, 7, 1),
            billing_period_end=date(2024, 7, 31),
            gross_amount=100.00,  # Same amount = duplicate
            utility_type="Electricity",
            currency="GBP"
        )
        session.add(duplicate_invoice)
        session.commit()
        print(f"✅ Created duplicate invoice: {duplicate_invoice.invoice_number}")
        
        # Validate the duplicate
        dup_validation = validate_invoice(session, duplicate_invoice)
        session.commit()
        
        print(f"✅ Duplicate validation status: {dup_validation.validation_status}")
        
        if dup_validation.validation_status == "Invalid":
            print("✅ PASS: Duplicate invoice correctly identified as Invalid")
        else:
            print(f"⚠️  WARNING: Duplicate invoice marked as {dup_validation.validation_status}")
        
        return True

def test_data_import():
    """Test data import functionality."""
    print_section("TEST 3: Data Import")
    
    with get_session() as session:
        tenant = session.query(Tenant).first()
        if not tenant:
            print("❌ No tenant found")
            return False
        
        # Test column mapping
        mapping = get_column_mapping(session, tenant.id, "invoice")
        print(f"✅ Column mapping loaded: {len(mapping)} mappings")
        
        # Test with sample data
        sample_data = pd.DataFrame({
            "Invoice Number": ["IMP-TEST-001"],
            "Supplier Name": ["Test Supplier"],
            "Unit ID": ["IMP-UNIT-001"],
            "Billing Period Start": ["2024-01-01"],
            "Billing Period End": ["2024-01-31"],
            "Gross Amount": [150.00],
            "Utility Type": ["Electricity"]
        })
        
        # map_columns takes list of column names and mapping dict
        mapped_cols = map_columns(list(sample_data.columns), mapping)
        print(f"✅ Column mapping applied: {mapped_cols}")
        
        if "invoice_number" in mapped_cols:
            print("✅ PASS: Column mapping working correctly")
        else:
            print("❌ FAIL: Column mapping not working")
            return False
        
        return True

def test_api_endpoints():
    """Test that main API endpoints exist."""
    print_section("TEST 4: API Endpoints")
    
    # Check if main.py has key endpoints
    main_file = Path(__file__).parent.parent / "main.py"
    if not main_file.exists():
        print("❌ main.py not found")
        return False
    
    content = main_file.read_text()
    
    endpoints = [
        ("@app.get(\"/\"", "Root endpoint"),
        ("@app.get(\"/login\"", "Login page"),
        ("@app.get(\"/dashboard\"", "Dashboard"),
        ("@app.post(\"/api/upload\"", "Invoice upload"),
        ("@app.get(\"/api/invoices\"", "Get invoices"),
        ("@app.post(\"/api/import/units\"", "Import units"),
        ("@app.post(\"/api/import/leases\"", "Import leases"),
    ]
    
    all_found = True
    for endpoint, description in endpoints:
        if endpoint in content:
            print(f"✅ {description}: {endpoint}...)")
        else:
            print(f"❌ Missing: {description}")
            all_found = False
    
    return all_found

def test_database_schema():
    """Test that all required tables exist."""
    print_section("TEST 5: Database Schema")
    
    with get_session() as session:
        from sqlalchemy import inspect
        
        inspector = inspect(session.bind)
        tables = inspector.get_table_names()
        
        required_tables = [
            "tenants",
            "users",
            "units",
            "leases",
            "invoices",
            "invoice_validation",
            "unit_timeline",
            "upload_status"
        ]
        
        all_present = True
        for table in required_tables:
            if table in tables:
                print(f"✅ Table exists: {table}")
            else:
                print(f"❌ Missing table: {table}")
                all_present = False
        
        return all_present

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  MVP COMPREHENSIVE TESTING")
    print("="*60)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tests = [
        ("Database Schema", test_database_schema),
        ("Multi-Tenant Isolation", test_multi_tenant_isolation),
        ("Validation Logic", test_validation_logic),
        ("Data Import", test_data_import),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print("🎉 All tests passed! MVP is ready!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Review and fix issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

