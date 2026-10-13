"""PDF viewer routes — filesystem path access disabled.

History
-------
A previous design exposed two routes that accepted a raw filesystem path
from the browser query string and served the file directly:

    GET /pdf-viewer?path=<filesystem-path>   (HTML shell)
    GET /pdf-content?path=<filesystem-path>  (bytes)

Phase 1 (commit 732f64b) added path confinement to UPLOAD_ROOT and a .pdf
extension allow-list via _safe_pdf_path().

Phase 2 analysis found that both endpoints were dead (no active UI caller)
because the in-memory UNMAPPED_QUEUE they depended on is never populated.
Rather than re-purpose them around ManualReviewQueue, the filesystem-serving
routes have been disabled entirely to eliminate unnecessary attack surface.

Both routes now return HTTP 410 Gone.  Authentication is still checked
first so unauthenticated callers receive 401, not 410.

Active PDF serving
------------------
PDF files in the manual-review workflow are served by:

    GET /manual-review/{queue_id}/pdf   (app/routes/manual_review.py)

That route performs DB-backed tenant-ownership verification (ManualReviewQueue
filtered by queue_id + tenant_id) before calling _safe_pdf_path() for
defence-in-depth path confinement.

_safe_pdf_path() helper
-----------------------
The helper is kept here because:
  - unit tests in tests/unit/test_pdf_path_traversal.py depend on it
  - app/routes/manual_review.py imports it for defence-in-depth

Future backlog
--------------
Processed invoice → source-document persistence:
  Invoice currently has tenant_id and source_batch but no durable source
  PDF reference.  If processed invoices need source-document viewing later,
  introduce a proper persistent document reference and tenant-owned
  authorization model. Do NOT repurpose /pdf-viewer or /pdf-content for this.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import get_current_user
from app.config import UPLOAD_DIR

router = APIRouter()

# Resolve UPLOAD_DIR once at import time so symlinks in the dir itself are
# already followed.  Every candidate path is resolved against this root.
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
    Raises :class:`~fastapi.HTTPException` (400, 403, or 404) on failure.
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


_DISABLED_DETAIL = (
    "This endpoint has been removed. "
    "PDF access is provided by GET /manual-review/{queue_id}/pdf"
)


@router.get("/pdf-viewer")
async def view_pdf(
    request: Request,
    current_user=Depends(get_current_user),
):
    """Disabled — returns HTTP 410 Gone.

    Authentication is still enforced so unauthenticated callers receive 401.
    No filesystem access of any kind occurs.
    """
    raise HTTPException(status_code=410, detail=_DISABLED_DETAIL)


@router.get("/pdf-content")
async def get_pdf_content(
    request: Request,
    current_user=Depends(get_current_user),
):
    """Disabled — returns HTTP 410 Gone.

    Authentication is still enforced so unauthenticated callers receive 401.
    No filesystem access of any kind occurs.
    """
    raise HTTPException(status_code=410, detail=_DISABLED_DETAIL)
