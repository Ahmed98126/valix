"""Batch unit matching for multiple invoices.

This module handles:
- Bulk unit matching for multiple invoices
- Confidence scoring and prioritization
- Review queue management
- Performance optimization for large batches
"""

import logging
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Invoice, Unit, InvoiceValidation
from app.unit_matcher import find_matching_units, auto_match_invoice_to_unit, check_unit_exists
from app.unit_mapping_config import apply_mapping_rules

logger = logging.getLogger(__name__)


class BatchMatchResult:
    """Result of batch unit matching."""
    def __init__(self):
        self.auto_matched: int = 0
        self.rule_matched: int = 0
        self.needs_review: int = 0
        self.exact_match: int = 0
        self.failed: int = 0
        self.matches: List[Dict] = []  # List of {invoice_id, unit_id, method, confidence}


def batch_match_invoices_to_units(
    session: Session,
    invoices: List[Invoice],
    tenant_id: int,
    auto_apply_threshold: float = 0.85,
    rule_priority: bool = True
) -> BatchMatchResult:
    """
    Match multiple invoices to units in batch.
    
    Args:
        session: Database session
        invoices: List of invoices to match
        tenant_id: Tenant ID
        auto_apply_threshold: Minimum confidence for auto-matching
        rule_priority: If True, check mapping rules before auto-matching
    
    Returns:
        BatchMatchResult with statistics
    """
    result = BatchMatchResult()
    
    # Pre-load all units for this tenant (performance optimization)
    units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
    unit_dict = {unit.unit_id: unit for unit in units}
    
    for invoice in invoices:
        try:
            # Step 1: Check if unit_id already exists (exact match)
            if invoice.unit_id and check_unit_exists(session, invoice.unit_id, tenant_id):
                result.exact_match += 1
                result.matches.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "unit_id": invoice.unit_id,
                    "method": "exact_match",
                    "confidence": 1.0
                })
                continue
            
            # Step 2: Apply mapping rules (if enabled)
            if rule_priority:
                matched_unit_id = apply_mapping_rules(session, invoice, tenant_id)
                if matched_unit_id:
                    invoice.unit_id = matched_unit_id
                    session.commit()
                    result.rule_matched += 1
                    result.matches.append({
                        "invoice_id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "unit_id": matched_unit_id,
                        "method": "mapping_rule",
                        "confidence": 1.0
                    })
                    continue
            
            # Step 3: Try auto-matching by address similarity
            matched_unit_id = auto_match_invoice_to_unit(
                session, invoice, tenant_id, auto_apply_threshold
            )
            
            if matched_unit_id:
                invoice.unit_id = matched_unit_id
                session.commit()
                result.auto_matched += 1
                
                # Get confidence score
                matches = find_matching_units(session, invoice, tenant_id, threshold=0.5)
                confidence = matches[0]["similarity_score"] if matches else 0.85
                
                result.matches.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "unit_id": matched_unit_id,
                    "method": "auto_match",
                    "confidence": confidence
                })
            else:
                # No match found - needs manual review
                result.needs_review += 1
                result.matches.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "unit_id": invoice.unit_id,
                    "method": "needs_review",
                    "confidence": 0.0,
                    "suggestions": find_matching_units(session, invoice, tenant_id, threshold=0.3)[:5]  # Top 5 suggestions
                })
        
        except Exception as e:
            logger.error(f"Error matching invoice {invoice.id}: {e}")
            result.failed += 1
    
    return result


def get_invoices_needing_review(
    session: Session,
    tenant_id: int,
    limit: Optional[int] = None
) -> List[Dict]:
    """
    Get invoices that need unit mapping review.
    
    Returns invoices where:
    - unit_id doesn't exist in database, OR
    - validation status is "Needs Review" with unit-related error
    """
    # Get all invoices for tenant
    invoices = session.query(Invoice).filter(Invoice.tenant_id == tenant_id).all()
    
    # Get all unit_ids that exist
    existing_units = {unit.unit_id for unit in session.query(Unit).filter(Unit.tenant_id == tenant_id).all()}
    
    needs_review = []
    
    for invoice in invoices:
        # Check if unit_id exists
        if invoice.unit_id not in existing_units:
            # Get validation to check for unit-related errors
            validation = session.query(InvoiceValidation).filter(
                InvoiceValidation.invoice_id == invoice.id
            ).first()
            
            error_note = validation.validation_notes if validation else None
            is_unit_error = error_note and ("not found" in error_note.lower() or "unit" in error_note.lower())
            
            if is_unit_error or not validation:
                # Get suggested matches
                from app.unit_matcher import find_matching_units
                suggestions = find_matching_units(session, invoice, tenant_id, threshold=0.3)[:5]
                
                needs_review.append({
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "current_unit_id": invoice.unit_id,
                    "address": invoice.address,
                    "supplier": invoice.supplier_name,
                    "billing_period": f"{invoice.billing_period_start} to {invoice.billing_period_end}",
                    "suggested_matches": suggestions,
                    "validation_status": validation.validation_status if validation else None,
                    "validation_notes": error_note
                })
    
    # Sort by invoice_number for easier review
    needs_review.sort(key=lambda x: x["invoice_number"])
    
    if limit:
        needs_review = needs_review[:limit]
    
    return needs_review

