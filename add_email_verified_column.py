"""Migration script to add email_verified column to users table.

Run this once to add the email_verified column to existing databases.
"""

from app.db import SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_email_verified_column():
    """Add email_verified column to users table if it doesn't exist."""
    session = SessionLocal()
    
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='email_verified'
        """)
        
        result = session.execute(check_query).fetchone()
        
        if result:
            logger.info("✅ Column 'email_verified' already exists in users table.")
            return
        
        # Add the column
        logger.info("Adding email_verified column to users table...")
        alter_query = text("""
            ALTER TABLE users 
            ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT FALSE
        """)
        
        session.execute(alter_query)
        session.commit()
        
        logger.info("✅ Successfully added email_verified column to users table!")
        logger.info("All existing users will have email_verified = FALSE by default.")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Error adding column: {e}", exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Adding email_verified column to users table...")
    print("=" * 60)
    add_email_verified_column()
    print("\n✅ Migration complete!")

