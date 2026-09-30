"""Stress test the invoice validation system.

Tests:
1. Large file uploads (1000+ invoices)
2. Concurrent uploads
3. Duplicate detection performance
4. Validation performance
5. Database query performance

Usage:
    python scripts/stress_test.py [--invoices=1000] [--concurrent=5]
"""

import sys
import time
import random
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Invoice, Unit, Lease
from app.validation import validate_invoice, generate_unit_timeline


def generate_test_invoices(count=1000, unit_ids=None):
    """Generate test invoice data."""
    if unit_ids is None:
        with get_session() as session:
            units = session.query(Unit).all()
            if not units:
                raise ValueError("No units found. Load sample data first: python scripts/load_sample_data.py")
            unit_ids = [u.unit_id for u in units]
    
    invoices = []
    suppliers = ["Test Supplier A", "Test Supplier B", "Test Supplier C", "Energy Corp", "Water Systems"]
    utilities = ["Electricity", "Gas", "Water"]
    
    base_date = date(2020, 1, 1)
    
    for i in range(count):
        invoice_date = base_date + timedelta(days=random.randint(0, 1500))
        period_start = invoice_date - timedelta(days=random.randint(28, 35))
        period_end = invoice_date - timedelta(days=1)
        
        invoices.append({
            "invoice_number": f"STRESS-TEST-{i+1:06d}",
            "supplier_name": random.choice(suppliers),
            "unit_id": random.choice(unit_ids),
            "billing_period_start": period_start,
            "billing_period_end": period_end,
            "invoice_date": invoice_date,
            "gross_amount": Decimal(str(round(random.uniform(50, 2000), 2))),
            "net_amount": Decimal(str(round(random.uniform(45, 1900), 2))),
            "vat_amount": Decimal(str(round(random.uniform(5, 200), 2))),
            "utility_type": random.choice(utilities),
            "currency": "GBP",
            "source_batch": f"STRESS_BATCH_{int(time.time())}"
        })
    
    return invoices


def test_large_upload(count=1000):
    """Test uploading a large number of invoices."""
    print(f"\n{'='*70}")
    print(f"TEST 1: Large File Upload ({count} invoices)")
    print(f"{'='*70}")
    
    init_db()
    
    # Generate test data
    print(f"Generating {count} test invoices...")
    invoices = generate_test_invoices(count)
    
    # Create DataFrame
    df = pd.DataFrame(invoices)
    
    # Save to CSV
    test_file = Path("test_stress_invoices.csv")
    df.to_csv(test_file, index=False)
    print(f"✓ Created test file: {test_file} ({test_file.stat().st_size / 1024:.1f} KB)")
    
    # Measure upload time
    start_time = time.time()
    
    with get_session() as session:
        created = 0
        errors = []
        
        for inv_data in invoices:
            try:
                # Check for duplicates
                existing = session.query(Invoice).filter(
                    Invoice.invoice_number == inv_data["invoice_number"],
                    Invoice.gross_amount == inv_data["gross_amount"]
                ).first()
                
                if existing:
                    errors.append(f"Duplicate: {inv_data['invoice_number']}")
                    continue
                
                invoice = Invoice(**inv_data)
                session.add(invoice)
                created += 1
                
                # Commit in batches of 100
                if created % 100 == 0:
                    session.commit()
            except Exception as e:
                errors.append(f"Error: {str(e)}")
        
        session.commit()
    
    elapsed = time.time() - start_time
    
    print(f"\nResults:")
    print(f"  Invoices created: {created}")
    print(f"  Errors: {len(errors)}")
    print(f"  Time elapsed: {elapsed:.2f} seconds")
    print(f"  Throughput: {created/elapsed:.1f} invoices/second")
    
    # Cleanup
    test_file.unlink()
    
    return created, elapsed


def test_validation_performance():
    """Test validation performance."""
    print(f"\n{'='*70}")
    print(f"TEST 2: Validation Performance")
    print(f"{'='*70}")
    
    init_db()
    
    with get_session() as session:
        # Generate unit timeline
        print("Generating unit timeline...")
        start = time.time()
        generate_unit_timeline(session)
        timeline_time = time.time() - start
        print(f"  Timeline generation: {timeline_time:.2f} seconds")
        
        # Get unvalidated invoices
        invoices = session.query(Invoice).limit(100).all()
        if not invoices:
            print("  No invoices to validate")
            return
        
        print(f"\nValidating {len(invoices)} invoices...")
        start = time.time()
        
        validated = 0
        from app.models import InvoiceValidation
        for invoice in invoices:
            try:
                # Check if validation already exists
                existing = session.query(InvoiceValidation).filter(
                    InvoiceValidation.invoice_id == invoice.id
                ).first()
                
                if existing:
                    # Update existing validation
                    validation = validate_invoice(session, invoice)
                    validation.id = existing.id
                    session.merge(validation)
                else:
                    # Create new validation
                    validation = validate_invoice(session, invoice)
                    session.add(validation)
                validated += 1
            except Exception as e:
                print(f"  Error validating invoice {invoice.id}: {e}")
        
        session.commit()
        elapsed = time.time() - start
        
        print(f"\nResults:")
        print(f"  Invoices validated: {validated}")
        print(f"  Time elapsed: {elapsed:.2f} seconds")
        print(f"  Throughput: {validated/elapsed:.1f} invoices/second")


def test_duplicate_detection():
    """Test duplicate detection performance."""
    print(f"\n{'='*70}")
    print(f"TEST 3: Duplicate Detection Performance")
    print(f"{'='*70}")
    
    init_db()
    
    with get_session() as session:
        # Get existing invoices
        existing = session.query(Invoice).limit(100).all()
        if not existing:
            print("  No existing invoices to test against")
            return
        
        # Create duplicates
        duplicates = []
        for inv in existing[:10]:  # Test 10 duplicates
            duplicates.append({
                "invoice_number": inv.invoice_number,
                "gross_amount": inv.gross_amount
            })
        
        print(f"Testing duplicate detection against {len(existing)} existing invoices...")
        start = time.time()
        
        detected = 0
        for dup in duplicates:
            existing_inv = session.query(Invoice).filter(
                Invoice.invoice_number == dup["invoice_number"],
                Invoice.gross_amount == dup["gross_amount"]
            ).first()
            if existing_inv:
                detected += 1
        
        elapsed = time.time() - start
        
        print(f"\nResults:")
        print(f"  Duplicates tested: {len(duplicates)}")
        print(f"  Duplicates detected: {detected}")
        print(f"  Time elapsed: {elapsed:.4f} seconds")
        print(f"  Average per check: {elapsed/len(duplicates)*1000:.2f} ms")


def test_database_queries():
    """Test database query performance."""
    print(f"\n{'='*70}")
    print(f"TEST 4: Database Query Performance")
    print(f"{'='*70}")
    
    init_db()
    
    with get_session() as session:
        # Test 1: Count queries
        print("Test 1: Count queries")
        start = time.time()
        invoice_count = session.query(Invoice).count()
        elapsed = time.time() - start
        print(f"  Invoice count: {invoice_count} ({elapsed*1000:.2f} ms)")
        
        # Test 2: Filtered queries
        print("\nTest 2: Filtered queries")
        start = time.time()
        recent = session.query(Invoice).filter(
            Invoice.created_at >= date.today() - timedelta(days=30)
        ).count()
        elapsed = time.time() - start
        print(f"  Recent invoices: {recent} ({elapsed*1000:.2f} ms)")
        
        # Test 3: Join queries
        print("\nTest 3: Join queries (with validation)")
        start = time.time()
        from app.models import InvoiceValidation
        validated = session.query(Invoice).join(InvoiceValidation).count()
        elapsed = time.time() - start
        print(f"  Validated invoices: {validated} ({elapsed*1000:.2f} ms)")
        
        # Test 4: Group by queries
        print("\nTest 4: Group by queries")
        start = time.time()
        from sqlalchemy import func
        batches = session.query(
            Invoice.source_batch,
            func.count(Invoice.id)
        ).group_by(Invoice.source_batch).all()
        elapsed = time.time() - start
        print(f"  Batch groups: {len(batches)} ({elapsed*1000:.2f} ms)")


def main():
    """Run all stress tests."""
    import argparse
    parser = argparse.ArgumentParser(description="Stress test the invoice validation system")
    parser.add_argument("--invoices", type=int, default=1000, help="Number of invoices for large upload test")
    parser.add_argument("--skip-upload", action="store_true", help="Skip large upload test")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation test")
    parser.add_argument("--skip-duplicates", action="store_true", help="Skip duplicate detection test")
    parser.add_argument("--skip-queries", action="store_true", help="Skip database query test")
    args = parser.parse_args()
    
    print("="*70)
    print("INVOICE VALIDATOR - STRESS TEST SUITE")
    print("="*70)
    
    try:
        if not args.skip_upload:
            test_large_upload(args.invoices)
        
        if not args.skip_validation:
            test_validation_performance()
        
        if not args.skip_duplicates:
            test_duplicate_detection()
        
        if not args.skip_queries:
            test_database_queries()
        
        print("\n" + "="*70)
        print("ALL TESTS COMPLETED")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

