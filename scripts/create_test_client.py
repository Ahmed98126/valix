"""Create a fresh test client with user account."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import Tenant, User
from app.auth import create_user, create_tenant

def create_test_client():
    """Create a test tenant and user for end-to-end testing."""
    print("👤 Creating test client...")
    
    with get_session() as session:
        try:
            # Create tenant
            tenant = create_tenant(
                session,
                name="Test Property Management",
                slug="test-properties"
            )
            print(f"✅ Created tenant: {tenant.name} (ID: {tenant.id}, Slug: {tenant.slug})")
            
            # Create user
            user = create_user(
                session,
                email="test@testproperties.com",
                password="test123",
                full_name="Test User",
                tenant_id=tenant.id
            )
            print(f"✅ Created user: {user.email} (ID: {user.id})")
            
            session.commit()
            
            print("\n" + "="*60)
            print("🎉 Test Client Created Successfully!")
            print("="*60)
            print(f"\n📧 Login Credentials:")
            print(f"   Email: {user.email}")
            print(f"   Password: test123")
            print(f"\n🏢 Tenant Info:")
            print(f"   Name: {tenant.name}")
            print(f"   Slug: {tenant.slug}")
            print(f"   ID: {tenant.id}")
            print("\n✅ You can now:")
            print("   1. Start the server: uvicorn main:app --reload")
            print("   2. Go to http://localhost:8000/login")
            print("   3. Login with the credentials above")
            print("   4. Upload test data files")
            
            return tenant, user
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error creating test client: {e}")
            raise

if __name__ == "__main__":
    create_test_client()

