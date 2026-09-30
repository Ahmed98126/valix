"""
Simplify account number handling by standardizing all account numbers to a consistent format.

This script:
1. Updates all existing account numbers in the database to a standardized format (no spaces or dashes)
2. Modifies the account mapping function to always normalize account numbers before storage and comparison
"""

import os
import sys
import logging
from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app.models import InvoiceUnitMapping

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def normalize_account_number(account_number):
    """Normalize account number by removing spaces and dashes."""
    if not account_number:
        return None
    return account_number.replace(" ", "").replace("-", "")

def update_existing_account_numbers():
    """Update all existing account numbers to standardized format."""
    session = SessionLocal()
    try:
        # Get all mappings
        mappings = session.query(InvoiceUnitMapping).all()
        logger.info(f"Found {len(mappings)} account mappings to update.")
        
        updated = 0
        for mapping in mappings:
            try:
                # Get normalized account number
                normalized = normalize_account_number(mapping.supplier_account_number)
                
                # Only update if different
                if normalized != mapping.supplier_account_number:
                    logger.info(f"Updating account number: '{mapping.supplier_account_number}' -> '{normalized}'")
                    mapping.supplier_account_number = normalized
                    updated += 1
            except Exception as e:
                logger.error(f"Error normalizing account number {mapping.supplier_account_number}: {str(e)}")
                continue
            
        session.commit()
        logger.info(f"Updated {updated} account mappings.")
        return True
    except Exception as e:
        logger.error(f"Error updating account numbers: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

def main():
    """Main function."""
    logger.info("Starting account number simplification...")
    
    # Update existing account numbers
    if not update_existing_account_numbers():
        logger.error("Failed to update account numbers. Exiting.")
        return
    
    logger.info("Account number simplification completed successfully.")
    logger.info("IMPORTANT: The system will now use standardized account numbers (no spaces or dashes).")
    logger.info("Make sure to update the account_mapping.py file to normalize account numbers before storage and comparison.")

if __name__ == "__main__":
    main()