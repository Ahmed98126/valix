"""Invoice-to-Unit mapping system with confidence scoring and batch processing.

This module provides a comprehensive mapping system that:
1. Handles batch processing of multiple invoices
2. Provides confidence scoring for matches
3. Supports manual review workflow
4. Maintains audit trail of mapping decisions
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Invoice, Unit, InvoiceValidation
from app.unit_matcher import find_matching_units, auto_match_invoice_to_unit, check_unit_exists

logger = logging.getLogger(__name__)


class MappingResult:
    """Result of invoice-to-unit mapping attempt."""
    
    def __init__(
        self,
        invoice_id: int,
        invoice_number: str,
        original_unit_id: str,
        matched_unit_id: Optional[str],
        confidence_score: float,
        match_method: str,  # 'exact', 'auto', 'manual', 'none'
        error_message: Optional[str] = None
    ):
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.original_unit_id = original_unit_id
        self.matched_unit_id = matched_unit_id
        self.confidence_score = confidence_score
        self.match_method = match_method
        self.error_message = error_message
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "original_unit_id": self.original_unit_id,
            "matched_unit_id": self.matched_unit_id,
            "confidence_score": self.confidence_score,
            "match_method": self.match_method,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat()
        }


def map_invoice_to_unit(
    session: Session,
    invoice: Invoice,
    tenant_id: int,
    auto_match_threshold: float = 0.85,
    require_manual_review: bool = False
) -> MappingResult:
    """
    Map a single invoice to a unit with confidence scoring.
    
    Args:
        session: Database session
        invoice: Invoice to map
        tenant_id: Tenant ID
        auto_match_threshold: Minimum confidence for auto-matching (0.0 to 1.0)
        require_manual_review: If True, always require manual review even for high confidence
    
    Returns:
        MappingResult with match details
    """
    original_unit_id = invoice.unit_id
    
    # Step 1: Check if unit_id already exists (exact match)
    if check_unit_exists(session, invoice.unit_id, tenant_id):
        return MappingResult(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            original_unit_id=original_unit_id,
            matched_unit_id=invoice.unit_id,
            confidence_score=1.0,
            match_method="exact"
        )
    
    # Step 2: Try auto-matching by address similarity
    if not require_manual_review:
        matched_unit_id = auto_match_invoice_to_unit(
            session, invoice, tenant_id, auto_apply_threshold=auto_match_threshold
        )
        
        if matched_unit_id:
            # Get confidence score
            matches = find_matching_units(session, invoice, tenant_id, threshold=0.3)
            confidence = matches[0]["similarity_score"] if matches else 0.0
            
            return MappingResult(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                original_unit_id=original_unit_id,
                matched_unit_id=matched_unit_id,
                confidence_score=confidence,
                match_method="auto"
            )
    
    # Step 3: Find potential matches for manual review
    matches = find_matching_units(session, invoice, tenant_id, threshold=0.3)
    
    if matches:
        # Return best match but mark as requiring review
        best_match = matches[0]
        return MappingResult(
            invoice_id=invoice.id,
            invoice_number=invoice.invoice_number,
            original_unit_id=original_unit_id,
            matched_unit_id=best_match["unit_id"],
            confidence_score=best_match["similarity_score"],
            match_method="manual_review_required",
            error_message=f"Low confidence match ({best_match['similarity_score']:.0%}). Manual review recommended."
        )
    
    # No matches found
    return MappingResult(
        invoice_id=invoice.id,
        invoice_number=invoice.invoice_number,
        original_unit_id=original_unit_id,
        matched_unit_id=None,
        confidence_score=0.0,
        match_method="none",
        error_message=f"Unit '{original_unit_id}' not found and no similar units found."
    )


def batch_map_invoices(
    session: Session,
    invoice_ids: List[int],
    tenant_id: int,
    auto_apply: bool = True,
    auto_match_threshold: float = 0.85
) -> Dict[str, any]:
    """
    Batch process multiple invoices for unit mapping.
    
    Args:
        session: Database session
        invoice_ids: List of invoice IDs to process
        tenant_id: Tenant ID
        auto_apply: If True, automatically apply high-confidence matches
        auto_match_threshold: Minimum confidence for auto-matching
    
    Returns:
        Dictionary with mapping results and statistics
    """
    results = []
    stats = {
        "total": len(invoice_ids),
        "exact_matches": 0,
        "auto_matched": 0,
        "manual_review_required": 0,
        "no_match": 0,
        "errors": 0
    }
    
    invoices = session.query(Invoice).filter(
        Invoice.id.in_(invoice_ids),
        Invoice.tenant_id == tenant_id
    ).all()
    
    for invoice in invoices:
        try:
            result = map_invoice_to_unit(
                session, invoice, tenant_id,
                auto_match_threshold=auto_match_threshold,
                require_manual_review=not auto_apply
            )
            
            results.append(result)
            
            # Update statistics
            if result.match_method == "exact":
                stats["exact_matches"] += 1
            elif result.match_method == "auto":
                stats["auto_matched"] += 1
                # Apply the match
                if auto_apply:
                    invoice.unit_id = result.matched_unit_id
            elif result.match_method == "manual_review_required":
                stats["manual_review_required"] += 1
            elif result.match_method == "none":
                stats["no_match"] += 1
            
        except Exception as e:
            logger.error(f"Error mapping invoice {invoice.id}: {e}")
            stats["errors"] += 1
            results.append(MappingResult(
                invoice_id=invoice.id,
                invoice_number=invoice.invoice_number,
                original_unit_id=invoice.unit_id,
                matched_unit_id=None,
                confidence_score=0.0,
                match_method="error",
                error_message=str(e)
            ))
    
    if auto_apply:
        session.commit()
    
    return {
        "results": [r.to_dict() for r in results],
        "statistics": stats
    }


def apply_unit_mapping(
    session: Session,
    invoice_id: int,
    unit_id: str,
    tenant_id: int,
    mapped_by: Optional[str] = None,
    confidence_score: Optional[float] = None
) -> Tuple[bool, str]:
    """
    Apply a unit mapping to an invoice and re-validate.
    
    Args:
        session: Database session
        invoice_id: Invoice ID
        unit_id: Unit ID to map to
        tenant_id: Tenant ID
        mapped_by: User/System that made the mapping
        confidence_score: Confidence score of the match
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    invoice = session.query(Invoice).filter(
        Invoice.id == invoice_id,
        Invoice.tenant_id == tenant_id
    ).first()
    
    if not invoice:
        return False, "Invoice not found"
    
    # Verify unit exists
    if not check_unit_exists(session, unit_id, tenant_id):
        return False, f"Unit '{unit_id}' not found"
    
    # Update invoice
    old_unit_id = invoice.unit_id
    invoice.unit_id = unit_id
    
    # Log mapping decision (store in validation_notes or separate audit table)
    mapping_note = f"Mapped from '{old_unit_id}' to '{unit_id}'"
    if mapped_by:
        mapping_note += f" by {mapped_by}"
    if confidence_score:
        mapping_note += f" (confidence: {confidence_score:.0%})"
    
    # Re-validate invoice
    from app.validation import validate_invoice, generate_unit_timeline
    generate_unit_timeline(session, unit_id=unit_id, tenant_id=tenant_id)
    
    validation = validate_invoice(session, invoice)
    
    # Add mapping note to validation
    if validation.validation_notes:
        validation.validation_notes += f"\n{mapping_note}"
    else:
        validation.validation_notes = mapping_note
    
    # Update or create validation record
    existing = session.query(InvoiceValidation).filter(
        InvoiceValidation.invoice_id == invoice.id
    ).first()
    
    if existing:
        validation.id = existing.id
        session.merge(validation)
    else:
        session.add(validation)
    
    session.commit()
    
    return True, f"Invoice mapped to {unit_id} and re-validated"


def get_unmapped_invoices(
    session: Session,
    tenant_id: int,
    batch_id: Optional[str] = None
) -> List[Dict]:
    """
    Get invoices that need unit mapping.
    
    Returns invoices where:
    - unit_id doesn't exist in database, OR
    - validation status is "Needs Review" due to unit not found
    """
    query = session.query(Invoice).filter(Invoice.tenant_id == tenant_id)
    
    if batch_id:
        query = query.filter(Invoice.source_batch == batch_id)
    
    invoices = query.all()
    unmapped = []
    
    for invoice in invoices:
        # Check if unit exists
        unit_exists = check_unit_exists(session, invoice.unit_id, tenant_id)
        
        # Check validation status
        validation = session.query(InvoiceValidation).filter(
            InvoiceValidation.invoice_id == invoice.id
        ).first()
        
        needs_mapping = (
            not unit_exists or
            (validation and validation.validation_status == "Needs Review" and
             validation.validation_notes and "not found" in validation.validation_notes.lower())
        )
        
        if needs_mapping:
            # Get potential matches
            matches = find_matching_units(session, invoice, tenant_id, threshold=0.3)
            
            unmapped.append({
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "unit_id": invoice.unit_id,
                "address": invoice.address,
                "supplier_name": invoice.supplier_name,
                "billing_period": f"{invoice.billing_period_start} to {invoice.billing_period_end}",
                "potential_matches": matches[:5],  # Top 5 matches
                "validation_status": validation.validation_status if validation else None,
                "validation_notes": validation.validation_notes if validation else None
            })
    
    return unmapped

