"""Routes package for the FastAPI application."""

from fastapi import APIRouter
from app.routes.account_mappings import router as account_mappings_router
from app.routes.unmapped_invoices import router as unmapped_invoices_router
from app.routes.pdf_viewer import router as pdf_viewer_router
from app.routes.extraction_patterns import router as extraction_patterns_router
from app.routes.manual_review import router as manual_review_router

# Create main router
router = APIRouter()

# Include all route modules
router.include_router(account_mappings_router)
router.include_router(unmapped_invoices_router)
router.include_router(pdf_viewer_router)
router.include_router(extraction_patterns_router)
router.include_router(manual_review_router)