"""
Fix account number formats in the database.

This script ensures that all account numbers in the database are stored consistently,
which helps with matching extracted account numbers from invoices.

It adds a normalized_account_number column to the invoice_unit_mappings table
and populates it with the normalized version of each account number.
"""

import os
import sys
import logging
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app.models import InvoiceUnitMapping
from app.normalize_account_numbers import normalize_account_number

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def add_normalized_column():
    """Add normalized_account_number column to invoice_unit_mappings table."""
    session = SessionLocal()
    try:
        # Check if column exists
        if session.bind.dialect.name == 'postgresql':
            # PostgreSQL
            result = session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='invoice_unit_mappings' AND column_name='normalized_account_number'"
            ))
            if result.fetchone():
                logger.info("Column normalized_account_number already exists.")
                return True
                
            # Add column
            session.execute(text(
                "ALTER TABLE invoice_unit_mappings ADD COLUMN normalized_account_number VARCHAR(255)"
            ))
        else:
            # SQLite - just try to add the column, will fail if it already exists
            try:
                session.execute(text(
                    "ALTER TABLE invoice_unit_mappings ADD COLUMN normalized_account_number VARCHAR(255)"
                ))
            except SQLAlchemyError as e:
                if "duplicate column name" in str(e).lower():
                    logger.info("Column normalized_account_number already exists.")
                    return True
                else:
                    raise
                
        session.commit()
        logger.info("Column added successfully.")
        return True
    except Exception as e:
        logger.error(f"Error adding column: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def update_normalized_account_numbers():
    """Update normalized_account_number column for all mappings."""
    session = SessionLocal()
    try:
        # Get all mappings
        mappings = session.query(InvoiceUnitMapping).all()
        logger.info(f"Found {len(mappings)} account mappings to update.")
        
        updated = 0
        for mapping in mappings:
            try:
                # Get normalized account number
                _, normalized = normalize_account_number(mapping.supplier_account_number)
                
                # Update mapping
                mapping.normalized_account_number = normalized
                updated += 1
            except Exception as e:
                logger.error(f"Error normalizing account number {mapping.supplier_account_number}: {str(e)}")
                continue
            
        session.commit()
        logger.info(f"Updated {updated} account mappings.")
        return True
    except Exception as e:
        logger.error(f"Error updating normalized account numbers: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Main function."""
    logger.info("Starting account number format fix...")
    
    # Add normalized_account_number column
    if not add_normalized_column():
        logger.error("Failed to add normalized_account_number column. Exiting.")
        return
    
    # Update normalized account numbers
    if not update_normalized_account_numbers():
        logger.error("Failed to update normalized account numbers. Exiting.")
        return
    
    logger.info("Account number format fix completed successfully.")

if __name__ == "__main__":
    main()