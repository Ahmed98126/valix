"""Routes for manual review queue.

This module provides FastAPI routes for managing the manual review queue.
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Form, Query, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates

# Templates for HTML responses
templates = Jinja2Templates(directory="templates")

from app.db import get_session
from app.auth import get_current_user
from app.models import User, ManualReviewQueue, Unit
from app.manual_review import (
    get_queue_items,
    get_queue_item,
    update_queue_item_status,
    process_reviewed_invoice
)

router = APIRouter()


@router.get("/manual-review")
async def manual_review_page(
    request: Request,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Render the manual review queue page.
    """
    try:
        # Ensure user has a tenant_id for multi-tenant isolation
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Tenant not assigned")
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get queue items
        queue_items, total_count = get_queue_items(
            tenant_id=current_user.tenant_id,
            status=status,
            limit=page_size,
            offset=offset,
            session=session
        )
        
        # Get units for dropdown
        units = session.query(Unit).filter(
            Unit.tenant_id == current_user.tenant_id
        ).order_by(Unit.unit_id).all()
        
        # Calculate pagination
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1
        
        return templates.TemplateResponse("manual_review.html", {
            "request": request,
            "queue_items": queue_items,
            "total_count": total_count,
            "units": units,
            "status_filter": status,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "current_user": current_user,
            "tenant_id": current_user.tenant_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Error loading manual review queue: {str(e)}",
            "current_user": current_user
        })


@router.get("/manual-review/{queue_id}")
async def manual_review_item_page(
    request: Request,
    queue_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Render the manual review item page.
    """
    # Get queue item
    queue_item = get_queue_item(
        queue_id=queue_id,
        tenant_id=current_user.tenant_id,
        session=session
    )
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    # Parse extracted data
    extracted_data = {}
    if queue_item.extracted_data:
        try:
            extracted_data = json.loads(queue_item.extracted_data)
        except:
            pass
    
    # Parse confidence scores
    confidence_scores = {}
    if queue_item.confidence_scores:
        try:
            confidence_scores = json.loads(queue_item.confidence_scores)
        except:
            pass
    
    # Get units for dropdown
    units = session.query(Unit).filter(
        Unit.tenant_id == current_user.tenant_id
    ).order_by(Unit.unit_id).all()
    
    return {
        "request": request,
        "queue_item": queue_item,
        "extracted_data": extracted_data,
        "confidence_scores": confidence_scores,
        "units": units,
        "current_user": current_user
    }


@router.post("/manual-review/{queue_id}/update-status")
async def update_status(
    queue_id: int,
    status: str = Form(...),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update the status of a queue item.
    """
    # Check if status is valid
    if status not in ["Pending", "In Review", "Completed", "Failed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    # Update status
    queue_item = update_queue_item_status(
        queue_id=queue_id,
        tenant_id=current_user.tenant_id,
        status=status,
        user_id=current_user.id,
        notes=notes,
        session=session
    )
    
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    
    return RedirectResponse(url=f"/manual-review/{queue_id}", status_code=303)


@router.post("/manual-review/{queue_id}/process")
async def process_review(
    queue_id: int,
    invoice_number: str = Form(...),
    supplier_name: str = Form(...),
    supplier_account_number: str = Form(...),
    unit_id: str = Form(...),
    billing_period_start: str = Form(...),
    billing_period_end: str = Form(...),
    invoice_date: str = Form(...),
    gross_amount: float = Form(...),
    net_amount: Optional[float] = Form(None),
    vat_amount: Optional[float] = Form(None),
    utility_type: str = Form(...),
    currency: str = Form("GBP"),
    address: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Process a reviewed invoice.
    """
    # Parse dates
    try:
        billing_period_start_date = datetime.strptime(billing_period_start, "%Y-%m-%d").date()
        billing_period_end_date = datetime.strptime(billing_period_end, "%Y-%m-%d").date()
        invoice_date_date = datetime.strptime(invoice_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Create invoice data
    invoice_data = {
        "invoice_number": invoice_number,
        "supplier_name": supplier_name,
        "supplier_account_number": supplier_account_number,
        "unit_id": unit_id,
        "billing_period_start": billing_period_start_date,
        "billing_period_end": billing_period_end_date,
        "invoice_date": invoice_date_date,
        "gross_amount": gross_amount,
        "net_amount": net_amount,
        "vat_amount": vat_amount,
        "utility_type": utility_type,
        "currency": currency,
        "address": address
    }
    
    # Process invoice
    try:
        invoice, validation = process_reviewed_invoice(
            queue_id=queue_id,
            tenant_id=current_user.tenant_id,
            invoice_data=invoice_data,
            user_id=current_user.id,
            session=session
        )
        
        return RedirectResponse(url="/invoices", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/manual-review/{queue_id}/pdf")
async def view_pdf(
    queue_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Serve the source PDF for a manual-review queue item.

    Authorization model (two-layer):
      1. DB ownership — get_queue_item() filters by (queue_id, tenant_id).
         If the item does not belong to the current user's tenant, None is
         returned and we raise 404 without revealing existence.
      2. Defence-in-depth — _safe_pdf_path() re-validates the path from the
         DB: must be inside UPLOAD_ROOT, must be a regular file, must have a
         .pdf extension.  This guards against DB-level tampering or path
         issues on the storage layer.
    """
    # Layer 1 — tenant ownership via database lookup.
    queue_item = get_queue_item(
        queue_id=queue_id,
        tenant_id=current_user.tenant_id,
        session=session
    )

    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Layer 2 — path confinement and type check, even though the path came
    # from the database (defence-in-depth against DB compromise / corruption).
    from app.routes.pdf_viewer import _safe_pdf_path
    safe_path = _safe_pdf_path(queue_item.pdf_path)

    return FileResponse(
        path=safe_path,
        filename=queue_item.original_filename or safe_path.name,
        media_type="application/pdf"
    )