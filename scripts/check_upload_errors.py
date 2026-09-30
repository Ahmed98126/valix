"""Check the latest upload errors from the database."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.upload_status import UploadStatus
import json

def check_latest_upload():
    """Display the latest upload status and errors."""
    init_db()
    
    with get_session() as session:
        # Get the most recent upload
        latest = session.query(UploadStatus).order_by(UploadStatus.started_at.desc()).first()
        
        if not latest:
            print("No uploads found in database.")
            return
        
        print(f"\n{'='*60}")
        print(f"Latest Upload Status")
        print(f"{'='*60}")
        print(f"Batch ID: {latest.batch_id}")
        print(f"File: {latest.file_name}")
        print(f"Status: {latest.status}")
        print(f"Started: {latest.started_at}")
        print(f"Completed: {latest.completed_at}")
        print(f"Total Rows: {latest.total_rows}")
        print(f"Invoices Created: {latest.invoices_created}")
        
        if latest.errors:
            print(f"\n{'='*60}")
            print("Errors:")
            print(f"{'='*60}")
            try:
                errors = json.loads(latest.errors)
                if isinstance(errors, list):
                    for i, err in enumerate(errors[:20], 1):  # Show first 20
                        print(f"{i}. {err}")
                    if len(errors) > 20:
                        print(f"\n... and {len(errors) - 20} more errors")
                else:
                    print(errors)
            except:
                print(latest.errors)
        
        print(f"\n{'='*60}\n")

if __name__ == "__main__":
    check_latest_upload()

