"""Apply enhanced PDF extraction tables migration.

This script applies the SQL migration for enhanced PDF extraction tables:
1. supplier_extraction_patterns
2. manual_review_queue

It follows the established pattern for database migrations in the project.

Usage:
    python scripts/migrate_enhanced_extraction_tables.py [--force]
"""

import sys
import os
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, engine, SessionLocal
from sqlalchemy import text, inspect


def check_if_migrated():
    """Check if migration has already been applied."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return 'supplier_extraction_patterns' in tables and 'manual_review_queue' in tables


def apply_migration(force=False):
    """Apply the enhanced PDF extraction tables migration."""
    print("="*70)
    print("ENHANCED PDF EXTRACTION TABLES MIGRATION")
    print("="*70)
    
    # Check if already migrated
    if check_if_migrated() and not force:
        print("\nWARNING: Migration appears to already be applied!")
        print("   Use --force to re-run migration (WARNING: May cause issues)")
        return False
    
    # Load migration SQL
    migration_path = Path(__file__).parent.parent / "migrations" / "add_enhanced_pdf_extraction_tables.sql"
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, "r") as f:
        sql = f.read()
    
    # Apply migration
    try:
        # Create a session using SessionLocal directly
        session = SessionLocal()
        
        try:
            print("\n[1/3] Applying migration SQL...")
            
            # Execute statements one by one
            for statement in sql.split(';'):
                if statement.strip():
                    session.execute(text(statement))
            
            session.commit()
            print("SUCCESS: Migration SQL applied successfully")
            
            # Verify tables were created
            print("\n[2/3] Verifying tables...")
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            if 'supplier_extraction_patterns' in tables:
                print("SUCCESS: supplier_extraction_patterns table exists")
            else:
                print("ERROR: supplier_extraction_patterns table not found")
                return False
            
            if 'manual_review_queue' in tables:
                print("SUCCESS: manual_review_queue table exists")
            else:
                print("ERROR: manual_review_queue table not found")
                return False
            
            # Create default extraction patterns
            print("\n[3/3] Creating default extraction patterns...")
            from app.extraction_patterns import create_default_patterns
            count = create_default_patterns(session)
            print(f"SUCCESS: Created {count} default extraction patterns")
            
            print("\n" + "="*70)
            print("MIGRATION SUCCESSFUL")
            print("="*70)
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"\nERROR: Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            session.close()
    except Exception as e:
        print(f"\nFailed to create session: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply enhanced PDF extraction tables migration")
    parser.add_argument("--force", action="store_true", help="Force migration even if already applied")
    args = parser.parse_args()
    
    success = apply_migration(force=args.force)
    sys.exit(0 if success else 1)