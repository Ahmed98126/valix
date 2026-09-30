"""Invoice-to-Unit Mapping Service.

This module provides a flexible, multi-strategy approach to mapping invoices to units.
Supports organization-specific mapping rules and custom configurations.

Mapping Priority (highest to lowest):
1. Exact Unit ID Match - Direct match if invoice.unit_id exists in database
2. Account Number Mapping - Custom mappings (supplier_account_number → unit_id)
3. Address Similarity Matching - Fuzzy matching based on address
4. Manual Mapping - User intervention required
"""

import logging
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from app.models import Invoice, Unit, InvoiceUnitMapping
from app.unit_matcher import find_matching_units, check_unit_exists, similarity_score

logger = logging.getLogger(__name__)


class InvoiceUnitMapper:
    """Service for mapping invoices to units using multiple strategies."""
    
    def __init__(self, session: Session, tenant_id: int):
        """Initialize mapper with database session and tenant context."""
        self.session = session
        self.tenant_id = tenant_id
    
    def map_invoice_to_unit(
        self,
        invoice: Invoice,
        extracted_unit_id: Optional[str] = None,
        auto_apply_threshold: float = 0.7
    ) -> Tuple[Optional[str], str, Dict]:
        """
        Map an invoice to a unit using priority-based strategies.
        
        Args:
            invoice: Invoice to map
            extracted_unit_id: Unit ID extracted from invoice (if any)
            auto_apply_threshold: Minimum confidence for auto-matching (0.0-1.0)
        
        Returns:
            Tuple of (matched_unit_id, mapping_method, mapping_details)
            - matched_unit_id: The matched unit_id or None
            - mapping_method: 'exact_match', 'account_mapping', 'address_match', 'manual_required'
            - mapping_details: Dict with confidence scores, alternatives, etc.
        """
        # Strategy 1: Exact Unit ID Match (highest priority)
        if extracted_unit_id and extracted_unit_id not in ["UNKNOWN", "None", "N/A", ""]:
            if check_unit_exists(self.session, extracted_unit_id, self.tenant_id):
                logger.info(f"Invoice {invoice.invoice_number}: Exact unit_id match: {extracted_unit_id}")
                return (
                    extracted_unit_id,
                    "exact_match",
                    {"confidence": 1.0, "method": "exact_unit_id"}
                )
        
        # Strategy 2: Account Number Mapping (custom mappings per tenant)
        account_mapping = self._find_account_number_mapping(invoice.supplier_account_number)
        if account_mapping:
            logger.info(f"Invoice {invoice.invoice_number}: Account number mapping: {account_mapping['unit_id']}")
            return (
                account_mapping["unit_id"],
                "account_mapping",
                {
                    "confidence": 1.0,
                    "method": "account_number_mapping",
                    "mapping_id": account_mapping["id"]
                }
            )
        
        # Strategy 3: Address Similarity Matching
        if invoice.address:
            logger.info(f"Invoice {invoice.invoice_number}: Attempting address matching with address: {invoice.address[:100]}")
            matches = find_matching_units(self.session, invoice, self.tenant_id, threshold=0.5)
            logger.info(f"Invoice {invoice.invoice_number}: Found {len(matches)} potential matches")
            if matches:
                top_match = matches[0]
                logger.info(
                    f"Invoice {invoice.invoice_number}: Top match: {top_match['unit_id']} "
                    f"(score: {top_match['similarity_score']:.0%}, address: {top_match.get('address', 'N/A')[:50]})"
                )
                if top_match["similarity_score"] >= auto_apply_threshold:
                    logger.info(
                        f"Invoice {invoice.invoice_number}: Address match: {top_match['unit_id']} "
                        f"(confidence: {top_match['similarity_score']:.0%})"
                    )
                    return (
                        top_match["unit_id"],
                        "address_match",
                        {
                            "confidence": top_match["similarity_score"],
                            "method": "address_similarity",
                            "alternatives": matches[1:3] if len(matches) > 1 else []  # Top 2 alternatives
                        }
                    )
                else:
                    # Low confidence - suggest for manual review
                    logger.warning(
                        f"Invoice {invoice.invoice_number}: Low confidence address match "
                        f"(best: {top_match['unit_id']}, score: {top_match['similarity_score']:.0%}, threshold: {auto_apply_threshold:.0%})"
                    )
                    return (
                        None,
                        "manual_required",
                        {
                            "confidence": top_match["similarity_score"],
                            "method": "address_similarity_low_confidence",
                            "suggestions": matches[:3],  # Top 3 suggestions
                            "reason": f"Best match has {top_match['similarity_score']:.0%} confidence (below {auto_apply_threshold:.0%} threshold)"
                        }
                    )
            else:
                logger.warning(f"Invoice {invoice.invoice_number}: No address matches found (threshold: 0.5)")
        else:
            logger.warning(f"Invoice {invoice.invoice_number}: No address available for matching")
        
        # Strategy 4: No match found - manual mapping required
        logger.warning(f"Invoice {invoice.invoice_number}: No unit match found - manual mapping required")
        return (
            None,
            "manual_required",
            {
                "confidence": 0.0,
                "method": "no_match",
                "reason": "No matching strategy succeeded"
            }
        )
    
    def _find_account_number_mapping(self, supplier_account_number: str) -> Optional[Dict]:
        """Find custom account number to unit_id mapping for this tenant."""
        if not supplier_account_number or supplier_account_number == "UNKNOWN":
            return None
        
        mapping = self.session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == self.tenant_id,
            InvoiceUnitMapping.supplier_account_number == supplier_account_number,
            InvoiceUnitMapping.is_active == True
        ).first()
        
        if mapping:
            return {
                "id": mapping.id,
                "unit_id": mapping.unit_id,
                "supplier_account_number": mapping.supplier_account_number,
                "supplier_name": mapping.supplier_name
            }
        
        return None
    
    def create_account_mapping(
        self,
        supplier_account_number: str,
        unit_id: str,
        supplier_name: Optional[str] = None
    ) -> InvoiceUnitMapping:
        """
        Create a custom account number to unit_id mapping.
        
        Args:
            supplier_account_number: The supplier account number
            unit_id: The unit_id to map to
            supplier_name: Optional supplier name for context
        
        Returns:
            Created InvoiceUnitMapping record
        """
        # Verify unit exists
        if not check_unit_exists(self.session, unit_id, self.tenant_id):
            raise ValueError(f"Unit {unit_id} does not exist for tenant {self.tenant_id}")
        
        # Check if mapping already exists
        existing = self.session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.tenant_id == self.tenant_id,
            InvoiceUnitMapping.supplier_account_number == supplier_account_number
        ).first()
        
        if existing:
            # Update existing mapping
            existing.unit_id = unit_id
            existing.supplier_name = supplier_name or existing.supplier_name
            existing.is_active = True
            logger.info(f"Updated account mapping: {supplier_account_number} → {unit_id}")
            return existing
        
        # Create new mapping
        mapping = InvoiceUnitMapping(
            tenant_id=self.tenant_id,
            supplier_account_number=supplier_account_number,
            unit_id=unit_id,
            supplier_name=supplier_name or "Unknown",
            is_active=True
        )
        self.session.add(mapping)
        logger.info(f"Created account mapping: {supplier_account_number} → {unit_id}")
        return mapping
    
    def get_unmapped_invoices(self) -> List[Invoice]:
        """Get all invoices that need manual mapping (unit_id is UNKNOWN or doesn't exist)."""
        invoices = self.session.query(Invoice).filter(
            Invoice.tenant_id == self.tenant_id
        ).all()
        
        unmapped = []
        for invoice in invoices:
            if not invoice.unit_id or invoice.unit_id in ["UNKNOWN", "None", "N/A", ""]:
                unmapped.append(invoice)
            elif not check_unit_exists(self.session, invoice.unit_id, self.tenant_id):
                unmapped.append(invoice)
        
        return unmapped
    
    def get_mapping_suggestions(self, invoice: Invoice, limit: int = 5) -> List[Dict]:
        """Get mapping suggestions for an invoice."""
        if invoice.address:
            matches = find_matching_units(self.session, invoice, self.tenant_id, threshold=0.3)
            return matches[:limit]
        return []

