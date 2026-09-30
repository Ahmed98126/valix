"""Analyze validation results and explain determinations.

Usage:
    python scripts/analyze_validation_results.py [invoice_number]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Invoice, InvoiceValidation, UnitTimeline


def analyze_invoice(invoice_number):
    """Analyze a specific invoice's validation result."""
    init_db()
    
    with get_session() as session:
        invoice = session.query(Invoice).filter(
            Invoice.invoice_number == invoice_number
        ).first()
        
        if not invoice:
            print(f"Invoice {invoice_number} not found")
            return
        
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        if not validation:
            print(f"No validation found for {invoice_number}")
            return
        
        print("="*70)
        print(f"ANALYSIS: {invoice_number}")
        print("="*70)
        print(f"\nInvoice Details:")
        print(f"  Unit ID: {invoice.unit_id}")
        print(f"  Period: {invoice.billing_period_start} to {invoice.billing_period_end}")
        print(f"  Amount: £{invoice.gross_amount}")
        print(f"  Supplier: {invoice.supplier_name}")
        
        print(f"\nValidation Results:")
        print(f"  Status: {validation.validation_status}")
        print(f"  Determination: {validation.determination}")
        print(f"  Invoice Days: {validation.invoice_days}")
        print(f"  Vacancy Overlap Days: {validation.total_vacancy_overlap_days}")
        print(f"  Daily Rate: £{validation.daily_rate:.2f}" if validation.daily_rate else "  Daily Rate: N/A")
        print(f"  Is Duplicate: {validation.is_duplicate}")
        
        # Get unit timeline
        timelines = session.query(UnitTimeline).filter(
            UnitTimeline.unit_id == invoice.unit_id
        ).order_by(UnitTimeline.period_start).all()
        
        print(f"\nUnit Timeline for {invoice.unit_id}:")
        for timeline in timelines:
            end_str = timeline.period_end.strftime("%Y-%m-%d") if timeline.period_end else "ongoing"
            status_icon = "[OCCUPIED]" if timeline.status == "occupied" else "[VACANT]"
            print(f"  {status_icon} {timeline.status:8} | {timeline.period_start} to {end_str}")
        
        # Check if invoice period overlaps with any timeline period
        print(f"\nOverlap Analysis:")
        invoice_start = invoice.billing_period_start
        invoice_end = invoice.billing_period_end
        
        vacancy_overlaps = []
        occupied_overlaps = []
        
        for timeline in timelines:
            timeline_start = timeline.period_start
            timeline_end = timeline.period_end if timeline.period_end else invoice_end
            
            # Check if periods overlap
            if not (invoice_end < timeline_start or invoice_start > timeline_end):
                overlap_start = max(invoice_start, timeline_start)
                overlap_end = min(invoice_end, timeline_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                
                if timeline.status == "vacant":
                    vacancy_overlaps.append({
                        "period": f"{timeline_start} to {timeline_end or 'ongoing'}",
                        "days": overlap_days
                    })
                else:
                    occupied_overlaps.append({
                        "period": f"{timeline_start} to {timeline_end or 'ongoing'}",
                        "days": overlap_days
                    })
        
        if vacancy_overlaps:
            print(f"  Vacancy Overlaps:")
            for overlap in vacancy_overlaps:
                print(f"    - {overlap['period']}: {overlap['days']} days")
        
        if occupied_overlaps:
            print(f"  Occupied Overlaps:")
            for overlap in occupied_overlaps:
                print(f"    - {overlap['period']}: {overlap['days']} days")
        
        # Explain the determination
        print(f"\nExplanation:")
        print(f"  Total Vacancy Overlap: {validation.total_vacancy_overlap_days} days")
        print(f"  Invoice Days: {validation.invoice_days} days")
        
        if validation.total_vacancy_overlap_days == 0:
            print(f"  → No overlap with vacancy periods = Invoice is during OCCUPIED period")
            print(f"  → Business Logic: Unit has tenant → Rental company NOT liable → 'Invalid' ✅")
            print(f"  → Determination: Invalid + Unpaid → 'COT'")
        elif validation.total_vacancy_overlap_days == validation.invoice_days:
            print(f"  → Full overlap with vacancy = Invoice is during VACANT period")
            print(f"  → Business Logic: Unit is vacant (no tenant) → Rental company IS liable → 'Valid' ✅")
            if invoice.unit_id.endswith('00'):
                print(f"  → Unit ends in '00' → 'Landlord Supply - OK TO PAY'")
            elif validation.daily_rate:
                if validation.daily_rate < 4:
                    print(f"  → Daily rate < £4 → 'OK TO PAY'")
                elif validation.daily_rate < 10:
                    print(f"  → Daily rate £4-£10 → 'OK TO PAY, SUBMIT METER READING'")
                else:
                    print(f"  → Daily rate >= £10 → 'DO NOT PAY, SUBMIT METER READING'")
        else:
            print(f"  → Partial overlap ({validation.total_vacancy_overlap_days}/{validation.invoice_days} days)")
            print(f"  → Status Logic: Partial overlap → 'Needs Review'")
            print(f"  → Determination: Needs Review → 'COT'")
        
        print()


def analyze_all_test_invoices():
    """Analyze all TEST-* invoices."""
    init_db()
    
    with get_session() as session:
        test_invoices = session.query(Invoice).filter(
            Invoice.invoice_number.like('TEST-%')
        ).order_by(Invoice.invoice_number).all()
        
        print("="*70)
        print("VALIDATION RESULTS ANALYSIS")
        print("="*70)
        print(f"\nFound {len(test_invoices)} test invoices\n")
        
        for invoice in test_invoices:
            analyze_invoice(invoice.invoice_number)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze_invoice(sys.argv[1])
    else:
        analyze_all_test_invoices()

