"""Initialize default extraction patterns for common suppliers.

This script creates default extraction patterns for common suppliers
like British Gas, E.ON, and Opus Energy.

Usage:
    python scripts/init_extraction_patterns.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.extraction_patterns import create_default_patterns


def init_patterns():
    """Initialize default extraction patterns."""
    # Initialize database
    init_db()
    
    with get_session() as session:
        # Create default patterns
        count = create_default_patterns(session)
        print(f"✅ Created {count} default extraction patterns")


if __name__ == "__main__":
    init_patterns()