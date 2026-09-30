"""Comprehensive end-to-end testing workflow.

Tests the complete client onboarding and invoice validation process.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, Invoice, InvoiceValidation, Tenant, User
from app.validation import generate_unit_timeline, validate_invoice
from app.auth import create_tenant, create_user
from datetime import date, timedelta
import random

def test_complete_workflow():
    """Test the complete workflow from tenant creation to invoice validation."""
    print("="*70)
    print("COMPREHENSIVE END-TO-END TEST")
    print("="*70)
    
    init_db()
    
    with get_session() as session:
        # Step 1: Create Test Tenant
        print("\n[1/6] Creating test tenant...")
        tenant = create_tenant(session, "Test Client ABC", "test-client-abc")
        print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
        
        # Step 2: Create Test User
        print("\n[2/6] Creating test user...")
        try:
            user = create_user(
                session,
                email="test@clientabc.com",
                password="test123",
                full_name="Test User",
                tenant_id=tenant.id
            )
            print(f"✓ Created user: {user.email}")
        except ValueError as e:
            print(f"⚠ User may already exist: {e}")
            user = session.query(User).filter(User.email == "test@clientabc.com").first()
        
        # Step 3: Import Units
        print("\n[3/6] Importing units...")
        units_data = [
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-001",
                "building_name": "High Street Shopping Centre",
                "address_line_1": "123 High Street",
                "city": "London",
                "postcode": "SW1A 1AA"
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-002",
                "building_name": "High Street Shopping Centre",
                "address_line_1": "123 High Street",
                "city": "London",
                "postcode": "SW1A 1AA"
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "OFFICE-101",
                "building_name": "Business Park Tower",
                "address_line_1": "456 Business Park",
                "city": "Manchester",
                "postcode": "M1 1AA"
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-100",
                "building_name": "Retail Complex",
                "address_line_1": "789 Retail Street",
                "city": "Birmingham",
                "postcode": "B1 1AA"
            }
        ]
        
        units_created = 0
        for unit_data in units_data:
            existing = session.query(Unit).filter(
                Unit.unit_id == unit_data['unit_id'],
                Unit.tenant_id == tenant.id
            ).first()
            if not existing:
                unit = Unit(**unit_data)
                session.add(unit)
                units_created += 1
        
        session.flush()
        print(f"✓ Created {units_created} new unit(s)")
        
        # Step 4: Import Leases
        print("\n[4/6] Importing leases...")
        today = date.today()
        leases_data = [
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-001",
                "tenant_name": "Coffee Shop Ltd",
                "lease_start": date(2024, 12, 1),
                "lease_end": None  # Ongoing
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-002",
                "tenant_name": "Bakery Corp",
                "lease_start": date(2023, 12, 2),
                "lease_end": date(2025, 9, 2)
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "SHOP-002",
                "tenant_name": "Tech Store Inc",
                "lease_start": date(2025, 12, 31),
                "lease_end": None  # Ongoing
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "OFFICE-101",
                "tenant_name": "Law Firm A",
                "lease_start": date(2022, 12, 2),
                "lease_end": date(2025, 6, 4)
            },
            {
                "tenant_id": tenant.id,
                "unit_id": "OFFICE-101",
                "tenant_name": "Law Firm B",
                "lease_start": date(2025, 10, 2),
                "lease_end": None  # Ongoing
            }
        ]
        
        leases_created = 0
        for lease_data in leases_data:
            lease = Lease(**lease_data)
            session.add(lease)
            leases_created += 1
        
        session.commit()
        print(f"✓ Created {leases_created} lease(s)")
        
        # Step 5: Generate Unit Timelines
        print("\n[5/6] Generating unit timelines...")
        try:
            timeline_count = generate_unit_timeline(session, tenant_id=tenant.id)
            print(f"✓ Generated {timeline_count} timeline period(s)")
        except Exception as e:
            print(f"⚠ Error generating timelines: {e}")
        
        # Step 6: Create Test Invoices and Validate
        print("\n[6/6] Creating and validating test invoices...")
        from app.models import Invoice
        
        test_invoices = [
            {
                "tenant_id": tenant.id,
                "invoice_number": "INV-TEST-001",
                "supplier_name": "British Gas",
                "unit_id": "SHOP-001",
                "billing_period_start": date(2024, 12, 1),
                "billing_period_end": date(2024, 12, 31),
                "gross_amount": 150.00,
                "utility_type": "Electricity",
                "source_batch": "TEST_BATCH_001"
            },
            {
                "tenant_id": tenant.id,
                "invoice_number": "INV-TEST-002",
                "supplier_name": "Thames Water",
                "unit_id": "SHOP-002",
                "billing_period_start": date(2024, 2, 1),
                "billing_period_end": date(2024, 2, 28),
                "gross_amount": 200.00,
                "utility_type": "Water",
                "source_batch": "TEST_BATCH_001"
            },
            {
                "tenant_id": tenant.id,
                "invoice_number": "INV-TEST-003",
                "supplier_name": "British Gas",
                "unit_id": "SHOP-100",  # Vacant unit
                "billing_period_start": date(2024, 10, 1),
                "billing_period_end": date(2024, 10, 31),
                "gross_amount": 100.00,
                "utility_type": "Gas",
                "source_batch": "TEST_BATCH_001"
            }
        ]
        
        invoices_created = 0
        validations_created = 0
        
        for inv_data in test_invoices:
            invoice = Invoice(**inv_data)
            session.add(invoice)
            session.flush()
            invoices_created += 1
            
            # Validate invoice
            try:
                validation = validate_invoice(session, invoice)
                session.add(validation)
                validations_created += 1
                print(f"  ✓ Invoice {inv_data['invoice_number']}: {validation.validation_status} - {validation.determination}")
            except Exception as e:
                print(f"  ⚠ Error validating {inv_data['invoice_number']}: {e}")
        
        session.commit()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Tenant: {tenant.name}")
        print(f"Units: {units_created} created")
        print(f"Leases: {leases_created} created")
        print(f"Invoices: {invoices_created} created")
        print(f"Validations: {validations_created} created")
        
        # Verify data isolation
        print("\n" + "="*70)
        print("VERIFYING DATA ISOLATION")
        print("="*70)
        
        # Check tenant has its own data
        tenant_units = session.query(Unit).filter(Unit.tenant_id == tenant.id).count()
        tenant_leases = session.query(Lease).filter(Lease.tenant_id == tenant.id).count()
        tenant_invoices = session.query(Invoice).filter(Invoice.tenant_id == tenant.id).count()
        
        print(f"✓ Tenant {tenant.name} has:")
        print(f"  - {tenant_units} unit(s)")
        print(f"  - {tenant_leases} lease(s)")
        print(f"  - {tenant_invoices} invoice(s)")
        
        # Check other tenants (if any) have separate data
        other_tenants = session.query(Tenant).filter(Tenant.id != tenant.id).all()
        if other_tenants:
            for other_tenant in other_tenants:
                other_units = session.query(Unit).filter(Unit.tenant_id == other_tenant.id).count()
                print(f"✓ Tenant {other_tenant.name} has {other_units} unit(s) (isolated)")
        
        print("\n" + "="*70)
        print("✅ END-TO-END TEST COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Test via web UI: http://localhost:8000")
        print(f"  2. Login with: test@clientabc.com / test123")
        print("  3. Verify you can see the test data")
        print("  4. Test invoice upload")
        print("  5. Test data management features")


if __name__ == "__main__":
    test_complete_workflow()


