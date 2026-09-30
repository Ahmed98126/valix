"""Check recent upload status and errors."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.upload_status import UploadStatus

with get_session() as session:
    status = session.query(UploadStatus).order_by(UploadStatus.id.desc()).first()
    
    if status:
        print(f"Batch ID: {status.batch_id}")
        print(f"Status: {status.status}")
        print(f"File: {status.file_name}")
        print(f"Tenant ID: {status.tenant_id}")
        print(f"Invoices Created: {status.invoices_created}")
        print(f"Total Rows: {status.total_rows}")
        print(f"\nErrors:")
        if status.errors:
            print(status.errors[:1000])
        else:
            print("None")
    else:
        print("No upload status found")

