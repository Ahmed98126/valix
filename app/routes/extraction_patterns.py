"""Routes for managing supplier extraction patterns.

This module provides FastAPI routes for managing supplier-specific extraction patterns.
"""

import os
import tempfile
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.requests import Request
from starlette.templating import Jinja2Templates

# Templates for HTML responses
templates = Jinja2Templates(directory="templates")

from app.db import get_session
from app.auth import get_current_user
from app.models import User, SupplierExtractionPattern
from app.extraction_patterns import (
    get_supplier_patterns,
    create_supplier_pattern,
    update_supplier_pattern,
    delete_supplier_pattern,
    import_patterns_from_excel,
    export_patterns_to_excel,
    create_pattern_template
)

router = APIRouter()


@router.get("/extraction-patterns")
async def extraction_patterns_page(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Render the extraction patterns management page.
    """
    try:
        # Ensure user has a tenant_id for multi-tenant isolation
        if not current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Tenant not assigned")
            
        # Get patterns for current tenant
        patterns = session.query(SupplierExtractionPattern).filter(
            SupplierExtractionPattern.tenant_id == current_user.tenant_id
        ).order_by(
            SupplierExtractionPattern.supplier_name,
            SupplierExtractionPattern.field_name,
            SupplierExtractionPattern.priority.desc()
        ).all()
        
        # Get global patterns
        global_patterns = session.query(SupplierExtractionPattern).filter(
            SupplierExtractionPattern.tenant_id.is_(None)
        ).order_by(
            SupplierExtractionPattern.supplier_name,
            SupplierExtractionPattern.field_name,
            SupplierExtractionPattern.priority.desc()
        ).all()
        
        # Get unique supplier names
        supplier_names = set()
        for pattern in patterns + global_patterns:
            supplier_names.add(pattern.supplier_name)
        
        # Get unique field names
        field_names = set()
        for pattern in patterns + global_patterns:
            field_names.add(pattern.field_name)
        
        return templates.TemplateResponse("extraction_patterns.html", {
            "request": request,
            "patterns": patterns,
            "global_patterns": global_patterns,
            "supplier_names": sorted(supplier_names) if supplier_names else [],
            "field_names": sorted(field_names) if field_names else [],
            "pattern_types": ["regex", "xpath", "table_cell"],
            "current_user": current_user,
            "tenant_id": current_user.tenant_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error_message": f"Error loading extraction patterns: {str(e)}",
            "current_user": current_user
        })


@router.post("/extraction-patterns/create")
async def create_pattern(
    supplier_name: str = Form(...),
    field_name: str = Form(...),
    pattern_type: str = Form(...),
    pattern_value: str = Form(...),
    priority: int = Form(0),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new extraction pattern.
    """
    try:
        pattern = create_supplier_pattern(
            supplier_name=supplier_name,
            field_name=field_name,
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            tenant_id=current_user.tenant_id,
            priority=priority,
            notes=notes,
            created_by_user_id=current_user.id,
            session=session
        )
        
        return RedirectResponse(url="/extraction-patterns", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extraction-patterns/update/{pattern_id}")
async def update_pattern_route(
    pattern_id: int,
    supplier_name: str = Form(...),
    field_name: str = Form(...),
    pattern_type: str = Form(...),
    pattern_value: str = Form(...),
    priority: int = Form(0),
    is_active: bool = Form(True),
    notes: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing extraction pattern.
    """
    # Check if pattern belongs to current tenant
    pattern = session.query(SupplierExtractionPattern).filter(
        SupplierExtractionPattern.id == pattern_id,
        SupplierExtractionPattern.tenant_id == current_user.tenant_id
    ).first()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    try:
        update_supplier_pattern(
            pattern_id=pattern_id,
            supplier_name=supplier_name,
            field_name=field_name,
            pattern_type=pattern_type,
            pattern_value=pattern_value,
            priority=priority,
            is_active=is_active,
            notes=notes,
            session=session
        )
        
        return RedirectResponse(url="/extraction-patterns", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/extraction-patterns/delete/{pattern_id}")
async def delete_pattern_route(
    pattern_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an extraction pattern.
    """
    # Check if pattern belongs to current tenant
    pattern = session.query(SupplierExtractionPattern).filter(
        SupplierExtractionPattern.id == pattern_id,
        SupplierExtractionPattern.tenant_id == current_user.tenant_id
    ).first()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    try:
        delete_supplier_pattern(pattern_id, session=session)
        return RedirectResponse(url="/extraction-patterns", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/extraction-patterns/template")
async def get_pattern_template(
    current_user: User = Depends(get_current_user)
):
    """
    Download extraction pattern template.
    """
    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        
        # Create template
        result = create_pattern_template(temp_path)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file
        return FileResponse(
            path=temp_path,
            filename=f"extraction_pattern_template_{datetime.now().strftime('%Y%m%d')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extraction-patterns/import")
async def import_patterns(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Import extraction patterns from Excel file.
    """
    try:
        # Save uploaded file
        fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        # Import patterns
        result = import_patterns_from_excel(
            file_path=temp_path,
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id,
            session=session
        )
        
        # Clean up
        os.unlink(temp_path)
        
        if not result["success"]:
            return JSONResponse(
                status_code=400,
                content={"detail": result["message"], "errors": result["errors"]}
            )
        
        return RedirectResponse(url="/extraction-patterns", status_code=303)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extraction-patterns/export")
async def export_patterns(
    supplier_name: Optional[str] = Query(None),
    field_name: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Export extraction patterns to Excel file.
    """
    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
        os.close(fd)
        
        # Export patterns
        result = export_patterns_to_excel(
            output_path=temp_path,
            tenant_id=current_user.tenant_id,
            supplier_name=supplier_name,
            field_name=field_name,
            include_inactive=include_inactive,
            session=session
        )
        
        if not result["success"]:
            # Clean up
            os.unlink(temp_path)
            raise HTTPException(status_code=500, detail=result["message"])
        
        # Return file
        return FileResponse(
            path=temp_path,
            filename=f"extraction_patterns_{datetime.now().strftime('%Y%m%d')}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/extraction-patterns/{pattern_id}")
async def get_pattern(
    pattern_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get extraction pattern by ID.
    """
    # Get pattern
    pattern = session.query(SupplierExtractionPattern).filter(
        SupplierExtractionPattern.id == pattern_id,
        SupplierExtractionPattern.tenant_id == current_user.tenant_id
    ).first()
    
    if not pattern:
        # Try global pattern
        pattern = session.query(SupplierExtractionPattern).filter(
            SupplierExtractionPattern.id == pattern_id,
            SupplierExtractionPattern.tenant_id.is_(None)
        ).first()
    
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    
    return {
        "id": pattern.id,
        "supplier_name": pattern.supplier_name,
        "field_name": pattern.field_name,
        "pattern_type": pattern.pattern_type,
        "pattern_value": pattern.pattern_value,
        "priority": pattern.priority,
        "is_active": pattern.is_active,
        "notes": pattern.notes,
        "is_global": pattern.tenant_id is None
    }