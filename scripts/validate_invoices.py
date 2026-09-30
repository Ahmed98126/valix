"""Script to validate invoices using the validation engine.

This script:
1. Generates unit timeline (vacancy periods) from leases
2. Validates all invoices (or invoices from a specific batch)
3. Saves validation results to the database

Usage:
    python scripts/validate_invoices.py [batch_number]
    
If batch_number is provided, only validates invoices from that batch.
Otherwise, validates all invoices.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func

from app.db import get_session, init_db
from app.models import Invoice, InvoiceValidation
from app.validation import validate_invoice, generate_unit_timeline


def validate_all_invoices(batch_number: str = None):
    """
    Validate all invoices (or invoices from a specific batch).
    
    Args:
        batch_number: Optional batch number to filter invoices
    """
    # Initialize database
    init_db()
    
    with get_session() as session:
        # Step 1: Generate unit timeline for all units
        print("Generating unit timeline (vacancy periods)...")
        timeline_count = generate_unit_timeline(session)
        print(f"✓ Generated {timeline_count} vacancy periods")
        
        # Step 2: Get invoices to validate
        query = session.query(Invoice)
        if batch_number:
            query = query.filter(Invoice.source_batch == batch_number)
            print(f"\nValidating invoices from batch: {batch_number}")
        else:
            print("\nValidating all invoices...")
        
        invoices = query.all()
        total_invoices = len(invoices)
        
        if total_invoices == 0:
            print("⚠ No invoices found to validate.")
            return
        
        print(f"Found {total_invoices} invoice(s) to validate\n")
        
        # Step 3: Validate each invoice
        validated_count = 0
        errors = []
        
        for i, invoice in enumerate(invoices, 1):
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
                    action = "Updated"
                else:
                    # Create new validation
                    validation = validate_invoice(session, invoice)
                    session.add(validation)
                    action = "Created"
                
                validated_count += 1
                
                # Print progress
                status_symbol = "✓" if validation.validation_status == "Valid" else "⚠" if validation.validation_status == "Needs Review" else "✗"
                print(f"[{i}/{total_invoices}] {status_symbol} {action} validation for invoice #{invoice.invoice_number} "
                      f"(Status: {validation.validation_status}, Determination: {validation.determination})")
                
            except Exception as e:
                error_msg = f"Invoice #{invoice.invoice_number}: {str(e)}"
                errors.append(error_msg)
                print(f"[{i}/{total_invoices}] ✗ ERROR: {error_msg}")
        
        # Commit all validations
        if validated_count > 0:
            session.commit()
            print(f"\n✓ Successfully validated {validated_count} invoice(s).")
        else:
            print("\n⚠ No invoices were validated.")
        
        if errors:
            print(f"\n⚠ {len(errors)} error(s) encountered during validation.")
        
        # Print summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        summary = session.query(
            InvoiceValidation.validation_status,
            InvoiceValidation.determination,
            func.count(InvoiceValidation.id).label('count')
        ).group_by(
            InvoiceValidation.validation_status,
            InvoiceValidation.determination
        ).all()
        
        for status, determination, count in summary:
            print(f"  {status} / {determination}: {count}")


def main():
    """Main entry point for the script."""
    batch_number = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        validate_all_invoices(batch_number)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

