"""Migrate existing database to multi-tenant architecture.

This script:
1. Creates tenants table
2. Adds tenant_id columns to all tables
3. Creates default tenant
4. Migrates existing data to default tenant

Usage:
    python scripts/migrate_to_multi_tenant.py [--force]
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db, engine
from app.models import (
    Base, Tenant, User, Unit, Lease, Invoice, 
    InvoiceValidation, UnitTimeline
)
from app.upload_status import UploadStatus
from sqlalchemy import text, inspect


def check_if_migrated():
    """Check if database already has tenants table."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return 'tenants' in tables


def migrate_database(force=False):
    """Migrate database to multi-tenant architecture."""
    print("="*70)
    print("MULTI-TENANT DATABASE MIGRATION")
    print("="*70)
    
    # Check if already migrated
    if check_if_migrated() and not force:
        print("\n⚠ Database appears to already be migrated!")
        print("   Use --force to re-run migration (WARNING: May cause issues)")
        return
    
    with get_session() as session:
        try:
            # Step 1: Create tenants table
            print("\n[1/5] Creating tenants table...")
            Tenant.__table__.create(engine, checkfirst=True)
            print("✓ Tenants table created")
            
            # Step 2: Create default tenant
            print("\n[2/5] Creating default tenant...")
            default_tenant = session.query(Tenant).filter(
                Tenant.slug == "default"
            ).first()
            
            if not default_tenant:
                default_tenant = Tenant(
                    name="Default Tenant",
                    slug="default",
                    is_active=True
                )
                session.add(default_tenant)
                session.commit()
                session.refresh(default_tenant)
                print(f"✓ Default tenant created (ID: {default_tenant.id})")
            else:
                print(f"✓ Default tenant already exists (ID: {default_tenant.id})")
            
            # Step 3: Add tenant_id columns to existing tables
            print("\n[3/5] Adding tenant_id columns to existing tables...")
            
            tables_to_migrate = [
                ('users', 'tenant_id', 'INTEGER'),
                ('users', 'is_super_admin', 'INTEGER DEFAULT 0'),  # SQLite uses INTEGER for boolean
                ('units', 'tenant_id', 'INTEGER'),
                ('leases', 'tenant_id', 'INTEGER'),
                ('invoices', 'tenant_id', 'INTEGER'),
                ('invoice_validation', 'tenant_id', 'INTEGER'),
                ('unit_timeline', 'tenant_id', 'INTEGER'),
            ]
            
            inspector = inspect(engine)
            for table_name, column_name, column_type in tables_to_migrate:
                if table_name in inspector.get_table_names():
                    # Check if column already exists
                    columns = [col['name'] for col in inspector.get_columns(table_name)]
                    if column_name not in columns:
                        try:
                            # Add column with default value
                            session.execute(text(
                                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                            ))
                            print(f"  ✓ Added {column_name} to {table_name}")
                        except Exception as e:
                            print(f"  ⚠ Error adding {column_name} to {table_name}: {e}")
                    else:
                        print(f"  ✓ {column_name} already exists in {table_name}")
            
            session.commit()
            
            # Step 4: Update existing data with default tenant_id
            print("\n[4/5] Migrating existing data to default tenant...")
            
            default_tenant_id = default_tenant.id
            
            # Update users (set tenant_id, create super admin if needed)
            users_updated = session.execute(text(
                f"UPDATE users SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {users_updated} user(s)")
            
            # Update units
            units_updated = session.execute(text(
                f"UPDATE units SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {units_updated} unit(s)")
            
            # Update leases
            leases_updated = session.execute(text(
                f"UPDATE leases SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {leases_updated} lease(s)")
            
            # Update invoices
            invoices_updated = session.execute(text(
                f"UPDATE invoices SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {invoices_updated} invoice(s)")
            
            # Update invoice_validations
            validations_updated = session.execute(text(
                f"UPDATE invoice_validation SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {validations_updated} validation(s)")
            
            # Update unit_timeline
            timeline_updated = session.execute(text(
                f"UPDATE unit_timeline SET tenant_id = {default_tenant_id} WHERE tenant_id IS NULL"
            )).rowcount
            print(f"  ✓ Updated {timeline_updated} timeline period(s)")
            
            session.commit()
            
            # Step 5: Add foreign key constraints (if using PostgreSQL)
            print("\n[5/5] Verifying migration...")
            
            # Check tenant counts
            tenant_count = session.query(Tenant).count()
            user_count = session.query(User).count()
            unit_count = session.query(Unit).count()
            
            print(f"\n✓ Migration complete!")
            print(f"  Tenants: {tenant_count}")
            print(f"  Users: {user_count}")
            print(f"  Units: {unit_count}")
            
            print("\n" + "="*70)
            print("MIGRATION SUCCESSFUL")
            print("="*70)
            print("\nNext steps:")
            print("  1. Update all queries to filter by tenant_id")
            print("  2. Update authentication to handle tenants")
            print("  3. Add tenant selection UI")
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate database to multi-tenant")
    parser.add_argument("--force", action="store_true", help="Force migration even if already migrated")
    args = parser.parse_args()
    
    try:
        migrate_database(force=args.force)
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

