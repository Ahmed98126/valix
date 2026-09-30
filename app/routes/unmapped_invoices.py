"""Unmapped invoices routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
from pathlib import Path

from app.db import get_session
from app.models import Unit
from app.auth import get_current_user, get_current_tenant
from app.account_mapping import create_account_mapping
from app.pdf_workflow import process_pdf_invoice

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# In-memory queue for unmapped invoices (in production, this would be in a database)
# This is just for demonstration purposes
UNMAPPED_QUEUE = []


@router.get("/unmapped-invoices", response_class=HTMLResponse)
async def get_unmapped_invoices(
    request: Request,
    page: int = 1,
    per_page: int = 9,  # Show 9 per page (3x3 grid)
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Display unmapped invoices page."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    # Filter queue by tenant
    tenant_queue = [item for item in UNMAPPED_QUEUE if item.get("tenant_id") == tenant_id]
    
    # Calculate pagination
    total_items = len(tenant_queue)
    total_pages = (total_items + per_page - 1) // per_page if total_items > 0 else 1
    
    # Paginate
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_items)
    current_items = tenant_queue[start_idx:end_idx] if start_idx < total_items else []
    
    # Get units for dropdown
    units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
    
    return templates.TemplateResponse(
        "unmapped_invoices.html",
        {
            "request": request,
            "unmapped_invoices": current_items,
            "units": units,
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages
        }
    )


@router.post("/unmapped-invoices/map")
async def map_invoice(
    background_tasks: BackgroundTasks,
    pdf_path: str = Form(...),
    account_number: str = Form(...),
    supplier_name: Optional[str] = Form(None),
    unit_id: str = Form(...),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Map an unmapped invoice and process it."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        # Create account mapping
        mapping = create_account_mapping(
            supplier_account_number=account_number,
            unit_id=unit_id,
            tenant_id=tenant_id,
            supplier_name=supplier_name,
            notes=notes,
            created_by_user_id=current_user.id,
            session=session
        )
        
        # Process the invoice in the background
        background_tasks.add_task(
            process_invoice_background,
            pdf_path=pdf_path,
            tenant_id=tenant_id,
            user_id=current_user.id
        )
        
        # Remove from queue
        global UNMAPPED_QUEUE
        UNMAPPED_QUEUE = [item for item in UNMAPPED_QUEUE if 
                         item.get("pdf_path") != pdf_path or 
                         item.get("tenant_id") != tenant_id]
        
        return RedirectResponse(
            url="/unmapped-invoices?message=Invoice+mapped+and+processing",
            status_code=303
        )
    except Exception as e:
        return RedirectResponse(
            url=f"/unmapped-invoices?message=Error+mapping+invoice:+{str(e)}&message_type=error",
            status_code=303
        )


def process_invoice_background(pdf_path: str, tenant_id: int, user_id: int):
    """Process invoice in background after mapping."""
    from app.db import SessionLocal
    
    session = SessionLocal()
    try:
        # Process the invoice
        result = process_pdf_invoice(
            pdf_path=pdf_path,
            tenant_id=tenant_id,
            user_id=user_id,
            session=session
        )
        
        # Log result
        if result["status"] == "success":
            print(f"Successfully processed invoice: {result['invoice_id']}")
        else:
            print(f"Failed to process invoice: {result['message']}")
    finally:
        session.close()


def add_to_unmapped_queue(
    pdf_path: str,
    account_number: str,
    supplier_name: Optional[str],
    extracted_data: dict,
    tenant_id: int
):
    """Add an unmapped invoice to the queue."""
    # In production, this would be stored in a database
    UNMAPPED_QUEUE.append({
        "pdf_path": pdf_path,
        "account_number": account_number,
        "supplier_name": supplier_name,
        "tenant_id": tenant_id,
        "invoice_number": extracted_data.get("invoice_number"),
        "invoice_date": extracted_data.get("invoice_date"),
        "address": extracted_data.get("address"),
        "gross_amount": extracted_data.get("gross_amount"),
        "currency": extracted_data.get("currency"),
        "utility_type": extracted_data.get("utility_type")
    })