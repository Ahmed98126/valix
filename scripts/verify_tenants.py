"""Verify tenants and users after migration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import Tenant, User

def verify_setup():
    """Verify tenant and user setup."""
    with get_session() as session:
        tenants = session.query(Tenant).all()
        users = session.query(User).all()
        
        print("="*60)
        print("TENANTS")
        print("="*60)
        if tenants:
            for t in tenants:
                print(f"  ID: {t.id} | Name: {t.name} | Slug: {t.slug} | Active: {t.is_active}")
        else:
            print("  No tenants found!")
        
        print(f"\n{'='*60}")
        print("USERS")
        print(f"{'='*60}")
        if users:
            for u in users:
                tenant_info = f"Tenant ID: {u.tenant_id}" if u.tenant_id else "No tenant (Super Admin)"
                print(f"  Email: {u.email}")
                print(f"    Full Name: {u.full_name}")
                print(f"    {tenant_info}")
                print(f"    Super Admin: {u.is_super_admin}")
                print(f"    Active: {u.is_active}")
                print()
        else:
            print("  No users found!")
        
        print(f"{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"  Tenants: {len(tenants)}")
        print(f"  Users: {len(users)}")
        print(f"  Regular Users: {sum(1 for u in users if not u.is_super_admin)}")
        print(f"  Super Admins: {sum(1 for u in users if u.is_super_admin)}")

if __name__ == "__main__":
    verify_setup()


