"""Test script to verify invoice-to-unit mapping works with current lease data.

This script helps test that PDF invoices correctly map to units and leases.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Invoice, Unit, Lease
from app.unit_matcher import find_matching_units, check_unit_exists
from datetime import date
from decimal import Decimal

def test_mapping():
    """Test invoice-to-unit mapping with sample data."""
    init_db()
    
    session = next(get_session())
    try:
        # Get first tenant
        from app.models import Tenant
        tenant = session.query(Tenant).first()
        if not tenant:
            print("No tenant found. Please create a tenant first.")
            return
        
        tenant_id = tenant.id
        print(f"Testing with tenant: {tenant.name} (ID: {tenant_id})")
        print("=" * 80)
        
        # Show current units
        units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
        print(f"\nCurrent Units in Database ({len(units)}):")
        for unit in units:
            address = ", ".join(filter(None, [
                unit.address_line_1,
                unit.address_line_2,
                unit.city,
                unit.postcode
            ]))
            print(f"  - {unit.unit_id}: {address}")
        
        # Show current leases
        leases = session.query(Lease).filter(Lease.tenant_id == tenant_id).all()
        print(f"\nCurrent Leases in Database ({len(leases)}):")
        for lease in leases:
            end_date = lease.lease_end.strftime('%Y-%m-%d') if lease.lease_end else 'Ongoing'
            print(f"  - {lease.unit_id}: {lease.tenant_name} ({lease.lease_start} to {end_date})")
        
        print("\n" + "=" * 80)
        
        # Test invoice scenarios
        test_invoices = [
            {
                "name": "Invoice with exact unit_id match",
                "invoice_number": "TEST-001",
                "unit_id": units[0].unit_id if units else "SHOP-001",
                "address": units[0].address_line_1 if units else "123 High Street, London"
            },
            {
                "name": "Invoice with address matching unit",
                "invoice_number": "TEST-002",
                "unit_id": "UNKNOWN",
                "address": units[0].address_line_1 + ", " + units[0].city + ", " + units[0].postcode if units else "123 High Street, London, SW1A 1AA"
            },
            {
                "name": "Invoice with no match",
                "invoice_number": "TEST-003",
                "unit_id": "UNKNOWN",
                "address": "999 Unknown Road, Nowhere, XX99 9XX"
            }
        ]
        
        print("\nTesting Invoice-to-Unit Mapping:")
        print("=" * 80)
        
        for test in test_invoices:
            print(f"\n{test['name']}:")
            print(f"  Invoice: {test['invoice_number']}")
            print(f"  Extracted unit_id: {test['unit_id']}")
            print(f"  Address: {test['address']}")
            
            # Create test invoice
            invoice = Invoice(
                tenant_id=tenant_id,
                invoice_number=test['invoice_number'],
                supplier_account_number="123456789",
                supplier_name="Test Supplier",
                unit_id=test['unit_id'],
                address=test['address'],
                billing_period_start=date(2024, 1, 1),
                billing_period_end=date(2024, 1, 31),
                gross_amount=Decimal("100.00"),
                utility_type="Electricity",
                currency="GBP"
            )
            
            # Check if unit_id exists
            if check_unit_exists(session, test['unit_id'], tenant_id):
                print(f"  ✅ Unit '{test['unit_id']}' exists in database - Direct match!")
            else:
                print(f"  ⚠️  Unit '{test['unit_id']}' NOT found - Trying address matching...")
                
                # Try address matching
                matches = find_matching_units(session, invoice, tenant_id, threshold=0.5)
                
                if matches:
                    print(f"  📋 Found {len(matches)} potential match(es):")
                    for i, match in enumerate(matches[:3], 1):  # Show top 3
                        print(f"    {i}. {match['unit_id']} (confidence: {match['similarity_score']:.0%})")
                        print(f"       Address: {match['address']}")
                        if match.get('postcode_match'):
                            print(f"       ✅ Postcode matches!")
                    
                    if matches[0]['similarity_score'] >= 0.7:
                        print(f"  ✅ High confidence match - Would auto-apply: {matches[0]['unit_id']}")
                    else:
                        print(f"  ⚠️  Low confidence - Would require manual mapping")
                else:
                    print(f"  ❌ No matches found - Manual mapping required")
            
            print()
    finally:
        session.close()

if __name__ == "__main__":
    test_mapping()

