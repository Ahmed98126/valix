"""PDF viewer routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import os
from pathlib import Path

from app.db import get_session
from app.auth import get_current_user, get_current_tenant
from app.config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/pdf-viewer", response_class=HTMLResponse)
async def view_pdf(
    request: Request,
    path: str = Query(...),
    current_user = Depends(get_current_user)
):
    """Display PDF viewer page."""
    # Security check - make sure the path is within the upload directory
    pdf_path = Path(path)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # For security, we'll serve the PDF through a separate endpoint
    pdf_url = f"/pdf-content?path={path}"
    
    return templates.TemplateResponse(
        "pdf_viewer.html",
        {
            "request": request,
            "pdf_url": pdf_url
        }
    )


@router.get("/pdf-content")
async def get_pdf_content(
    path: str = Query(...),
    current_user = Depends(get_current_user)
):
    """Serve PDF content."""
    # Security check - make sure the path is within the upload directory
    pdf_path = Path(path)
    
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf"
    )