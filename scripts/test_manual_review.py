"""Test manual review queue functionality.

This script tests the manual review queue functionality by:
1. Adding a PDF invoice to the queue
2. Listing queue items
3. Processing a queue item

Usage:
    python scripts/test_manual_review.py path/to/invoice.pdf [tenant_id]
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.manual_review import queue_for_manual_review, get_queue_items, process_reviewed_invoice
from app.pdf_processor import PDFProcessor
from app.models import Tenant


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def test_manual_review(pdf_path, tenant_id=None):
    """Test manual review queue functionality."""
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    print_section(f"Testing Manual Review Queue: {pdf_path.name}")
    
    # Initialize database
    init_db()
    
    with get_session() as session:
        # Get tenant ID if not provided
        if tenant_id is None:
            # Get first tenant
            tenant = session.query(Tenant).first()
            if tenant:
                tenant_id = tenant.id
                print(f"Using tenant: {tenant.name} (ID: {tenant.id})")
            else:
                print("❌ No tenants found. Please create a tenant first.")
                return
        
        # Step 1: Extract data from PDF
        print_section("Extracting Data from PDF")
        try:
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(str(pdf_path))
            print("✅ Extracted data from PDF")
        except Exception as e:
            print(f"❌ Error extracting data: {str(e)}")
            return
        
        # Step 2: Add to manual review queue
        print_section("Adding to Manual Review Queue")
        queue_item = queue_for_manual_review(
            pdf_path=str(pdf_path),
            tenant_id=tenant_id,
            raw_data=extracted_data,
            original_filename=pdf_path.name,
            notes="Test manual review",
            session=session
        )
        print(f"✅ Added to queue with ID: {queue_item.id}")
        
        # Step 3: List queue items
        print_section("Queue Items")
        queue_items, total_count = get_queue_items(
            tenant_id=tenant_id,
            session=session
        )
        print(f"Total items in queue: {total_count}")
        
        for i, item in enumerate(queue_items):
            print(f"\nItem {i+1}:")
            print(f"  ID: {item.id}")
            print(f"  PDF: {item.pdf_path}")
            print(f"  Status: {item.status}")
            print(f"  Created: {item.created_at}")
        
        # Step 4: Process a queue item
        print_section("Processing Queue Item")
        
        # Sample invoice data (in a real scenario, this would come from the UI)
        invoice_data = {
            "invoice_number": f"TEST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "supplier_name": "Test Supplier",
            "supplier_account_number": "TEST-ACCOUNT-123",
            "unit_id": "UNIT-001",  # This should be a valid unit_id
            "billing_period_start": datetime.now().date(),
            "billing_period_end": datetime.now().date(),
            "invoice_date": datetime.now().date(),
            "gross_amount": 100.00,
            "net_amount": 83.33,
            "vat_amount": 16.67,
            "utility_type": "Electricity",
            "currency": "GBP",
            "address": "123 Test Street, London, SW1A 1AA"
        }
        
        # Process the queue item
        try:
            invoice, validation = process_reviewed_invoice(
                queue_id=queue_item.id,
                tenant_id=tenant_id,
                invoice_data=invoice_data,
                user_id=1,  # This should be a valid user_id
                session=session
            )
            
            print("✅ Processed queue item")
            print(f"Invoice ID: {invoice.id}")
            print(f"Validation Status: {validation.validation_status}")
            print(f"Determination: {validation.determination}")
        except Exception as e:
            print(f"❌ Error processing queue item: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_manual_review.py path/to/invoice.pdf [tenant_id]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    tenant_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    test_manual_review(pdf_path, tenant_id)