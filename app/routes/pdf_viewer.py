"""PDF viewer routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.auth import get_current_user
from app.config import UPLOAD_DIR

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Resolve UPLOAD_DIR once at import time so symlinks in the dir itself are
# already followed. Every candidate path is resolved against this root.
UPLOAD_ROOT: Path = Path(UPLOAD_DIR).resolve()


def _safe_pdf_path(path_str: str) -> Path:
    """Resolve *path_str* and verify it is safe to serve.

    Checks (in order):
    1. The resolved path must be inside UPLOAD_ROOT — blocks absolute paths,
       relative traversal (``../``), and symlink escapes, because
       ``Path.resolve()`` follows all symlinks before the confinement check.
    2. The path must point to an existing regular file (not a directory,
       device node, etc.).
    3. The file extension must be ``.pdf`` (case-insensitive) — prevents
       serving ``.env``, ``.db``, ``.py``, etc. even if they somehow end up
       inside the upload directory.

    Returns the resolved :class:`~pathlib.Path` on success.
    Raises :class:`~fastapi.HTTPException` (403 or 404) on failure.
    """
    try:
        # resolve() turns any path into an absolute, symlink-free path.
        resolved = Path(path_str).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path")

    # 1. Confinement: the resolved path must be inside UPLOAD_ROOT.
    try:
        resolved.relative_to(UPLOAD_ROOT)
    except ValueError:
        # Do NOT reveal which files exist outside the upload dir.
        raise HTTPException(status_code=403, detail="Access denied")

    # 2. Must be an existing regular file (not a directory, FIFO, etc.).
    if not resolved.is_file():
        raise HTTPException(status_code=404, detail="PDF not found")

    # 3. Extension must be .pdf — reject .env, .db, .py, .txt, etc.
    if resolved.suffix.lower() != ".pdf":
        raise HTTPException(status_code=403, detail="Access denied")

    return resolved


@router.get("/pdf-viewer", response_class=HTMLResponse)
async def view_pdf(
    request: Request,
    path: str = Query(...),
    current_user = Depends(get_current_user)
):
    """Display PDF viewer page."""
    # Validate path before probing the filesystem so we don't become a
    # file-existence oracle for paths outside the upload directory.
    _safe_pdf_path(path)

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
    """Serve PDF content — path must be inside the configured upload directory."""
    safe_path = _safe_pdf_path(path)

    return FileResponse(
        path=safe_path,
        media_type="application/pdf"
    )
