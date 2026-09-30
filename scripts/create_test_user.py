"""Script to create a test user for login testing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.auth import create_user, create_tenant
from app.models import Tenant

def create_test_user():
    """Create a test user with tenant."""
    with get_session() as session:
        try:
            # Get or create default tenant
            default_tenant = session.query(Tenant).filter(
                Tenant.slug == "default"
            ).first()
            
            if not default_tenant:
                default_tenant = create_tenant(session, "Default Tenant", "default")
                print(f"✓ Created default tenant: {default_tenant.name}")
            
            # Create regular user
            try:
                user = create_user(
                    session,
                    email="admin@test.com",
                    password="admin123",
                    full_name="Test Admin",
                    tenant_id=default_tenant.id
                )
                print(f"✓ Test user created successfully!")
                print(f"  Email: {user.email}")
                print(f"  Password: admin123")
                print(f"  Tenant: {default_tenant.name}")
                print(f"\nYou can now login at http://localhost:8000/login")
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"⚠ User already exists. Try logging in with:")
                    print(f"  Email: admin@test.com")
                    print(f"  Password: admin123")
                else:
                    raise
            
            # Create super admin user
            try:
                super_admin = create_user(
                    session,
                    email="superadmin@test.com",
                    password="admin123",
                    full_name="Super Admin",
                    is_super_admin=True
                )
                print(f"\n✓ Super admin user created!")
                print(f"  Email: {super_admin.email}")
                print(f"  Password: admin123")
                print(f"  Can access all tenants")
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"\n⚠ Super admin already exists")
                else:
                    raise
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_test_user()



