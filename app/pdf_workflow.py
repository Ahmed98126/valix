"""PDF invoice processing workflow.

This module handles the complete workflow for processing PDF invoices:
1. Extract data using Azure Document Intelligence
2. Normalize data to invoice schema
3. Map to unit using account number
4. Create invoice record
5. Run validation
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Invoice, InvoiceValidation, Unit
from app.pdf_processor import PDFProcessor
from app.pdf_normalizer import normalize_pdf_invoice
from app.enhanced_pdf_processor import process_pdf_with_enhanced_extraction
from app.manual_review import queue_for_manual_review
from app.account_mapping import get_unit_for_account
from app.validation import validate_invoice

logger = logging.getLogger(__name__)


class UnmappedInvoiceError(Exception):
    """Exception raised when an invoice cannot be mapped to a unit."""
    pass


def process_pdf_invoice(
    pdf_path: str,
    tenant_id: int,
    user_id: Optional[int] = None,
    session: Optional[Session] = None,
    use_enhanced_extraction: bool = True
) -> Dict[str, Any]:
    """
    Process PDF invoice with account mapping.
    
    Args:
        pdf_path: Path to PDF file
        tenant_id: Tenant ID for multi-tenant support
        user_id: Optional user ID who initiated the process
        session: Optional database session
        use_enhanced_extraction: Whether to use enhanced extraction (supplier-specific patterns)
    
    Returns:
        Dictionary with processing results
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        logger.info(f"Processing PDF invoice: {pdf_path}")
        
        if use_enhanced_extraction:
            # Use enhanced extraction with supplier-specific patterns
            result = process_pdf_with_enhanced_extraction(
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                queue_if_low_confidence=True,
                session=session
            )
            
            # If queued for manual review, return result
            if result["status"] == "queued":
                logger.info(f"Invoice queued for manual review: {pdf_path}")
                return result
            
            # If error, return result
            if result["status"] == "error":
                logger.error(f"Error processing invoice: {result['message']}")
                return result
            
            # Use normalized data from enhanced extraction
            normalized_data = result["normalized_data"]
            
            if not normalized_data or len(normalized_data) == 0:
                logger.warning(f"No normalized data from enhanced extraction: {os.path.basename(pdf_path)}")
                return {
                    "status": "error",
                    "message": "Failed to extract structured data from PDF",
                    "pdf_path": pdf_path
                }
            
            # Use first invoice if multiple were extracted (rare case)
            invoice_data = normalized_data[0]
            confidence_scores = result.get("confidence_scores", {})
        else:
            # Use standard extraction (original method)
            # Step 1: Extract data using Azure Document Intelligence
            processor = PDFProcessor()
            extracted_data = processor.extract_invoice(pdf_path)
            logger.info(f"Extracted data from PDF: {os.path.basename(pdf_path)}")
            
            # Step 2: Normalize data to invoice schema
            normalized_data = normalize_pdf_invoice(extracted_data)
            
            if not normalized_data or len(normalized_data) == 0:
                logger.warning(f"Failed to normalize data from PDF: {os.path.basename(pdf_path)}")
                return {
                    "status": "error",
                    "message": "Failed to extract structured data from PDF",
                    "pdf_path": pdf_path
                }
            
            # Use first invoice if multiple were extracted (rare case)
            invoice_data = normalized_data[0]
            confidence_scores = {}
        
        # Step 3: Map to unit using account number
        account_number = invoice_data.get("supplier_account_number")
        supplier_name = invoice_data.get("supplier_name")
        
        if not account_number:
            logger.warning(f"No account number found in PDF: {os.path.basename(pdf_path)}")
            
            # Queue for manual review
            queue_for_manual_review(
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                extracted_data=invoice_data,
                notes="No account number found",
                session=session
            )
            
            return {
                "status": "queued",
                "message": "No account number found in invoice, queued for manual review",
                "pdf_path": pdf_path,
                "extracted_data": invoice_data
            }
        
        # Look up unit using account mapping
        unit_id = get_unit_for_account(
            account_number=account_number,
            supplier_name=supplier_name,
            tenant_id=tenant_id,
            session=session
        )
        
        if not unit_id:
            logger.warning(f"No unit mapping found for account: {account_number}")
            return {
                "status": "unmapped",
                "message": f"No unit mapping found for account: {account_number}",
                "pdf_path": pdf_path,
                "account_number": account_number,
                "supplier_name": supplier_name,
                "extracted_data": invoice_data
            }
        
        # Step 4: Create invoice record
        # Generate batch ID if not provided
        batch_id = f"PDF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Create invoice
        invoice = Invoice(
            tenant_id=tenant_id,
            invoice_number=invoice_data.get("invoice_number"),
            supplier_name=supplier_name,
            supplier_account_number=account_number,
            unit_id=unit_id,
            address=invoice_data.get("address"),
            billing_period_start=invoice_data.get("billing_period_start"),
            billing_period_end=invoice_data.get("billing_period_end"),
            invoice_date=invoice_data.get("invoice_date"),
            gross_amount=invoice_data.get("gross_amount"),
            net_amount=invoice_data.get("net_amount"),
            vat_amount=invoice_data.get("vat_amount"),
            utility_type=invoice_data.get("utility_type"),
            currency=invoice_data.get("currency", "GBP"),
            source_batch=batch_id
        )
        
        session.add(invoice)
        session.flush()  # Get invoice.id
        
        logger.info(f"Created invoice record: {invoice.invoice_number}, unit: {unit_id}")
        
        # Step 5: Run validation
        validation = validate_invoice(session, invoice)
        session.add(validation)
        session.commit()
        
        logger.info(f"Validated invoice: {invoice.invoice_number}, status: {validation.validation_status}")
        
        return {
            "status": "success",
            "message": f"Successfully processed invoice: {invoice.invoice_number}",
            "invoice_id": invoice.id,
            "unit_id": unit_id,
            "validation_status": validation.validation_status,
            "determination": validation.determination,
            "confidence_scores": confidence_scores,
            "pdf_path": pdf_path
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF invoice: {str(e)}")
        # Rollback any changes
        session.rollback()
        return {
            "status": "error",
            "message": f"Error processing PDF invoice: {str(e)}",
            "pdf_path": pdf_path
        }
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def process_pdf_batch(
    pdf_paths: List[str],
    tenant_id: int,
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process a batch of PDF invoices.
    
    Args:
        pdf_paths: List of paths to PDF files
        tenant_id: Tenant ID for multi-tenant support
        user_id: Optional user ID who initiated the process
    
    Returns:
        Dictionary with processing results
    """
    session = SessionLocal()
    
    try:
        results = {
            "total": len(pdf_paths),
            "success": 0,
            "error": 0,
            "unmapped": 0,
            "invoices": []
        }
        
        for pdf_path in pdf_paths:
            result = process_pdf_invoice(
                pdf_path=pdf_path,
                tenant_id=tenant_id,
                user_id=user_id,
                session=session
            )
            
            results["invoices"].append(result)
            
            if result["status"] == "success":
                results["success"] += 1
            elif result["status"] == "unmapped":
                results["unmapped"] += 1
            else:
                results["error"] += 1
        
        return results
    
    finally:
        session.close()


class UnmappedInvoiceQueue:
    """Queue for invoices that couldn't be mapped to units."""
    
    @staticmethod
    def add_to_queue(
        pdf_path: str,
        account_number: str,
        supplier_name: Optional[str],
        extracted_data: Dict[str, Any],
        tenant_id: int,
        session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Add unmapped invoice to queue for manual mapping.
        
        This is a placeholder for now. In a real implementation, you would:
        1. Create an UnmappedInvoice model
        2. Store the invoice data in the database
        3. Provide a UI for users to map these invoices
        
        Args:
            pdf_path: Path to PDF file
            account_number: Extracted account number
            supplier_name: Extracted supplier name
            extracted_data: Extracted invoice data
            tenant_id: Tenant ID
            session: Optional database session
        
        Returns:
            Dictionary with result
        """
        # This is a placeholder implementation
        # In a real implementation, you would store this in the database
        logger.warning(f"Added unmapped invoice to queue: {pdf_path}, account: {account_number}")
        
        return {
            "status": "queued",
            "message": f"Invoice queued for manual mapping: {os.path.basename(pdf_path)}",
            "pdf_path": pdf_path,
            "account_number": account_number,
            "supplier_name": supplier_name
        }