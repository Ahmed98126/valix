"""
Normalize existing account numbers in the database.

This script updates all existing account numbers to use the normalized format
(no spaces or dashes) for consistent matching.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import SessionLocal
from app.models import InvoiceUnitMapping
from app.account_mapping import normalize_account_number

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_account_numbers():
    """Update all account numbers to normalized format."""
    session = SessionLocal()
    try:
        # Get all mappings
        mappings = session.query(InvoiceUnitMapping).all()
        logger.info(f"Found {len(mappings)} account mappings to update.")
        
        updated = 0
        for mapping in mappings:
            # Get normalized account number
            normalized = normalize_account_number(mapping.supplier_account_number)
            
            # Only update if different
            if normalized != mapping.supplier_account_number:
                logger.info(f"Updating account number: '{mapping.supplier_account_number}' -> '{normalized}'")
                mapping.supplier_account_number = normalized
                updated += 1
        
        if updated > 0:
            session.commit()
            logger.info(f"Updated {updated} account mappings.")
        else:
            logger.info("No account mappings needed updating.")
            
        return True
    except Exception as e:
        logger.error(f"Error updating account numbers: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    logger.info("Starting account number normalization...")
    if update_account_numbers():
        logger.info("Account number normalization completed successfully.")
    else:
        logger.error("Account number normalization failed.")
        sys.exit(1)