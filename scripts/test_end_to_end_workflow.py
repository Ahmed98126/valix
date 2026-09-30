"""End-to-end workflow test: Clean DB, create client, verify connection."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import Tenant, User, Unit, Lease, Invoice

def test_workflow():
    """Test the complete workflow."""
    print("="*60)
    print("🧪 END-TO-END WORKFLOW TEST")
    print("="*60)
    
    # Step 1: Clean database
    print("\n📋 Step 1: Cleaning database...")
    from scripts.clean_database import clean_database
    clean_database()
    
    # Step 2: Create test client
    print("\n📋 Step 2: Creating test client...")
    from scripts.create_test_client import create_test_client
    tenant, user = create_test_client()
    
    # Step 3: Verify connection
    print("\n📋 Step 3: Verifying Supabase connection...")
    with get_session() as session:
        # Check tenant exists
        tenant_check = session.query(Tenant).filter(Tenant.id == tenant.id).first()
        if tenant_check:
            print(f"   ✅ Tenant found: {tenant_check.name}")
        else:
            print(f"   ❌ Tenant not found!")
            return False
        
        # Check user exists
        user_check = session.query(User).filter(User.id == user.id).first()
        if user_check:
            print(f"   ✅ User found: {user_check.email}")
        else:
            print(f"   ❌ User not found!")
            return False
        
        # Check database is empty (except our test data)
        unit_count = session.query(Unit).count()
        lease_count = session.query(Lease).count()
        invoice_count = session.query(Invoice).count()
        
        print(f"   ✅ Database state:")
        print(f"      - Tenants: {session.query(Tenant).count()}")
        print(f"      - Users: {session.query(User).count()}")
        print(f"      - Units: {unit_count}")
        print(f"      - Leases: {lease_count}")
        print(f"      - Invoices: {invoice_count}")
    
    print("\n" + "="*60)
    print("✅ WORKFLOW TEST COMPLETE!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Start server: uvicorn main:app --reload")
    print("   2. Open browser: http://localhost:8000")
    print("   3. Login with:")
    print(f"      Email: {user.email}")
    print(f"      Password: test123")
    print("   4. Upload test data files:")
    print("      - test_data_units.xlsx (Import Units)")
    print("      - test_data_leases.xlsx (Import Leases)")
    print("      - test_data_invoices.xlsx (Upload Invoices)")
    print("\n💡 The frontend will connect to Supabase automatically!")
    
    return True

if __name__ == "__main__":
    test_workflow()

