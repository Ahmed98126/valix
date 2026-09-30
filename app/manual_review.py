"""Manual review queue management.

This module provides functions to manage the manual review queue for PDF invoices
that couldn't be automatically processed.
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models import ManualReviewQueue, Invoice, InvoiceValidation
from app.db import SessionLocal
from app.validation import validate_invoice

logger = logging.getLogger(__name__)


def queue_for_manual_review(
    pdf_path: str,
    tenant_id: int,
    extracted_data: Optional[Dict[str, Any]] = None,
    raw_data: Optional[Dict[str, Any]] = None,
    confidence_scores: Optional[Dict[str, float]] = None,
    original_filename: Optional[str] = None,
    notes: Optional[str] = None,
    session: Optional[Session] = None
) -> ManualReviewQueue:
    """
    Add a PDF invoice to the manual review queue.
    
    Args:
        pdf_path: Path to the PDF file
        tenant_id: Tenant ID
        extracted_data: Optional extracted data (will be stored as JSON)
        raw_data: Optional raw data from Azure (will be stored as JSON)
        confidence_scores: Optional confidence scores (will be stored as JSON)
        original_filename: Optional original filename
        notes: Optional notes
        session: Optional database session
    
    Returns:
        Created ManualReviewQueue object
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Convert data to JSON strings
        extracted_data_json = json.dumps(extracted_data) if extracted_data else None
        raw_data_json = json.dumps(raw_data) if raw_data else None
        confidence_scores_json = json.dumps(confidence_scores) if confidence_scores else None
        
        # Get original filename if not provided
        if not original_filename and pdf_path:
            original_filename = os.path.basename(pdf_path)
        
        # Create queue item
        queue_item = ManualReviewQueue(
            tenant_id=tenant_id,
            pdf_path=pdf_path,
            original_filename=original_filename,
            extracted_data=extracted_data_json,
            raw_data=raw_data_json,
            confidence_scores=confidence_scores_json,
            status="Pending",
            notes=notes
        )
        
        session.add(queue_item)
        session.commit()
        
        logger.info(f"Added PDF to manual review queue: {pdf_path}")
        return queue_item
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding to manual review queue: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def get_queue_items(
    tenant_id: int,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    session: Optional[Session] = None
) -> Tuple[List[ManualReviewQueue], int]:
    """
    Get items from the manual review queue.
    
    Args:
        tenant_id: Tenant ID
        status: Optional status filter ("Pending", "In Review", "Completed", "Failed")
        limit: Maximum number of items to return
        offset: Offset for pagination
        session: Optional database session
    
    Returns:
        Tuple of (queue_items, total_count)
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Build query - always filter by tenant_id for multi-tenant isolation
        if not tenant_id:
            logger.warning("No tenant_id provided for get_queue_items, returning empty result")
            return [], 0
            
        query = session.query(ManualReviewQueue).filter(
            ManualReviewQueue.tenant_id == tenant_id
        )
        
        # Filter by status if provided
        if status:
            query = query.filter(ManualReviewQueue.status == status)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        queue_items = query.order_by(
            desc(ManualReviewQueue.created_at)
        ).offset(offset).limit(limit).all()
        
        return queue_items, total_count
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def get_queue_item(
    queue_id: int,
    tenant_id: int,
    session: Optional[Session] = None
) -> Optional[ManualReviewQueue]:
    """
    Get a specific item from the manual review queue.
    
    Args:
        queue_id: Queue item ID
        tenant_id: Tenant ID (for security)
        session: Optional database session
    
    Returns:
        ManualReviewQueue object or None if not found
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get queue item
        queue_item = session.query(ManualReviewQueue).filter(
            ManualReviewQueue.id == queue_id,
            ManualReviewQueue.tenant_id == tenant_id
        ).first()
        
        return queue_item
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def update_queue_item_status(
    queue_id: int,
    tenant_id: int,
    status: str,
    user_id: Optional[int] = None,
    notes: Optional[str] = None,
    session: Optional[Session] = None
) -> Optional[ManualReviewQueue]:
    """
    Update the status of a queue item.
    
    Args:
        queue_id: Queue item ID
        tenant_id: Tenant ID (for security)
        status: New status ("Pending", "In Review", "Completed", "Failed")
        user_id: Optional user ID who updated the status
        notes: Optional notes
        session: Optional database session
    
    Returns:
        Updated ManualReviewQueue object or None if not found
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get queue item
        queue_item = session.query(ManualReviewQueue).filter(
            ManualReviewQueue.id == queue_id,
            ManualReviewQueue.tenant_id == tenant_id
        ).first()
        
        if not queue_item:
            return None
        
        # Update status
        queue_item.status = status
        
        # Update reviewer if provided
        if user_id:
            queue_item.reviewed_by_user_id = user_id
        
        # Update notes if provided
        if notes:
            queue_item.notes = notes
        
        # Update reviewed_at if status is "Completed" or "Failed"
        if status in ["Completed", "Failed"]:
            queue_item.reviewed_at = datetime.utcnow()
        
        session.commit()
        
        logger.info(f"Updated queue item {queue_id} status to {status}")
        return queue_item
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating queue item status: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def process_reviewed_invoice(
    queue_id: int,
    tenant_id: int,
    invoice_data: Dict[str, Any],
    user_id: int,
    session: Optional[Session] = None
) -> Tuple[Optional[Invoice], Optional[InvoiceValidation]]:
    """
    Process a manually reviewed invoice.
    
    Args:
        queue_id: Queue item ID
        tenant_id: Tenant ID
        invoice_data: Invoice data (from manual review)
        user_id: User ID who reviewed the invoice
        session: Optional database session
    
    Returns:
        Tuple of (invoice, validation) or (None, None) if failed
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get queue item
        queue_item = session.query(ManualReviewQueue).filter(
            ManualReviewQueue.id == queue_id,
            ManualReviewQueue.tenant_id == tenant_id
        ).first()
        
        if not queue_item:
            return None, None
        
        # Create invoice
        invoice = Invoice(
            tenant_id=tenant_id,
            invoice_number=invoice_data.get("invoice_number"),
            supplier_name=invoice_data.get("supplier_name"),
            supplier_account_number=invoice_data.get("supplier_account_number"),
            unit_id=invoice_data.get("unit_id"),
            address=invoice_data.get("address"),
            billing_period_start=invoice_data.get("billing_period_start"),
            billing_period_end=invoice_data.get("billing_period_end"),
            invoice_date=invoice_data.get("invoice_date"),
            gross_amount=invoice_data.get("gross_amount"),
            net_amount=invoice_data.get("net_amount"),
            vat_amount=invoice_data.get("vat_amount"),
            utility_type=invoice_data.get("utility_type"),
            currency=invoice_data.get("currency", "GBP"),
            source_batch=f"MANUAL_{datetime.now().strftime('%Y%m%d')}"
        )
        
        session.add(invoice)
        session.flush()  # Get invoice.id
        
        # Validate invoice
        validation = validate_invoice(session, invoice)
        session.add(validation)
        
        # Update queue item
        queue_item.status = "Completed"
        queue_item.reviewed_by_user_id = user_id
        queue_item.reviewed_at = datetime.utcnow()
        queue_item.notes = f"Processed by user {user_id}. Invoice ID: {invoice.id}"
        
        session.commit()
        
        logger.info(f"Processed reviewed invoice {invoice.id} from queue item {queue_id}")
        return invoice, validation
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error processing reviewed invoice: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()


def delete_queue_item(
    queue_id: int,
    tenant_id: int,
    session: Optional[Session] = None
) -> bool:
    """
    Delete a queue item.
    
    Args:
        queue_id: Queue item ID
        tenant_id: Tenant ID (for security)
        session: Optional database session
    
    Returns:
        True if deleted, False if not found
    """
    # Use provided session or create a new one
    close_session = False
    if session is None:
        session = SessionLocal()
        close_session = True
    
    try:
        # Get queue item
        queue_item = session.query(ManualReviewQueue).filter(
            ManualReviewQueue.id == queue_id,
            ManualReviewQueue.tenant_id == tenant_id
        ).first()
        
        if not queue_item:
            return False
        
        # Delete queue item
        session.delete(queue_item)
        session.commit()
        
        logger.info(f"Deleted queue item {queue_id}")
        return True
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting queue item: {str(e)}")
        raise
    
    finally:
        # Close session if we created it
        if close_session:
            session.close()