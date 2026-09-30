"""Clean all data from database (keeps tables, removes all records)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import (
    Tenant, User, Unit, Lease, Invoice, 
    InvoiceValidation, UnitTimeline
)
from app.upload_status import UploadStatus

def clean_database():
    """Remove all data from all tables (keeps table structure)."""
    print("🧹 Cleaning database...")
    
    with get_session() as session:
        try:
            # Delete in reverse order of dependencies
            print("  Deleting invoice validations...")
            session.query(InvoiceValidation).delete()
            
            print("  Deleting invoices...")
            session.query(Invoice).delete()
            
            print("  Deleting unit timeline...")
            session.query(UnitTimeline).delete()
            
            print("  Deleting leases...")
            session.query(Lease).delete()
            
            print("  Deleting units...")
            session.query(Unit).delete()
            
            print("  Deleting upload status...")
            session.query(UploadStatus).delete()
            
            print("  Deleting users...")
            session.query(User).delete()
            
            print("  Deleting tenants...")
            session.query(Tenant).delete()
            
            session.commit()
            print("✅ Database cleaned successfully!")
            print("   All tables are empty and ready for fresh data.")
            
        except Exception as e:
            session.rollback()
            print(f"❌ Error cleaning database: {e}")
            raise

if __name__ == "__main__":
    clean_database()

