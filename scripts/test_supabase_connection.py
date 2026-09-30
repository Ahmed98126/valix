"""Test Supabase database connection."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import engine, get_session
from app.models import Tenant, User

def test_connection():
    """Test database connection and basic queries."""
    try:
        print("🔌 Testing Supabase connection...")
        
        # Test connection
        with engine.connect() as conn:
            print("✅ Database connection successful!")
        
        # Test session
        with get_session() as session:
            # Try to query tenants
            tenants = session.query(Tenant).all()
            print(f"✅ Session works! Found {len(tenants)} tenant(s)")
            
            # Try to query users
            users = session.query(User).all()
            print(f"✅ Found {len(users)} user(s)")
            
            # Show database info
            from sqlalchemy import text
            result = session.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL version: {version[:50]}...")
            
        print("\n🎉 All tests passed! Supabase connection is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check your .env file has DATABASE_URL set correctly")
        print("2. Verify your password is correct (no [YOUR-PASSWORD] placeholder)")
        print("3. Make sure psycopg2-binary is installed: pip install psycopg2-binary")
        print("4. Check Supabase project is active and database is provisioned")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

