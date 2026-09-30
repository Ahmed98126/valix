"""Migrate database for enhanced PDF extraction.

This script applies the migration for enhanced PDF extraction:
1. Creates supplier_extraction_patterns table
2. Creates manual_review_queue table
3. Initializes default extraction patterns

Usage:
    python scripts/migrate_enhanced_extraction.py
"""

import sys
import os
from pathlib import Path
import sqlite3

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.extraction_patterns import create_default_patterns
from app.config import DATABASE_URL


def apply_migration():
    """Apply migration for enhanced PDF extraction."""
    print("Applying migration for enhanced PDF extraction...")
    
    # Check if using SQLite or PostgreSQL
    if DATABASE_URL.startswith("sqlite"):
        # SQLite migration
        apply_sqlite_migration()
    else:
        # PostgreSQL migration
        apply_postgres_migration()
    
    # Initialize default patterns
    with get_session() as session:
        count = create_default_patterns(session)
        print(f"✅ Created {count} default extraction patterns")
    
    print("✅ Migration completed successfully")


def apply_sqlite_migration():
    """Apply migration for SQLite database."""
    print("Applying SQLite migration...")
    
    # Extract database path from URL
    db_path = DATABASE_URL.replace("sqlite:///", "")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create supplier_extraction_patterns table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS supplier_extraction_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER,
        supplier_name TEXT NOT NULL,
        field_name TEXT NOT NULL,
        pattern_type TEXT NOT NULL,
        pattern_value TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1 NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        created_by_user_id INTEGER,
        notes TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by_user_id) REFERENCES users (id) ON DELETE SET NULL
    )
    """)
    
    # Create indexes for supplier_extraction_patterns
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_tenant_id ON supplier_extraction_patterns(tenant_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_supplier_name ON supplier_extraction_patterns(supplier_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_field_name ON supplier_extraction_patterns(field_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_supplier_extraction_patterns_is_active ON supplier_extraction_patterns(is_active)")
    
    # Create manual_review_queue table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS manual_review_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        pdf_path TEXT NOT NULL,
        original_filename TEXT,
        extracted_data TEXT,
        raw_data TEXT,
        confidence_scores TEXT,
        status TEXT DEFAULT 'Pending' NOT NULL,
        reviewed_by_user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        reviewed_at TIMESTAMP,
        notes TEXT,
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
        FOREIGN KEY (reviewed_by_user_id) REFERENCES users (id) ON DELETE SET NULL
    )
    """)
    
    # Create indexes for manual_review_queue
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_review_queue_tenant_id ON manual_review_queue(tenant_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_review_queue_status ON manual_review_queue(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_review_queue_created_at ON manual_review_queue(created_at)")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("✅ SQLite migration applied successfully")


def apply_postgres_migration():
    """Apply migration for PostgreSQL database."""
    print("Applying PostgreSQL migration...")
    
    # Read migration SQL file
    migration_path = Path(__file__).parent.parent / "migrations" / "add_enhanced_pdf_extraction_tables.sql"
    
    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return
    
    with open(migration_path, "r") as f:
        sql = f.read()
    
    # Execute migration SQL
    # For PostgreSQL, we'll use the psycopg2 library
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        # Extract connection parameters from URL
        # Format: postgresql://username:password@host:port/dbname
        url = DATABASE_URL.replace("postgresql://", "")
        auth, rest = url.split("@")
        username, password = auth.split(":")
        host_port, dbname = rest.split("/")
        
        if ":" in host_port:
            host, port = host_port.split(":")
        else:
            host = host_port
            port = "5432"
        
        # Connect to database
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            dbname=dbname
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Execute migration SQL
        with conn.cursor() as cursor:
            cursor.execute(sql)
        
        conn.close()
        
        print("✅ PostgreSQL migration applied successfully")
    
    except ImportError:
        print("❌ psycopg2 not installed. Please install it to run PostgreSQL migrations.")
        print("   pip install psycopg2-binary")
    except Exception as e:
        print(f"❌ Error applying PostgreSQL migration: {str(e)}")


if __name__ == "__main__":
    apply_migration()