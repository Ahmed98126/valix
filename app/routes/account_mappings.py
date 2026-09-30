"""Account mapping routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import pandas as pd
from pathlib import Path

from app.db import get_session
from app.models import InvoiceUnitMapping, Unit
from app.auth import get_current_user, get_current_tenant
from app.account_mapping import (
    create_account_mapping,
    get_account_mappings,
    delete_account_mapping,
    import_account_mappings,
    export_account_mappings,
    create_mapping_template
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Helper function to get unique suppliers
def get_unique_suppliers(session: Session, tenant_id: int) -> List[str]:
    """Get unique supplier names for a tenant."""
    mappings = session.query(InvoiceUnitMapping.supplier_name).filter(
        InvoiceUnitMapping.tenant_id == tenant_id,
        InvoiceUnitMapping.is_active == True,
        InvoiceUnitMapping.supplier_name != None
    ).distinct().all()
    
    return [m[0] for m in mappings if m[0]]


@router.get("/mappings", response_class=HTMLResponse)
async def get_mappings(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    supplier: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Display account mappings page."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    # Base query
    query = session.query(InvoiceUnitMapping).filter(
        InvoiceUnitMapping.tenant_id == tenant_id,
        InvoiceUnitMapping.is_active == True
    )
    
    # Apply filters
    if search:
        query = query.filter(
            InvoiceUnitMapping.supplier_account_number.ilike(f"%{search}%") |
            InvoiceUnitMapping.unit_id.ilike(f"%{search}%") |
            InvoiceUnitMapping.supplier_name.ilike(f"%{search}%")
        )
    
    if supplier:
        query = query.filter(InvoiceUnitMapping.supplier_name == supplier)
    
    # Count total
    total_items = query.count()
    total_pages = (total_items + per_page - 1) // per_page
    
    # Paginate
    mappings = query.order_by(InvoiceUnitMapping.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Get units for dropdown
    units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
    
    # Get unique suppliers for filter
    suppliers = get_unique_suppliers(session, tenant_id)
    
    return templates.TemplateResponse(
        "mappings.html",
        {
            "request": request,
            "mappings": mappings,
            "units": units,
            "suppliers": suppliers,
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "search": search,
            "supplier_filter": supplier
        }
    )


@router.post("/mappings/create")
async def create_mapping(
    request: Request,
    supplier_name: str = Form(...),
    supplier_account_number: str = Form(...),
    unit_id: str = Form(...),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Create a new account mapping."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        mapping = create_account_mapping(
            supplier_account_number=supplier_account_number,
            unit_id=unit_id,
            tenant_id=tenant_id,
            supplier_name=supplier_name,
            notes=notes,
            created_by_user_id=current_user.id,
            session=session
        )
        
        return RedirectResponse(
            url="/mappings?message=Mapping+created+successfully",
            status_code=303
        )
    except Exception as e:
        return templates.TemplateResponse(
            "mappings.html",
            {
                "request": request,
                "message": f"Error creating mapping: {str(e)}",
                "message_type": "error"
            },
            status_code=400
        )


@router.post("/mappings/update")
async def update_mapping(
    mapping_id: int = Form(...),
    supplier_name: str = Form(...),
    supplier_account_number: str = Form(...),
    unit_id: str = Form(...),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Update an existing account mapping."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        # Check if mapping exists and belongs to this tenant
        mapping = session.query(InvoiceUnitMapping).filter(
            InvoiceUnitMapping.id == mapping_id,
            InvoiceUnitMapping.tenant_id == tenant_id
        ).first()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        # Update mapping
        mapping.supplier_name = supplier_name
        mapping.supplier_account_number = supplier_account_number
        mapping.unit_id = unit_id
        mapping.notes = notes
        
        session.commit()
        
        return RedirectResponse(
            url="/mappings?message=Mapping+updated+successfully",
            status_code=303
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating mapping: {str(e)}")


@router.post("/mappings/delete")
async def delete_mapping_route(
    mapping_id: int = Form(...),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Delete an account mapping (soft delete)."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        result = delete_account_mapping(
            mapping_id=mapping_id,
            tenant_id=tenant_id,
            session=session
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        return RedirectResponse(
            url="/mappings?message=Mapping+deleted+successfully",
            status_code=303
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting mapping: {str(e)}")


@router.get("/mappings/template")
async def get_template():
    """Download account mapping template."""
    # Create temp file
    fd, path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)
    
    # Create template
    result = create_mapping_template(path)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Failed to create template")
    
    return FileResponse(
        path=path,
        filename="account_mapping_template.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/mappings/import")
async def import_mappings_route(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Import account mappings from Excel file."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        # Save uploaded file
        content = await file.read()
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        with os.fdopen(fd, 'wb') as tmp:
            tmp.write(content)
        
        # Import mappings
        result = import_account_mappings(
            file_path=path,
            tenant_id=tenant_id,
            created_by_user_id=current_user.id,
            session=session
        )
        
        # Clean up temp file
        os.unlink(path)
        
        if not result["success"]:
            return RedirectResponse(
                url=f"/mappings?message={result['message']}&message_type=error",
                status_code=303
            )
        
        return RedirectResponse(
            url=f"/mappings?message={result['message']}&message_type=success",
            status_code=303
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error importing mappings: {str(e)}")


@router.get("/mappings/export")
async def export_mappings_route(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Export account mappings to Excel file."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    try:
        # Create temp file
        fd, path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        
        # Export mappings
        result = export_account_mappings(
            tenant_id=tenant_id,
            output_path=path,
            session=session
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        return FileResponse(
            path=path,
            filename=f"account_mappings_{datetime.now().strftime('%Y%m%d')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error exporting mappings: {str(e)}")


@router.get("/api/mappings/{mapping_id}")
async def get_mapping(
    mapping_id: int,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user),
    tenant = Depends(get_current_tenant)
):
    """Get mapping details for API."""
    # Extract tenant_id from Tenant object
    tenant_id = tenant.id if tenant else None
    
    mapping = session.query(InvoiceUnitMapping).filter(
        InvoiceUnitMapping.id == mapping_id,
        InvoiceUnitMapping.tenant_id == tenant_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return {
        "id": mapping.id,
        "supplier_name": mapping.supplier_name,
        "supplier_account_number": mapping.supplier_account_number,
        "unit_id": mapping.unit_id,
        "notes": mapping.notes
    }