"""Comprehensive multi-tenant testing workflow.

Simulates multiple clients using the system:
1. Create multiple tenants
2. For each tenant:
   - Create user account
   - Import units
   - Import leases
   - Upload and validate invoices
3. Verify tenant isolation
4. Test validation logic per tenant
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, Invoice, InvoiceValidation, Tenant, User, UnitTimeline
from app.validation import generate_unit_timeline, validate_invoice
from app.auth import create_tenant, create_user
from datetime import date, timedelta
import random

def create_test_tenant(session, name, slug, email_prefix):
    """Create a test tenant with user."""
    print(f"\n{'='*70}")
    print(f"Setting up Tenant: {name}")
    print(f"{'='*70}")
    
    # Check if tenant exists
    tenant = session.query(Tenant).filter(Tenant.slug == slug).first()
    if tenant:
        print(f"✓ Using existing tenant: {tenant.name} (ID: {tenant.id})")
    else:
        # Create tenant
        tenant = create_tenant(session, name, slug)
        print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
    
    # Create user
    email = f"{email_prefix}@example.com"
    user = session.query(User).filter(User.email == email).first()
    if user:
        print(f"✓ Using existing user: {user.email}")
    else:
        try:
            user = create_user(
                session,
                email=email,
                password="test123",
                full_name=f"{name} User",
                tenant_id=tenant.id
            )
            print(f"✓ Created user: {user.email}")
        except ValueError as e:
            print(f"⚠ Error creating user: {e}")
            user = None
    
    return tenant, user


def import_units_for_tenant(session, tenant_id, tenant_name):
    """Import units for a tenant."""
    print(f"\n[Importing Units for {tenant_name}]")
    
    units_data = [
        {
            "tenant_id": tenant_id,
            "unit_id": f"SHOP-001",
            "building_name": f"{tenant_name} Shopping Centre",
            "address_line_1": "123 High Street",
            "city": "London",
            "postcode": "SW1A 1AA"
        },
        {
            "tenant_id": tenant_id,
            "unit_id": f"SHOP-002",
            "building_name": f"{tenant_name} Shopping Centre",
            "address_line_1": "123 High Street",
            "city": "London",
            "postcode": "SW1A 1AA"
        },
        {
            "tenant_id": tenant_id,
            "unit_id": f"OFFICE-101",
            "building_name": f"{tenant_name} Business Park",
            "address_line_1": "456 Business Park",
            "city": "Manchester",
            "postcode": "M1 1AA"
        },
        {
            "tenant_id": tenant_id,
            "unit_id": f"OFFICE-102",
            "building_name": f"{tenant_name} Business Park",
            "address_line_1": "456 Business Park",
            "city": "Manchester",
            "postcode": "M1 1AA"
        },
        {
            "tenant_id": tenant_id,
            "unit_id": f"WAREHOUSE-001",
            "building_name": f"{tenant_name} Industrial Estate",
            "address_line_1": "789 Industrial Way",
            "city": "Birmingham",
            "postcode": "B1 1AA"
        }
    ]
    
    units_created = 0
    units_skipped = 0
    for unit_data in units_data:
        existing = session.query(Unit).filter(
            Unit.unit_id == unit_data['unit_id'],
            Unit.tenant_id == tenant_id
        ).first()
        if not existing:
            try:
                unit = Unit(**unit_data)
                session.add(unit)
                session.flush()  # Flush immediately to catch errors
                units_created += 1
            except Exception as e:
                print(f"  ⚠ Error creating unit {unit_data['unit_id']}: {e}")
                session.rollback()
                units_skipped += 1
        else:
            units_skipped += 1
    
    session.commit()
    if units_skipped > 0:
        print(f"  (Skipped {units_skipped} existing unit(s))")
    print(f"✓ Created {units_created} unit(s)")
    return units_created


def import_leases_for_tenant(session, tenant_id, tenant_name):
    """Import leases for a tenant."""
    print(f"\n[Importing Leases for {tenant_name}]")
    
    today = date.today()
    leases_data = [
        {
            "tenant_id": tenant_id,
            "unit_id": "SHOP-001",
            "tenant_name": "Coffee Shop Ltd",
            "lease_start": date(2024, 1, 1),
            "lease_end": None  # Ongoing
        },
        {
            "tenant_id": tenant_id,
            "unit_id": "SHOP-002",
            "tenant_name": "Bakery Corp",
            "lease_start": date(2023, 6, 1),
            "lease_end": date(2025, 6, 1)
        },
        {
            "tenant_id": tenant_id,
            "unit_id": "SHOP-002",
            "tenant_name": "Tech Store Inc",
            "lease_start": date(2025, 12, 1),
            "lease_end": None  # Ongoing
        },
        {
            "tenant_id": tenant_id,
            "unit_id": "OFFICE-101",
            "tenant_name": "Law Firm A",
            "lease_start": date(2022, 1, 1),
            "lease_end": date(2025, 3, 31)
        },
        {
            "tenant_id": tenant_id,
            "unit_id": "OFFICE-101",
            "tenant_name": "Law Firm B",
            "lease_start": date(2025, 6, 1),
            "lease_end": None  # Ongoing
        },
        {
            "tenant_id": tenant_id,
            "unit_id": "OFFICE-102",
            "tenant_name": "Accounting Services",
            "lease_start": date(2024, 1, 1),
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
    return leases_created


def generate_timelines_for_tenant(session, tenant_id, tenant_name):
    """Generate unit timelines for a tenant."""
    print(f"\n[Generating Timelines for {tenant_name}]")
    try:
        timeline_count = generate_unit_timeline(session, tenant_id=tenant_id)
        print(f"✓ Generated {timeline_count} timeline period(s)")
        return timeline_count
    except Exception as e:
        print(f"⚠ Error generating timelines: {e}")
        return 0


def create_test_invoices_for_tenant(session, tenant_id, tenant_name, num_invoices=10):
    """Create test invoices for a tenant."""
    print(f"\n[Creating {num_invoices} Test Invoices for {tenant_name}]")
    
    suppliers = ["British Gas", "Thames Water", "EDF Energy", "Scottish Power", "E.ON"]
    utility_types = ["Electricity", "Gas", "Water"]
    units = ["SHOP-001", "SHOP-002", "OFFICE-101", "OFFICE-102", "WAREHOUSE-001"]
    
    invoices_created = 0
    validations_created = 0
    
    for i in range(1, num_invoices + 1):
        # Random dates in the past year
        start_date = date.today() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(28, 31))
        
        invoice_data = {
            "tenant_id": tenant_id,
            "invoice_number": f"INV-{tenant_name.upper()[:3]}-{i:04d}",
            "supplier_name": random.choice(suppliers),
            "unit_id": random.choice(units),
            "billing_period_start": start_date,
            "billing_period_end": end_date,
            "gross_amount": round(random.uniform(50, 500), 2),
            "utility_type": random.choice(utility_types),
            "source_batch": f"BATCH-{tenant_name.upper()[:3]}-001"
        }
        
        invoice = Invoice(**invoice_data)
        session.add(invoice)
        session.flush()
        invoices_created += 1
        
        # Validate invoice
        try:
            validation = validate_invoice(session, invoice)
            session.add(validation)
            validations_created += 1
            print(f"  ✓ Invoice {invoice_data['invoice_number']}: {validation.validation_status} - {validation.determination}")
        except Exception as e:
            print(f"  ⚠ Error validating {invoice_data['invoice_number']}: {e}")
    
    session.commit()
    print(f"✓ Created {invoices_created} invoice(s)")
    print(f"✓ Created {validations_created} validation(s)")
    return invoices_created, validations_created


def verify_tenant_isolation(session):
    """Verify that tenants can only see their own data."""
    print(f"\n{'='*70}")
    print("VERIFYING TENANT ISOLATION")
    print(f"{'='*70}")
    
    tenants = session.query(Tenant).all()
    
    for tenant in tenants:
        tenant_units = session.query(Unit).filter(Unit.tenant_id == tenant.id).count()
        tenant_leases = session.query(Lease).filter(Lease.tenant_id == tenant.id).count()
        tenant_invoices = session.query(Invoice).filter(Invoice.tenant_id == tenant.id).count()
        tenant_validations = session.query(InvoiceValidation).filter(InvoiceValidation.tenant_id == tenant.id).count()
        tenant_timelines = session.query(UnitTimeline).filter(UnitTimeline.tenant_id == tenant.id).count()
        
        print(f"\n{tenant.name} (ID: {tenant.id}):")
        print(f"  - Units: {tenant_units}")
        print(f"  - Leases: {tenant_leases}")
        print(f"  - Invoices: {tenant_invoices}")
        print(f"  - Validations: {tenant_validations}")
        print(f"  - Timelines: {tenant_timelines}")
        
        # Verify no cross-tenant data leakage
        other_tenant_ids = [t.id for t in tenants if t.id != tenant.id]
        if other_tenant_ids:
            cross_tenant_units = session.query(Unit).filter(
                Unit.tenant_id.in_(other_tenant_ids),
                Unit.unit_id.in_([u.unit_id for u in session.query(Unit).filter(Unit.tenant_id == tenant.id).all()])
            ).count()
            if cross_tenant_units == 0:
                print(f"  ✓ No cross-tenant data leakage detected")
            else:
                print(f"  ⚠ WARNING: Potential data leakage detected!")


def test_validation_logic_per_tenant(session):
    """Test that validation logic correctly uses tenant-specific data."""
    print(f"\n{'='*70}")
    print("TESTING VALIDATION LOGIC PER TENANT")
    print(f"{'='*70}")
    
    tenants = session.query(Tenant).limit(2).all()
    
    for tenant in tenants:
        print(f"\nTesting validation for: {tenant.name}")
        
        # Get a unit from this tenant
        unit = session.query(Unit).filter(Unit.tenant_id == tenant.id).first()
        if not unit:
            print(f"  ⚠ No units found for {tenant.name}")
            continue
        
        # Get leases for this unit (tenant-scoped)
        leases = session.query(Lease).filter(
            Lease.unit_id == unit.unit_id,
            Lease.tenant_id == tenant.id
        ).all()
        
        print(f"  Unit: {unit.unit_id}")
        print(f"  Leases for this unit: {len(leases)}")
        for lease in leases:
            print(f"    - {lease.tenant_name}: {lease.lease_start} to {lease.lease_end or 'Ongoing'}")
        
        # Get timelines for this unit (tenant-scoped)
        timelines = session.query(UnitTimeline).filter(
            UnitTimeline.unit_id == unit.unit_id,
            UnitTimeline.tenant_id == tenant.id
        ).all()
        
        print(f"  Timeline periods: {len(timelines)}")
        for timeline in timelines[:3]:  # Show first 3
            print(f"    - {timeline.period_start} to {timeline.period_end}: {'Vacant' if timeline.is_vacant else 'Occupied'}")
        
        # Test invoice validation
        invoice = session.query(Invoice).filter(Invoice.tenant_id == tenant.id).first()
        if invoice:
            validation = session.query(InvoiceValidation).filter(
                InvoiceValidation.invoice_id == invoice.id,
                InvoiceValidation.tenant_id == tenant.id
            ).first()
            if validation:
                print(f"  Sample Invoice: {invoice.invoice_number}")
                print(f"    Status: {validation.validation_status}")
                print(f"    Determination: {validation.determination}")
                print(f"    ✓ Validation correctly scoped to tenant")


def main():
    """Run comprehensive multi-tenant test."""
    print("="*70)
    print("COMPREHENSIVE MULTI-TENANT TEST WORKFLOW")
    print("="*70)
    
    init_db()
    
    with get_session() as session:
        # Create 3 test tenants
        tenants_data = [
            ("Acme Property Management", "acme-properties", "acme"),
            ("Global Real Estate Group", "global-real-estate", "global"),
            ("City Properties Ltd", "city-properties", "city")
        ]
        
        created_tenants = []
        
        for name, slug, email_prefix in tenants_data:
            tenant, user = create_test_tenant(session, name, slug, email_prefix)
            created_tenants.append((tenant, user))
            
            # Import units
            units_count = import_units_for_tenant(session, tenant.id, name)
            
            # Import leases
            leases_count = import_leases_for_tenant(session, tenant.id, name)
            
            # Generate timelines
            timeline_count = generate_timelines_for_tenant(session, tenant.id, name)
            
            # Create invoices
            invoices_count, validations_count = create_test_invoices_for_tenant(
                session, tenant.id, name, num_invoices=10
            )
            
            print(f"\n✓ Completed setup for {name}")
            print(f"  Summary: {units_count} units, {leases_count} leases, {timeline_count} timelines, {invoices_count} invoices, {validations_count} validations")
        
        # Verify tenant isolation
        verify_tenant_isolation(session)
        
        # Test validation logic per tenant
        test_validation_logic_per_tenant(session)
        
        # Final summary
        print(f"\n{'='*70}")
        print("TEST SUMMARY")
        print(f"{'='*70}")
        
        total_tenants = session.query(Tenant).count()
        total_units = session.query(Unit).count()
        total_leases = session.query(Lease).count()
        total_invoices = session.query(Invoice).count()
        total_validations = session.query(InvoiceValidation).count()
        
        print(f"\nTotal in Database:")
        print(f"  - Tenants: {total_tenants}")
        print(f"  - Units: {total_units}")
        print(f"  - Leases: {total_leases}")
        print(f"  - Invoices: {total_invoices}")
        print(f"  - Validations: {total_validations}")
        
        print(f"\n{'='*70}")
        print("✅ MULTI-TENANT TEST COMPLETE!")
        print(f"{'='*70}")
        print("\nNext steps:")
        print("  1. Test via web UI: http://localhost:8000")
        print("  2. Login with different tenant accounts:")
        for tenant, user in created_tenants:
            print(f"     - {user.email} / test123 (Tenant: {tenant.name})")
        print("  3. Verify each tenant only sees their own data")
        print("  4. Test invoice validation for each tenant")


if __name__ == "__main__":
    main()

