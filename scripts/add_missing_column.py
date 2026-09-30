"""Quick script to add missing is_super_admin column."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, engine
from sqlalchemy import text, inspect

def add_missing_column():
    """Add is_super_admin column if missing."""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_super_admin' in columns:
        print("✓ Column 'is_super_admin' already exists")
        return
    
    with get_session() as session:
        try:
            session.execute(text('ALTER TABLE users ADD COLUMN is_super_admin INTEGER DEFAULT 0'))
            session.commit()
            print("✓ Added 'is_super_admin' column to users table")
        except Exception as e:
            print(f"✗ Error: {e}")
            session.rollback()

if __name__ == "__main__":
    add_missing_column()


