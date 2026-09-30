"""Validation engine for invoice validation.

This module implements the validation logic based on the Databricks SQL scripts:
- Duplicate detection
- Vacancy period calculation
- Invoice-vacancy overlap checking
- Validation status determination
- Final determination generation
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, case

from app.models import Invoice, Lease, Unit, UnitTimeline, InvoiceValidation


def calculate_invoice_days(invoice: Invoice) -> Optional[int]:
    """Calculate the number of days in the invoice billing period."""
    if not invoice.billing_period_start or not invoice.billing_period_end:
        return None
    delta = invoice.billing_period_end - invoice.billing_period_start
    return delta.days + 1  # +1 to include both start and end dates


def calculate_daily_rate(invoice: Invoice) -> Optional[Decimal]:
    """Calculate daily rate: gross_amount / invoice_days."""
    invoice_days = calculate_invoice_days(invoice)
    if not invoice_days or invoice_days == 0:
        return None
    if not invoice.gross_amount:
        return None
    return Decimal(str(invoice.gross_amount)) / Decimal(str(invoice_days))


def check_date_overlap(
    start1: date, end1: date,
    start2: date, end2: Optional[date]
) -> int:
    """
    Calculate the number of overlapping days between two date ranges.
    
    Args:
        start1, end1: First date range (invoice period)
        start2, end2: Second date range (vacancy period, end2 can be None for ongoing)
    
    Returns:
        Number of overlapping days (0 if no overlap)
    """
    # If vacancy has no end date, treat it as ongoing (use invoice end date)
    if end2 is None:
        end2 = end1
    
    # Check if there's any overlap
    if end1 < start2 or start1 > end2:
        return 0
    
    # Calculate overlap
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    
    if overlap_start > overlap_end:
        return 0
    
    delta = overlap_end - overlap_start
    return delta.days + 1  # +1 to include both start and end dates


def check_duplicate_invoice(
    session: Session,
    invoice: Invoice,
    exclude_batch: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Check if an invoice is a duplicate based on invoice_number + gross_amount.
    
    Returns:
        Tuple of (is_duplicate: bool, duplicate_batch_numbers: str or None)
    """
    # Find invoices with same invoice_number and gross_amount (within same tenant)
    query = session.query(Invoice).filter(
        Invoice.invoice_number == invoice.invoice_number,
        Invoice.gross_amount == invoice.gross_amount,
        Invoice.id != invoice.id  # Exclude the current invoice
    )
    # Filter by tenant_id (duplicates only matter within same tenant)
    if invoice.tenant_id:
        query = query.filter(Invoice.tenant_id == invoice.tenant_id)
    
    if exclude_batch:
        query = query.filter(Invoice.source_batch != exclude_batch)
    
    duplicates = query.all()
    
    if not duplicates:
        return False, None
    
    # Collect batch numbers
    batch_numbers = [inv.source_batch for inv in duplicates if inv.source_batch]
    batch_numbers = list(set(batch_numbers))  # Remove duplicates
    
    if not batch_numbers:
        return True, None
    
    return True, ", ".join(batch_numbers)


def calculate_vacancy_periods(session: Session, unit_id: str, tenant_id: Optional[int] = None) -> List[UnitTimeline]:
    """
    Calculate vacancy periods for a unit based on leases.
    
    This implements the logic from the SQL:
    1. Gaps between consecutive leases
    2. Never-leased units (vacant from unit creation)
    3. Pre-first-lease vacancy (from unit creation to first lease)
    
    Returns:
        List of UnitTimeline records representing vacancy periods
    """
    # Get the unit
    unit = session.query(Unit).filter(Unit.unit_id == unit_id).first()
    if not unit:
        return []
    
    # Get all leases for this unit, ordered by start date (with tenant filtering)
    lease_query = session.query(Lease).filter(
        Lease.unit_id == unit_id
    )
    if tenant_id:
        lease_query = lease_query.filter(Lease.tenant_id == tenant_id)
    leases = lease_query.order_by(Lease.lease_start).all()
    
    vacancy_periods = []
    
    # Get unit to access tenant_id
    unit = session.query(Unit).filter(Unit.unit_id == unit_id).first()
    if not unit:
        return vacancy_periods
    
    if not leases:
        # Never-leased unit: vacant from unit creation (or a default start date)
        # Note: We don't have unit creation date in our model, so we'll use a far past date
        # In production, you'd want to add unit_start_date to the Unit model
        vacancy_start = date(2000, 1, 1)  # Default far past date
        vacancy_periods.append(UnitTimeline(
            tenant_id=tenant_id or unit.tenant_id,
            unit_id=unit_id,
            period_start=vacancy_start,
            period_end=None,  # Ongoing vacancy
            status='vacant',
            lease_id=None,
            days_in_period=None
        ))
        return vacancy_periods
    
    # Find gaps between leases
    for i in range(len(leases)):
        current_lease = leases[i]
        
        # Get the end date of current lease (if it has ended)
        if current_lease.lease_end:
            lease_end = current_lease.lease_end
            vacancy_start = lease_end + timedelta(days=1)
            
            # Check if there's a next lease
            if i + 1 < len(leases):
                next_lease = leases[i + 1]
                next_lease_start = next_lease.lease_start
                
                # If there's a gap between leases, create vacancy period
                if vacancy_start < next_lease_start:
                    vacancy_end = next_lease_start - timedelta(days=1)
                    days = (vacancy_end - vacancy_start).days + 1
                    
                    vacancy_periods.append(UnitTimeline(
                        tenant_id=tenant_id or unit.tenant_id,
                        unit_id=unit_id,
                        period_start=vacancy_start,
                        period_end=vacancy_end,
                        status='vacant',
                        lease_id=None,
                        days_in_period=days
                    ))
            else:
                # Last lease ended, vacancy continues (no end date)
                vacancy_periods.append(UnitTimeline(
                    tenant_id=tenant_id or unit.tenant_id,
                    unit_id=unit_id,
                    period_start=vacancy_start,
                    period_end=None,  # Ongoing vacancy
                    status='vacant',
                    lease_id=None,
                    days_in_period=None
                ))
    
    # Check for pre-first-lease vacancy
    first_lease = leases[0]
    # Again, we'd use unit_start_date in production
    unit_start = date(2000, 1, 1)  # Default
    
    if unit_start < first_lease.lease_start:
        vacancy_end = first_lease.lease_start - timedelta(days=1)
        days = (vacancy_end - unit_start).days + 1
        
        vacancy_periods.append(UnitTimeline(
            tenant_id=tenant_id or unit.tenant_id,
            unit_id=unit_id,
            period_start=unit_start,
            period_end=vacancy_end,
            status='vacant',
            lease_id=None,
            days_in_period=days
        ))
    
    return vacancy_periods


def check_invoice_vacancy_overlap(
    session: Session,
    invoice: Invoice
) -> Tuple[int, Optional[str]]:
    """
    Check how many days of the invoice billing period overlap with vacancy periods.
    
    Returns:
        Tuple of (total_overlap_days, error_message)
        - If unit not found, returns (0, "Unit not found")
        - If no leases exist, returns (invoice_days, "No leases found")
        - Otherwise returns (overlap_days, None)
    """
    # First, check if the unit exists
    unit = session.query(Unit).filter(Unit.unit_id == invoice.unit_id).first()
    if not unit:
        # Unit doesn't exist - can't determine liability
        # Return a special value to indicate unit not found
        return 0, f"Unit '{invoice.unit_id}' not found in database"
    
    # Get all vacancy periods for this unit
    vacancy_periods = session.query(UnitTimeline).filter(
        UnitTimeline.unit_id == invoice.unit_id,
        UnitTimeline.status == 'vacant',
        or_(
            # Vacancy period overlaps with invoice period
            and_(
                UnitTimeline.period_start <= invoice.billing_period_end,
                or_(
                    UnitTimeline.period_end >= invoice.billing_period_start,
                    UnitTimeline.period_end.is_(None)  # Ongoing vacancy
                )
            )
        )
    ).all()
    
    # Check if unit has any leases
    leases = session.query(Lease).filter(Lease.unit_id == invoice.unit_id).all()
    if not leases:
        # Unit exists but has no leases - entire period is vacancy
        # Company is liable for the full period
        invoice_days = calculate_invoice_days(invoice)
        return invoice_days if invoice_days else 0, "Unit has no leases - company liable"
    
    total_overlap = 0
    
    for vacancy in vacancy_periods:
        overlap = check_date_overlap(
            invoice.billing_period_start,
            invoice.billing_period_end,
            vacancy.period_start,
            vacancy.period_end
        )
        total_overlap += overlap
    
    return total_overlap, None


def determine_validation_status(
    invoice: Invoice,
    invoice_days: Optional[int],
    total_overlap: int,
    error_message: Optional[str] = None
) -> str:
    """
    Determine validation status based on overlap with vacancy periods.
    
    Business Logic (Commercial Real Estate Company Perspective):
    - "Invalid" = Tenant is liable (tenant should pay - outgoing COT)
    - "Valid" = Real estate company is liable (company should pay - incoming COT/vacancy)
    - "Needs Review" = Cannot determine (unit not found, no data, partial overlap)
    
    COT (Change of Tenancy) meanings:
    - Incoming COT: Unit coming back into portfolio (vacant → occupied)
    - Outgoing COT: Unit being occupied by tenant (occupied → vacant)
    
    Logic:
    - If unit not found or error: Return "Needs Review" (requires manual mapping)
    
    - total_overlap = 0: Invoice period has NO overlap with vacancy periods
      → Invoice period is fully within an active lease period
      → Tenant IS liable (tenant should pay)
      → Should be "Invalid" (outgoing COT - tenant should pay)
    
    - total_overlap = invoice_days: Invoice period FULLY overlaps with vacancy
      → Entire invoice period is during vacancy (no lease)
      → Real estate company IS liable (company should pay)
      → Should be "Valid" (incoming COT/vacancy - company should pay)
    
    - Partial overlap: Some days in lease, some in vacancy
      → Mixed liability (both tenant and company)
      → Should be "Needs Review" (COT - needs investigation)
    """
    # If there's an error (unit not found, etc.), return Needs Review
    if error_message:
        return 'Needs Review'
    
    if invoice_days is None:
        return 'Needs Review'
    
    if invoice.gross_amount and invoice.gross_amount < 0:
        return 'Valid'  # Credit note (company should claim)
    
    # If no overlap with vacancy, invoice period is fully within active lease
    # → Tenant IS liable (tenant should pay) → "Invalid" (outgoing COT)
    if total_overlap == 0:
        return 'Invalid'  # No vacancy overlap = active lease = tenant liable = outgoing COT
    
    # If full overlap with vacancy, invoice period is fully vacant (no lease)
    # → Real estate company IS liable (company should pay) → "Valid" (incoming COT/vacancy)
    if total_overlap == invoice_days:
        return 'Valid'  # Full vacancy overlap = no lease = company liable = incoming COT/vacancy
    
    if total_overlap > invoice_days:
        return 'Valid'  # Edge case (shouldn't happen, but handle it)
    
    # Partial overlap - some days in lease, some in vacancy
    # → Mixed liability (both tenant and company) → Needs Review (COT)
    return 'Needs Review'


def generate_determination(
    invoice: Invoice,
    validation_status: str,
    payment_status: Optional[str],
    daily_rate: Optional[Decimal],
    unit_id: str
) -> str:
    """
    Generate final determination based on business rules.
    
    Implements the determination logic from the SQL Final_Invoice_Payments CTE.
    """
    # Rule 1: Negative gross amount (credit note)
    if invoice.gross_amount and invoice.gross_amount < 0:
        if unit_id.endswith('00'):
            return 'Landlord Supply - OK TO CLAIM'
        return 'OK TO CLAIM'
    
    # Rule 2: Unit ending in '00' = Landlord Supply
    if unit_id.endswith('00'):
        return 'Landlord Supply - OK TO PAY'
    
    # Rule 3: Zero VAT
    if invoice.vat_amount == 0 or (invoice.vat_amount is not None and invoice.vat_amount == Decimal('0')):
        return 'LPI'
    
    # Rule 4: Valid invoice, unpaid, daily rate < £4
    if (validation_status == 'Valid' and 
        payment_status == 'Unpaid' and 
        daily_rate is not None and 
        daily_rate < 4):
        return 'OK TO PAY'
    
    # Rule 5: Valid invoice, unpaid, daily rate £4-£10
    if (validation_status == 'Valid' and 
        payment_status == 'Unpaid' and 
        daily_rate is not None and 
        4 <= daily_rate < 10):
        return 'OK TO PAY, SUBMIT METER READING'
    
    # Rule 6: Valid invoice, unpaid, daily rate >= £10
    if (validation_status == 'Valid' and 
        payment_status == 'Unpaid' and 
        daily_rate is not None and 
        daily_rate >= 10):
        return 'DO NOT PAY, SUBMIT METER READING'
    
    # Rule 7: Needs Review (partial overlap - mixed liability)
    if validation_status == 'Needs Review':
        return 'COT'  # Change of Tenancy - needs investigation (mixed liability)
    
    # Rule 8: Valid invoice, paid
    if validation_status == 'Valid' and payment_status == 'Paid':
        return 'NO ACTION'
    
    # Rule 9: Invalid invoice, unpaid (tenant is liable - outgoing COT)
    if validation_status == 'Invalid' and payment_status == 'Unpaid':
        return 'COT'  # Change of Tenancy - outgoing (tenant should pay)
    
    # Rule 10: Invalid invoice, paid
    if validation_status == 'Invalid' and payment_status == 'Paid':
        return 'CREDIT OWED'
    
    # Rule 11: Invalid invoice, part paid
    if validation_status == 'Invalid' and payment_status == 'Part Paid':
        return 'CREDIT OWED'
    
    # Rule 12: Valid invoice, part paid
    if validation_status == 'Valid' and payment_status == 'Part Paid':
        return 'Investigate Payments'
    
    # Rule 13: Needs Review, part paid
    if validation_status == 'Needs Review' and payment_status == 'Part Paid':
        return 'Investigate Payments'
    
    return 'Unknown'


def validate_invoice(
    session: Session,
    invoice: Invoice,
    payment_status: Optional[str] = None
) -> InvoiceValidation:
    """
    Run full validation on a single invoice.
    
    This is the main function that orchestrates all validation steps:
    1. Check for duplicates
    2. Calculate invoice days and daily rate
    3. Check vacancy overlap
    4. Determine validation status
    5. Generate final determination
    
    Args:
        session: Database session
        invoice: Invoice to validate
        payment_status: Optional payment status ('Paid', 'Unpaid', 'Part Paid')
    
    Returns:
        InvoiceValidation record with all validation results
    """
    # Step 1: Check for duplicates
    is_duplicate, duplicate_batch = check_duplicate_invoice(session, invoice)
    
    # Step 2: Calculate invoice days and daily rate
    invoice_days = calculate_invoice_days(invoice)
    daily_rate = calculate_daily_rate(invoice)
    
    # Step 3: Check vacancy overlap
    total_overlap, error_message = check_invoice_vacancy_overlap(session, invoice)
    
    # Step 4: Determine validation status
    validation_status = determine_validation_status(invoice, invoice_days, total_overlap, error_message)
    
    # Step 5: Generate determination (default to 'Unpaid' if not provided)
    if payment_status is None:
        payment_status = 'Unpaid'
    
    determination = generate_determination(
        invoice, validation_status, payment_status, daily_rate, invoice.unit_id
    )
    
    # Create validation record
    validation = InvoiceValidation(
        tenant_id=invoice.tenant_id,
        invoice_id=invoice.id,
        invoice_days=invoice_days,
        total_vacancy_overlap_days=total_overlap,
        validation_status=validation_status,
        duplicate_batch=duplicate_batch,
        is_duplicate='Yes' if is_duplicate else 'No',
        payment_status=payment_status,
        daily_rate=daily_rate,
        determination=determination,
        validation_notes=error_message  # Store error message if unit not found
    )
    
    return validation


def generate_unit_timeline(session: Session, unit_id: Optional[str] = None, tenant_id: Optional[int] = None) -> int:
    """
    Generate unit timeline (vacancy periods) for units.
    
    If unit_id is provided, only generates for that unit.
    If tenant_id is provided, only generates for that tenant's units.
    Otherwise, generates for all units.
    
    Returns:
        Number of timeline records created
    """
    query = session.query(Unit)
    
    if tenant_id:
        query = query.filter(Unit.tenant_id == tenant_id)
    
    if unit_id:
        query = query.filter(Unit.unit_id == unit_id)
    
    units = query.all()
    
    total_created = 0
    
    for unit in units:
        # Delete existing timeline records for this unit (with tenant filtering)
        timeline_query = session.query(UnitTimeline).filter(UnitTimeline.unit_id == unit.unit_id)
        if tenant_id:
            timeline_query = timeline_query.filter(UnitTimeline.tenant_id == tenant_id)
        timeline_query.delete()
        
        # Calculate vacancy periods
        vacancy_periods = calculate_vacancy_periods(session, unit.unit_id, tenant_id=tenant_id)
        
        # Also create occupied periods from leases (with tenant filtering)
        lease_query = session.query(Lease).filter(Lease.unit_id == unit.unit_id)
        if tenant_id:
            lease_query = lease_query.filter(Lease.tenant_id == tenant_id)
        leases = lease_query.all()
        
        for lease in leases:
            occupied_period = UnitTimeline(
                tenant_id=tenant_id or unit.tenant_id,
                unit_id=unit.unit_id,
                period_start=lease.lease_start,
                period_end=lease.lease_end,
                status='occupied',
                lease_id=lease.id,
                days_in_period=calculate_invoice_days(Invoice(
                    billing_period_start=lease.lease_start,
                    billing_period_end=lease.lease_end or date.today()
                )) if lease.lease_end else None
            )
            session.add(occupied_period)
        
        # Add vacancy periods
        for vacancy in vacancy_periods:
            session.add(vacancy)
            total_created += 1
    
    session.commit()
    return total_created

