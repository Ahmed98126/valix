"""Quick test setup - creates one tenant with test data for manual testing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Unit, Lease, Invoice, InvoiceValidation, Tenant, User
from app.validation import generate_unit_timeline, validate_invoice
from app.auth import create_tenant, create_user
from datetime import date, timedelta
import random

def main():
    """Create a test tenant with complete data for manual testing."""
    print("="*70)
    print("QUICK TEST SETUP - Creating Test Tenant")
    print("="*70)
    
    init_db()
    
    with get_session() as session:
        # Create tenant
        tenant_name = "Test Client"
        tenant_slug = "test-client"
        email = "test@client.com"
        
        tenant = session.query(Tenant).filter(Tenant.slug == tenant_slug).first()
        if not tenant:
            tenant = create_tenant(session, tenant_name, tenant_slug)
            print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
        else:
            print(f"✓ Using existing tenant: {tenant.name} (ID: {tenant.id})")
        
        # Create user
        user = session.query(User).filter(User.email == email).first()
        if not user:
            user = create_user(session, email, "test123", "Test User", tenant.id)
            print(f"✓ Created user: {user.email}")
        else:
            print(f"✓ Using existing user: {user.email}")
        
        # Import 5 units
        print("\n[Importing Units]")
        units_data = [
            {"unit_id": "SHOP-001", "building_name": "High Street Mall", "address_line_1": "123 High St", "city": "London", "postcode": "SW1A 1AA"},
            {"unit_id": "SHOP-002", "building_name": "High Street Mall", "address_line_1": "123 High St", "city": "London", "postcode": "SW1A 1AA"},
            {"unit_id": "OFFICE-101", "building_name": "Business Tower", "address_line_1": "456 Business Ave", "city": "Manchester", "postcode": "M1 1AA"},
            {"unit_id": "OFFICE-102", "building_name": "Business Tower", "address_line_1": "456 Business Ave", "city": "Manchester", "postcode": "M1 1AA"},
            {"unit_id": "WAREHOUSE-001", "building_name": "Industrial Park", "address_line_1": "789 Industrial Way", "city": "Birmingham", "postcode": "B1 1AA"},
        ]
        
        units_created = 0
        units_existing = 0
        for unit_data in units_data:
            existing = session.query(Unit).filter(
                Unit.unit_id == unit_data['unit_id'],
                Unit.tenant_id == tenant.id
            ).first()
            if not existing:
                # Check if unit_id exists for any tenant (old constraint issue)
                any_existing = session.query(Unit).filter(
                    Unit.unit_id == unit_data['unit_id']
                ).first()
                if any_existing:
                    # Use a unique unit_id for this tenant
                    unit_data['unit_id'] = f"{unit_data['unit_id']}-T{tenant.id}"
                    print(f"  ⚠ Adjusted unit_id to {unit_data['unit_id']} (to avoid constraint)")
                
                try:
                    unit = Unit(tenant_id=tenant.id, **unit_data)
                    session.add(unit)
                    session.flush()
                    units_created += 1
                except Exception as e:
                    print(f"  ⚠ Error creating unit {unit_data['unit_id']}: {e}")
                    session.rollback()
                    units_existing += 1
            else:
                units_existing += 1
        
        session.commit()
        if units_existing > 0:
            print(f"  (Skipped {units_existing} existing unit(s))")
        print(f"✓ Created {units_created} unit(s)")
        
        # Import 6 leases
        print("\n[Importing Leases]")
        leases_data = [
            {"unit_id": "SHOP-001", "tenant_name": "Coffee Shop Ltd", "lease_start": date(2024, 1, 1), "lease_end": None},
            {"unit_id": "SHOP-002", "tenant_name": "Bakery Corp", "lease_start": date(2023, 6, 1), "lease_end": date(2025, 6, 1)},
            {"unit_id": "SHOP-002", "tenant_name": "Tech Store Inc", "lease_start": date(2025, 12, 1), "lease_end": None},
            {"unit_id": "OFFICE-101", "tenant_name": "Law Firm A", "lease_start": date(2022, 1, 1), "lease_end": date(2025, 3, 31)},
            {"unit_id": "OFFICE-101", "tenant_name": "Law Firm B", "lease_start": date(2025, 6, 1), "lease_end": None},
            {"unit_id": "OFFICE-102", "tenant_name": "Accounting Services", "lease_start": date(2024, 1, 1), "lease_end": None},
        ]
        
        leases_created = 0
        for lease_data in leases_data:
            lease = Lease(tenant_id=tenant.id, **lease_data)
            session.add(lease)
            leases_created += 1
        
        session.commit()
        print(f"✓ Created {leases_created} lease(s)")
        
        # Generate timelines
        print("\n[Generating Timelines]")
        try:
            timeline_count = generate_unit_timeline(session, tenant_id=tenant.id)
            print(f"✓ Generated {timeline_count} timeline period(s)")
        except Exception as e:
            print(f"⚠ Error: {e}")
        
        # Create 10 invoices
        print("\n[Creating 10 Test Invoices]")
        suppliers = ["British Gas", "Thames Water", "EDF Energy", "Scottish Power"]
        utility_types = ["Electricity", "Gas", "Water"]
        units = ["SHOP-001", "SHOP-002", "OFFICE-101", "OFFICE-102", "WAREHOUSE-001"]
        
        invoices_created = 0
        validations_created = 0
        
        for i in range(1, 11):
            start_date = date.today() - timedelta(days=random.randint(30, 365))
            end_date = start_date + timedelta(days=random.randint(28, 31))
            
            invoice = Invoice(
                tenant_id=tenant.id,
                invoice_number=f"INV-{i:04d}",
                supplier_name=random.choice(suppliers),
                unit_id=random.choice(units),
                billing_period_start=start_date,
                billing_period_end=end_date,
                gross_amount=round(random.uniform(50, 500), 2),
                utility_type=random.choice(utility_types),
                source_batch="TEST-BATCH-001"
            )
            session.add(invoice)
            session.flush()
            invoices_created += 1
            
            try:
                validation = validate_invoice(session, invoice)
                session.add(validation)
                validations_created += 1
            except Exception as e:
                print(f"  ⚠ Error validating INV-{i:04d}: {e}")
        
        session.commit()
        print(f"✓ Created {invoices_created} invoice(s)")
        print(f"✓ Created {validations_created} validation(s)")
        
        print(f"\n{'='*70}")
        print("✅ TEST SETUP COMPLETE!")
        print(f"{'='*70}")
        print(f"\nLogin Credentials:")
        print(f"  Email: {email}")
        print(f"  Password: test123")
        print(f"\nData Created:")
        print(f"  - Units: {units_created}")
        print(f"  - Leases: {leases_created}")
        print(f"  - Invoices: {invoices_created}")
        print(f"  - Validations: {validations_created}")
        print(f"\nNext Steps:")
        print(f"  1. Start server: python -m uvicorn main:app --reload")
        print(f"  2. Go to: http://localhost:8000")
        print(f"  3. Login with: {email} / test123")
        print(f"  4. Test the complete workflow!")

if __name__ == "__main__":
    main()

