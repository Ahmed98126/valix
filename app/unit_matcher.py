"""Unit matching logic for invoices.

This module provides functions to match invoices to units based on:
- Exact unit_id match
- Address similarity matching
- Manual mapping suggestions
"""

import logging
import re
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from difflib import SequenceMatcher

from app.models import Invoice, Unit

logger = logging.getLogger(__name__)


def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity score between two strings (0.0 to 1.0)."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower().strip(), str2.lower().strip()).ratio()


def find_matching_units(
    session: Session,
    invoice: Invoice,
    tenant_id: int,
    threshold: float = 0.6
) -> List[Dict]:
    """
    Find potential unit matches for an invoice based on address similarity.
    
    This matches invoices to units by comparing:
    1. Full address similarity (street, city, postcode)
    2. Postcode matching (exact match = high confidence)
    3. Street address similarity
    4. Unit ID similarity (if invoice has a unit_id)
    
    Args:
        session: Database session
        invoice: Invoice to match
        tenant_id: Tenant ID to filter units
        threshold: Minimum similarity score (0.0 to 1.0)
    
    Returns:
        List of potential unit matches with similarity scores, sorted by confidence
    """
    # Get all units for this tenant
    units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
    
    if not units:
        return []
    
    matches = []
    invoice_address = invoice.address or ""
    invoice_unit_id = invoice.unit_id or ""
    
    # Extract postcode from invoice address (UK format: AB12 3CD or AB123CD)
    invoice_postcode = None
    if invoice_address:
        postcode_match = re.search(r'([A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2})', invoice_address.upper())
        if postcode_match:
            invoice_postcode = postcode_match.group(1).strip().replace(" ", "")
    
    for unit in units:
        # Build unit address string
        unit_address_parts = []
        if unit.address_line_1:
            unit_address_parts.append(unit.address_line_1)
        if unit.address_line_2:
            unit_address_parts.append(unit.address_line_2)
        if unit.city:
            unit_address_parts.append(unit.city)
        if unit.postcode:
            unit_address_parts.append(unit.postcode)
        unit_address = ", ".join(unit_address_parts)
        
        # Extract postcode from unit address
        unit_postcode = None
        if unit.postcode:
            unit_postcode = unit.postcode.upper().replace(" ", "")
        
        # Calculate similarity scores
        address_similarity = similarity_score(invoice_address, unit_address) if invoice_address else 0.0
        unit_id_similarity = similarity_score(invoice_unit_id, unit.unit_id) if invoice_unit_id else 0.0
        
        # Postcode match bonus (if postcodes match exactly, boost confidence)
        postcode_match_bonus = 0.0
        if invoice_postcode and unit_postcode and invoice_postcode == unit_postcode:
            postcode_match_bonus = 0.2  # Boost by 20% for exact postcode match
        
        # Street address similarity (more important than full address)
        street_similarity = 0.0
        if invoice_address and unit.address_line_1:
            # Extract street from invoice address (first line before comma or newline)
            invoice_street = invoice_address.split(',')[0].split('\n')[0].strip()
            street_similarity = similarity_score(invoice_street, unit.address_line_1)
        
        # Combined score (weighted):
        # - 40% full address similarity
        # - 30% street address similarity  
        # - 20% unit_id similarity (if available)
        # - 10% postcode match bonus
        combined_score = (
            (address_similarity * 0.4) +
            (street_similarity * 0.3) +
            (unit_id_similarity * 0.2) +
            postcode_match_bonus
        )
        
        # If postcode matches exactly, ensure it's included even if score is slightly below threshold
        if postcode_match_bonus > 0:
            combined_score = max(combined_score, 0.7)  # Minimum 70% if postcode matches
        
        if combined_score >= threshold:
            matches.append({
                "unit_id": unit.unit_id,
                "building_name": unit.building_name,
                "address": unit_address,
                "similarity_score": round(combined_score, 3),
                "address_similarity": round(address_similarity, 3),
                "street_similarity": round(street_similarity, 3),
                "unit_id_similarity": round(unit_id_similarity, 3),
                "postcode_match": postcode_match_bonus > 0
            })
    
    # Sort by similarity score (highest first)
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return matches


def auto_match_invoice_to_unit(
    session: Session,
    invoice: Invoice,
    tenant_id: int,
    auto_apply_threshold: float = 0.85
) -> Optional[str]:
    """
    Automatically match invoice to unit if high confidence match found.
    
    Args:
        session: Database session
        invoice: Invoice to match
        tenant_id: Tenant ID
        auto_apply_threshold: Minimum similarity for auto-matching (default 0.85 = 85%)
    
    Returns:
        Matched unit_id if found, None otherwise
    """
    matches = find_matching_units(session, invoice, tenant_id, threshold=0.5)
    
    if not matches:
        return None
    
    # If top match has high confidence, auto-match
    top_match = matches[0]
    if top_match["similarity_score"] >= auto_apply_threshold:
        logger.info(f"Auto-matched invoice {invoice.invoice_number} to unit {top_match['unit_id']} (score: {top_match['similarity_score']})")
        return top_match["unit_id"]
    
    return None


def check_unit_exists(session: Session, unit_id: str, tenant_id: int) -> bool:
    """Check if a unit exists in the database."""
    unit = session.query(Unit).filter(
        Unit.unit_id == unit_id,
        Unit.tenant_id == tenant_id
    ).first()
    return unit is not None

