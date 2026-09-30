"""Review validation results line by line and compare with Databricks SQL logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session
from app.models import Invoice, InvoiceValidation, UnitTimeline, Lease
from datetime import date

def review_invoices():
    """Review each invoice's validation result."""
    with get_session() as session:
        # Get all invoices with their validations
        invoices = session.query(Invoice).order_by(Invoice.id).all()
        
        print("="*80)
        print("INVOICE VALIDATION RESULTS - LINE BY LINE REVIEW")
        print("="*80)
        print()
        
        for invoice in invoices:
            validation = session.query(InvoiceValidation).filter(
                InvoiceValidation.invoice_id == invoice.id
            ).first()
            
            if not validation:
                print(f"❌ Invoice {invoice.invoice_number} has no validation record")
                continue
            
            # Get lease info for this unit
            leases = session.query(Lease).filter(
                Lease.unit_id == invoice.unit_id,
                Lease.tenant_id == invoice.tenant_id
            ).order_by(Lease.lease_start).all()
            
            # Get timeline periods for this unit
            timeline = session.query(UnitTimeline).filter(
                UnitTimeline.unit_id == invoice.unit_id,
                UnitTimeline.tenant_id == invoice.tenant_id
            ).order_by(UnitTimeline.period_start).all()
            
            print(f"Invoice: {invoice.invoice_number}")
            print(f"  Unit: {invoice.unit_id}")
            print(f"  Supplier: {invoice.supplier_name}")
            print(f"  Period: {invoice.billing_period_start} to {invoice.billing_period_end}")
            print(f"  Amount: £{invoice.gross_amount}")
            print()
            
            print(f"  📊 Validation Metrics:")
            print(f"     Invoice Days: {validation.invoice_days}")
            print(f"     Vacancy Overlap Days: {validation.total_vacancy_overlap_days}")
            print(f"     Daily Rate: £{validation.daily_rate:.2f}" if validation.daily_rate else "     Daily Rate: N/A")
            print()
            
            print(f"  ✅ Status: {validation.validation_status}")
            print(f"  📝 Determination: {validation.determination}")
            print()
            
            # Explain the logic
            print(f"  🔍 Logic Explanation:")
            if validation.invoice_days is None:
                print(f"     → InvoiceDays IS NULL → Status = 'Needs Review'")
            elif invoice.gross_amount < 0:
                print(f"     → GrossAmount < 0 (credit note) → Status = 'Valid'")
            elif validation.total_vacancy_overlap_days == 0:
                print(f"     → TotalOverlap = 0 (no vacancy overlap = OCCUPIED period)")
                print(f"     → Status = 'Invalid' (tenant is liable, rental company NOT liable)")
            elif validation.total_vacancy_overlap_days == validation.invoice_days:
                print(f"     → TotalOverlap = InvoiceDays (full vacancy overlap = VACANT period)")
                print(f"     → Status = 'Valid' (no tenant, rental company IS liable)")
            elif validation.total_vacancy_overlap_days > validation.invoice_days:
                print(f"     → TotalOverlap > InvoiceDays (edge case) → Status = 'Valid'")
            else:
                print(f"     → Partial overlap → Status = 'Needs Review'")
            
            # Determination logic
            print(f"  📋 Determination Logic:")
            if invoice.unit_id.endswith('00'):
                print(f"     → Unit ends in '00' → 'Landlord Supply - OK TO PAY'")
            elif invoice.vat_amount == 0:
                print(f"     → VAT = 0 → 'LPI'")
            elif validation.validation_status == 'Valid' and validation.daily_rate:
                if validation.daily_rate < 4:
                    print(f"     → Valid, Unpaid, Daily Rate < £4 → 'OK TO PAY'")
                elif 4 <= validation.daily_rate < 10:
                    print(f"     → Valid, Unpaid, Daily Rate £4-£10 → 'OK TO PAY, SUBMIT METER READING'")
                elif validation.daily_rate >= 10:
                    print(f"     → Valid, Unpaid, Daily Rate >= £10 → 'DO NOT PAY, SUBMIT METER READING'")
            elif validation.validation_status == 'Invalid':
                print(f"     → Invalid status → 'COT'")
            elif validation.validation_status == 'Needs Review':
                print(f"     → Needs Review status → 'COT'")
            
            print()
            print(f"  📅 Lease Information:")
            if leases:
                for lease in leases:
                    end_str = lease.lease_end.strftime('%Y-%m-%d') if lease.lease_end else 'Ongoing'
                    print(f"     {lease.tenant_name}: {lease.lease_start} to {end_str}")
            else:
                print(f"     No leases found for this unit")
            
            print()
            print(f"  📅 Timeline Periods:")
            if timeline:
                for period in timeline[:5]:  # Show first 5 periods
                    end_str = period.period_end.strftime('%Y-%m-%d') if period.period_end else 'Ongoing'
                    print(f"     {period.status.upper()}: {period.period_start} to {end_str}")
            else:
                print(f"     No timeline periods found")
            
            print()
            print("-"*80)
            print()

if __name__ == "__main__":
    review_invoices()

