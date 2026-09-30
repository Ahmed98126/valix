"""Create dummy tenants/organizations for testing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.auth import create_tenant
from app.models import Tenant

def create_dummy_tenants():
    """Create several dummy tenants for testing."""
    dummy_tenants = [
        ("Acme Property Management", "acme-properties"),
        ("Global Real Estate Group", "global-real-estate"),
        ("City Properties Ltd", "city-properties"),
        ("Metro Commercial Holdings", "metro-commercial"),
        ("Premier Property Services", "premier-properties"),
    ]
    
    with get_session() as session:
        created_count = 0
        existing_count = 0
        
        for name, slug in dummy_tenants:
            # Check if tenant already exists
            existing = session.query(Tenant).filter(
                Tenant.slug == slug
            ).first()
            
            if existing:
                print(f"  ⚠ {name} already exists (slug: {slug})")
                existing_count += 1
            else:
                try:
                    tenant = create_tenant(session, name, slug)
                    print(f"  ✓ Created: {name} (slug: {slug})")
                    created_count += 1
                except Exception as e:
                    print(f"  ✗ Error creating {name}: {e}")
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"  Created: {created_count} new tenant(s)")
        print(f"  Already existed: {existing_count} tenant(s)")
        
        # Show all tenants
        all_tenants = session.query(Tenant).filter(
            Tenant.is_active == True
        ).order_by(Tenant.name).all()
        
        print(f"\n  Total active tenants: {len(all_tenants)}")
        print(f"\n  Available tenants:")
        for tenant in all_tenants:
            print(f"    - {tenant.name} ({tenant.slug})")

if __name__ == "__main__":
    print("="*60)
    print("CREATING DUMMY TENANTS")
    print("="*60)
    print()
    create_dummy_tenants()
    print("\n" + "="*60)
    print("DONE!")
    print("="*60)
    print("\nYou can now see these organizations in the login dropdown!")


