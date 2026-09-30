"""Script to clean up all test data from the database.

WARNING: This will delete ALL users, tenants, and related data!
Only use this for development/testing purposes.
"""

from app.db import SessionLocal, init_db
from app.models import User, Tenant, Invoice, Unit, Lease, UnitTimeline, InvoiceValidation, InvoiceValidation
from app.password_reset import PasswordResetToken
from app.email_verification import EmailVerificationToken
from app.upload_status import UploadStatus
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_all_data():
    """Delete all test data from the database."""
    session = SessionLocal()
    
    try:
        logger.info("Starting database cleanup...")
        
        # Delete in order to respect foreign key constraints
        
        # 1. Delete email verification tokens (references users)
        deleted_tokens = session.query(EmailVerificationToken).delete()
        logger.info(f"Deleted {deleted_tokens} email verification tokens")
        
        # 2. Delete password reset tokens (references users)
        deleted_reset_tokens = session.query(PasswordResetToken).delete()
        logger.info(f"Deleted {deleted_reset_tokens} password reset tokens")
        
        # 3. Delete upload status (references users/tenants)
        deleted_uploads = session.query(UploadStatus).delete()
        logger.info(f"Deleted {deleted_uploads} upload status records")
        
        # 4. Delete unit timelines (references units/leases)
        deleted_timelines = session.query(UnitTimeline).delete()
        logger.info(f"Deleted {deleted_timelines} unit timelines")
        
        # 5. Delete leases (references units/tenants)
        deleted_leases = session.query(Lease).delete()
        logger.info(f"Deleted {deleted_leases} leases")
        
        # 6. Delete units (references tenants)
        deleted_units = session.query(Unit).delete()
        logger.info(f"Deleted {deleted_units} units")
        
        # 7. Delete invoice_validation records first (references invoices)
        deleted_validations = session.query(InvoiceValidation).delete()
        logger.info(f"Deleted {deleted_validations} invoice validation records")
        
        # 8. Delete invoices (references tenants)
        deleted_invoices = session.query(Invoice).delete()
        logger.info(f"Deleted {deleted_invoices} invoices")
        
        # 9. Delete users (references tenants)
        deleted_users = session.query(User).delete()
        logger.info(f"Deleted {deleted_users} users")
        
        # 10. Delete tenants (no dependencies)
        deleted_tenants = session.query(Tenant).delete()
        logger.info(f"Deleted {deleted_tenants} tenants")
        
        # Commit all deletions
        session.commit()
        
        logger.info("✅ Database cleanup completed successfully!")
        logger.info("All users, tenants, and related data have been deleted.")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error during cleanup: {e}", exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("WARNING: This will delete ALL data from the database!")
    print("=" * 60)
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        cleanup_all_data()
        print("\n✅ Cleanup complete! You can now test the signup feature.")
    else:
        print("Cleanup cancelled.")

