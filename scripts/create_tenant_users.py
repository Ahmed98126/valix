"""Create test users for each tenant/organization."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.auth import create_user
from app.models import Tenant

def create_tenant_users():
    """Create test users for each tenant."""
    with get_session() as session:
        # Get all active tenants
        tenants = session.query(Tenant).filter(
            Tenant.is_active == True
        ).order_by(Tenant.name).all()
        
        if not tenants:
            print("⚠ No tenants found! Run create_dummy_tenants.py first.")
            return
        
        print("="*60)
        print("CREATING TEST USERS FOR EACH TENANT")
        print("="*60)
        print()
        
        created_count = 0
        existing_count = 0
        
        for tenant in tenants:
            # Create user email based on tenant slug
            email = f"admin@{tenant.slug}.com"
            password = "admin123"  # Simple password for testing
            full_name = f"{tenant.name} Admin"
            
            try:
                user = create_user(
                    session,
                    email=email,
                    password=password,
                    full_name=full_name,
                    tenant_id=tenant.id,
                    is_super_admin=False
                )
                print(f"  ✓ Created: {email} for {tenant.name}")
                print(f"    Password: {password}")
                created_count += 1
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"  ⚠ {email} already exists for {tenant.name}")
                    existing_count += 1
                else:
                    print(f"  ✗ Error creating {email}: {e}")
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"  Created: {created_count} new user(s)")
        print(f"  Already existed: {existing_count} user(s)")
        
        # Show all users with their tenants
        print(f"\n{'='*60}")
        print("TEST USER CREDENTIALS")
        print(f"{'='*60}")
        print()
        print("Regular Users (Tenant-scoped):")
        print("-" * 60)
        
        for tenant in tenants:
            email = f"admin@{tenant.slug}.com"
            print(f"  Organization: {tenant.name}")
            print(f"    Email: {email}")
            print(f"    Password: admin123")
            print()
        
        # Also show super admin if it exists
        from app.models import User
        super_admin = session.query(User).filter(
            User.is_super_admin == True
        ).first()
        
        if super_admin:
            print("Super Admin (All tenants):")
            print("-" * 60)
            print(f"  Email: {super_admin.email}")
            print(f"  Password: admin123")
            print(f"  Can access all tenants")
            print()
        
        print(f"{'='*60}")
        print("QUICK REFERENCE")
        print(f"{'='*60}")
        print()
        print("Copy-paste ready credentials:")
        print()
        for tenant in tenants:
            email = f"admin@{tenant.slug}.com"
            print(f"  {email} / admin123  →  {tenant.name}")

if __name__ == "__main__":
    create_tenant_users()
    print("\n✅ Done! You can now login with any of these accounts.")


