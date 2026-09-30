"""Explain how a specific invoice is validated against leasing data.

Usage:
    python scripts/explain_invoice_validation.py INVOICE_NUMBER
    python scripts/explain_invoice_validation.py TEST-OCC-0001
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Invoice, InvoiceValidation, Unit, Lease, UnitTimeline
from app.validation import check_invoice_vacancy_overlap, calculate_invoice_days, calculate_daily_rate


def explain_invoice_validation(invoice_number):
    """Explain how an invoice is validated."""
    init_db()
    
    with get_session() as session:
        # Find invoice
        invoice = session.query(Invoice).filter(
            Invoice.invoice_number == invoice_number
        ).first()
        
        if not invoice:
            print(f"❌ Invoice '{invoice_number}' not found!")
            print("\nAvailable invoices:")
            invoices = session.query(Invoice).limit(10).all()
            for inv in invoices:
                print(f"  - {inv.invoice_number}")
            return
        
        # Get validation
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        if not validation:
            print(f"❌ Invoice '{invoice_number}' has not been validated yet!")
            return
        
        print("="*80)
        print(f"INVOICE VALIDATION EXPLANATION: {invoice_number}")
        print("="*80)
        
        print(f"\n📄 INVOICE DETAILS:")
        print(f"   Invoice Number: {invoice.invoice_number}")
        print(f"   Supplier: {invoice.supplier_name}")
        print(f"   Unit ID: {invoice.unit_id}")
        print(f"   Billing Period: {invoice.billing_period_start} to {invoice.billing_period_end}")
        print(f"   Gross Amount: £{invoice.gross_amount}")
        print(f"   Utility Type: {invoice.utility_type}")
        
        # Get unit
        unit = session.query(Unit).filter(Unit.unit_id == invoice.unit_id).first()
        if unit:
            print(f"\n🏢 UNIT DETAILS:")
            print(f"   Unit ID: {unit.unit_id}")
            print(f"   Building: {unit.building_name}")
            print(f"   Address: {unit.address_line_1}, {unit.city}")
            if unit.unit_id.endswith('00'):
                print(f"   ⚠️  LANDLORD SUPPLY UNIT (ends in '00')")
        
        # Get leases for this unit
        leases = session.query(Lease).filter(
            Lease.unit_id == invoice.unit_id
        ).order_by(Lease.lease_start).all()
        
        print(f"\n📋 LEASES FOR THIS UNIT ({len(leases)} total):")
        if leases:
            for i, lease in enumerate(leases, 1):
                end_date = lease.lease_end.strftime("%Y-%m-%d") if lease.lease_end else "ONGOING"
                print(f"   {i}. {lease.tenant_name}")
                print(f"      Period: {lease.lease_start} to {end_date}")
                
                # Check if invoice period overlaps with this lease
                invoice_start = invoice.billing_period_start
                invoice_end = invoice.billing_period_end
                lease_start = lease.lease_start
                lease_end = lease.lease_end if lease.lease_end else date.today()
                
                if invoice_start <= lease_end and invoice_end >= lease_start:
                    overlap_start = max(invoice_start, lease_start)
                    overlap_end = min(invoice_end, lease_end)
                    overlap_days = (overlap_end - overlap_start).days + 1
                    print(f"      ⚠️  OVERLAPS with invoice: {overlap_start} to {overlap_end} ({overlap_days} days)")
        else:
            print("   No leases (unit never leased - always vacant)")
        
        # Get timeline
        timelines = session.query(UnitTimeline).filter(
            UnitTimeline.unit_id == invoice.unit_id
        ).order_by(UnitTimeline.period_start).all()
        
        print(f"\n📅 VACANCY/OCCUPIED TIMELINE ({len(timelines)} periods):")
        invoice_start = invoice.billing_period_start
        invoice_end = invoice.billing_period_end
        
        total_overlap = 0
        for i, timeline in enumerate(timelines, 1):
            status_icon = "🟢" if timeline.status == "occupied" else "🔴"
            end_date = timeline.period_end.strftime("%Y-%m-%d") if timeline.period_end else "ONGOING"
            
            # Check overlap
            period_start = timeline.period_start
            period_end = timeline.period_end if timeline.period_end else date.today()
            
            if invoice_start <= period_end and invoice_end >= period_start:
                overlap_start = max(invoice_start, period_start)
                overlap_end = min(invoice_end, period_end)
                overlap_days = (overlap_end - overlap_start).days + 1
                
                if timeline.status == "vacant":
                    total_overlap += overlap_days
                    print(f"   {i}. {status_icon} {timeline.status.upper()}: {period_start} to {end_date}")
                    print(f"      ✅ OVERLAPS with invoice: {overlap_start} to {overlap_end} ({overlap_days} days) ← VACANCY")
                else:
                    print(f"   {i}. {status_icon} {timeline.status.upper()}: {period_start} to {end_date}")
                    print(f"      ❌ OVERLAPS with invoice: {overlap_start} to {overlap_end} ({overlap_days} days) ← OCCUPIED")
            else:
                print(f"   {i}. {status_icon} {timeline.status.upper()}: {period_start} to {end_date} (no overlap)")
        
        # Validation calculation
        print(f"\n🔍 VALIDATION CALCULATION:")
        invoice_days = validation.invoice_days
        print(f"   Invoice Days: {invoice_days} days")
        print(f"   Total Vacancy Overlap: {validation.total_vacancy_overlap_days} days")
        print(f"   Daily Rate: £{validation.daily_rate:.2f}/day" if validation.daily_rate else "   Daily Rate: N/A")
        
        # Status explanation
        print(f"\n📊 STATUS DETERMINATION:")
        print(f"   Result: {validation.validation_status}")
        if validation.total_vacancy_overlap_days == 0:
            print(f"   Reason: No overlap with vacancy (0 days) → Invalid")
            print(f"   Meaning: Invoice period is during OCCUPIED period → Tenant is liable")
        elif validation.total_vacancy_overlap_days == invoice_days:
            print(f"   Reason: Full overlap with vacancy ({validation.total_vacancy_overlap_days} days = {invoice_days} days) → Valid")
            print(f"   Meaning: Invoice period is during VACANT period → Landlord is liable")
        elif 0 < validation.total_vacancy_overlap_days < invoice_days:
            print(f"   Reason: Partial overlap ({validation.total_vacancy_overlap_days} days out of {invoice_days} days) → Needs Review")
            print(f"   Meaning: Invoice period spans both occupied and vacant periods")
        else:
            print(f"   Reason: Edge case (overlap > invoice days)")
        
        # Determination explanation
        print(f"\n✅ FINAL DETERMINATION:")
        print(f"   Result: {validation.determination}")
        
        if invoice.unit_id.endswith('00'):
            print(f"   Reason: Unit ends in '00' → Always 'Landlord Supply - OK TO PAY'")
            print(f"   Note: This rule overrides status and daily rate")
        elif validation.validation_status == 'Valid':
            if validation.daily_rate:
                if validation.daily_rate < 4:
                    print(f"   Reason: Valid + Daily Rate < £4 (£{validation.daily_rate:.2f}) → 'OK TO PAY'")
                elif 4 <= validation.daily_rate < 10:
                    print(f"   Reason: Valid + Daily Rate £4-£10 (£{validation.daily_rate:.2f}) → 'OK TO PAY, SUBMIT METER READING'")
                else:
                    print(f"   Reason: Valid + Daily Rate >= £10 (£{validation.daily_rate:.2f}) → 'DO NOT PAY, SUBMIT METER READING'")
        elif validation.validation_status == 'Invalid':
            print(f"   Reason: Invalid status → 'COT' (Check on This)")
        elif validation.validation_status == 'Needs Review':
            print(f"   Reason: Needs Review status → 'COT' (Check on This)")
        
        print("\n" + "="*80)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/explain_invoice_validation.py INVOICE_NUMBER")
        print("Example: python scripts/explain_invoice_validation.py TEST-OCC-0001")
        sys.exit(1)
    
    invoice_number = sys.argv[1]
    
    try:
        explain_invoice_validation(invoice_number)
    except Exception as e:
        print(f"\nERROR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()


